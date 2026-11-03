"""Resume document parsing service using PyMuPDF and python-docx.

Handles in-memory parsing, strict signature verification, corrupt document handling,
scanned PDF detection (OCR notice), and safe metadata generation without storing files.
"""

import io
import logging
import os
import re
import zipfile
from typing import Optional, Tuple

import docx
import pymupdf

from app.config import settings
from app.schemas.resume import DocumentMetadata, ResumeParseResponse

logger = logging.getLogger("skillgraph.resume_parser")


class ResumeParserError(Exception):
    """Base exception for resume parsing errors."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class UnsupportedFileTypeError(ResumeParserError):
    """Raised when file signature or extension is not a supported PDF or DOCX."""

    def __init__(self, message: str = "Unsupported file type. Only PDF and DOCX files are supported."):
        super().__init__(message, status_code=415)


class FileTooLargeError(ResumeParserError):
    """Raised when file exceeds the maximum allowed upload size."""

    def __init__(self, message: str):
        super().__init__(message, status_code=413)


class EmptyFileError(ResumeParserError):
    """Raised when uploaded file contains zero bytes."""

    def __init__(self, message: str = "Uploaded file is empty (0 bytes)."):
        super().__init__(message, status_code=400)


class CorruptDocumentError(ResumeParserError):
    """Raised when file cannot be parsed due to corrupt data or invalid internal structure."""

    def __init__(self, message: str = "The document appears to be corrupt or unreadable."):
        super().__init__(message, status_code=422)


def sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize filename to prevent path traversal or special character injection."""
    if not filename:
        return "unnamed_resume"
    # Extract basename and strip dangerous characters
    cleaned = re.sub(r"[^\w\s\.-]", "_", filename.strip())
    return cleaned[:120] or "unnamed_resume"


def detect_file_type(content: bytes, filename: str) -> str:
    """Validate file type by checking file extension first, then verifying magic bytes.

    Returns:
        'pdf' or 'docx'

    Raises:
        UnsupportedFileTypeError: If extension is not PDF/DOCX, or if file signature
                                does not match a valid document for that extension.
        CorruptDocumentError: If ZIP structure for DOCX is malformed.
    """
    ext = os.path.splitext(filename.lower())[1] if filename else ""

    # 1. Check file extension first
    if ext not in [".pdf", ".docx"]:
        raise UnsupportedFileTypeError(
            f"Unsupported file type '{ext or 'unknown'}'. Only PDF and DOCX files are supported."
        )

    # 2. For supported extensions, validate actual file signature/content
    if ext == ".pdf":
        if b"%PDF-" in content[:1024]:
            return "pdf"
        raise UnsupportedFileTypeError(
            "File signature does not match a valid PDF document. Files must be genuine PDF documents."
        )

    if ext == ".docx":
        if (
            content.startswith(b"PK\x03\x04")
            or content.startswith(b"PK\x05\x06")
            or content.startswith(b"PK\x07\x08")
        ):
            try:
                with zipfile.ZipFile(io.BytesIO(content)) as z:
                    namelist = z.namelist()
                    if "word/document.xml" in namelist or "[Content_Types].xml" in namelist:
                        return "docx"
            except zipfile.BadZipFile:
                raise CorruptDocumentError("The DOCX document is corrupt or has an invalid ZIP structure.")
            except Exception as exc:
                raise CorruptDocumentError(f"Unable to read DOCX package: {str(exc)}")

        raise UnsupportedFileTypeError(
            "File signature does not match a valid DOCX document. Files must be genuine DOCX documents."
        )

    raise UnsupportedFileTypeError("Unsupported file type. Only PDF and DOCX files are supported.")


def extract_text_from_pdf(content: bytes) -> Tuple[str, int, bool]:
    """Extract plain text from PDF bytes using modern PyMuPDF (pymupdf).

    Returns:
        Tuple of (extracted_text, page_count, requires_ocr)

    Raises:
        CorruptDocumentError: If document cannot be opened or parsed.
    """
    try:
        doc = pymupdf.open(stream=content, filetype="pdf")
    except Exception as exc:
        logger.warning("Failed to open PDF document: %s", type(exc).__name__)
        raise CorruptDocumentError("Failed to parse PDF document. File may be corrupted or password-protected.")

    try:
        page_count = len(doc)
        if page_count == 0:
            return "", 0, False

        text_parts = []
        has_images = False

        for page in doc:
            page_text = page.get_text()
            if page_text:
                text_parts.append(page_text)
            # Detect whether page has embedded raster images
            images = page.get_images()
            if images and len(images) > 0:
                has_images = True

        full_text = "\n\n".join(text_parts).strip()

        # If text is virtually empty but pages contain images, it's likely a scanned PDF
        requires_ocr = False
        if len(full_text) < settings.MIN_TEXT_LENGTH_THRESHOLD and has_images:
            requires_ocr = True

        return full_text, page_count, requires_ocr
    except Exception as exc:
        if isinstance(exc, ResumeParserError):
            raise
        logger.warning("Error while extracting PDF text: %s", type(exc).__name__)
        raise CorruptDocumentError("An error occurred while reading the PDF content.")
    finally:
        doc.close()


