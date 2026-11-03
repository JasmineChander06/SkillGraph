"""Job Descriptions API — endpoints for comparing resumes against pasted job descriptions."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.job_description import (
    JobDescriptionAnalysisResult,
    JobDescriptionAnalyzeRequest,
)
from app.services import job_description_analyzer

router = APIRouter(prefix="/api/job-descriptions", tags=["Job Descriptions"])


@router.post(
    "/analyze",
    response_model=JobDescriptionAnalysisResult,
    summary="Compare resume text against a pasted job description",
)
async def analyze_job_description(
    request: JobDescriptionAnalyzeRequest,
) -> JobDescriptionAnalysisResult:
    """
    Extract skills, experience constraints, and stated qualification tiers from
    a pasted job description and compare them against candidate resume text.

    * **resume_text**: Plain-text content from the candidate's parsed resume.
    * **job_description_text**: Unstructured text of the target job description.

    Returns extracted skills, matched skills, missing skills, potentially related skills,
    required vs preferred skills (where wording explicitly supports it), experience
    requirements, transparent coverage calculation, and analytical caveats.
    """
    return job_description_analyzer.analyze_job_description(
        resume_text=request.resume_text,
        job_description_text=request.job_description_text,
    )

