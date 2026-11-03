"""Roles API — endpoints for browsing, exploring, and comparing role profiles."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import market_insights, role_discovery

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("/", summary="List and explore role profiles")
async def list_roles(
    family: Optional[str] = Query(None, description="Filter by role family (e.g. 'AI/ML', 'Engineering', 'Data')"),
    level: Optional[str] = Query(None, description="Filter by experience level (e.g. 'entry', 'mid', 'senior')"),
    maturity: Optional[str] = Query(None, description="Filter by maturity ('established' or 'emerging')"),
    q: Optional[str] = Query(None, description="Free-text search query across title and description"),
):
    """
    Return a summary of roles in the catalogue, with optional filtering by family,
    experience level, maturity status, and search query.
    """
    roles = role_discovery.list_roles_explorer(
        family=family,
        level=level,
        maturity=maturity,
        query=q,
    )
    return {"roles": roles}


@router.get("/compare", summary="Compare two roles and compute skill overlap")
async def compare_roles(
    role_a: str = Query(..., description="First role ID to compare"),
    role_b: str = Query(..., description="Second role ID to compare"),
):
    """
    Perform bidirectional comparative analysis between two roles:
    * Shared core skills
    * Unique skills to Role A and Role B
    * Jaccard overlap similarity index
    * Transition bridge skills and estimated hours in both directions
    * Seniority, accessibility, and emerging title nuances
    """
    if not role_a or not role_b:
        raise HTTPException(status_code=422, detail="Both 'role_a' and 'role_b' parameters are required.")

    try:
        comparison = role_discovery.compare_roles(role_a, role_b)
        return comparison
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/{role_id}", summary="Get a single role profile with full details")
async def get_role(role_id: str):
    """
    Return the comprehensive profile for the specified role, including:
    * Responsibilities & Prerequisites
    * Core & Optional skills (with categories and study hours)
    * Example real-world projects
    * Emerging-role maturity & entry-level accessibility guidance
    * Top related roles based on skill overlap
    * Evidence-aware market summary (or curated guidance disclaimer)
    """
    profile = role_discovery.get_role_full_details(role_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found. Use GET /api/roles to list valid IDs.",
        )
    return profile


@router.get("/{role_id}/related", summary="Get related roles based on skill overlap")
async def get_related_roles(
    role_id: str,
    top_n: int = Query(4, ge=1, le=10, description="Maximum number of related roles to return"),
):
    """
    Suggest related roles for `role_id` ranked by Jaccard skill overlap, with
    shared skills and bridge transition skills.
    """
    profile = role_discovery.get_role_full_details(role_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found.")

    related = role_discovery.get_related_roles(role_id, top_n=top_n)
    return {
        "role_id": role_id,
        "canonical_title": profile.get("canonical_title", role_id),
        "related_roles": related,
    }


@router.get("/{role_id}/market-summary", summary="Get evidence-aware market summary")
async def get_role_market_summary(
    role_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve evidence-aware market summary for `role_id`.
    Returns empirical posting frequencies if a verified dataset exists, or transparent
    curated guidance if unverified. Never fabricates synthetic statistics.
    """
    profile = role_discovery.get_role_full_details(role_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"Role '{role_id}' not found.")

    summary = market_insights.get_market_summary(role_id, db=db)
    return summary
