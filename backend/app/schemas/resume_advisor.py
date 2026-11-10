"""Schemas for Resume Quality Assessment and Suggestions Engine."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ResumeCritiqueRequest(BaseModel):
    """Input payload for resume critique and rating."""
    text: Optional[str] = Field(None, description="Plain text content of the resume to analyze")
    resume_id: Optional[int] = Field(None, description="ID of a persisted resume to analyze")


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


class ResumeCritiqueResponse(BaseModel):
    """Complete resume review and recommendation report."""
    overall_score: int = Field(..., ge=0, le=100, description="Overall resume rating out of 100")
    rating_label: str = Field(..., description="Descriptive rating: Exceptional, Competitive, Developing, Needs Critical Revision")
    dimension_scores: DimensionScores = Field(..., description="Breakdown across scoring dimensions")
    strengths: List[str] = Field(default_factory=list, description="Observed strengths in the resume")
    things_to_add: List[str] = Field(default_factory=list, description="Actionable elements and keywords to incorporate")
    things_to_remove: List[str] = Field(default_factory=list, description="Fluff words, cliches, or obsolete tools to eliminate")
    bullet_improvements: List[BulletImprovement] = Field(default_factory=list, description="Specific before-and-after bullet rewrites")
    summary: str = Field(..., description="Executive summary of the resume critique")

