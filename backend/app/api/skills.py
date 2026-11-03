"""Skills API — endpoint for skill-gap analysis of resume text against a role."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.analysis import AnalysisResult, AnalyzeRequest
from app.services import skill_analyzer

router = APIRouter(prefix="/api/skills", tags=["Skills"])


@router.post(
    "/analyze",
    response_model=AnalysisResult,
    summary="Analyse resume text against a target role",
)
async def analyze_skills(request: AnalyzeRequest) -> AnalysisResult:
    """
    Detect skills present in the supplied text, compare them against the target
    role's required skill tiers, and return a structured gap analysis.

    * **text**: The extracted plain-text content of a resume.
    * **role_id**: A valid role identifier from ``GET /api/roles``.

    Returns **404** if the role ID is unknown.
    """
    try:
        result = skill_analyzer.analyze(text=request.text, role_id=request.role_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return result

