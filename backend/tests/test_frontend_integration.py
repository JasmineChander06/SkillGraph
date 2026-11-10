"""Integration test verifying full frontend-backend workflow contracts.

Verifies:
- Registration, login, and authenticated Bearer requests
- Static asset serving for HTML, CSS, and JS
- In-memory PDF upload via multipart FormData
- Role retrieval (all 11 profiles)
- Skill-gap analysis (matched, missing, uncertain)
- Job-description analysis
- Roadmap generation, retrieval, and task patch
- Progress retrieval and persistence
- Token invalidation / expired token rejection
"""

from __future__ import annotations

import io
import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, init_db
from app.main import app


@pytest.fixture
def integration_client():
    """Create isolated test client with in-memory SQLite and StaticPool."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    init_db(bind_engine=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_static_frontend_files_served(integration_client):
    """Verify all HTML pages and assets are served with HTTP 200."""
    routes = [
        "/frontend/index.html",
        "/frontend/dashboard.html",
        "/frontend/roles.html",
        "/frontend/roadmap.html",
        "/frontend/resume-review.html",
        "/frontend/coding.html",
        "/frontend/analytics.html",
        "/frontend/css/variables.css",
        "/frontend/css/style.css",
        "/frontend/css/components.css",
        "/frontend/css/dashboard.css",
        "/frontend/css/roadmap.css",
        "/frontend/js/config.js",
        "/frontend/js/api.js",
        "/frontend/js/app.js",
        "/frontend/js/dashboard.js",
        "/frontend/js/roles.js",
        "/frontend/js/roadmap.js",
        "/frontend/js/resume-review.js",
        "/frontend/js/coding.js",
        "/frontend/js/analytics.js",
    ]
    for r in routes:
        res = integration_client.get(r)
        assert res.status_code == 200, f"Route {r} returned {res.status_code}"
        assert len(res.content) > 0


def test_complete_frontend_backend_integration_lifecycle(integration_client):
    """Execute complete end-to-end user workflow matching frontend UI interactions."""

    # 1. Registration
    reg_res = integration_client.post("/api/auth/register", json={
        "email": "frontend.user@example.com",
        "password": "StrongPassword123!",
        "full_name": "Frontend Tester"
    })
    assert reg_res.status_code == 201
    auth_data = reg_res.json()
    assert "access_token" in auth_data
    assert auth_data["user"]["email"] == "frontend.user@example.com"
    token = auth_data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Login
    login_res = integration_client.post("/api/auth/login", json={
        "email": "frontend.user@example.com",
        "password": "StrongPassword123!"
    })
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # 3. Authenticated profile
    me_res = integration_client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["full_name"] == "Frontend Tester"

    # 4. Role retrieval & discovery
    roles_res = integration_client.get("/api/roles/")
    assert roles_res.status_code == 200
    roles_data = roles_res.json()
    roles = roles_data.get("roles", roles_data)
    assert len(roles) == 11
    role_ids = [r["id"] for r in roles]
    assert "harness-engineer" in role_ids
    assert "backend-engineer" in role_ids

    # 4b. Role details, comparison & market summary
    detail_res = integration_client.get("/api/roles/backend-engineer")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["canonical_title"] == "Backend Engineer"
    assert "market_summary" in detail_data
    assert "related_roles" in detail_data

    compare_res = integration_client.get("/api/roles/compare?role_a=backend-engineer&role_b=harness-engineer")
    assert compare_res.status_code == 200
    assert "shared_core_skills" in compare_res.json()
    assert "overlap_percentage" in compare_res.json()

    # 5. Resume upload using FormData
    doc = pymupdf.open()
    page = doc.new_page()
    resume_text = (
        "Frontend Tester. Experienced Python engineer with Docker, Kubernetes, "
        "PyTorch, eval harnesses, pytest, and CI/CD pipelines."
    )
    page.insert_text((50, 72), resume_text)
    pdf_bytes = doc.tobytes()
    doc.close()

    upload_res = integration_client.post(
        "/api/resume/parse",
        files={"file": ("candidate_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 200
    parsed = upload_res.json()
    assert parsed["success"] is True
    assert "Docker" in parsed["text"]

    # Check that resume was persisted
    resumes_res = integration_client.get("/api/resume/records", headers=headers)
    assert resumes_res.status_code == 200
    assert len(resumes_res.json()) == 1

    # 6. Skill-gap analysis
    skill_res = integration_client.post(
        "/api/skills/analyze",
        json={"text": parsed["text"], "role_id": "harness-engineer"},
        headers=headers,
    )
    assert skill_res.status_code == 200
    analysis = skill_res.json()
    assert analysis["role_id"] == "harness-engineer"
    assert len(analysis["matched_skills"]) > 0
    assert "coverage_percent" in analysis
    assert "missing_skills" in analysis
    assert "uncertain_skills" in analysis

    # 7. Job description analysis
    jd_res = integration_client.post(
        "/api/job-descriptions/analyze",
        json={
            "resume_text": parsed["text"],
            "job_description_text": "Required: Python, Docker, CI/CD. Preferred: PyTorch. 3+ years experience required."
        },
        headers=headers,
    )
    assert jd_res.status_code == 200
    jd_analysis = jd_res.json()
    assert jd_analysis["matched_count"] > 0
    assert len(jd_analysis["experience_requirements"]) >= 1

    # 8. Roadmap generation
    roadmap_res = integration_client.post(
        "/api/roadmaps/generate",
        json={
            "role_id": "harness-engineer",
            "weekly_hours": 10,
            "resume_text": parsed["text"]
        },
        headers=headers,
    )
    assert roadmap_res.status_code == 200
    generated = roadmap_res.json()
    assert generated["total_weeks"] == 6
    assert len(generated["tasks"]) > 0
    assert "capstone_project" in generated

    # 9. Roadmap retrieval
    list_roadmaps_res = integration_client.get("/api/roadmaps", headers=headers)
    assert list_roadmaps_res.status_code == 200
    saved_roadmaps = list_roadmaps_res.json()
    assert len(saved_roadmaps) == 1
    roadmap_id = saved_roadmaps[0]["id"]

    get_roadmap_res = integration_client.get(f"/api/roadmaps/{roadmap_id}", headers=headers)
    assert get_roadmap_res.status_code == 200
    retrieved = get_roadmap_res.json()
    first_task = retrieved["tasks"][0]
    first_task_id = first_task["id"]
    assert first_task["completion_status"] == "pending"

    # 10. Task completion update
    patch_res = integration_client.patch(
        f"/api/roadmaps/{roadmap_id}/tasks/{first_task_id}",
        json={"status": "completed", "notes": "Completed initial harness setup"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["ok"] is True
    assert patch_res.json()["status"] == "completed"

    # 11. Progress retrieval after update
    progress_res = integration_client.get("/api/progress", headers=headers)
    assert progress_res.status_code == 200
    progress = progress_res.json()
    assert progress["total_tasks"] > 0
    assert progress["completed_tasks"] == 1
    assert progress["completion_percentage"] > 0.0
    assert progress["active_roadmaps_count"] == 1

    # 12. Expired / Invalid token rejection (HTTP 401)
    invalid_res = integration_client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.token"})
    assert invalid_res.status_code == 401

    # 13. Resume critique & suggestions
    critique_res = integration_client.post(
        "/api/resume/critique",
        json={"text": parsed["text"]},
        headers=headers,
    )
    assert critique_res.status_code == 200
    critique = critique_res.json()
    assert "overall_score" in critique
    assert "rating_label" in critique
    assert "dimension_scores" in critique
    assert len(critique["bullet_improvements"]) > 0

    # 14. Market trends analytics
    trends_res = integration_client.get("/api/job-descriptions/market-trends")
    assert trends_res.status_code == 200
    trends = trends_res.json()
    assert trends["total_roles_analyzed"] == 11
    assert len(trends["top_in_demand_skills"]) > 0

    # 15. Coding profiles validation rejection (empty payload)
    prof_invalid = integration_client.post("/api/profiles/analyze", json={})
    assert prof_invalid.status_code == 422
