"""Phase 3 tests: skill extraction, gap analysis, and roles/skills API endpoints."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.skill_extractor import extract_skills
from app.services.skill_analyzer import analyze

client = TestClient(app)

# ---------------------------------------------------------------------------
# Skill extraction unit tests
# ---------------------------------------------------------------------------


class TestSkillExtraction:
    """Tests for the skill_extractor.extract_skills function."""

    def test_extract_python_canonical(self):
        """'Python' in text should be detected via canonical name."""
        results = extract_skills("I have 3 years of experience with Python.")
        ids = {r.skill_id for r in results}
        assert "python" in ids

    def test_extract_python_alias(self):
        """'python3' should resolve to the Python skill via alias."""
        results = extract_skills("Wrote scripts in python3 for automation.")
        ids = {r.skill_id for r in results}
        assert "python" in ids

    def test_extract_alias_matched_via_field(self):
        """When matched via alias the matched_via field should equal 'alias'."""
        results = extract_skills("Used sklearn for feature engineering.")
        match = next((r for r in results if r.skill_id == "scikit_learn"), None)
        assert match is not None
        assert match.matched_via == "alias"

    def test_extract_canonical_matched_via_field(self):
        """When matched via canonical name the matched_via field should equal 'canonical'."""
        results = extract_skills("Proficient in Docker and Kubernetes.")
        match = next((r for r in results if r.skill_id == "docker"), None)
        assert match is not None
        assert match.matched_via == "canonical"

    def test_extract_case_insensitive(self):
        """Matching must be case-insensitive (e.g. 'PYTORCH' → PyTorch)."""
        results = extract_skills("Trained models using PYTORCH.")
        ids = {r.skill_id for r in results}
        assert "pytorch" in ids

    def test_no_false_positive_c_in_cpp(self):
        """'C++' in text must NOT trigger the standalone 'C' (c_lang) skill."""
        results = extract_skills("Experienced with C++ for systems programming.")
        ids = {r.skill_id for r in results}
        assert "c_lang" not in ids
        assert "cpp" in ids

    def test_no_false_positive_c_in_csharp(self):
        """'C#' in text must NOT trigger the standalone 'C' (c_lang) skill."""
        results = extract_skills("Built a backend service in C#.")
        ids = {r.skill_id for r in results}
        assert "c_lang" not in ids

    def test_no_false_positive_java_in_javascript(self):
        """'JavaScript' in text must NOT trigger the 'Java' skill."""
        results = extract_skills("Front-end work in JavaScript and React.")
        ids = {r.skill_id for r in results}
        assert "java" not in ids
        assert "javascript" in ids

    def test_c_lang_detected_alone(self):
        """Bare 'C' surrounded by spaces should be detected as c_lang."""
        results = extract_skills("Low-level programming in C for embedded systems.")
        ids = {r.skill_id for r in results}
        assert "c_lang" in ids

    def test_deduplication(self):
        """Each skill_id should appear at most once even if mentioned multiple times."""
        results = extract_skills("Python Python Python python3 py")
        python_hits = [r for r in results if r.skill_id == "python"]
        assert len(python_hits) == 1

    def test_empty_text_returns_empty(self):
        """Empty input text should produce an empty list."""
        results = extract_skills("")
        assert results == []

    def test_multiple_skills_detected(self):
        """A realistic resume snippet should detect multiple distinct skills."""
        text = (
            "Experienced Python developer with FastAPI, PostgreSQL, Docker, "
            "and Redis. Familiar with Kubernetes and AWS."
        )
        results = extract_skills(text)
        ids = {r.skill_id for r in results}
        assert ids.issuperset({"python", "fastapi", "postgresql", "docker", "redis"})


# ---------------------------------------------------------------------------
# Skill analyser unit tests
# ---------------------------------------------------------------------------


class TestSkillAnalyzer:
    """Tests for the skill_analyzer.analyze function."""

    def test_analyze_known_role_returns_result(self):
        """Analyzing against a known role should return an AnalysisResult."""
        result = analyze("Python FastAPI PostgreSQL Docker Redis git", "backend-engineer")
        assert result.role_id == "backend-engineer"
        assert result.role_title == "Backend Engineer"

    def test_analyze_unknown_role_raises_key_error(self):
        """An unknown role ID should raise KeyError."""
        with pytest.raises(KeyError):
            analyze("Python", "nonexistent-role")

    def test_coverage_all_matched(self):
        """When all core skills are present, coverage should be 100 %."""
        # backend-engineer core: python, fastapi, postgresql, redis, docker, rest_api, git
        text = (
            "Python FastAPI PostgreSQL Redis Docker REST API git"
        )
        result = analyze(text, "backend-engineer")
        assert result.coverage_percent == pytest.approx(100.0, abs=1.0)
        assert result.matched_core_skills == result.total_core_skills

    def test_coverage_none_matched(self):
        """When no skills are present the coverage should be 0 %."""
        result = analyze("I love hiking and cooking.", "backend-engineer")
        assert result.coverage_percent == pytest.approx(0.0, abs=0.1)
        assert result.matched_core_skills == 0

    def test_coverage_formula(self):
        """Manually verify: exactly 3 of 7 core skills → ~42.86 %."""
        # backend-engineer core: python, fastapi, postgresql, redis, docker, rest_api, git
        # Supply only: python, fastapi, docker  (3 out of 7)
        text = "Python FastAPI Docker"
        result = analyze(text, "backend-engineer")
        expected = 3 / 7 * 100
        assert result.coverage_percent == pytest.approx(expected, abs=1.0)
        assert result.matched_core_skills == 3
        assert result.total_core_skills == 7

    def test_missing_skills_returned(self):
        """Skills not in the text should appear in missing_skills."""
        result = analyze("Python", "backend-engineer")
        missing_ids = {g.skill_id for g in result.missing_skills}
        # fastapi, postgresql, redis, docker, rest_api, git are all absent
        assert "fastapi" in missing_ids
        assert "docker" in missing_ids

    def test_uncertain_skills_returned(self):
        """A recommended (non-core) skill present in text should appear in uncertain_skills."""
        # kubernetes is recommended for backend-engineer, not core
        text = "Python FastAPI Docker Kubernetes"
        result = analyze(text, "backend-engineer")
        uncertain_ids = {sm.skill_id for sm in result.uncertain_skills}
        assert "kubernetes" in uncertain_ids
        # It should NOT appear in matched_skills (core only)
        matched_ids = {sm.skill_id for sm in result.matched_skills}
        assert "kubernetes" not in matched_ids

    def test_priority_gaps_ordering(self):
        """Priority gaps should be ordered by importance: critical before high before medium."""
        result = analyze("I love hiking.", "backend-engineer")
        # All core skills are missing; priority_gaps ≤ 5
        assert len(result.priority_gaps) <= 5
        importance_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        ranks = [importance_order.get(g.importance, 99) for g in result.priority_gaps]
        assert ranks == sorted(ranks), "Priority gaps must be sorted by importance."

    def test_priority_gaps_at_most_five(self):
        """Priority gaps list must never exceed 5 items."""
        result = analyze("I love hiking and cooking.", "ai-infrastructure-engineer")
        assert len(result.priority_gaps) <= 5

    def test_coverage_note_present(self):
        """The coverage_note field must contain a non-empty disclaimer string."""
        result = analyze("Python", "backend-engineer")
        assert result.coverage_note
        assert len(result.coverage_note) > 20


# ---------------------------------------------------------------------------
# Roles API endpoint tests
# ---------------------------------------------------------------------------


class TestRolesAPI:
    """Tests for GET /api/roles and GET /api/roles/{role_id}."""

    def test_list_roles_returns_ok(self):
        """GET /api/roles should respond with 200."""
        response = client.get("/api/roles/")
        assert response.status_code == 200

    def test_list_roles_returns_all_eleven(self):
        """GET /api/roles should return all 11 role profiles."""
        response = client.get("/api/roles/")
        data = response.json()
        assert "roles" in data
        assert len(data["roles"]) == 11

    def test_list_roles_contains_expected_ids(self):
        """Each expected role ID must appear in the list."""
        expected_ids = {
            "backend-engineer",
            "machine-learning-engineer",
            "data-engineer",
            "data-analyst",
            "ai-agent-engineer",
            "llmops-engineer",
            "ai-evaluation-engineer",
            "ai-infrastructure-engineer",
            "forward-deployed-engineer",
            "forward-deployed-ai-engineer",
            "harness-engineer",
        }
        response = client.get("/api/roles/")
        data = response.json()
        returned_ids = {r["id"] for r in data["roles"]}
        assert expected_ids == returned_ids

    def test_get_role_by_id_returns_ok(self):
        """GET /api/roles/backend-engineer should respond with 200."""
        response = client.get("/api/roles/backend-engineer")
        assert response.status_code == 200

    def test_get_role_by_id_returns_full_profile(self):
        """The returned profile should contain all expected top-level fields."""
        response = client.get("/api/roles/backend-engineer")
        profile = response.json()
        required_fields = {
            "id", "canonical_title", "role_family", "core_skills",
            "recommended_skills", "description", "responsibilities",
        }
        assert required_fields.issubset(set(profile.keys()))

    def test_get_role_unknown_id_returns_404(self):
        """GET /api/roles/nonexistent should respond with 404."""
        response = client.get("/api/roles/nonexistent")
        assert response.status_code == 404

    def test_get_harness_engineer(self):
        """The harness-engineer profile should be retrievable."""
        response = client.get("/api/roles/harness-engineer")
        assert response.status_code == 200
        data = response.json()
        assert data["canonical_title"] == "Harness Engineer"


# ---------------------------------------------------------------------------
# Skills analysis API endpoint tests
# ---------------------------------------------------------------------------


class TestSkillsAPI:
    """Tests for POST /api/skills/analyze."""

    def test_analyze_valid_role_returns_200(self):
        """POST /api/skills/analyze with valid payload should return 200."""
        payload = {
            "text": "Python FastAPI Docker PostgreSQL Redis git REST API",
            "role_id": "backend-engineer",
        }
        response = client.post("/api/skills/analyze", json=payload)
        assert response.status_code == 200

    def test_analyze_response_shape(self):
        """Response must contain all expected top-level fields."""
        payload = {"text": "Python FastAPI Docker", "role_id": "backend-engineer"}
        response = client.post("/api/skills/analyze", json=payload)
        data = response.json()
        required_keys = {
            "role_id", "role_title", "matched_skills", "missing_skills",
            "uncertain_skills", "coverage_percent", "coverage_note",
            "total_core_skills", "matched_core_skills", "priority_gaps",
        }
        assert required_keys.issubset(set(data.keys()))

    def test_analyze_unknown_role_returns_404(self):
        """POST /api/skills/analyze with unknown role_id should return 404."""
        payload = {"text": "Python FastAPI", "role_id": "nonexistent"}
        response = client.post("/api/skills/analyze", json=payload)
        assert response.status_code == 404

    def test_analyze_coverage_all_core(self):
        """Full core skill coverage should yield 100 %."""
        # backend-engineer core: python, fastapi, postgresql, redis, docker, rest_api, git
        payload = {
            "text": "Python FastAPI PostgreSQL Redis Docker REST API git",
            "role_id": "backend-engineer",
        }
        response = client.post("/api/skills/analyze", json=payload)
        data = response.json()
        assert data["coverage_percent"] == pytest.approx(100.0, abs=1.0)

    def test_analyze_coverage_empty_text(self):
        """Empty text should yield 0 % coverage."""
        payload = {"text": "", "role_id": "backend-engineer"}
        response = client.post("/api/skills/analyze", json=payload)
        data = response.json()
        assert data["coverage_percent"] == pytest.approx(0.0, abs=0.1)
        assert data["matched_core_skills"] == 0

    def test_analyze_missing_text_field_returns_422(self):
        """Request missing required fields should return 422 Unprocessable Entity."""
        response = client.post("/api/skills/analyze", json={"role_id": "backend-engineer"})
        assert response.status_code == 422

    def test_analyze_llmops_role(self):
        """Analysis should work for the llmops-engineer role."""
        payload = {
            "text": "Python MLflow OpenAI API prompt engineering Docker git",
            "role_id": "llmops-engineer",
        }
        response = client.post("/api/skills/analyze", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["role_title"] == "LLMOps Engineer"

