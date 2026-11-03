"""Resume parsing API endpoint."""

import logging
from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.schemas.resume import ResumeParseResponse
from app.services.resume_parser import (
    CorruptDocumentError,
    EmptyFileError,
    FileTooLargeError,
    ResumeParserError,
    UnsupportedFileTypeError,
    parse_resume_bytes,
)

logger = logging.getLogger("skillgraph.api.resume")

router = APIRouter(prefix="/api/resume", tags=["Resume"])


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse Resume Document",
    description="Upload a PDF or DOCX resume to extract plain text and safe metadata in memory.",
)
async def parse_resume(file: UploadFile = File(..., description="Resume file (PDF or DOCX)")) -> ResumeParseResponse:
    """Accept and parse a PDF or DOCX resume in memory.

    Validates file signature, size, and structure. Does not store files permanently
    or log sensitive candidate information.
    """
    try:
        content = await file.read()
        return parse_resume_bytes(content=content, original_filename=file.filename)
    except UnsupportedFileTypeError as exc:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=exc.message,
        )
    except FileTooLargeError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=exc.message,
        )
    except EmptyFileError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )
    except CorruptDocumentError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.message,
        )
    except ResumeParserError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=exc.message,
        )
    except Exception as exc:
        logger.error("Unexpected error parsing resume: %s", type(exc).__name__, exc_info=False)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the resume document.",
        )

