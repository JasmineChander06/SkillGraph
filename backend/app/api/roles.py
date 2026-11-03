"""Roles API — endpoints for browsing the role profile catalogue."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.services import skill_analyzer

router = APIRouter(prefix="/api/roles", tags=["Roles"])


@router.get("/", summary="List all role profiles")
async def list_roles():
    """Return a summary of every role in the catalogue (id, title, family, level)."""
    return {"roles": skill_analyzer.list_roles()}


@router.get("/{role_id}", summary="Get a single role profile by ID")
async def get_role(role_id: str):
    """
    Return the full profile for the specified role.

    Raises **404** if the role ID is not in the catalogue.
    """
    profile = skill_analyzer.get_role(role_id)
    if profile is None:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{role_id}' not found. Use GET /api/roles to list valid IDs.",
        )
    return profile

