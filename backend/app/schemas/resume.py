"""Pydantic schemas for resume parsing requests and responses."""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    """Safe document metadata without storing or leaking sensitive file contents."""

    filename: str = Field(..., description="Sanitized original document filename")
    file_type: str = Field(..., description="Detected document format: 'pdf' or 'docx'")
    file_size_bytes: int = Field(..., ge=0, description="Size of the uploaded file in bytes")
    page_count: Optional[int] = Field(None, description="Total pages extracted (PDF only)")
    paragraph_count: Optional[int] = Field(None, description="Total paragraphs extracted (DOCX only)")
    word_count: int = Field(..., ge=0, description="Estimated total word count")
    character_count: int = Field(..., ge=0, description="Total characters in extracted text")
    requires_ocr: bool = Field(
        False,
        description="True if the PDF appears to be a scanned or image-based document requiring OCR",
    )
    is_empty_or_whitespace: bool = Field(
        False,
        description="True if the document contains no meaningful text",
    )


class ResumeParseResponse(BaseModel):
    """Structured JSON response returned by the resume parsing endpoint."""

    success: bool = Field(..., description="Indicates whether text was successfully parsed")
    message: str = Field(..., description="Informative status message or guidance")
    text: str = Field(default="", description="Extracted plain text from the document")
    metadata: DocumentMetadata = Field(..., description="Safe document metadata")
    skills: List[str] = Field(default_factory=list, description="Extracted technical skill identifiers")
    categorized_skills: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Skills grouped by category (Language, Framework, Database, Cloud/DevOps, Tools, AI/ML)",
    )
    sections: Dict[str, str] = Field(
        default_factory=dict,
        description="Detected resume sections (experience, education, projects, certifications, skills)",
    )


class UpdateSkillsRequest(BaseModel):
    """Payload to update confirmed skills for a resume."""

    skills: List[str] = Field(..., description="List of confirmed skill names or IDs")

