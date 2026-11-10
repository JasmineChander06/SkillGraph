"""Profiles API — endpoints for analyzing GitHub and LeetCode interview signals."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.resume import ResumeRecord
from app.models.user import User
from app.schemas.coding_profiles import CodingProfilesRequest, CodingProfilesResponse
from app.services.auth import get_current_user, get_optional_current_user
from app.services.coding_profiles import analyze_coding_profiles

logger = logging.getLogger("skillgraph.api.profiles")

router = APIRouter(prefix="/api/profiles", tags=["Coding Profiles"])


@router.post(
    "/analyze",
    response_model=CodingProfilesResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Technical Coding Profiles",
    description="Fetch and score engineering signals from GitHub (repos, stars, languages) and LeetCode (DSA readiness, solved counts).",
)
async def analyze_profiles(
    payload: CodingProfilesRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> CodingProfilesResponse:
    """Analyze provided GitHub and/or LeetCode profiles and compute technical interview readiness."""
    gh = payload.github_username.strip() if payload.github_username else None
    lc = payload.leetcode_username.strip() if payload.leetcode_username else None

    if not gh and not lc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide at least one handle: 'github_username' or 'leetcode_username'.",
        )

    user_skills: Optional[List[str]] = None
    target_role: Optional[str] = None

    if current_user:
        target_role = current_user.target_role
        resume = (
            db.query(ResumeRecord)
            .filter(ResumeRecord.user_id == current_user.id, ResumeRecord.is_deleted == False)
            .order_by(ResumeRecord.created_at.desc())
            .first()
        )
        if resume and resume.extracted_skills_json:
            try:
                user_skills = json.loads(resume.extracted_skills_json)
            except Exception:
                user_skills = None

    result = await analyze_coding_profiles(
        github_username=gh,
        leetcode_username=lc,
        user_skills=user_skills,
        target_role=target_role,
    )

    # Persist handles and full signal report to authenticated user profile
    if current_user:
        if gh:
            current_user.github_username = gh
        if lc:
            current_user.leetcode_username = lc
        current_user.coding_signal_json = result.model_dump_json()
        try:
            db.commit()
            db.refresh(current_user)
        except Exception as exc:
            logger.warning("Failed to save coding handles: %s", exc)
            db.rollback()

    return result


@router.get(
    "/saved",
    status_code=status.HTTP_200_OK,
    summary="Get Saved Coding Handles",
)
async def get_saved_coding_handles(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve saved GitHub and LeetCode usernames for the authenticated user."""
    return {
        "github_username": current_user.github_username,
        "leetcode_username": current_user.leetcode_username,
    }


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User's Saved Coding Signal Analysis",
)
async def get_my_coding_analysis(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Return cached coding profile report if available."""
    if current_user.coding_signal_json:
        try:
            return json.loads(current_user.coding_signal_json)
        except Exception:
            pass
    return {
        "github_username": current_user.github_username,
        "leetcode_username": current_user.leetcode_username,
        "saved_report": None,
    }

