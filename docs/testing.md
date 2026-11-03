# SkillGraph Backend Verification & Testing Guide

> **Document Version:** 1.0.0  
> **Test Framework:** Pytest 9.2.0  
> **Environment:** Python 3.13.7 (Windows / Virtual Environment)  
> **Latest Suite Run:** 122 passed, 0 failed, 4 warnings in 6.62s  

---

## 1. Testing Philosophy & Verification Standard

A passing `GET /api/health` endpoint only verifies that the web server process is responsive. It provides zero guarantees regarding:
* Cryptographic security of credentials.
* Accurate skill boundary extraction and alias deduplication.
* Correctness of prerequisite ordering and effort distribution in roadmaps.
* Referential integrity and cascading deletion in the persistence layer.
* Cross-tenant data isolation and Insecure Direct Object Reference (IDOR) prevention.

SkillGraph enforces an evidence-based testing methodology where **every core business workflow, data persistence model, and authentication gate is verified with automated deterministic test fixtures**.

---

## 2. Test Architecture & Fixture Isolation

### In-Memory Database Isolation
Tests executing database operations use an isolated SQLite in-memory database:
```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
```
* **`StaticPool`**: Ensures that all connections opened by FastAPI dependency calls (`get_db`) share the same in-memory SQLite state during a single test case.
* **`app.dependency_overrides[get_db]`**: Overrides the database session generator on a per-test basis.
* **Teardown**: Calls `Base.metadata.drop_all(bind=engine)` and clears dependency overrides after each test.
* **No persistent disk pollution**: Zero temporary files left on disk during automated test runs.

---

## 3. Test Suite Inventory

| Test Suite File | Test Count | Domain Covered | Status |
| :--- | :---: | :--- | :---: |
| `tests/test_auth.py` | 16 | User registration, login, token expiry, tampering, password hashing. | **16 / 16 PASSED** |
| `tests/test_workflow.py` | 11 | End-to-end user lifecycle, IDOR prevention, ownership verification, progress tracking. | **11 / 11 PASSED** |
| `tests/test_database.py` | 11 | Schema creation, constraints, relationships, cascading deletion, restart simulation. | **11 / 11 PASSED** |
| `tests/test_skills.py` | 36 | Skill extraction boundaries, case-insensitivity, aliases, role profiling, gap analysis. | **36 / 36 PASSED** |
| `tests/test_job_description.py` | 17 | JD segmentation, experience extraction, required vs preferred classification, coverage. | **17 / 17 PASSED** |
| `tests/test_roadmap.py` | 16 | 6-week curriculum generation, prerequisite chains, effort limits, resource verification. | **16 / 16 PASSED** |
| `tests/test_resume.py` | 10 | PDF/DOCX byte parsing, magic bytes, spoofing rejection, corruption handling, OCR flags. | **10 / 10 PASSED** |
| `tests/test_health.py` | 5 | Health check payload, root greeting, CORS allowed origins, disallowed origin rejection. | **5 / 5 PASSED** |
| **Total** | **122** | **Full Backend Pipeline** | **122 / 122 PASSED** |

---

## 4. Comprehensive Endpoint Verification Matrix

Every implemented endpoint in the application has been mapped to automated test assertions:

