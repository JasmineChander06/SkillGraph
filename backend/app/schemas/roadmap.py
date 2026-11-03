"""Pydantic schemas for the 6-week personalized learning roadmap."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class LearningResource(BaseModel):
    """Learning resource attached to a roadmap task."""

    title: str = Field(..., description="Title or name of the learning material.")
    url: Optional[str] = Field(None, description="URL if verified; None if awaiting verification.")
    is_verified: bool = Field(
        default=False,
        description="True if the URL has been validated against official documentation or trusted sources.",
    )
    verification_status: str = Field(
        default="Verified",
        description="'Verified' for curated official sources; 'Requires verification' otherwise.",
    )


class RoadmapTask(BaseModel):
    """An individual actionable task within a weekly study plan."""

    id: str = Field(..., description="Unique task identifier.")
    title: str = Field(..., description="Actionable title of the learning task.")
    description: str = Field(..., description="Detailed instructions, topics to cover, or mini-project.")
    target_skill: str = Field(..., description="Canonical name of the target skill.")
    week: int = Field(..., ge=1, le=6, description="Target study week (1 to 6).")
    estimated_effort: int = Field(
        ...,
        ge=1,
        description="Estimated study and practice effort in hours.",
    )
    prerequisites: List[str] = Field(
        default_factory=list,
        description="List of skills or foundational concepts that must precede this task.",
    )
    learning_resource: LearningResource = Field(
        ...,
        description="Curated or suggested learning resource.",
    )
    completion_status: str = Field(
        default="pending",
        description="Status of the task ('pending', 'in_progress', 'completed').",
    )


class WeekPlan(BaseModel):
    """Plan for a single week of the 6-week roadmap."""

    week_number: int = Field(..., ge=1, le=6)
    theme: str = Field(..., description="Overarching weekly focus or milestone.")
    weekly_hours_allocated: int = Field(..., ge=0, description="Sum of estimated effort hours for this week.")
    tasks: List[RoadmapTask] = Field(default_factory=list)
    milestone_project: Optional[str] = Field(None, description="Optional weekly mini-project or check-in.")


class RoadmapGenerateRequest(BaseModel):
    """Payload for generating a personalized 6-week learning roadmap."""

    role_id: str = Field(..., description="Target role identifier (e.g. 'harness-engineer').")
    existing_skills: List[str] = Field(
        default_factory=list,
        description="List of skills already acquired by the user (IDs or names).",
    )
    missing_skills: Optional[List[str]] = Field(
        default=None,
        description="Explicit list of skills to learn. If omitted, automatically computed from role requirements.",
    )
    weekly_hours: Optional[int] = Field(
        default=10,
        ge=1,
        le=60,
        description="Estimated weekly study availability in hours (default 10 hours/week).",
    )
    resume_text: Optional[str] = Field(
        default=None,
        description="Optional resume text. If provided, existing skills will be extracted automatically.",
    )


class Roadmap(BaseModel):
    """Complete 6-week learning roadmap response."""

    role_id: str = Field(..., description="Target role identifier.")
    role_title: str = Field(..., description="Canonical title of the target role.")
    total_weeks: int = Field(default=6, description="Duration in weeks (fixed at 6).")
    target_weekly_hours: int = Field(..., description="Weekly study availability.")
    total_estimated_hours: int = Field(..., description="Total hours across all 6 weeks.")
    weeks: List[WeekPlan] = Field(..., description="Ordered weekly progression (Weeks 1 through 6).")
    tasks: List[RoadmapTask] = Field(..., description="Flat list of all tasks in chronological order.")
    capstone_project: str = Field(..., description="Role-specific capstone project description.")
    prerequisite_chains: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Mapping of skill to its required prerequisites.",
    )
    notes: List[str] = Field(
        default_factory=list,
        description="Guiding notes on pacing, prerequisites, and resource verification.",
    )

