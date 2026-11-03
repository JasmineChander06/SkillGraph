"""Pydantic schemas for skill extraction and gap analysis."""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    """Request body for the skill analysis endpoint."""

    text: str = Field(..., description="Extracted resume text to analyse.")
    role_id: str = Field(..., description="Target role identifier (e.g. 'backend-engineer').")


class SkillMatch(BaseModel):
    """A skill that was found in the supplied text."""

    skill_id: str = Field(..., description="Canonical skill identifier from the skill catalogue.")
    canonical_name: str = Field(..., description="Human-readable canonical skill name.")
    category: str = Field(..., description="Skill category (e.g. 'Language', 'DevOps').")
    matched_via: str = Field(
        ..., description="How the skill was matched: 'canonical', 'alias'."
    )


class SkillGap(BaseModel):
    """A required skill that was NOT found in the supplied text."""

    skill_id: str = Field(..., description="Canonical skill identifier.")
    canonical_name: str = Field(..., description="Human-readable canonical skill name.")
    category: str = Field(..., description="Skill category.")
    importance: str = Field(..., description="Importance level: critical, high, medium, or low.")
    estimated_hours: int = Field(..., description="Estimated self-study hours to acquire this skill.")


class AnalysisResult(BaseModel):
    """Complete skill-gap analysis result for one resume against one role."""

    role_id: str = Field(..., description="The target role identifier.")
    role_title: str = Field(..., description="Human-readable canonical role title.")
    matched_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="All skills detected in the text that appear in any role tier.",
    )
    missing_skills: List[SkillGap] = Field(
        default_factory=list,
        description="Core skills required by the role that were not detected.",
    )
    uncertain_skills: List[SkillMatch] = Field(
        default_factory=list,
        description=(
            "Skills detected in the text that appear in the role's recommended or optional "
            "tiers, but not the core tier."
        ),
    )
    coverage_percent: float = Field(
        ...,
        description="Percentage of core skills that were matched (0–100).",
        ge=0.0,
        le=100.0,
    )
    coverage_note: str = Field(
        ...,
        description=(
            "Disclaimer explaining what the coverage score does and does not mean."
        ),
    )
    total_core_skills: int = Field(..., description="Total number of core skills for this role.")
    matched_core_skills: int = Field(
        ..., description="Number of core skills detected in the text."
    )
    priority_gaps: List[SkillGap] = Field(
        default_factory=list,
        description="Up to five highest-priority missing core skills, ordered by importance.",
    )

