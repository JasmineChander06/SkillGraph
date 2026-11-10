"""Job Descriptions API — endpoints for comparing resumes against pasted job descriptions."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.job_description import JobDescriptionAnalysisRecord
from app.models.user import User
from app.schemas.job_description import (
    JobDescriptionAnalysisResult,
    JobDescriptionAnalyzeRequest,
)
from app.services import job_description_analyzer
from app.services.auth import get_current_user, get_optional_current_user
from app.services.job_market_analytics import compute_market_trends

logger = logging.getLogger("skillgraph.api.job_descriptions")

router = APIRouter(tags=["Job Descriptions"])


@router.post(
    "/api/job-descriptions/analyze",
    response_model=JobDescriptionAnalysisResult,
    summary="Compare resume text against a pasted job description",
)
@router.post(
    "/jobs/match",
    response_model=JobDescriptionAnalysisResult,
    include_in_schema=False,
)
async def analyze_job_description(
    request: JobDescriptionAnalyzeRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> JobDescriptionAnalysisResult:
    """Extract skills, experience constraints, and stated qualification tiers from
    a pasted job description and compare them against candidate resume text.

    Persists the analysis record if the caller is authenticated.
    """
    result = job_description_analyzer.analyze_job_description(
        resume_text=request.resume_text,
        job_description_text=request.job_description_text,
    )

    if current_user:
        try:
            record = JobDescriptionAnalysisRecord(
                user_id=current_user.id,
                job_description_text=request.job_description_text[:5000],  # Cap text for safety
                coverage_percent=result.coverage_percent,
                extracted_skills_json=json.dumps([s.model_dump() for s in result.extracted_skills]),
                matched_skills_json=json.dumps([s.model_dump() for s in result.matched_skills]),
                missing_skills_json=json.dumps([s.model_dump() for s in result.missing_skills]),
                required_skills_json=json.dumps([s.model_dump() for s in result.required_skills]),
                preferred_skills_json=json.dumps([s.model_dump() for s in result.preferred_skills]),
                experience_requirements_json=json.dumps([e.model_dump() for e in result.experience_requirements]),
                caveats_json=json.dumps(result.caveats),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            logger.info("Persisted JobDescriptionAnalysisRecord ID %s for User ID %s", record.id, current_user.id)
        except Exception as exc:
            logger.warning("Failed to persist JobDescriptionAnalysisRecord: %s", exc)
            db.rollback()

    return result


@router.get(
    "/api/job-descriptions/analyses",
    status_code=status.HTTP_200_OK,
    summary="List Authenticated User's Job Description Analyses",
)
async def list_user_jd_analyses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all job description analysis records belonging to the authenticated user."""
    records = (
        db.query(JobDescriptionAnalysisRecord)
        .filter(JobDescriptionAnalysisRecord.user_id == current_user.id)
        .order_by(JobDescriptionAnalysisRecord.created_at.desc())
        .all()
    )
    return [
        {
            "id": r.id,
            "job_title": r.job_title,
            "company_name": r.company_name,
            "coverage_percent": r.coverage_percent,
            "matched_skills_count": len(r.get_matched_skills()),
            "missing_skills_count": len(r.get_missing_skills()),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get(
    "/api/job-descriptions/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Specific Job Description Analysis Record",
)
async def get_user_jd_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve details for a specific job analysis. Enforces ownership check (IDOR protection)."""
    record = (
        db.query(JobDescriptionAnalysisRecord)
        .filter(JobDescriptionAnalysisRecord.id == analysis_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description analysis record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this job description analysis record.",
        )

    return {
        "id": record.id,
        "job_title": record.job_title,
        "company_name": record.company_name,
        "coverage_percent": record.coverage_percent,
        "extracted_skills": record.get_extracted_skills(),
        "matched_skills": record.get_matched_skills(),
        "missing_skills": record.get_missing_skills(),
        "experience_requirements": record.get_experience_requirements(),
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.delete(
    "/api/job-descriptions/analyses/{analysis_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Job Description Analysis Record",
)
async def delete_user_jd_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a job description analysis record owned by the authenticated user."""
    record = (
        db.query(JobDescriptionAnalysisRecord)
        .filter(JobDescriptionAnalysisRecord.id == analysis_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description analysis record not found.")

    if record.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this job description analysis record.",
        )

    db.delete(record)
    db.commit()
    return {"ok": True, "message": f"Job description analysis record {analysis_id} deleted."}


@router.get(
    "/api/job-descriptions/market-trends",
    status_code=status.HTTP_200_OK,
    summary="Get Aggregate Job Market Trends",
    description="Retrieve top in-demand skills, category distributions, skill pairs, and empirical benchmarks across role families.",
)
async def get_market_trends(
    family: Optional[str] = None,
) -> Dict[str, Any]:
    """Return aggregated cross-role market signals and demand density."""
    return compute_market_trends(family=family)