| Endpoint | Method | Auth Required | Automated Test Function | Verified Status |
| :--- | :---: | :---: | :--- | :---: |
| `/api/health` | GET | No | `test_health.py::test_health_check_returns_200` | PASSED |
| `/` | GET | No | `test_health.py::test_root_endpoint` | PASSED |
| `/api/auth/register` | POST | No | `test_auth.py::TestUserRegistration::test_register_success` | PASSED |
| `/auth/signup` | POST | No | `test_auth.py::TestUserRegistration::test_register_architecture_compat_endpoint` | PASSED |
| `/api/auth/login` | POST | No | `test_auth.py::TestUserLogin::test_login_success` | PASSED |
| `/auth/login` | POST | No | `test_auth.py::TestUserLogin::test_login_architecture_compat_endpoint` | PASSED |
| `/api/auth/me` | GET | Yes | `test_auth.py::TestTokenSecurityAndValidation::test_get_current_user_profile_success` | PASSED |
| `/api/resume/parse` | POST | Optional | `test_resume.py::test_parse_valid_pdf` | PASSED |
| `/api/resume/records` | GET | Yes | `test_workflow.py::TestResumePrivacyAndOwnership::test_authenticated_resume_upload_and_idor` | PASSED |
| `/api/resume/records/{id}` | GET | Yes | `test_workflow.py::TestResumePrivacyAndOwnership::test_authenticated_resume_upload_and_idor` | PASSED |
| `/api/resume/records/{id}` | DELETE | Yes | `test_workflow.py::TestResumePrivacyAndOwnership::test_authenticated_resume_upload_and_idor` | PASSED |
| `/api/roles/` | GET | No | `test_skills.py::TestRolesAPI::test_list_roles_returns_all_eleven` | PASSED |
| `/api/roles/{role_id}` | GET | No | `test_skills.py::TestRolesAPI::test_get_role_by_id_returns_full_profile` | PASSED |
| `/api/skills/analyze` | POST | Optional | `test_skills.py::TestSkillsAPI::test_analyze_valid_role_returns_200` | PASSED |
| `/api/skills/analyses` | GET | Yes | `test_workflow.py::TestCompleteUserWorkflow::test_full_candidate_lifecycle` | PASSED |
| `/api/skills/analyses/{id}` | GET | Yes | `test_workflow.py::TestUserDataIsolationAndIDOR::test_user_cannot_access_other_users_skill_analysis` | PASSED |
| `/api/skills/analyses/{id}` | DELETE | Yes | `test_workflow.py::TestResourceLifecycleAndEdgeCases::test_delete_skill_analysis_by_owner` | PASSED |
| `/api/job-descriptions/analyze` | POST | Optional | `test_job_description.py::TestJobDescriptionAPI::test_analyze_endpoint_success` | PASSED |
| `/api/job-descriptions/analyses` | GET | Yes | `test_workflow.py::TestCompleteUserWorkflow::test_full_candidate_lifecycle` | PASSED |
| `/api/job-descriptions/analyses/{id}` | GET | Yes | `test_workflow.py::TestUserDataIsolationAndIDOR::test_user_cannot_access_other_users_job_analysis` | PASSED |
| `/api/job-descriptions/analyses/{id}` | DELETE | Yes | `test_workflow.py::TestResourceLifecycleAndEdgeCases::test_delete_job_analysis_by_owner` | PASSED |
| `/api/roadmaps/generate` | POST | Optional | `test_roadmap.py::TestRoadmapAPI::test_generate_roadmap_success` | PASSED |
| `/api/roadmaps` | GET | Yes | `test_workflow.py::TestCompleteUserWorkflow::test_full_candidate_lifecycle` | PASSED |
| `/api/roadmaps/{roadmap_id}` | GET | Yes | `test_workflow.py::TestUserDataIsolationAndIDOR::test_user_cannot_access_other_users_roadmap` | PASSED |
| `/api/roadmaps/{roadmap_id}` | DELETE | Yes | `test_workflow.py::TestUserDataIsolationAndIDOR::test_user_cannot_delete_other_users_roadmap` | PASSED |
| `/api/roadmaps/{r_id}/tasks/{t_id}` | PATCH | Yes | `test_workflow.py::TestCompleteUserWorkflow::test_full_candidate_lifecycle` | PASSED |
| `/api/roadmaps/tasks/{t_id}` | PATCH | Yes | `test_workflow.py::TestResourceLifecycleAndEdgeCases::test_direct_task_patch_and_mismatched_roadmap` | PASSED |
| `/api/progress` | GET | Yes | `test_workflow.py::TestCompleteUserWorkflow::test_full_candidate_lifecycle` | PASSED |

---

