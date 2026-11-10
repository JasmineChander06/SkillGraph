"""Comprehensive Audit Tests: Security, Two-Account User Isolation, and Full E2E Journey."""

from __future__ import annotations

import io
import json
import uuid
from datetime import timedelta

import pymupdf
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, init_db
from app.main import app
from app.services.auth import create_access_token


def make_test_pdf(text: str) -> bytes:
    """Generate in-memory test PDF."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    content = doc.tobytes()
    doc.close()
    return content


@pytest.fixture
def audit_client():
    """Isolated test client with an in-memory database."""
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


class TestSecurityAndUserIsolation:
    """Verify strict multi-tenant user isolation and IDOR protection across all endpoints."""

    def test_two_accounts_cannot_access_or_modify_each_others_resumes(self, audit_client):
        # 1. Register User A
        res_a = audit_client.post("/api/auth/register", json={
            "email": "user_a@example.com",
            "password": "Password123!",
            "full_name": "User Alpha"
        })
        token_a = res_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        # 2. Register User B
        res_b = audit_client.post("/api/auth/register", json={
            "email": "user_b@example.com",
            "password": "Password123!",
            "full_name": "User Beta"
        })
        token_b = res_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 3. User B uploads a resume
        pdf_b = make_test_pdf("User Beta: Python, Kubernetes, Terraform engineer.")
        upload_b = audit_client.post(
            "/api/resume/parse",
            files={"file": ("resume_beta.pdf", pdf_b, "application/pdf")},
            headers=headers_b,
        )
        assert upload_b.status_code == 200

        records_b = audit_client.get("/api/resume/records", headers=headers_b).json()
        assert len(records_b) == 1
        rec_id_b = records_b[0]["id"]

        # 4. User A attempts to view User B's resume details -> MUST return 403 Forbidden
        idor_get = audit_client.get(f"/api/resume/records/{rec_id_b}", headers=headers_a)
        assert idor_get.status_code == 403
        assert "forbidden" in idor_get.json()["detail"].lower()

        # 5. User A attempts to edit User B's confirmed skills -> MUST return 403 Forbidden
        idor_put = audit_client.put(
            f"/api/resume/records/{rec_id_b}/skills",
            json={"skills": ["HackedSkill"]},
            headers=headers_a,
        )
        assert idor_put.status_code == 403

        # 6. User A attempts to delete User B's resume -> MUST return 403 Forbidden
        idor_del = audit_client.delete(f"/api/resume/records/{rec_id_b}", headers=headers_a)
        assert idor_del.status_code == 403

        # 7. Verify User B's resume was NOT modified or deleted
        check_b = audit_client.get(f"/api/resume/records/{rec_id_b}", headers=headers_b)
        assert check_b.status_code == 200
        assert check_b.json()["filename"] == "resume_beta.pdf"

    def test_two_accounts_cannot_access_or_modify_each_others_roadmaps(self, audit_client):
        # 1. Setup User A and User B
        res_a = audit_client.post("/api/auth/register", json={
            "email": "user_a2@example.com",
            "password": "Password123!",
            "full_name": "User Alpha 2"
        })
        headers_a = {"Authorization": f"Bearer {res_a.json()['access_token']}"}

        res_b = audit_client.post("/api/auth/register", json={
            "email": "user_b2@example.com",
            "password": "Password123!",
            "full_name": "User Beta 2"
        })
        headers_b = {"Authorization": f"Bearer {res_b.json()['access_token']}"}

        # 2. User B generates a roadmap
        gen_b = audit_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "backend-engineer", "weekly_hours": 10},
            headers=headers_b,
        )
        assert gen_b.status_code == 200

        roadmaps_b = audit_client.get("/api/roadmaps", headers=headers_b).json()
        assert len(roadmaps_b) == 1
        rmap_id_b = roadmaps_b[0]["id"]

        detail_b = audit_client.get(f"/api/roadmaps/{rmap_id_b}", headers=headers_b).json()
        task_id_b = detail_b["tasks"][0]["id"]

        # 3. User A tries to view User B's roadmap -> 403
        idor_get = audit_client.get(f"/api/roadmaps/{rmap_id_b}", headers=headers_a)
        assert idor_get.status_code == 403

        # 4. User A tries to update User B's task status -> 403
        idor_patch = audit_client.patch(
            f"/api/roadmaps/{rmap_id_b}/tasks/{task_id_b}",
            json={"status": "completed"},
            headers=headers_a,
        )
        assert idor_patch.status_code == 403

        # 5. User A tries to delete User B's roadmap -> 403
        idor_del = audit_client.delete(f"/api/roadmaps/{rmap_id_b}", headers=headers_a)
        assert idor_del.status_code == 403

        # 6. User A's roadmaps list is empty
        roadmaps_a = audit_client.get("/api/roadmaps", headers=headers_a).json()
        assert len(roadmaps_a) == 0

    def test_unauthenticated_requests_are_rejected(self, audit_client):
        """Protected endpoints must strictly return 401 Unauthorized without a valid Bearer token."""
        assert audit_client.get("/api/auth/me").status_code == 401
        assert audit_client.get("/api/resume/records").status_code == 401
        assert audit_client.get("/api/roadmaps").status_code == 401
        assert audit_client.get("/api/progress").status_code == 401
        assert audit_client.put("/api/resume/skills", json={"skills": ["Python"]}).status_code == 401

    def test_expired_token_is_rejected(self, audit_client):
        """Expired JWT tokens must return 401 Unauthorized."""
        expired_token = create_access_token(
            data={"sub": "1", "email": "test@example.com"},
            expires_delta=timedelta(seconds=-10),
        )
        res = audit_client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert res.status_code == 401

    def test_forged_signature_token_is_rejected(self, audit_client):
        """Tampered tokens must fail cryptographic signature verification."""
        valid_token = create_access_token(data={"sub": "1", "email": "test@example.com"})
        tampered_token = valid_token[:-4] + "fake"
        res = audit_client.get("/api/auth/me", headers={"Authorization": f"Bearer {tampered_token}"})
        assert res.status_code == 401


class TestFullEndToEndUserJourney:
    """Verify complete 10-step user workflow with real data persistence."""

    def test_complete_career_readiness_lifecycle(self, audit_client):
        # 1. Register Account
        reg_res = audit_client.post("/api/auth/register", json={
            "email": "career.engineer@example.com",
            "password": "SecurePassword999!",
            "full_name": "Alex Mercer"
        })
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Login
        login_res = audit_client.post("/api/auth/login", json={
            "email": "career.engineer@example.com",
            "password": "SecurePassword999!"
        })
        assert login_res.status_code == 200

        # 3. Calibration / Profile Onboarding
        onboard_res = audit_client.post("/api/auth/onboarding", json={
            "education_stage": "Early Career Engineer (0-2 yrs)",
            "career_interests": "Distributed Systems, Backend APIs",
            "skill_level": "Intermediate",
            "target_role": "backend-engineer",
            "secondary_role": "data-engineer"
        }, headers=headers)
        assert onboard_res.status_code == 200
        user_prof = onboard_res.json()
        assert user_prof["target_role"] == "backend-engineer"
        assert user_prof["secondary_role"] == "data-engineer"

        # 4. Upload Resume
        pdf_bytes = make_test_pdf(
            "Alex Mercer. Software Engineer. Proficient in Python, SQL, Git, Linux. "
            "Building web services with basic Docker."
        )
        upload_res = audit_client.post(
            "/api/resume/parse",
            files={"file": ("alex_mercer_resume.pdf", pdf_bytes, "application/pdf")},
            headers=headers,
        )
        assert upload_res.status_code == 200
        parsed = upload_res.json()
        assert parsed["success"] is True

        # 5. Extract and Review Skills (Edit / Add skills)
        confirmed_skills = ["Python", "SQL", "Git", "Docker", "FastAPI", "PostgreSQL"]
        update_skills_res = audit_client.put(
            "/api/resume/skills",
            json={"skills": confirmed_skills},
            headers=headers,
        )
        assert update_skills_res.status_code == 200

        # 6. Two-Role Comparison with User Skills
        compare_res = audit_client.get(
            "/api/roles/compare?role_a=backend-engineer&role_b=data-engineer",
            headers=headers,
        )
        assert compare_res.status_code == 200
        comp = compare_res.json()
        assert comp["overlap_percentage"] > 0
        assert comp["user_comparison"]["has_user_skills"] is True
        assert comp["user_comparison"]["role_a"]["readiness_percent"] > 0
        assert comp["user_comparison"]["role_b"]["readiness_percent"] > 0

        # 7. Generate Personalized 6-Week Roadmap (auto-using confirmed skills)
        roadmap_res = audit_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "backend-engineer", "weekly_hours": 12},
            headers=headers,
        )
        assert roadmap_res.status_code == 200
        roadmap = roadmap_res.json()
        assert roadmap["role_id"] == "backend-engineer"
        assert roadmap["total_weeks"] == 6
        assert len(roadmap["tasks"]) > 0
        assert roadmap["capstone_project"] is not None

        # 8. Check Progress Tracking & Toggle Checkbox Task
        roadmaps_list = audit_client.get("/api/roadmaps", headers=headers).json()
        assert len(roadmaps_list) == 1
        roadmap_id = roadmaps_list[0]["id"]

        full_roadmap = audit_client.get(f"/api/roadmaps/{roadmap_id}", headers=headers).json()
        first_task = full_roadmap["tasks"][0]
        assert first_task["completion_status"] == "pending"

        # Complete the first task
        task_update = audit_client.patch(
            f"/api/roadmaps/{roadmap_id}/tasks/{first_task['id']}",
            json={"status": "completed"},
            headers=headers,
        )
        assert task_update.status_code == 200
        assert task_update.json()["status"] == "completed"

        # 9. Verify Progress Summary & Dashboard
        progress_res = audit_client.get("/api/progress", headers=headers)
        assert progress_res.status_code == 200
        progress_data = progress_res.json()
        assert progress_data["completed_tasks"] >= 1
        assert progress_data["completion_percentage"] > 0

        # 10. Verify Data Retention after Simulated Refresh
        # Refetching /api/auth/me, /api/resume/records, and /api/roadmaps
        refreshed_me = audit_client.get("/api/auth/me", headers=headers).json()
        assert refreshed_me["target_role"] == "backend-engineer"
        assert refreshed_me["secondary_role"] == "data-engineer"

        refreshed_resumes = audit_client.get("/api/resume/records", headers=headers).json()
        assert len(refreshed_resumes) == 1

        refreshed_roadmaps = audit_client.get("/api/roadmaps", headers=headers).json()
        assert len(refreshed_roadmaps) == 1
        assert refreshed_roadmaps[0]["completed_tasks"] >= 1
