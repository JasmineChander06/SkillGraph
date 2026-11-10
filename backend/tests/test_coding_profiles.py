"""Tests for Technical Coding Profiles (GitHub & LeetCode) Integration."""

import anyio
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services.coding_profiles import (
    analyze_coding_profiles,
    fetch_github_signal,
    fetch_leetcode_signal,
)

client = TestClient(app)


def test_github_signal_mock():
    """Verify GitHub signal parses repos, stargazers, and primary languages properly."""
    async def run():
        def mock_handler(request: httpx.Request):
            url = str(request.url)
            if "/users/octocat/repos" in url:
                return httpx.Response(200, json=[
                    {"name": "repo1", "stargazers_count": 12, "language": "Python"},
                    {"name": "repo2", "stargazers_count": 8, "language": "TypeScript"},
                    {"name": "repo3", "stargazers_count": 5, "language": "Python"},
                ])
            elif "/users/octocat" in url:
                return httpx.Response(200, json={
                    "login": "octocat",
                    "name": "The Octocat",
                    "avatar_url": "https://avatars.githubusercontent.com/u/583231",
                    "public_repos": 8,
                    "followers": 25,
                })
            return httpx.Response(404)

        mock_transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=mock_transport) as mock_client:
            signal = await fetch_github_signal("octocat", client=mock_client)

        assert signal is not None
        assert signal.username == "octocat"
        assert signal.public_repos == 8
        assert signal.total_stars == 25
        assert "Python" in signal.primary_languages
        assert signal.quality_score >= 50

    anyio.run(run)


def test_leetcode_signal_mock():
    """Verify LeetCode signal extracts problem counts and calculates DSA readiness."""
    async def run():
        def mock_handler(request: httpx.Request):
            return httpx.Response(200, json={
                "data": {
                    "matchedUser": {
                        "username": "tourist",
                        "profile": {"ranking": 45000},
                        "submitStatsGlobal": {
                            "acSubmissionNum": [
                                {"difficulty": "All", "count": 220},
                                {"difficulty": "Easy", "count": 60},
                                {"difficulty": "Medium", "count": 130},
                                {"difficulty": "Hard", "count": 30},
                            ]
                        }
                    }
                }
            })

        mock_transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=mock_transport) as mock_client:
            signal = await fetch_leetcode_signal("tourist", client=mock_client)

        assert signal is not None
        assert signal.username == "tourist"
        assert signal.total_solved == 220
        assert signal.medium_solved == 130
        assert signal.hard_solved == 30
        assert signal.dsa_readiness_score >= 80
        assert signal.dsa_readiness_tier == "Interview Ready"
        assert len(signal.interview_recommendations) > 0

    anyio.run(run)


def test_combined_profiles_analysis():
    """Verify analyze_coding_profiles calculates a combined score."""
    async def run():
        def mock_handler(request: httpx.Request):
            url = str(request.url)
            if "github.com" in url:
                if "/repos" in url:
                    return httpx.Response(200, json=[{"name": "app", "stargazers_count": 5, "language": "Python"}])
                return httpx.Response(200, json={"login": "dev", "public_repos": 4, "followers": 2})
            elif "leetcode.com" in url:
                return httpx.Response(200, json={
                    "data": {
                        "matchedUser": {
                            "username": "dev",
                            "profile": {"ranking": 120000},
                            "submitStatsGlobal": {
                                "acSubmissionNum": [
                                    {"difficulty": "All", "count": 55},
                                    {"difficulty": "Easy", "count": 35},
                                    {"difficulty": "Medium", "count": 20},
                                    {"difficulty": "Hard", "count": 0},
                                ]
                            }
                        }
                    }
                })
            return httpx.Response(404)

        mock_transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=mock_transport) as mock_client:
            report = await analyze_coding_profiles(
                github_username="dev",
                leetcode_username="dev",
                client=mock_client,
            )

        assert report.github is not None
        assert report.leetcode is not None
        assert report.combined_signal_score > 0
        assert len(report.strengths) >= 2

    anyio.run(run)


def test_github_project_evidence_and_three_tier_breakdown():
    """Verify repo projects demonstrated skills and 3-tier competency breakdown."""
    async def run():
        def mock_handler(request: httpx.Request):
            url = str(request.url)
            if "/users/alice/repos" in url:
                return httpx.Response(200, json=[
                    {
                        "name": "fastapi-service",
                        "description": "Production REST API built with FastAPI, Docker, and PostgreSQL",
                        "language": "Python",
                        "topics": ["fastapi", "docker", "postgresql"],
                        "stargazers_count": 10,
                        "html_url": "https://github.com/alice/fastapi-service",
                    }
                ])
            elif "/users/alice" in url:
                return httpx.Response(200, json={
                    "login": "alice",
                    "public_repos": 1,
                    "followers": 5,
                })
            return httpx.Response(404)

        mock_transport = httpx.MockTransport(mock_handler)
        async with httpx.AsyncClient(transport=mock_transport) as mock_client:
            report = await analyze_coding_profiles(
                github_username="alice",
                user_skills=["Python", "Git", "SQL"],
                target_role="backend-engineer",
                client=mock_client,
            )

        assert report.github is not None
        assert len(report.github.top_projects) == 1
        proj = report.github.top_projects[0]
        assert proj.name == "fastapi-service"
        assert any("python" in s.lower() or "fastapi" in s.lower() for s in proj.demonstrated_skills)

        # 3-tier breakdown check
        assert report.skills_breakdown is not None
        assert "Python" in report.skills_breakdown.resume_skills
        assert len(report.skills_breakdown.coding_verified_skills) > 0
        assert isinstance(report.skills_breakdown.skills_needing_evidence, list)

    anyio.run(run)


def test_api_profiles_endpoint_empty_payload_returns_422():
    """POST /api/profiles/analyze with neither username must return 422."""
    response = client.post("/api/profiles/analyze", json={})
    assert response.status_code == 422


def test_api_profiles_endpoint_whitespace_returns_422():
    """POST /api/profiles/analyze with whitespace handles must return 422."""
    response = client.post("/api/profiles/analyze", json={"github_username": "   "})
    assert response.status_code == 422
