"""Skills API — endpoint for skill-gap analysis of resume text against a role."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analysis import SkillAnalysisRecord
from app.models.user import User
from app.schemas.analysis import AnalysisResult, AnalyzeRequest
from app.services import skill_analyzer
from app.services.auth import get_current_user, get_optional_current_user

logger = logging.getLogger("skillgraph.api.skills")

router = APIRouter(tags=["Skills"])


@router.post(
    "/api/skills/analyze",
    response_model=AnalysisResult,
    summary="Analyse resume text against a target role",
)
async def analyze_skills(
    request: AnalyzeRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> AnalysisResult:
    """Detect skills present in the supplied text, compare them against the target
    role's required skill tiers, and return a structured gap analysis.

    Persists the analysis record if the caller is authenticated.
    """
    try:
        result = skill_analyzer.analyze(text=request.text, role_id=request.role_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if current_user:
        try:
            record = SkillAnalysisRecord(
                user_id=current_user.id,
                role_id=result.role_id,
                role_title=result.role_title,
                coverage_percent=result.coverage_percent,
                matched_skills_json=json.dumps([m.model_dump() for m in result.matched_skills]),
                missing_skills_json=json.dumps([m.model_dump() for m in result.missing_skills]),
                uncertain_skills_json=json.dumps([m.model_dump() for m in result.uncertain_skills]),
                priority_gaps_json=json.dumps([m.model_dump() for m in result.priority_gaps]),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Persisted SkillAnalysisRecord ID %s for User ID %s", record.id, current_user.id)
        except Exception as exc:
            logger.warning("Failed to persist SkillAnalysisRecord: %s", exc)
            db.rollback()

    return result


@router.get(
    "/api/skills/analyses",
    status_code=status.HTTP_200_OK,
    summary="List Authenticated User's Skill Analyses",
)
async def list_user_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all skill analysis records belonging to the authenticated user."""
    records = (
        db.query(SkillAnalysisRecord)
        .filter(SkillAnalysisRecord.user_id == current_user.id)
        .order_by(SkillAnalysisRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "role_id": r.role_id,
            "role_title": r.role_title,
            "coverage_percent": r.coverage_percent,
            "matched_skills_count": len(r.get_matched_skills()),
            "missing_skills_count": len(r.get_missing_skills()),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get(
    "/api/skills/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Specific Skill Analysis Record",
)
async def get_user_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve details for a specific analysis. Enforces ownership check (IDOR protection)."""
    record = (
        db.query(SkillAnalysisRecord)
        .filter(SkillAnalysisRecord.id == analysis_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this analysis record.",
        )

    return {
        "id": record.id,
        "role_id": record.role_id,
        "role_title": record.role_title,
        "coverage_percent": record.coverage_percent,
        "matched_skills": record.get_matched_skills(),
        "missing_skills": record.get_missing_skills(),
        "uncertain_skills": record.get_uncertain_skills(),
        "priority_gaps": record.get_priority_gaps(),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.delete(
    "/api/skills/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Skill Analysis Record",
)
async def delete_user_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a skill analysis record owned by the authenticated user."""
    record = (
        db.query(SkillAnalysisRecord)
        .filter(SkillAnalysisRecord.id == analysis_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this analysis record.",
        )

    db.delete(record)
    db.commit()
    return {"ok": True, "message": f"Skill analysis record {analysis_id} deleted."}


# Architecture.md compatibility endpoints
@router.get("/skills/gap", include_in_schema=False)
async def skills_gap_compat(role: str = Query(..., description="Target role name or id")):
    """Architecture doc compatibility endpoint."""
    try:
        result = skill_analyzer.analyze(text="", role_id=role)
        return {
            "role": result.role_title,
            "readiness": round(result.coverage_percent),
            "missing": [m.canonical_name for m in result.missing_skills],
            "present": [
                {"name": m.canonical_name, "level": 80, "category": m.category}
                for m in result.matched_skills
            ],
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
