"""Resume parsing and authenticated management API endpoints."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resume import ResumeRecord
from app.models.user import User
from app.schemas.resume import ResumeParseResponse
from app.services.auth import get_current_user, get_optional_current_user
from app.services.resume_parser import (
    CorruptDocumentError,
    EmptyFileError,
    FileTooLargeError,
    ResumeParserError,
    UnsupportedFileTypeError,
    parse_resume_bytes,
)
from app.services.skill_extractor import extract_skills

logger = logging.getLogger("skillgraph.api.resume")

router = APIRouter(tags=["Resume"])


@router.post(
    "/api/resume/parse",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    summary="Parse Resume Document",
    description="Upload a PDF or DOCX resume to extract plain text and safe metadata. Persists record if authenticated.",
)
@router.post(
    "/resume/upload",
    response_model=ResumeParseResponse,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def parse_resume(
    file: UploadFile = File(..., description="Resume file (PDF or DOCX)"),
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ResumeParseResponse:
    """Accept and parse a PDF or DOCX resume in memory.

    Validates file signature, size, and structure.
    If the caller is authenticated, persists the extracted metadata and text.
    """
    try:
        content = await file.read()
        parsed = parse_resume_bytes(content=content, original_filename=file.filename)

        if current_user and parsed.success and parsed.text:
            try:
                extracted = extract_skills(parsed.text)
                extracted_json = json.dumps([s.model_dump() for s in extracted])
                record = ResumeRecord(
                    user_id=current_user.id,
                    filename=parsed.metadata.filename,
                    file_type=parsed.metadata.file_type,
                    file_size_bytes=parsed.metadata.file_size_bytes,
                    extracted_text=parsed.text,
                    extracted_skills_json=extracted_json,
                )
                db.add(record)
                db.commit()
                db.refresh(record)
                logger.info("Persisted ResumeRecord ID %s for User ID %s", record.id, current_user.id)
            except Exception as exc:
                logger.warning("Failed to persist ResumeRecord: %s", exc)
                db.rollback()

        return parsed
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


@router.get(
    "/api/resume/records",
    status_code=status.HTTP_200_OK,
    summary="List Authenticated User's Saved Resumes",
)
async def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all active resume records owned by the authenticated user."""
    records = (
        db.query(ResumeRecord)
        .filter(ResumeRecord.user_id == current_user.id, ResumeRecord.is_deleted == False)
        .order_by(ResumeRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "filename": r.filename,
            "file_type": r.file_type,
            "file_size_bytes": r.file_size_bytes,
            "extracted_skills_count": len(r.get_extracted_skills()),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get(
    "/api/resume/records/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Specific Resume Record",
)
async def get_resume_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve specific resume content and metadata.

    Enforces strict ownership check (IDOR protection).
    """
    record = (
        db.query(ResumeRecord)
        .filter(ResumeRecord.id == record_id, ResumeRecord.is_deleted == False)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this resume record.",
        )

    return {
        "id": record.id,
        "filename": record.filename,
        "file_type": record.file_type,
        "file_size_bytes": record.file_size_bytes,
        "extracted_text": record.extracted_text,
        "extracted_skills": record.get_extracted_skills(),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.delete(
    "/api/resume/records/{record_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Resume Record",
)
async def delete_resume_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a resume record owned by the authenticated user.

    Enforces strict ownership check (IDOR protection).
    """
    record = (
        db.query(ResumeRecord)
        .filter(ResumeRecord.id == record_id, ResumeRecord.is_deleted == False)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this resume record.",
        )

    db.delete(record)
    db.commit()
    return {"ok": True, "message": f"Resume record {record_id} permanently deleted."}
