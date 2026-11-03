"""Phase 4 tests: Job description analysis, experience extraction, section parsing, and API endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.job_description_analyzer import (
    analyze_job_description,
    create_market_summary_record,
    extract_experience_requirements,
    segment_job_description,
)

client = TestClient(app)

# ---------------------------------------------------------------------------
# Sample Test Fixtures
# ---------------------------------------------------------------------------

SAMPLE_JD_STRUCTURED = """
About Us:
Acme Corp is pioneering intelligent workflows for global logistics.

Requirements:
* 5+ years of experience with Python
* Strong proficiency in FastAPI, PostgreSQL, and Docker
* Experience with Git and version control
* Bachelor's degree in Computer Science or equivalent

Nice to have:
* Familiarity with Kubernetes and AWS
* Experience with Redis caching

Benefits:
* Competitive salary and equity
* Health insurance
"""

SAMPLE_JD_UNSTRUCTURED = """
Looking for a passionate backend developer who knows Python, Docker, and Redis.
Must be eager to learn and collaborate with our engineering team.
"""

SAMPLE_RESUME_MATCHING = """
Senior Software Engineer
Proficient in Python, FastAPI, Docker, and Git.
Hands-on experience building REST APIs with PostgreSQL.
Worked with Google Cloud Platform (GCP).
"""

SAMPLE_RESUME_MINIMAL = """
Junior Web Developer
Experience with HTML, CSS, and vanilla JavaScript.
"""


# ---------------------------------------------------------------------------
# Section Segmentation Unit Tests
# ---------------------------------------------------------------------------


class TestSectionSegmentation:
    """Unit tests for parsing job description structural sections."""

    def test_segment_structured_job_description(self):
        """Should detect 'required', 'preferred', and 'general' sections."""
        sections = segment_job_description(SAMPLE_JD_STRUCTURED)
        section_types = [st for st, _ in sections]
        assert "required" in section_types
        assert "preferred" in section_types
        assert "general" in section_types

    def test_segment_unstructured_text_defaults_to_general(self):
        """Unstructured text without explicit headers should be marked as general."""
        sections = segment_job_description(SAMPLE_JD_UNSTRUCTURED)
        for st, _ in sections:
            assert st == "general"


# ---------------------------------------------------------------------------
# Experience Requirement Extractor Tests
# ---------------------------------------------------------------------------


class TestExperienceExtraction:
    """Unit tests for extracting tenure and degree constraints."""

    def test_extract_years_of_experience(self):
        """Should detect '5+ years of experience with Python'."""
        reqs = extract_experience_requirements(SAMPLE_JD_STRUCTURED)
        tenure_reqs = [r for r in reqs if r.requirement_type == "tenure"]
        assert len(tenure_reqs) >= 1
        first = tenure_reqs[0]
        assert first.years == 5.0
        assert "python" in (first.topic or "").lower() or "5+ years" in first.raw_text.lower()

    def test_extract_degree_requirement(self):
        """Should detect Bachelor's degree requirement."""
        reqs = extract_experience_requirements(SAMPLE_JD_STRUCTURED)
        edu_reqs = [r for r in reqs if r.requirement_type == "education"]
        assert len(edu_reqs) >= 1
        assert "bachelor" in edu_reqs[0].raw_text.lower()

    def test_no_experience_requirements_in_plain_text(self):
        """Text without numbers or degree mentions should return empty list."""
        reqs = extract_experience_requirements("We are a fast-growing startup looking for team players.")
        assert reqs == []


# ---------------------------------------------------------------------------
# Comparative Skill-Gap Service Tests
# ---------------------------------------------------------------------------