def extract_text_from_docx(content: bytes) -> Tuple[str, int]:
    """Extract plain text from DOCX bytes using python-docx.

    Returns:
        Tuple of (extracted_text, paragraph_count)

    Raises:
        CorruptDocumentError: If document structure is corrupt or unreadable.
    """
    try:
        doc = docx.Document(io.BytesIO(content))
    except Exception as exc:
        logger.warning("Failed to open DOCX document: %s", type(exc).__name__)
        raise CorruptDocumentError("Failed to parse DOCX document. File may be corrupted.")

    try:
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        paragraph_count = len(doc.paragraphs)

        # Also extract text from any tables embedded in the resume
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)

        full_text = "\n\n".join(paragraphs).strip()
        return full_text, paragraph_count
    except Exception as exc:
        logger.warning("Error while extracting DOCX text: %s", type(exc).__name__)
        raise CorruptDocumentError("An error occurred while reading DOCX content.")


def parse_resume_bytes(content: bytes, original_filename: Optional[str] = None) -> ResumeParseResponse:
    """Validate, inspect signatures, and extract plain text and safe metadata in memory.

    Does NOT persist uploaded resumes or log sensitive contents.
    """
    file_size = len(content)

    # 1. Size validation
    if file_size == 0:
        raise EmptyFileError("Uploaded file is empty (0 bytes).")

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise FileTooLargeError(f"File size ({file_size} bytes) exceeds the maximum allowed limit of {max_mb} MB.")

    safe_name = sanitize_filename(original_filename)

    # 2. File type detection via extension and magic bytes
    file_type = detect_file_type(content, safe_name)

    # 3. Text extraction
    page_count: Optional[int] = None
    paragraph_count: Optional[int] = None
    requires_ocr = False

    if file_type == "pdf":
        extracted_text, page_count, requires_ocr = extract_text_from_pdf(content)
    elif file_type == "docx":
        extracted_text, paragraph_count = extract_text_from_docx(content)
    else:
        raise UnsupportedFileTypeError()

    clean_text = extracted_text.strip()
    char_count = len(clean_text)
    word_count = len(clean_text.split()) if clean_text else 0
    is_empty_or_whitespace = char_count < settings.MIN_TEXT_LENGTH_THRESHOLD

    # Determine informative user status message
    if requires_ocr:
        message = (
            "This document appears to be a scanned or image-based PDF. "
            "Text extraction requires Optical Character Recognition (OCR), "
            "which is not currently enabled."
        )
        success = False
    elif is_empty_or_whitespace:
        message = (
            "The document was processed, but little to no readable text was found. "
            "Please ensure the resume contains selectable text."
        )
        success = False
    else:
        message = f"Resume parsed successfully ({word_count} words extracted)."
        success = True

    # 4. Construct safe metadata (NO sensitive resume text is logged)
    metadata = DocumentMetadata(
        filename=safe_name,
        file_type=file_type,
        file_size_bytes=file_size,
        page_count=page_count,
        paragraph_count=paragraph_count,
        word_count=word_count,
        character_count=char_count,
        requires_ocr=requires_ocr,
        is_empty_or_whitespace=is_empty_or_whitespace,
    )

    # Safe structured logging: only high-level metrics, never user content
    logger.info(
        "Parsed resume: filename=%s, size=%d bytes, type=%s, pages=%s, words=%d, ocr=%s",
        metadata.filename,
        metadata.file_size_bytes,
        metadata.file_type,
        metadata.page_count,
        metadata.word_count,
        metadata.requires_ocr,
    )

    return ResumeParseResponse(
        success=success,
        message=message,
        text=clean_text,
        metadata=metadata,
    )