## 5. Security & Data Isolation Audit

### Password Security
* **Algorithm:** PBKDF2-HMAC-SHA256 with 100,000 iterations and a random 16-byte salt.
* **Verified in `test_auth.py`:**
  - Hashes are never identical for the same password across users (`test_two_identical_passwords_have_unique_salts`).
  - Plaintext is absent from database fields (`test_passwords_are_never_plaintext`).
  - Timing-safe verification using `secrets.compare_digest`.

### Insecure Direct Object Reference (IDOR) Protection
* **Verified in `test_workflow.py`:**
  - **Roadmaps:** User B cannot read (`GET /api/roadmaps/{alice_id}`) or delete (`DELETE /api/roadmaps/{alice_id}`) Alice's roadmap. Returns `403 Forbidden`.
  - **Tasks:** User B cannot update Alice's roadmap tasks (`PATCH /api/roadmaps/{alice_r_id}/tasks/{alice_t_id}`). Returns `403 Forbidden`.
  - **Resumes:** User B cannot fetch or delete Alice's parsed resume records. Returns `403 Forbidden`.
  - **Analyses:** User B cannot inspect Alice's skill-gap or JD comparisons. Returns `403 Forbidden`.
  - **Mismatched Roadmaps:** Attempting to update a task with an unassociated roadmap ID returns `400 Bad Request`.

---

## 6. Passing Tests vs Untested / Out-of-Scope Behaviors

To maintain absolute documentation integrity, the boundaries of current test coverage are delineated below:

### What IS Formally Verified & Passing (122 Tests)
1. **Resume Text Ingestion:** PDF and DOCX parsing, memory-only processing, rejection of spoofed extensions, rejection of files > 5 MB, detection of empty/scanned PDFs.
2. **Deterministic Skill Extraction:** Boundary matching (no false positives for `C` in `C++` or `Java` in `JavaScript`), case-insensitive alias mapping, deduplication.
3. **Role Profile Validation:** All 11 role profiles (Harness Engineer, Forward Deployed Engineer, Forward Deployed AI Engineer, AI Agent Engineer, LLMOps Engineer, AI Evaluation Engineer, AI Infrastructure Engineer, Data Analyst, Data Engineer, Machine Learning Engineer, Backend Engineer).
4. **Roadmap Curriculum Generation:** Pedagogical 6-week progression, prerequisite chains, weekly study hour constraints, capstone projects, verified resource links.
5. **Job Description Extraction:** Section segmentation (required vs preferred), tenure extraction, coverage calculation, transparent analytical caveats.
6. **Authentication & JWT Lifecycle:** Registration, duplicate email rejection (409), password length validation (422), login verification, token signing, expiration checking, signature tampering detection.
7. **Relational Persistence:** In-memory and file-backed SQLite transactions, cascading deletions (deleting user purges all subordinate records), progress state surviving application restarts.

### What is Explicitly UNTESTED or Out-of-Scope in Current Phase
1. **Live Web Scraping:** Scraping live job boards (LinkedIn, Indeed) is intentionally avoided in accordance with ethical standards and project specifications.
2. **Third-Party OAuth / SSO:** Social sign-in providers (GitHub OAuth, Google OAuth) are not yet implemented; only email/password Bearer token auth is active.
3. **Production PostgreSQL / pgvector:** Tests run against SQLite. Alembic migrations and PostgreSQL `pgvector` schemas are reserved for cloud deployment phases.
4. **Email Dispatching:** User registration does not send transactional activation emails (SMTP/SES integration is unconfigured).
5. **Frontend Client UI:** The vanilla JavaScript single-page application is not tested within the Python `pytest` suite.

---

## 7. How to Execute the Test Suite

From the repository root on Windows:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m pytest -v
```

To run a specific test suite:
```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_auth.py -v
.\.venv\Scripts\python.exe -m pytest tests/test_workflow.py -v
```

To run with coverage reporting (if `pytest-cov` is installed):
```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app tests/
```