class TestJobDescriptionAnalyzerService:
    """Unit tests for the core comparative analysis service."""

    def test_analyze_structured_jd_delineates_required_and_preferred(self):
        """Required and preferred skills must be identified separately based on wording."""
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MATCHING,
            job_description_text=SAMPLE_JD_STRUCTURED,
        )

        required_ids = {s.skill_id for s in result.required_skills}
        preferred_ids = {s.skill_id for s in result.preferred_skills}

        # Core required skills from Requirements section
        assert "python" in required_ids
        assert "fastapi" in required_ids
        assert "postgresql" in required_ids
        assert "docker" in required_ids

        # Preferred skills from Nice to have section
        assert "kubernetes" in preferred_ids
        assert "aws" in preferred_ids or "redis" in preferred_ids

    def test_matched_and_missing_skills_classification(self):
        """Skills should be partitioned into matched and missing based on resume content."""
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MATCHING,
            job_description_text=SAMPLE_JD_STRUCTURED,
        )

        matched_ids = {s.skill_id for s in result.matched_skills}
        missing_ids = {s.skill_id for s in result.missing_skills}

        # Resume contains: Python, FastAPI, Docker, Git, PostgreSQL
        assert "python" in matched_ids
        assert "fastapi" in matched_ids
        assert "docker" in matched_ids
        assert "postgresql" in matched_ids

        # Resume lacks: Kubernetes, AWS, Redis
        assert "kubernetes" in missing_ids
        assert "aws" in missing_ids

    def test_potentially_related_skills_detection(self):
        """Resume skills sharing a category with missing skills should appear in potentially_related."""
        # JD asks for AWS (Cloud) which resume lacks, but resume has GCP (Cloud)
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MATCHING,
            job_description_text=SAMPLE_JD_STRUCTURED,
        )

        related_ids = {s.skill_id for s in result.potentially_related_skills}
        assert "gcp" in related_ids

    def test_coverage_calculation_for_structured_jd(self):
        """Coverage should be evaluated against required skills when distinction exists."""
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MATCHING,
            job_description_text=SAMPLE_JD_STRUCTURED,
        )
        # All required skills (python, fastapi, postgresql, docker, git) are matched in this resume
        assert result.coverage_percent == pytest.approx(100.0, abs=1.0)

    def test_coverage_with_zero_matches(self):
        """Resume with no matching skills should yield 0.0 coverage."""
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MINIMAL,
            job_description_text=SAMPLE_JD_STRUCTURED,
        )
        assert result.coverage_percent == pytest.approx(0.0, abs=0.1)
        assert result.matched_count == 0

    def test_unstructured_jd_evaluates_all_skills_with_caveat(self):
        """When JD has no headers, all extracted skills are evaluated and caveat is added."""
        result = analyze_job_description(
            resume_text=SAMPLE_RESUME_MATCHING,
            job_description_text=SAMPLE_JD_UNSTRUCTURED,
        )
        # Python, Docker, Redis are in JD
        assert result.total_jd_skills >= 3
        assert len(result.required_skills) == 0  # No structural distinction present
        assert len(result.preferred_skills) == 0
        # Check that caveat explains the absence of distinction
        assert any("did not contain recognizable" in c for c in result.caveats)

    def test_decoupled_from_role_profiles(self):
        """Analysis must not inject skills from curated role profiles not in the JD."""
        result = analyze_job_description(
            resume_text="",
            job_description_text="We need someone who knows Python.",
        )
        jd_skill_ids = {s.skill_id for s in result.extracted_skills}
        assert jd_skill_ids == {"python"}


# ---------------------------------------------------------------------------
# Market Data Metadata Ingestion Architecture Tests
# ---------------------------------------------------------------------------


class TestMarketDataIngestionArchitecture:
    """Tests verifying the data retention model for future permitted market collection."""

    def test_market_summary_record_creation(self):
        """Verify that market summary record holds all mandatory audit fields."""
        record = create_market_summary_record(
            source="Official-Partner-API",
            collection_date="2026-11-03",
            geography="US-Remote",
            sample_size=150,
            skill_detection_method="SkillGraph-Regex-v1.0",
        )
        assert record.source == "Official-Partner-API"
        assert record.collection_date == "2026-11-03"
        assert record.geography == "US-Remote"
        assert record.sample_size == 150
        assert record.skill_detection_method == "SkillGraph-Regex-v1.0"


# ---------------------------------------------------------------------------
# API Endpoint Integration Tests
# ---------------------------------------------------------------------------


class TestJobDescriptionAPI:
    """Integration tests for POST /api/job-descriptions/analyze."""

    def test_analyze_endpoint_success(self):
        """POST /api/job-descriptions/analyze with valid payload returns 200 and schema."""
        payload = {
            "resume_text": SAMPLE_RESUME_MATCHING,
            "job_description_text": SAMPLE_JD_STRUCTURED,
        }
        response = client.post("/api/job-descriptions/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "extracted_skills" in data
        assert "matched_skills" in data
        assert "missing_skills" in data
        assert "potentially_related_skills" in data
        assert "required_skills" in data
        assert "preferred_skills" in data
        assert "experience_requirements" in data
        assert "coverage_percent" in data
        assert "caveats" in data
        assert len(data["caveats"]) >= 4

    def test_analyze_endpoint_empty_resume_allowed(self):
        """POST with empty resume_text is permitted and computes zero match."""
        payload = {
            "resume_text": "",
            "job_description_text": "Looking for a Python developer with Docker expertise.",
        }
        response = client.post("/api/job-descriptions/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["coverage_percent"] == 0.0
        assert len(data["matched_skills"]) == 0
        assert len(data["missing_skills"]) >= 2

    def test_analyze_endpoint_empty_job_description_fails(self):
        """POST with empty job_description_text returns 422 Unprocessable Content."""
        payload = {
            "resume_text": "Experienced developer",
            "job_description_text": "   ",
        }
        response = client.post("/api/job-descriptions/analyze", json=payload)
        assert response.status_code == 422

    def test_analyze_endpoint_missing_job_description_field_fails(self):
        """POST missing job_description_text field returns 422."""
        payload = {"resume_text": "Experienced developer"}
        response = client.post("/api/job-descriptions/analyze", json=payload)
        assert response.status_code == 422

