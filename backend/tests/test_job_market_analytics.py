"""Tests for Job Market Analytics and Trends service."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.job_market_analytics import compute_market_trends

client = TestClient(app)


def test_compute_market_trends_all_families():
    """Verify compute_market_trends returns skills, categories, and maturity counts."""
    data = compute_market_trends()
    assert data["total_roles_analyzed"] == 11
    assert "top_in_demand_skills" in data
    assert len(data["top_in_demand_skills"]) >= 8
    assert "category_distribution" in data
    assert "maturity_breakdown" in data
    assert data["maturity_breakdown"]["established_roles"] == 4
    assert data["maturity_breakdown"]["emerging_roles"] == 7
    assert "skill_pairs" in data
    assert len(data["empirical_benchmarks"]) == 3


def test_compute_market_trends_filter_family():
    """Verify market trends can be filtered by role family."""
    data = compute_market_trends(family="AI/ML")
    assert data["total_roles_analyzed"] > 0
    assert data["total_roles_analyzed"] < 11
    assert data["role_family_filter"] == "AI/ML"


def test_get_market_trends_api_endpoint():
    """Verify GET /api/job-descriptions/market-trends returns 200 with schema."""
    response = client.get("/api/job-descriptions/market-trends")
    assert response.status_code == 200
    res_data = response.json()
    assert "top_in_demand_skills" in res_data
    assert "category_distribution" in res_data
    assert "skill_pairs" in res_data
    assert "methodology_disclaimer" in res_data

