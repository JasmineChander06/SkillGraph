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
from app.schemas.resume import ResumeParseResponse, UpdateSkillsRequest
from app.schemas.resume_advisor import ResumeCritiqueRequest, ResumeCritiqueResponse
from app.services.auth import get_current_user, get_optional_current_user
from app.services.resume_advisor import critique_resume_text
from app.services.resume_parser import (
    CorruptDocumentError,
    EmptyFileError,
    FileTooLargeError,
    ResumeParserError,
    UnsupportedFileTypeError,
    parse_resume_bytes,
)
from app.services.skill_extractor import extract_skills, get_skill_meta

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

    raw_skills = record.get_extracted_skills()
    clean_skills = [
        (s.get("canonical_name") or s.get("name") or s.get("skill_id") or "")
        if isinstance(s, dict) else str(s)
        for s in raw_skills
    ]
    return {
        "id": record.id,
        "filename": record.filename,
        "file_type": record.file_type,
        "file_size_bytes": record.file_size_bytes,
        "extracted_text": record.extracted_text,
        "extracted_skills": clean_skills,
        "extracted_skills_detail": raw_skills,
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


@router.put(
    "/api/resume/records/{record_id}/skills",
    status_code=status.HTTP_200_OK,
    summary="Update Confirmed Skills on Specific Resume",
)
async def update_resume_skills(
    record_id: int,
    payload: UpdateSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Save user-confirmed or corrected skills to a specific resume record."""
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

    enriched = []
    for s in payload.skills:
        clean = s.strip().lower()
        meta = get_skill_meta(clean)
        enriched.append({
            "skill_id": clean,
            "canonical_name": meta.get("canonical", s.strip()),
            "category": meta.get("category", "General"),
            "matched_via": "user_confirmed",
        })
    record.set_extracted_skills(enriched)
    db.commit()
    db.refresh(record)
    return {
        "ok": True,
        "resume_id": record.id,
        "skills_count": len(enriched),
        "skills": enriched,
    }


@router.put(
    "/api/resume/skills",
    status_code=status.HTTP_200_OK,
    summary="Update Confirmed Skills on Latest Resume",
)
async def update_latest_resume_skills(
    payload: UpdateSkillsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Save user-confirmed or corrected skills to the user's latest resume record."""
    latest = (
        db.query(ResumeRecord)
        .filter(ResumeRecord.user_id == current_user.id, ResumeRecord.is_deleted == False)
        .order_by(ResumeRecord.id.desc())
        .first()
    )
    if not latest:
        latest = ResumeRecord(
            user_id=current_user.id,
            filename="Confirmed Skills Profile",
            file_type="manual",
            file_size_bytes=0,
            extracted_text=" ".join(payload.skills),
        )
        db.add(latest)
        db.flush()

    enriched = []
    for s in payload.skills:
        clean = s.strip().lower()
        meta = get_skill_meta(clean)
        enriched.append({
            "skill_id": clean,
            "canonical_name": meta.get("canonical", s.strip()),
            "category": meta.get("category", "General"),
            "matched_via": "user_confirmed",
        })
    latest.set_extracted_skills(enriched)
    db.commit()
    db.refresh(latest)
    return {
        "ok": True,
        "resume_id": latest.id,
        "skills_count": len(enriched),
        "skills": enriched,
    }


@router.post(
    "/api/resume/critique",
    response_model=ResumeCritiqueResponse,
    status_code=status.HTTP_200_OK,
    summary="Critique and Rate Resume",
    description="Analyze resume text or saved resume ID for quantification, action verbs, keyword density, and fluff elimination.",
)
async def critique_resume(
    payload: ResumeCritiqueRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ResumeCritiqueResponse:
    """Audit resume text, provide a score from 0-100, suggest things to add/remove, and Google XYZ bullet rewrites."""
    text_to_analyze = payload.text

    if not text_to_analyze and payload.resume_id:
        record = (
            db.query(ResumeRecord)
            .filter(ResumeRecord.id == payload.resume_id, ResumeRecord.is_deleted == False)
            .first()
        )
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Specified resume record not found.")
        if current_user and record.user_id and record.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied: you do not own this resume.")
        text_to_analyze = record.extracted_text

    if not text_to_analyze and current_user:
        latest = (
            db.query(ResumeRecord)
            .filter(ResumeRecord.user_id == current_user.id, ResumeRecord.is_deleted == False)
            .order_by(ResumeRecord.id.desc())
            .first()
        )
        if latest:
            text_to_analyze = latest.extracted_text

    if not text_to_analyze:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide resume text or specify a valid resume_id to critique.",
        )

    # Resolve target role: from payload, or from user profile
    target_role = payload.target_role
    if not target_role and current_user:
        target_role = current_user.target_role

    return critique_resume_text(text_to_analyze, target_role_id=target_role)

