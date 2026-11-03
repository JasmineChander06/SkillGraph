"""Pydantic schemas for Job Description analysis and market data ingestion."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.analysis import SkillMatch


class JobDescriptionAnalyzeRequest(BaseModel):
    """Request payload for comparing resume text against a job description."""

    resume_text: str = Field(
        default="",
        description="Extracted text from the candidate's resume.",
    )
    job_description_text: str = Field(
        ...,
        description="Pasted text of the job description to analyze.",
    )

    @field_validator("job_description_text")
    @classmethod
    def validate_job_description_not_empty(cls, value: str) -> str:
        """Ensure the job description contains non-whitespace characters."""
        if not value or not value.strip():
            raise ValueError("Job description text cannot be empty or whitespace only.")
        return value


class ExperienceRequirement(BaseModel):
    """An identifiable experience or education requirement parsed from the text."""

    raw_text: str = Field(..., description="Exact or near-verbatim text fragment identifying the requirement.")
    years: Optional[float] = Field(None, description="Extracted numerical years requirement, if quantifiable.")
    topic: Optional[str] = Field(None, description="The specific skill, domain, or degree mentioned.")
    requirement_type: str = Field(
        default="tenure",
        description="Type of requirement: 'tenure' (years of experience) or 'education' (degrees).",
    )


class MarketSummaryMetadata(BaseModel):
    """Audit metadata required for future market data collection and aggregation."""

    source: str = Field(..., description="Authorized provider, partner API, or open public dataset name.")
    collection_date: str = Field(..., description="ISO 8601 date of retrieval.")
    geography: str = Field(..., description="Geographic jurisdiction or scope (e.g. 'US-Remote', 'Global').")
    sample_size: int = Field(..., ge=1, description="Number of unique deduplicated postings in the sample.")
    skill_detection_method: str = Field(..., description="Identifier and version of the extraction pipeline.")


class JobDescriptionAnalysisResult(BaseModel):
    """Comprehensive comparison between a candidate's resume and a job description."""

    extracted_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="All unique skills detected anywhere in the job description.",
    )
    matched_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Skills present in both the job description and the candidate's resume.",
    )
    missing_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Skills detected in the job description that were NOT found in the candidate's resume.",
    )
    potentially_related_skills: List[SkillMatch] = Field(
        default_factory=list,
        description=(
            "Skills detected in the resume that share a category with missing skills, "
            "or skills listed in the preferred qualifications."
        ),
    )
    required_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Skills appearing in explicitly designated 'Required' or 'Minimum' qualification sections.",
    )
    preferred_skills: List[SkillMatch] = Field(
        default_factory=list,
        description="Skills appearing in explicitly designated 'Preferred' or 'Nice-to-have' qualification sections.",
    )
    experience_requirements: List[ExperienceRequirement] = Field(
        default_factory=list,
        description="Identifiable tenure or educational requirements parsed from the job description.",
    )
    coverage_percent: float = Field(
        ...,
        description="Percentage of required skills matched (or all extracted skills if unclassified).",
        ge=0.0,
        le=100.0,
    )
    total_jd_skills: int = Field(..., description="Total unique skills extracted from the job description.")
    matched_count: int = Field(..., description="Count of job description skills matched in the resume.")
    missing_count: int = Field(..., description="Count of job description skills missing from the resume.")
    caveats: List[str] = Field(
        default_factory=list,
        description="Explicit limitations and contextual caveats regarding free-text parsing and match scores.",
    )

