"""Profiles API — endpoints for analyzing GitHub and LeetCode interview signals."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, status

from app.schemas.coding_profiles import CodingProfilesRequest, CodingProfilesResponse
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
async def analyze_profiles(payload: CodingProfilesRequest) -> CodingProfilesResponse:
    """Analyze provided GitHub and/or LeetCode profiles and compute technical interview readiness."""
    gh = payload.github_username.strip() if payload.github_username else None
    lc = payload.leetcode_username.strip() if payload.leetcode_username else None

    if not gh and not lc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide at least one handle: 'github_username' or 'leetcode_username'.",
        )

    return await analyze_coding_profiles(github_username=gh, leetcode_username=lc)

