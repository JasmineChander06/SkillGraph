"""Tests for Role Discovery, Relationships, Role Comparisons, and Evidence-Aware Market Summaries."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import market_insights, role_discovery

client = TestClient(app)


# ---------------------------------------------------------------------------
# Unit & Taxonomy Tests: Emerging vs Established Roles
# ---------------------------------------------------------------------------

class TestRoleTaxonomyAndEmergingRoles:
    """Tests verifying role classification, maturity, and entry-level accessibility."""

    def test_all_expanded_taxonomy_roles_present(self):
        roles = role_discovery.list_roles_explorer()
        assert len(roles) == 11
        role_ids = {r["id"] for r in roles}

        # Check required expanded roles
        assert "harness-engineer" in role_ids
        assert "forward-deployed-engineer" in role_ids
        assert "ai-agent-engineer" in role_ids
        assert "llmops-engineer" in role_ids
        assert "ai-evaluation-engineer" in role_ids
        assert "ai-infrastructure-engineer" in role_ids

    def test_emerging_roles_delineation(self):
        """Emerging roles must not be described as equally established."""
        emerging_ids = [
            "harness-engineer",
            "forward-deployed-engineer",
            "ai-agent-engineer",
            "llmops-engineer",
            "ai-evaluation-engineer",
            "ai-infrastructure-engineer",
        ]
        for role_id in emerging_ids:
            details = role_discovery.get_role_full_details(role_id)
            assert details is not None
            assert details["maturity"] == "emerging"
            assert details["emerging_context"] is not None
            assert len(details["emerging_context"]) > 20

    def test_established_roles_delineation(self):
        """Established roles must carry established maturity status without emerging flags."""
        established_ids = ["backend-engineer", "data-analyst", "data-engineer", "machine-learning-engineer"]
        for role_id in established_ids:
            details = role_discovery.get_role_full_details(role_id)
            assert details is not None
            assert details["maturity"] == "established"
            assert details["emerging_context"] is None

    def test_entry_level_accessibility_warnings(self):
        """Specialized emerging roles must NOT be marked accessible to entry-level candidates."""
        # Advanced/emerging roles must not be entry-accessible
        not_entry_accessible = [
            "ai-infrastructure-engineer",
            "llmops-engineer",
            "ai-evaluation-engineer",
            "harness-engineer",
            "forward-deployed-engineer",
        ]
        for role_id in not_entry_accessible:
            details = role_discovery.get_role_full_details(role_id)
            assert details["entry_level_accessible"] is False
            assert "not" in details["accessibility_guidance"].lower() or "requires" in details["accessibility_guidance"].lower()

        # Data analyst and backend engineer are accessible
        data_analyst = role_discovery.get_role_full_details("data-analyst")
        assert data_analyst["entry_level_accessible"] is True

    def test_filter_roles_by_family(self):
        ai_roles = role_discovery.list_roles_explorer(family="AI/ML")
        assert len(ai_roles) >= 4
        for r in ai_roles:
            assert r["role_family"] == "AI/ML"

    def test_filter_roles_by_maturity(self):
        emerging = role_discovery.list_roles_explorer(maturity="emerging")
        established = role_discovery.list_roles_explorer(maturity="established")
        assert len(emerging) == 7
        assert len(established) == 4
        assert len(emerging) + len(established) == 11

    def test_search_roles_by_query(self):
        eval_roles = role_discovery.list_roles_explorer(query="evaluation")
        assert any(r["id"] == "ai-evaluation-engineer" for r in eval_roles)

        agent_roles = role_discovery.list_roles_explorer(query="Agent")
        assert len(agent_roles) == 1
        assert agent_roles[0]["id"] == "ai-agent-engineer"


# ---------------------------------------------------------------------------
# Unit Tests: Role Details Structure
# ---------------------------------------------------------------------------

class TestRoleDetailsStructure:
    """Verify that every role page payload contains all required attributes."""

    @pytest.mark.parametrize("role_id", [
        "harness-engineer",
        "forward-deployed-engineer",
        "ai-agent-engineer",
        "llmops-engineer",
        "ai-evaluation-engineer",
        "ai-infrastructure-engineer",
        "backend-engineer",
    ])
    def test_role_details_mandatory_fields(self, role_id):
        details = role_discovery.get_role_full_details(role_id)
        assert details is not None

        # Verify all sections required by prompt
        assert "responsibilities" in details and len(details["responsibilities"]) >= 3
        assert "prerequisites" in details
        assert "core_skills" in details and len(details["core_skills"]) >= 5
        assert "optional_skills" in details
        assert "example_projects" in details and len(details["example_projects"]) >= 2
        assert "related_roles" in details and len(details["related_roles"]) >= 1
        assert "market_summary" in details

        # Verify enriched skill details
        for skill in details["core_skills_details"]:
            assert "id" in skill
            assert "canonical_name" in skill
            assert "category" in skill
            assert "estimated_hours" in skill


# ---------------------------------------------------------------------------
# Unit Tests: Related Roles & Relationships
# ---------------------------------------------------------------------------

class TestRoleRelationships:
    """Verify related role suggestions and Jaccard similarity metrics."""

    def test_related_roles_returns_ranked_suggestions(self):
        related = role_discovery.get_related_roles("backend-engineer", top_n=3)
        assert len(related) == 3

        # Related roles should not contain the role itself
        related_ids = [r["role_id"] for r in related]
        assert "backend-engineer" not in related_ids

        # Scores should be sorted descending
        scores = [r["overlap_percentage"] for r in related]
        assert scores == sorted(scores, reverse=True)

    def test_related_roles_includes_shared_and_bridge_skills(self):
        related = role_discovery.get_related_roles("backend-engineer", top_n=2)
        first = related[0]
        assert "shared_skills" in first
        assert "bridge_skills" in first
        assert isinstance(first["overlap_percentage"], float)
        assert 0.0 <= first["overlap_percentage"] <= 100.0

    def test_llmops_related_to_ai_infrastructure(self):
        related = role_discovery.get_related_roles("llmops-engineer", top_n=5)
        related_ids = [r["role_id"] for r in related]
        # LLMOps shares container, kubernetes, and cloud infra with AI Infra
        assert "ai-infrastructure-engineer" in related_ids


# ---------------------------------------------------------------------------
# Unit Tests: Role Comparisons & Skill Overlap
# ---------------------------------------------------------------------------

class TestRoleComparison:
    """Verify bidirectional role comparison and bridge skill calculations."""

    def test_compare_backend_and_data_engineer(self):
        comparison = role_discovery.compare_roles("backend-engineer", "data-engineer")

        assert comparison["role_a"]["id"] == "backend-engineer"
        assert comparison["role_b"]["id"] == "data-engineer"

        shared_ids = {s["id"] for s in comparison["shared_core_skills"]}
        unique_a_ids = {s["id"] for s in comparison["unique_to_role_a"]}
        unique_b_ids = {s["id"] for s in comparison["unique_to_role_b"]}

        # Python and Docker are core to both
        assert "python" in shared_ids
        assert "docker" in shared_ids

        # FastAPI is unique to Backend Engineer
        assert "fastapi" in unique_a_ids
        # Airflow and Spark are unique to Data Engineer
        assert "airflow" in unique_b_ids
        assert "spark" in unique_b_ids

        # Transition bridges
        bridge_a_to_b = comparison["transition_a_to_b"]
        assert bridge_a_to_b["bridge_skills_count"] == len(unique_b_ids)
        assert bridge_a_to_b["estimated_hours"] > 0

        bridge_b_to_a = comparison["transition_b_to_a"]
        assert bridge_b_to_a["bridge_skills_count"] == len(unique_a_ids)
        assert bridge_b_to_a["estimated_hours"] > 0

        # Overlap percentage
        assert 0.0 < comparison["overlap_percentage"] < 100.0

    def test_compare_same_role_has_full_overlap(self):
        comparison = role_discovery.compare_roles("backend-engineer", "backend-engineer")
        assert comparison["overlap_percentage"] == 100.0
        assert len(comparison["unique_to_role_a"]) == 0
        assert len(comparison["unique_to_role_b"]) == 0
        assert comparison["transition_a_to_b"]["estimated_hours"] == 0

    def test_compare_nonexistent_role_raises_keyerror(self):
        with pytest.raises(KeyError):
            role_discovery.compare_roles("backend-engineer", "unknown-role")


# ---------------------------------------------------------------------------
# Unit & Integration Tests: Evidence-Aware Market Summaries
# ---------------------------------------------------------------------------

class TestMarketSummaryCalculations:
    """Verify evidence-aware market summaries: verified datasets vs curated guidance."""

    def test_verified_role_market_summary(self):
        """Backend Engineer has a verified empirical sample with documented provenance."""
        summary = market_insights.get_market_summary("backend-engineer")
        assert summary["has_verified_data"] is True
        assert "metadata" in summary

        meta = summary["metadata"]
        assert meta["source"] == "US Tech Job Postings Public Archive (Q4 2024 - Q1 2025)"
        assert meta["geography"] == "US-Remote"
        assert meta["sample_size"] == 120
        assert meta["skill_detection_method"] == "SkillGraph-Regex-v1.0"

        # Check skill frequencies
        top_req = summary["top_required_skills"]
        assert len(top_req) > 0
        python_skill = next((s for s in top_req if s["skill_id"] == "python"), None)
        assert python_skill is not None
        assert python_skill["frequency_count"] == 96
        assert python_skill["frequency_percent"] == 80.0

    def test_emerging_role_transparent_curated_guidance(self):
        """AI Evaluation Engineer has no verified large-sample dataset; must display curated guidance."""
        summary = market_insights.get_market_summary("ai-evaluation-engineer")
        assert summary["has_verified_data"] is False
        assert summary["guidance_type"] == "curated_competency_framework"
        assert "Curated guidance" in summary["data_notice"]
        assert "strictly prohibits" in summary["data_notice"]
        assert "curated_skills" in summary
        assert len(summary["curated_skills"]) > 0

    def test_calculate_market_summary_under_threshold(self):
        """Fewer than 5 records must return insufficient sample guidance without fake stats."""
        records = [
            {"required_skills": [{"skill_id": "python"}], "preferred_skills": []},
            {"required_skills": [{"skill_id": "docker"}], "preferred_skills": []},
        ]
        summary = market_insights.calculate_market_summary_from_records(records, "custom-role")
        assert summary["has_verified_data"] is False
        assert summary["guidance_type"] == "insufficient_sample"
        assert "below statistical reporting threshold" in summary["data_notice"]

    def test_calculate_market_summary_sufficient_sample(self):
        """5 or more records calculates genuine empirical percentages."""
        records = [
            {"required_skills": [{"skill_id": "python"}], "preferred_skills": [{"skill_id": "docker"}]},
            {"required_skills": [{"skill_id": "python"}, {"skill_id": "sql"}], "preferred_skills": []},
            {"required_skills": [{"skill_id": "python"}], "preferred_skills": [{"skill_id": "docker"}]},
            {"required_skills": [{"skill_id": "sql"}], "preferred_skills": [{"skill_id": "docker"}]},
            {"required_skills": [{"skill_id": "python"}], "preferred_skills": []},
        ]
        summary = market_insights.calculate_market_summary_from_records(
            records=records,
            role_id="custom-role",
            source_label="Test Real Job Feed",
            geography="Global-Remote",
            collection_date="2026-11-03",
        )
        assert summary["has_verified_data"] is True
        assert summary["metadata"]["sample_size"] == 5
        assert summary["metadata"]["source"] == "Test Real Job Feed"

        # Python is required in 4 out of 5 postings (80.0%)
        top_req = summary["top_required_skills"]
        py_item = next(s for s in top_req if s["skill_id"] == "python")
        assert py_item["frequency_count"] == 4
        assert py_item["frequency_percent"] == 80.0

        # Docker is preferred in 3 out of 5 postings (60.0%)
        top_pref = summary["top_preferred_skills"]
        dock_item = next(s for s in top_pref if s["skill_id"] == "docker")
        assert dock_item["frequency_count"] == 3
        assert dock_item["frequency_percent"] == 60.0


# ---------------------------------------------------------------------------
# API Integration Tests
# ---------------------------------------------------------------------------

class TestRolesEndpointsIntegration:
    """Verify HTTP contracts for newly added /api/roles endpoints."""

    def test_roles_explorer_endpoint(self):
        res = client.get("/api/roles?maturity=emerging")
        assert res.status_code == 200
        data = res.json()
        assert "roles" in data
        assert len(data["roles"]) == 7
        for r in data["roles"]:
            assert r["maturity"] == "emerging"

    def test_compare_endpoint_success(self):
        res = client.get("/api/roles/compare?role_a=backend-engineer&role_b=data-engineer")
        assert res.status_code == 200
        data = res.json()
        assert "shared_core_skills" in data
        assert "unique_to_role_a" in data
        assert "unique_to_role_b" in data
        assert "overlap_percentage" in data
        assert "transition_a_to_b" in data

    def test_compare_endpoint_missing_param_returns_422(self):
        res = client.get("/api/roles/compare?role_a=backend-engineer")
        assert res.status_code == 422

    def test_compare_endpoint_unknown_role_returns_404(self):
        res = client.get("/api/roles/compare?role_a=backend-engineer&role_b=fake-role")
        assert res.status_code == 404

    def test_role_details_endpoint_contains_rich_structure(self):
        res = client.get("/api/roles/harness-engineer")
        assert res.status_code == 200
        data = res.json()
        assert data["canonical_title"] == "Harness Engineer"
        assert data["maturity"] == "emerging"
        assert "responsibilities" in data
        assert "prerequisites" in data
        assert "example_projects" in data
        assert "related_roles" in data
        assert "market_summary" in data

    def test_related_roles_endpoint(self):
        res = client.get("/api/roles/ai-agent-engineer/related?top_n=3")
        assert res.status_code == 200
        data = res.json()
        assert "related_roles" in data
        assert len(data["related_roles"]) <= 3
        for rel in data["related_roles"]:
            assert "overlap_percentage" in rel
            assert "bridge_skills" in rel

    def test_market_summary_endpoint(self):
        res = client.get("/api/roles/backend-engineer/market-summary")
        assert res.status_code == 200
        data = res.json()
        assert data["role_id"] == "backend-engineer"
        assert data["has_verified_data"] is True
