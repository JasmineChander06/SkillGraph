"""Phase 5 tests: 6-Week Learning Roadmap generation, prerequisite ordering, and API endpoint."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.roadmap_generator import generate_roadmap

client = TestClient(app)


# ---------------------------------------------------------------------------
# Roadmap Generator Service Unit Tests
# ---------------------------------------------------------------------------


class TestRoadmapGeneratorService:
    """Unit tests for the 6-week roadmap generation service."""

    def test_six_week_structure(self):
        """The generated roadmap must contain exactly 6 weeks in chronological order."""
        roadmap = generate_roadmap(
            role_id="backend-engineer",
            existing_skills=["git"],
            weekly_hours=10,
        )
        assert roadmap.total_weeks == 6
        assert len(roadmap.weeks) == 6
        week_numbers = [w.week_number for w in roadmap.weeks]
        assert week_numbers == [1, 2, 3, 4, 5, 6]

    def test_every_task_has_required_fields(self):
        """Every task in the roadmap must contain all required attributes."""
        roadmap = generate_roadmap(
            role_id="backend-engineer",
            existing_skills=[],
            weekly_hours=10,
        )
        assert len(roadmap.tasks) > 0
        for task in roadmap.tasks:
            assert task.title
            assert task.description
            assert task.target_skill
            assert 1 <= task.week <= 6
            assert task.estimated_effort >= 1
            assert isinstance(task.prerequisites, list)
            assert task.learning_resource is not None
            assert task.learning_resource.title
            assert task.completion_status == "pending"

    def test_prerequisite_ordering_python_before_fastapi(self):
        """Foundational prerequisites (e.g. Python) must be scheduled in a week <= dependent frameworks (FastAPI)."""
        # User lacks both Python and FastAPI
        roadmap = generate_roadmap(
            role_id="backend-engineer",
            existing_skills=["git"],
            weekly_hours=12,
        )
        python_tasks = [t for t in roadmap.tasks if "python" in t.target_skill.lower()]
        fastapi_tasks = [t for t in roadmap.tasks if "fastapi" in t.target_skill.lower()]

        if python_tasks and fastapi_tasks:
            python_week = min(t.week for t in python_tasks)
            fastapi_week = min(t.week for t in fastapi_tasks)
            assert python_week <= fastapi_week, (
                f"Python (week {python_week}) must precede or coincide with FastAPI (week {fastapi_week})"
            )

    def test_prerequisite_ordering_docker_before_kubernetes(self):
        """Docker must be scheduled in a week <= Kubernetes."""
        roadmap = generate_roadmap(
            role_id="harness-engineer",
            existing_skills=[],
            weekly_hours=12,
        )
        docker_tasks = [t for t in roadmap.tasks if "docker" in t.target_skill.lower()]
        k8s_tasks = [t for t in roadmap.tasks if "kubernetes" in t.target_skill.lower()]

        if docker_tasks and k8s_tasks:
            docker_week = min(t.week for t in docker_tasks)
            k8s_week = min(t.week for t in k8s_tasks)
            assert docker_week <= k8s_week, (
                f"Docker (week {docker_week}) must precede or coincide with Kubernetes (week {k8s_week})"
            )

    def test_role_specific_capstone_project_harness_engineer(self):
        """Harness Engineer roadmap must feature a deployment pipeline / harness capstone project."""
        roadmap = generate_roadmap(role_id="harness-engineer")
        assert roadmap.capstone_project
        # Week 6 must include the capstone task
        week_6_tasks = roadmap.weeks[5].tasks
        assert any("capstone" in t.title.lower() for t in week_6_tasks)
        assert any("harness" in roadmap.capstone_project.lower() or "pipeline" in roadmap.capstone_project.lower() for t in week_6_tasks)

    def test_role_specific_capstone_project_ai_agent_engineer(self):
        """AI Agent Engineer roadmap must feature an agentic / ReAct capstone project."""
        roadmap = generate_roadmap(role_id="ai-agent-engineer")
        assert roadmap.capstone_project
        week_6_tasks = roadmap.weeks[5].tasks
        assert any("capstone" in t.title.lower() for t in week_6_tasks)

    def test_avoid_recommending_entire_catalogue(self):
        """The roadmap must remain focused (no more than 7 skills scheduled) rather than dumping all skills."""
        roadmap = generate_roadmap(role_id="backend-engineer", existing_skills=[])
        unique_skills = {t.target_skill for t in roadmap.tasks if t.target_skill != "Backend Engineer"}
        # Must not dump the entire ~60-skill catalogue
        assert len(unique_skills) <= 7

    def test_empty_skill_gap_generates_mastery_roadmap(self):
        """When candidate already meets all core skills, generate an advanced mastery roadmap without errors."""
        all_backend_core = ["python", "fastapi", "postgresql", "redis", "docker", "rest_api", "git"]
        roadmap = generate_roadmap(
            role_id="backend-engineer",
            existing_skills=all_backend_core,
            weekly_hours=10,
        )
        assert roadmap.total_weeks == 6
        assert len(roadmap.tasks) > 0
        # Should include mastery note
        assert any("mastery" in n.lower() or "already meets" in n.lower() for n in roadmap.notes)

    def test_unknown_role_raises_key_error(self):
        """Requesting an unknown role ID must raise KeyError."""
        with pytest.raises(KeyError):
            generate_roadmap(role_id="nonexistent-role-id")

    def test_effort_limits_and_weekly_hours_budget(self):
        """Weekly hours allocated per week must reasonably align with weekly_hours availability."""
        target_hours = 15
        roadmap = generate_roadmap(
            role_id="backend-engineer",
            weekly_hours=target_hours,
        )
        assert roadmap.target_weekly_hours == target_hours
        for week in roadmap.weeks:
            # Each week should not drastically exceed the user's weekly availability
            assert week.weekly_hours_allocated <= target_hours * 1.5

    def test_resource_verification_labels(self):
        """Official documentation resources must be verified; unverified guides must be labeled."""
        roadmap = generate_roadmap(role_id="backend-engineer")
        verified_count = 0
        unverified_count = 0

        for task in roadmap.tasks:
            res = task.learning_resource
            if res.is_verified:
                assert res.url is not None
                assert "Verified" in res.verification_status
                verified_count += 1
            else:
                assert "Requires verification" in res.verification_status
                unverified_count += 1

        # At least some standard core skills should have verified official docs
        assert verified_count >= 1


# ---------------------------------------------------------------------------
# Roadmap API Endpoint Integration Tests
# ---------------------------------------------------------------------------


class TestRoadmapAPI:
    """Integration tests for POST /api/roadmaps/generate."""

    def test_generate_roadmap_success(self):
        """POST /api/roadmaps/generate with valid payload returns 200 and complete schema."""
        payload = {
            "role_id": "backend-engineer",
            "existing_skills": ["python", "git"],
            "weekly_hours": 10,
        }
        response = client.post("/api/roadmaps/generate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["role_id"] == "backend-engineer"
        assert data["total_weeks"] == 6
        assert len(data["weeks"]) == 6
        assert len(data["tasks"]) >= 6
        assert "capstone_project" in data
        assert "prerequisite_chains" in data
        assert "notes" in data

    def test_generate_roadmap_with_resume_text(self):
        """POST with resume_text extracts skills and customizes roadmap."""
        payload = {
            "role_id": "backend-engineer",
            "resume_text": "Experienced Python developer with Docker and Git.",
            "weekly_hours": 8,
        }
        response = client.post("/api/roadmaps/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["target_weekly_hours"] == 8

    def test_generate_roadmap_unknown_role_returns_404(self):
        """POST with unknown role_id returns 404 Not Found."""
        payload = {
            "role_id": "nonexistent-engineer",
            "weekly_hours": 10,
        }
        response = client.post("/api/roadmaps/generate", json=payload)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_generate_roadmap_invalid_weekly_hours_returns_422(self):
        """POST with weekly_hours < 1 returns 422 Unprocessable Content."""
        payload = {
            "role_id": "backend-engineer",
            "weekly_hours": 0,
        }
        response = client.post("/api/roadmaps/generate", json=payload)
        assert response.status_code == 422

    def test_generate_roadmap_harness_engineer_endpoint(self):
        """POST for harness-engineer returns complete 6-week roadmap."""
        payload = {
            "role_id": "harness-engineer",
            "weekly_hours": 12,
        }
        response = client.post("/api/roadmaps/generate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["role_title"] == "Harness Engineer"
        assert len(data["weeks"]) == 6

