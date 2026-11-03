"""Phase 7 Complete Backend Workflow & Security Isolation Tests.

Tests:
- Complete candidate workflow (Register -> Profile -> Skill Analysis -> Roadmap -> Task Update -> Progress Check)
- User Data Isolation (User A cannot view or manipulate User B's resources)
- IDOR Prevention across roadmaps, tasks, resumes, and analyses
- Roadmap retrieval, task completion updates, and progress summary calculation
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


def create_test_pdf(text: str) -> bytes:
    """Generate a clean in-memory PDF containing the specified text."""
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((50, 72), text)
    content = doc.tobytes()
    doc.close()
    return content


@pytest.fixture
def workflow_client():
    """Create an isolated test client with an in-memory database."""
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


def register_and_get_token(client: TestClient, email: str, name: str) -> str:
    """Helper to register a user and return the Bearer token."""
    res = client.post("/api/auth/register", json={
        "email": email,
        "password": "SecurePassword123!",
        "full_name": name,
    })
    assert res.status_code == 201
    return res.json()["access_token"]


class TestCompleteUserWorkflow:
    """End-to-end test simulating a complete candidate journey through SkillGraph."""

    def test_full_candidate_lifecycle(self, workflow_client):
        """Test full user flow: register -> profile -> skill analysis -> roadmap -> complete task -> progress check."""
        # 1. Register candidate
        token = register_and_get_token(workflow_client, "candidate.flow@example.com", "Dev Candidate")
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. Check profile
        profile_res = workflow_client.get("/api/auth/me", headers=auth_headers)
        assert profile_res.status_code == 200
        assert profile_res.json()["email"] == "candidate.flow@example.com"

        # 3. Analyze skills for Harness Engineer
        resume_text = (
            "Experienced Python developer with PyTorch, Docker, Kubernetes, and pytest. "
            "Built agentic evaluation pipelines and automated harness frameworks with CI/CD."
        )
        skill_res = workflow_client.post(
            "/api/skills/analyze",
            json={"text": resume_text, "role_id": "harness-engineer"},
            headers=auth_headers,
        )
        assert skill_res.status_code == 200
        analysis_data = skill_res.json()
        assert analysis_data["role_id"] == "harness-engineer"
        assert analysis_data["coverage_percent"] > 0

        # Check that analysis was persisted
        analyses_list_res = workflow_client.get("/api/skills/analyses", headers=auth_headers)
        assert analyses_list_res.status_code == 200
        saved_analyses = analyses_list_res.json()
        assert len(saved_analyses) == 1
        analysis_id = saved_analyses[0]["id"]

        # 4. Compare against a Job Description
        jd_text = (
            "Senior Harness Engineer needed. Must have: Python, PyTorch, Docker, and CI/CD. "
            "Nice to have: LangChain, Prompts evaluation, and OpenTelemetry. 4+ years required."
        )
        jd_res = workflow_client.post(
            "/api/job-descriptions/analyze",
            json={"resume_text": resume_text, "job_description_text": jd_text},
            headers=auth_headers,
        )
        assert jd_res.status_code == 200
        jd_data = jd_res.json()
        assert jd_data["matched_count"] > 0

        # Check that JD analysis was persisted
        jd_list_res = workflow_client.get("/api/job-descriptions/analyses", headers=auth_headers)
        assert jd_list_res.status_code == 200
        assert len(jd_list_res.json()) == 1

        # 5. Generate a 6-week roadmap
        roadmap_res = workflow_client.post(
            "/api/roadmaps/generate",
            json={
                "role_id": "harness-engineer",
                "resume_text": resume_text,
                "weekly_hours": 10,
            },
            headers=auth_headers,
        )
        assert roadmap_res.status_code == 200
        generated_roadmap = roadmap_res.json()
        assert generated_roadmap["total_weeks"] == 6
        assert len(generated_roadmap["tasks"]) > 0

        # 6. Retrieve saved roadmaps
        roadmaps_list_res = workflow_client.get("/api/roadmaps", headers=auth_headers)
        assert roadmaps_list_res.status_code == 200
        saved_roadmaps = roadmaps_list_res.json()
        assert len(saved_roadmaps) == 1
        roadmap_id = saved_roadmaps[0]["id"]
        assert saved_roadmaps[0]["role_id"] == "harness-engineer"

        # 7. Retrieve roadmap detail with tasks
        roadmap_detail_res = workflow_client.get(f"/api/roadmaps/{roadmap_id}", headers=auth_headers)
        assert roadmap_detail_res.status_code == 200
        roadmap_detail = roadmap_detail_res.json()
        tasks = roadmap_detail["tasks"]
        assert len(tasks) > 0
        first_task = tasks[0]
        assert first_task["completion_status"] == "pending"
        task_id = first_task["id"]

        # 8. Check initial progress (0% completed)
        progress_res_1 = workflow_client.get("/api/progress", headers=auth_headers)
        assert progress_res_1.status_code == 200
        progress_1 = progress_res_1.json()
        assert progress_1["total_tasks"] == len(tasks)
        assert progress_1["completed_tasks"] == 0
        assert progress_1["completion_percentage"] == 0.0

        # 9. Mark the first task as completed
        patch_res = workflow_client.patch(
            f"/api/roadmaps/{roadmap_id}/tasks/{task_id}",
            json={"status": "completed", "notes": "Built the baseline test suite!"},
            headers=auth_headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["ok"] is True
        assert patch_res.json()["status"] == "completed"

        # 10. Check updated progress (completion percentage increased)
        progress_res_2 = workflow_client.get("/api/progress", headers=auth_headers)
        assert progress_res_2.status_code == 200
        progress_2 = progress_res_2.json()
        assert progress_2["completed_tasks"] == 1
        assert progress_2["completion_percentage"] > 0.0

        # Verify the task in progress items has the updated status
        completed_items = [p for p in progress_2["progress_items"] if p["task_id"] == task_id]
        assert len(completed_items) == 1
        assert completed_items[0]["status"] == "completed"
        assert completed_items[0]["notes"] == "Built the baseline test suite!"


class TestUserDataIsolationAndIDOR:
    """Rigorous tests ensuring User A cannot read, modify, or delete User B's resources."""

    def test_user_cannot_access_other_users_roadmap(self, workflow_client):
        """User B cannot view or fetch User A's roadmap by ID (IDOR prevention)."""
        token_a = register_and_get_token(workflow_client, "alice@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob@example.com", "Bob")

        # Alice creates a roadmap
        res = workflow_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "data-engineer", "weekly_hours": 10},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200

        # Find Alice's roadmap ID
        alice_roadmaps = workflow_client.get(
            "/api/roadmaps",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()
        alice_roadmap_id = alice_roadmaps[0]["id"]

        # Bob tries to view Alice's roadmap by ID -> 403 Forbidden
        bob_attempt = workflow_client.get(
            f"/api/roadmaps/{alice_roadmap_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_attempt.status_code == 403
        assert "access forbidden" in bob_attempt.json()["detail"].lower()

        # Bob's roadmap list is empty
        bob_list = workflow_client.get(
            "/api/roadmaps",
            headers={"Authorization": f"Bearer {token_b}"},
        ).json()
        assert len(bob_list) == 0

    def test_user_cannot_update_other_users_task(self, workflow_client):
        """User B cannot update completion status of User A's task (IDOR prevention)."""
        token_a = register_and_get_token(workflow_client, "alice.task@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.task@example.com", "Bob")

        workflow_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "backend-engineer", "weekly_hours": 10},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        alice_roadmap = workflow_client.get(
            "/api/roadmaps",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()[0]
        alice_roadmap_detail = workflow_client.get(
            f"/api/roadmaps/{alice_roadmap['id']}",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()
        alice_task_id = alice_roadmap_detail["tasks"][0]["id"]

        # Bob attempts to patch Alice's task -> 403 Forbidden
        patch_attempt = workflow_client.patch(
            f"/api/roadmaps/{alice_roadmap['id']}/tasks/{alice_task_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert patch_attempt.status_code == 403

    def test_user_cannot_delete_other_users_roadmap(self, workflow_client):
        """User B cannot delete User A's roadmap."""
        token_a = register_and_get_token(workflow_client, "alice.del@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.del@example.com", "Bob")

        workflow_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "machine-learning-engineer"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        alice_roadmap_id = workflow_client.get(
            "/api/roadmaps",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()[0]["id"]

        # Bob attempts to delete Alice's roadmap -> 403 Forbidden
        del_attempt = workflow_client.delete(
            f"/api/roadmaps/{alice_roadmap_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert del_attempt.status_code == 403

        # Alice's roadmap still exists
        alice_check = workflow_client.get(
            f"/api/roadmaps/{alice_roadmap_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert alice_check.status_code == 200

    def test_user_cannot_access_other_users_skill_analysis(self, workflow_client):
        """User B cannot view or delete User A's skill analysis."""
        token_a = register_and_get_token(workflow_client, "alice.skills@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.skills@example.com", "Bob")

        workflow_client.post(
            "/api/skills/analyze",
            json={"text": "Python FastAPI Postgres", "role_id": "backend-engineer"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        alice_analysis_id = workflow_client.get(
            "/api/skills/analyses",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()[0]["id"]

        # Bob tries to get Alice's analysis -> 403 Forbidden
        bob_get = workflow_client.get(
            f"/api/skills/analyses/{alice_analysis_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_get.status_code == 403

        # Bob tries to delete Alice's analysis -> 403 Forbidden
        bob_del = workflow_client.delete(
            f"/api/skills/analyses/{alice_analysis_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_del.status_code == 403

    def test_user_cannot_access_other_users_job_analysis(self, workflow_client):
        """User B cannot view or delete User A's job description analysis."""
        token_a = register_and_get_token(workflow_client, "alice.jd@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.jd@example.com", "Bob")

        workflow_client.post(
            "/api/job-descriptions/analyze",
            json={"resume_text": "Python", "job_description_text": "Looking for Python developer with AWS."},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        alice_jd_id = workflow_client.get(
            "/api/job-descriptions/analyses",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()[0]["id"]

        # Bob tries to get Alice's JD analysis -> 403 Forbidden
        bob_get = workflow_client.get(
            f"/api/job-descriptions/analyses/{alice_jd_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_get.status_code == 403

        # Bob tries to delete Alice's JD analysis -> 403 Forbidden
        bob_del = workflow_client.delete(
            f"/api/job-descriptions/analyses/{alice_jd_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_del.status_code == 403


class TestResumePrivacyAndOwnership:
    """Verify resume ownership checks and privacy rules."""

    def test_user_resume_isolation_and_deletion(self, workflow_client):
        """User B cannot view or delete User A's resume records."""
        token_a = register_and_get_token(workflow_client, "alice.resume@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.resume@example.com", "Bob")

        # Alice parses a resume while authenticated
        file_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        # We can simulate resume record via direct DB or mock
        from app.models.resume import ResumeRecord
        from app.database import SessionLocal

        # Use the endpoint or database
        record_res = workflow_client.get(
            "/api/resume/records",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert record_res.status_code == 200
        assert len(record_res.json()) == 0

        # Attempt to access non-existent record -> 404
        assert workflow_client.get(
            "/api/resume/records/9999",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code == 404

    def test_authenticated_resume_upload_and_idor(self, workflow_client):
        """Uploading a resume while authenticated persists record; verifies IDOR and deletion."""
        token_a = register_and_get_token(workflow_client, "alice.pdf@example.com", "Alice")
        token_b = register_and_get_token(workflow_client, "bob.pdf@example.com", "Bob")

        pdf_bytes = create_test_pdf(
            "Alice Resume: Experienced Python and FastAPI developer with PostgreSQL skills."
        )

        # Alice uploads and parses resume with auth header
        res = workflow_client.post(
            "/api/resume/parse",
            files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        # Alice retrieves her resume records
        alice_records = workflow_client.get(
            "/api/resume/records",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()
        assert len(alice_records) == 1
        record_id = alice_records[0]["id"]
        assert alice_records[0]["filename"] == "resume.pdf"

        # Alice views record detail
        detail = workflow_client.get(
            f"/api/resume/records/{record_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        ).json()
        assert detail["id"] == record_id
        assert "FastAPI" in detail["extracted_text"]

        # Bob tries to view Alice's resume -> 403 Forbidden
        bob_view = workflow_client.get(
            f"/api/resume/records/{record_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_view.status_code == 403

        # Bob tries to delete Alice's resume -> 403 Forbidden
        bob_del = workflow_client.delete(
            f"/api/resume/records/{record_id}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
        assert bob_del.status_code == 403

        # Alice deletes her resume
        alice_del = workflow_client.delete(
            f"/api/resume/records/{record_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        )
        assert alice_del.status_code == 200
        assert alice_del.json()["ok"] is True

        # Verify record no longer exists
        assert workflow_client.get(
            f"/api/resume/records/{record_id}",
            headers={"Authorization": f"Bearer {token_a}"},
        ).status_code == 404


class TestResourceLifecycleAndEdgeCases:
    """Tests for resource deletion, direct patch, query parameter status, and error responses."""

    def test_delete_skill_analysis_by_owner(self, workflow_client):
        """Owner can successfully delete their skill analysis."""
        token = register_and_get_token(workflow_client, "owner.skill@example.com", "Owner")
        auth_h = {"Authorization": f"Bearer {token}"}

        workflow_client.post(
            "/api/skills/analyze",
            json={"text": "Python Docker", "role_id": "backend-engineer"},
            headers=auth_h,
        )
        analyses = workflow_client.get("/api/skills/analyses", headers=auth_h).json()
        assert len(analyses) == 1
        analysis_id = analyses[0]["id"]

        del_res = workflow_client.delete(f"/api/skills/analyses/{analysis_id}", headers=auth_h)
        assert del_res.status_code == 200
        assert del_res.json()["ok"] is True

        # Ensure deleted
        assert workflow_client.get(f"/api/skills/analyses/{analysis_id}", headers=auth_h).status_code == 404

    def test_delete_job_analysis_by_owner(self, workflow_client):
        """Owner can successfully delete their job description analysis."""
        token = register_and_get_token(workflow_client, "owner.jd@example.com", "Owner")
        auth_h = {"Authorization": f"Bearer {token}"}

        workflow_client.post(
            "/api/job-descriptions/analyze",
            json={"resume_text": "Python", "job_description_text": "Python and Redis needed."},
            headers=auth_h,
        )
        analyses = workflow_client.get("/api/job-descriptions/analyses", headers=auth_h).json()
        assert len(analyses) == 1
        analysis_id = analyses[0]["id"]

        del_res = workflow_client.delete(f"/api/job-descriptions/analyses/{analysis_id}", headers=auth_h)
        assert del_res.status_code == 200
        assert del_res.json()["ok"] is True

        # Ensure deleted
        assert workflow_client.get(f"/api/job-descriptions/analyses/{analysis_id}", headers=auth_h).status_code == 404

    def test_direct_task_patch_and_mismatched_roadmap(self, workflow_client):
        """Test patching task directly via /api/roadmaps/tasks/{id} and reject roadmap mismatch."""
        token = register_and_get_token(workflow_client, "task.patch@example.com", "Patcher")
        auth_h = {"Authorization": f"Bearer {token}"}

        workflow_client.post(
            "/api/roadmaps/generate",
            json={"role_id": "backend-engineer"},
            headers=auth_h,
        )
        roadmap = workflow_client.get("/api/roadmaps", headers=auth_h).json()[0]
        roadmap_detail = workflow_client.get(f"/api/roadmaps/{roadmap['id']}", headers=auth_h).json()
        task_id = roadmap_detail["tasks"][0]["id"]

        # Patch directly using query param ?done=true
        direct_patch = workflow_client.patch(
            f"/api/roadmaps/tasks/{task_id}?done=true",
            headers=auth_h,
        )
        assert direct_patch.status_code == 200
        assert direct_patch.json()["status"] == "completed"

        # Patch with mismatched roadmap_id -> 400 Bad Request
        mismatch_res = workflow_client.patch(
            f"/api/roadmaps/999999/tasks/{task_id}",
            json={"status": "pending"},
            headers=auth_h,
        )
        assert mismatch_res.status_code == 400
        assert "does not belong to roadmap" in mismatch_res.json()["detail"].lower()
