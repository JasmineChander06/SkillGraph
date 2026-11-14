"""Schemas for Resume Quality Assessment and Suggestions Engine."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ResumeCritiqueRequest(BaseModel):
    """Input payload for resume critique and rating."""
    text: Optional[str] = Field(None, description="Plain text content of the resume to analyze")
    resume_id: Optional[int] = Field(None, description="ID of a persisted resume to analyze")
    target_role: Optional[str] = Field(None, description="Target role ID for role-aware suggestions")


class DimensionScores(BaseModel):
    """Scoring breakdown across 4 core dimensions (25 points each, totaling 100)."""
    quantification: float = Field(..., description="Metrics, percentages, numbers, scale (0-25)")
    action_verbs: float = Field(..., description="Strong active leadership verbs vs passive voice (0-25)")
    keyword_density: float = Field(..., description="Technical skill density and domain vocabulary (0-25)")
    brevity_and_clarity: float = Field(..., description="Absence of cliches, buzzwords, and fluff (0-25)")


class BulletImprovement(BaseModel):
    """Before-and-after recommendation for a bullet point using Google XYZ formula."""
    original: str = Field(..., description="Original or detected weak bullet phrasing")
    improved: str = Field(..., description="High-impact rewrite following 'Accomplished [X] measured by [Y] by doing [Z]'")
    reason: str = Field(..., description="Explanation of the critique and improvement")


class ThingToAdd(BaseModel):
    """A specific, resume-based suggestion for content to add."""
    suggestion: str = Field(..., description="What should be added")
    section: str = Field("", description="Which resume section needs improvement")
    why: str = Field("", description="Why it should be added")
    context: str = Field("", description="The original resume context that triggered the suggestion")
    needs_user_input: bool = Field(False, description="Whether the user needs to provide additional information")


class ThingToRemove(BaseModel):
    """A specific sentence or phrase from the resume flagged for removal or rewriting."""
    original_line: str = Field(..., description="The exact original sentence from the resume")
    issue: str = Field(..., description="What is wrong with this line")
    recommendation: str = Field(..., description="Specific rewrite suggestion or removal rationale")
    action: str = Field("REWRITE", description="REMOVE, REWRITE, or KEEP")
    section: str = Field("", description="The resume section where this was found")


class ResumeCritiqueResponse(BaseModel):
    """Complete resume review and recommendation report."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall resume rating out of 100")
    rating_label: str = Field(..., description="Descriptive rating: Exceptional, Competitive, Developing, Needs Critical Revision")
    dimension_scores: DimensionScores = Field(..., description="Breakdown across scoring dimensions")
    strengths: List[str] = Field(default_factory=list, description="Observed strengths in the resume")
    things_to_add: List[ThingToAdd] = Field(default_factory=list, description="Actionable content-specific suggestions to incorporate")
    things_to_remove: List[ThingToRemove] = Field(default_factory=list, description="Specific lines flagged for removal or rewriting")
    bullet_improvements: List[BulletImprovement] = Field(default_factory=list, description="Specific before-and-after bullet rewrites from the actual resume")
    summary: str = Field(..., description="Executive summary of the resume critique")
    target_role_title: Optional[str] = Field(None, description="The target role used for personalization")
