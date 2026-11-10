"""Schemas for Coding Profiles (GitHub & LeetCode) technical interview signal."""

from __future__ import annotations

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class CodingProfilesRequest(BaseModel):
    """Input payload containing target GitHub and/or LeetCode handles."""
    github_username: Optional[str] = Field(None, description="GitHub username handle")
    leetcode_username: Optional[str] = Field(None, description="LeetCode username handle")


class GitHubSignal(BaseModel):
    """Derived engineering signals from public GitHub account."""
    username: str
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    profile_url: str
    public_repos: int = Field(..., ge=0)
    followers: int = Field(..., ge=0)
    total_stars: int = Field(default=0, ge=0)
    primary_languages: Dict[str, float] = Field(default_factory=dict, description="Language percentage distribution")
    quality_score: int = Field(..., ge=0, le=100, description="Overall repository quality and activity score")
    summary: str


class LeetCodeSignal(BaseModel):
    """Interview problem-solving metrics and DSA readiness derived from LeetCode."""
    username: str
    profile_url: str
    total_solved: int = Field(..., ge=0)
    easy_solved: int = Field(default=0, ge=0)
    medium_solved: int = Field(default=0, ge=0)
    hard_solved: int = Field(default=0, ge=0)
    acceptance_rate: float = Field(default=0.0, ge=0.0, le=100.0)
    ranking: Optional[int] = Field(default=None)
    dsa_readiness_score: int = Field(..., ge=0, le=100, description="Calculated DSA readiness index for technical interviews")
    dsa_readiness_tier: str = Field(..., description="Interview Ready, Approaching Ready, Developing, Early Practice")
    interview_recommendations: List[str] = Field(default_factory=list)


class CodingProfilesResponse(BaseModel):
    """Consolidated technical interview and coding signal report."""
    github: Optional[GitHubSignal] = None
    leetcode: Optional[LeetCodeSignal] = None
    combined_signal_score: int = Field(..., ge=0, le=100)
    strengths: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    summary: str

