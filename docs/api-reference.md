# SkillGraph API Reference Manual

> **Base URL:** `http://127.0.0.1:8000`  
> **API Version:** `1.0.0`  
> **Interactive Documentation:** `/docs` (Swagger UI) and `/redoc` (ReDoc)  
> **OpenAPI Specification:** `/openapi.json`  

---

## 1. Authentication & Security Conventions

### Authentication Scheme
SkillGraph uses standard HTTP Bearer token authentication with JSON Web Tokens (JWT) signed with HMAC-SHA256 (`HS256`).

* **Header Format:** `Authorization: Bearer <access_token>`
* **Token Lifetime:** 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
* **Optional Authentication:** Endpoints such as `POST /api/resume/parse`, `POST /api/skills/analyze`, `POST /api/job-descriptions/analyze`, and `POST /api/roadmaps/generate` can be invoked anonymously or with a Bearer token. When a valid token is supplied, records are automatically persisted and linked to the authenticated user's account.

### Common Error Responses
| HTTP Code | Description | Schema |
| :--- | :--- | :--- |
| `400 Bad Request` | Malformed parameters, mismatched IDs, or empty required files. | `{"detail": "..."}` |
| `401 Unauthorized` | Missing token, expired token, or invalid credentials. | `{"detail": "..."}` |
| `403 Forbidden` | Access forbidden due to IDOR violation or inactive account. | `{"detail": "..."}` |
| `404 Not Found` | The requested resource (role, user, roadmap, task) does not exist. | `{"detail": "..."}` |
| `409 Conflict` | Duplicate registration attempt with an already registered email. | `{"detail": "..."}` |
| `413 Payload Too Large` | Uploaded document exceeds 5 MB limit. | `{"detail": "..."}` |
| `415 Unsupported Media Type` | Uploaded file format is not PDF or DOCX. | `{"detail": "..."}` |
| `422 Unprocessable Entity` | Validation failure or corrupted document structure. | `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}` |

---

## 2. System Health & Metadata

### `GET /api/health`
* **Method:** `GET`
* **Path:** `/api/health`
* **Authentication:** None (Public)
* **Description:** Health check confirming application operational status.
* **Response (200 OK):**
  ```json
  {
    "status": "ok",
    "app": "SkillGraph API",
    "version": "1.0.0",
    "environment": "development"
  }
  ```

### `GET /`
* **Method:** `GET`
* **Path:** `/`
* **Authentication:** None (Public)
* **Description:** API root greeting and direct link to documentation.
* **Response (200 OK):**
  ```json
  {
    "message": "Welcome to SkillGraph API",
    "version": "1.0.0",
    "docs_url": "/docs",
    "health_check": "/api/health"
  }
  ```

---

## 3. Authentication & Profile Endpoints

### `POST /api/auth/register` (Alias: `POST /auth/signup`)
* **Method:** `POST`
* **Path:** `/api/auth/register`
* **Authentication:** None (Public)
* **Description:** Creates a candidate account with salted PBKDF2-HMAC-SHA256 password hashing.
* **Request Schema (`UserRegisterRequest`):**
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `email` | `string` (Email) | Yes | Valid email format. |
  | `password` | `string` | Yes | Minimum 8 characters. |
  | `full_name` | `string` | No | Candidate display name. |
  | `name` | `string` | No | Alias for `full_name`. |
* **Example Request:**
  ```json
  {
    "email": "candidate@example.com",
    "password": "StrongPassword123!",
    "full_name": "Ada Lovelace"
  }
  ```
* **Successful Response (`201 Created`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in_minutes": 30,
    "user": {
      "id": 1,
      "email": "candidate@example.com",
      "full_name": "Ada Lovelace",
      "name": "Ada Lovelace",
      "is_active": true,
      "created_at": "2026-11-03T18:00:00Z"
    }
  }
  ```
* **Errors:** `409 Conflict` (email already exists), `422 Unprocessable Entity` (short password or invalid email format).

---

### `POST /api/auth/login` (Alias: `POST /auth/login`)
* **Method:** `POST`
* **Path:** `/api/auth/login`
* **Authentication:** None (Public)
* **Description:** Verifies password and issues signed JWT bearer token.
* **Request Schema (`UserLoginRequest`):**
  ```json
  {
    "email": "candidate@example.com",
    "password": "StrongPassword123!"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expires_in_minutes": 30,
    "user": {
      "id": 1,
      "email": "candidate@example.com",
      "full_name": "Ada Lovelace",
      "name": "Ada Lovelace",
      "is_active": true,
      "created_at": "2026-11-03T18:00:00Z"
    }
  }
  ```
* **Errors:** `401 Unauthorized` (invalid email or password), `403 Forbidden` (account deactivated).

---

### `GET /api/auth/me` (Alias: `GET /auth/me`)
* **Method:** `GET`
* **Path:** `/api/auth/me`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Returns current authenticated user profile.
* **Successful Response (`200 OK`):**
  ```json
  {
    "id": 1,
    "email": "candidate@example.com",
    "full_name": "Ada Lovelace",
    "name": "Ada Lovelace",
    "is_active": true,
    "created_at": "2026-11-03T18:00:00Z"
  }
  ```
* **Errors:** `401 Unauthorized` (missing, invalid, or expired token).

---

### `POST /api/auth/forgot-password` (Alias: `POST /auth/forgot-password`)
* **Method:** `POST`
* **Path:** `/api/auth/forgot-password`
* **Authentication:** None (Public)
* **Rate Limit:** 5 requests per 15 minutes per IP/email
* **Description:** Initiates a password recovery process. Generates a cryptographically random token, stores its SHA-256 hash and expiration (20 mins) in the database, sends a branded email with the reset link, and returns a constant-time generic confirmation.
* **Request Schema (`ForgotPasswordRequest`):**
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `email` | `string` (Email) | Yes | Valid registered email address. |
* **Example Request:**
  ```json
  {
    "email": "candidate@example.com"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "If an account with that email exists, we've sent password reset instructions to your inbox."
  }
  ```
* **Errors:** `422 Unprocessable Entity` (invalid email format), `429 Too Many Requests` (rate limit exceeded).

---

### `POST /api/auth/reset-password` (Alias: `POST /auth/reset-password`)
* **Method:** `POST`
* **Path:** `/api/auth/reset-password`
* **Authentication:** None (Public, authorized by cryptographic reset token)
* **Description:** Resets the user's password using the single-use reset token received via email. Validates token expiration, hashes the new password with salted PBKDF2-HMAC-SHA256, updates the user's password, and immediately invalidates the reset token to prevent reuse.
* **Request Schema (`ResetPasswordRequest`):**
  | Field | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `token` | `string` | Yes | Cryptographic reset token (min 16 chars). |
  | `new_password` | `string` | Yes | New password satisfying complexity requirements (min 8 chars, 1 upper, 1 lower, 1 digit, 1 special symbol). |
* **Example Request:**
  ```json
  {
    "token": "4a7f9b8c2e1d0f3a6b5c8e7d4f1a2b3c",
    "new_password": "NewSecurePassword#2026!"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Password has been reset successfully. You can now sign in with your new password."
  }
  ```
* **Errors:** `400 Bad Request` (invalid or expired token, already used token), `422 Unprocessable Entity` (weak password failing complexity requirements).

---

## 4. Resume Parsing & Record Management

### `POST /api/resume/parse` (Alias: `POST /resume/upload`)
* **Method:** `POST`
* **Path:** `/api/resume/parse`
* **Content-Type:** `multipart/form-data`
* **Authentication:** Optional (`Bearer <token>`). If authenticated, persists `ResumeRecord`.
* **Request:** `file` form field containing a PDF or DOCX file (up to 5 MB).
* **Successful Response (`200 OK`):**
  ```json
  {
    "success": true,
    "message": "Resume parsed successfully.",
    "text": "Ada Lovelace\nPython developer with PyTorch, Docker, Kubernetes...",
    "metadata": {
      "filename": "ada_lovelace_resume.pdf",
      "file_type": "pdf",
      "file_size_bytes": 14200,
      "page_count": 1,
      "paragraph_count": null,
      "word_count": 312,
      "character_count": 1940,
      "requires_ocr": false,
      "is_empty_or_whitespace": false
    }
  }
  ```
* **Errors:** `400 Bad Request` (empty file), `413 Payload Too Large` (> 5MB), `415 Unsupported Media Type` (non-PDF/DOCX), `422 Unprocessable Entity` (corrupted document).

---

### `GET /api/resume/records`
* **Method:** `GET`
* **Path:** `/api/resume/records`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Lists all active resume records owned by the authenticated caller.
* **Successful Response (`200 OK`):**
  ```json
  [
    {
      "id": 1,
      "filename": "ada_lovelace_resume.pdf",
      "file_type": "pdf",
      "file_size_bytes": 14200,
      "extracted_skills_count": 8,
      "created_at": "2026-11-03T18:10:00Z"
    }
  ]
  ```

---

### `GET /api/resume/records/{record_id}`
* **Method:** `GET`
* **Path:** `/api/resume/records/{record_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Retrieves the extracted plain text and skill tags for a resume record.
* **Access Control:** Enforces ownership check (`record.user_id == current_user.id`).
* **Successful Response (`200 OK`):**
  ```json
  {
    "id": 1,
    "filename": "ada_lovelace_resume.pdf",
    "file_type": "pdf",
    "file_size_bytes": 14200,
    "extracted_text": "Ada Lovelace\nPython developer...",
    "extracted_skills": [
      {
        "skill_id": "python",
        "canonical_name": "Python",
        "category": "Programming Languages",
        "matched_via": "canonical"
      }
    ],
    "created_at": "2026-11-03T18:10:00Z"
  }
  ```
* **Errors:** `403 Forbidden` (IDOR prevention: not the owner), `404 Not Found` (non-existent ID).

---

### `DELETE /api/resume/records/{record_id}`
* **Method:** `DELETE`
* **Path:** `/api/resume/records/{record_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Permanently deletes the resume record and extracted text.
* **Successful Response (`200 OK`):**
  ```json
  {
    "ok": true,
    "message": "Resume record 1 permanently deleted."
  }
  ```
* **Errors:** `403 Forbidden` (IDOR prevention), `404 Not Found`.

---

## 5. Curated Role Ontologies, Discovery & Market Insights

### `GET /api/roles/`
* **Method:** `GET`
* **Path:** `/api/roles/`
* **Authentication:** None (Public)
* **Query Parameters:**
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `family` | `string` | No | Filter by role family (`AI/ML`, `Engineering`, `Data`, `DevOps/Platform`). |
  | `level` | `string` | No | Filter by experience level (`entry`, `mid`, `senior`). |
  | `maturity` | `string` | No | Filter by maturity classification (`established` or `emerging`). |
  | `q` | `string` | No | Free-text search query across canonical title, description, and key skills. |
* **Description:** Returns the complete catalog of 11 industry role profiles, supporting the expanded career taxonomy (including Harness Engineer, Forward Deployed Engineer, AI Agent Engineer, LLMOps Engineer, AI Evaluation Engineer, and AI Infrastructure Engineer).
* **Successful Response (`200 OK`):**
  ```json
  {
    "roles": [
      {
        "id": "harness-engineer",
        "canonical_title": "Harness Engineer",
        "role_family": "DevOps/Platform",
        "description": "Designs, implements, and maintains CI/CD, deployment, and platform engineering workflows...",
        "experience_level": "mid",
        "entry_level_accessible": false,
        "maturity": "emerging",
        "highlight_skills": ["Docker", "Kubernetes", "Git", "AWS"],
        "core_skill_count": 7
      }
    ]
  }
  ```

---

### `GET /api/roles/compare`
* **Method:** `GET`
* **Path:** `/api/roles/compare`
* **Authentication:** None (Public)
* **Query Parameters:**
  | Parameter | Type | Required | Description |
  | :--- | :--- | :--- | :--- |
  | `role_a` | `string` | Yes | First role ID (e.g. `backend-engineer`). |
  | `role_b` | `string` | Yes | Second role ID (e.g. `data-engineer`). |
* **Description:** Performs deterministic bidirectional skill overlap analysis and computes transition bridge skills with estimated study hours.
* **Successful Response (`200 OK`):**
  ```json
  {
    "role_a": {
      "id": "backend-engineer",
      "canonical_title": "Backend Engineer",
      "role_family": "Engineering",
      "experience_level": "mid",
      "maturity": "established",
      "entry_level_accessible": true
    },
    "role_b": {
      "id": "data-engineer",
      "canonical_title": "Data Engineer",
      "role_family": "Data",
      "experience_level": "mid",
      "maturity": "established",
      "entry_level_accessible": true
    },
    "shared_core_skills": [
      {"id": "docker", "canonical_name": "Docker", "category": "DevOps", "estimated_hours": 25},
      {"id": "python", "canonical_name": "Python", "category": "Language", "estimated_hours": 40}
    ],
    "unique_to_role_a": [
      {"id": "fastapi", "canonical_name": "FastAPI", "category": "Backend Framework", "estimated_hours": 35}
    ],
    "unique_to_role_b": [
      {"id": "airflow", "canonical_name": "Apache Airflow", "category": "Data Engineering", "estimated_hours": 30},
      {"id": "spark", "canonical_name": "Apache Spark", "category": "Data Engineering", "estimated_hours": 45}
    ],
    "overlap_percentage": 27.3,
    "shared_core_count": 3,
    "total_unique_core_count": 11,
    "transition_a_to_b": {
      "target_role": "Data Engineer",
      "bridge_skills": [...],
      "bridge_skills_count": 4,
      "estimated_hours": 135
    },
    "transition_b_to_a": {
      "target_role": "Backend Engineer",
      "bridge_skills": [...],
      "bridge_skills_count": 4,
      "estimated_hours": 115
    }
  }
  ```
* **Errors:** `404 Not Found` (non-existent role ID), `422 Unprocessable Content` (missing query parameters).

---

### `GET /api/roles/{role_id}`
* **Method:** `GET`
* **Path:** `/api/roles/{role_id}`
* **Authentication:** None (Public)
* **Description:** Returns the comprehensive profile for a role, including responsibilities, prerequisites, enriched core and optional skills, real-world milestone projects, emerging discipline context, top related roles, and market summary.
* **Path Parameter:** `role_id` (e.g. `harness-engineer`, `backend-engineer`, `llmops-engineer`).
* **Successful Response (`200 OK`):** Enriched schema containing `responsibilities`, `prerequisites_details`, `core_skills_details`, `recommended_skills_details`, `optional_skills_details`, `example_projects`, `maturity`, `emerging_context`, `related_roles`, and `market_summary`.
* **Errors:** `404 Not Found` for invalid role ID.

---

### `GET /api/roles/{role_id}/related`
* **Method:** `GET`
* **Path:** `/api/roles/{role_id}/related`
* **Authentication:** None (Public)
* **Query Parameters:**
  | Parameter | Type | Default | Description |
  | :--- | :--- | :--- | :--- |
  | `top_n` | `integer` | 4 | Maximum number of suggestions (1–10). |
* **Description:** Returns ranked related role suggestions based on composite Jaccard skill overlap, with shared competencies and missing bridge skills.
* **Successful Response (`200 OK`):**
  ```json
  {
    "role_id": "ai-agent-engineer",
    "canonical_title": "AI Agent Engineer",
    "related_roles": [
      {
        "role_id": "forward-deployed-ai-engineer",
        "canonical_title": "Forward Deployed AI Engineer",
        "role_family": "AI/ML",
        "experience_level": "senior",
        "maturity": "emerging",
        "entry_level_accessible": false,
        "overlap_percentage": 58.2,
        "shared_core_count": 5,
        "shared_skills": [...],
        "bridge_skills": [...]
      }
    ]
  }
  ```
* **Errors:** `404 Not Found` for invalid role ID.

---

### `GET /api/roles/{role_id}/market-summary`
* **Method:** `GET`
* **Path:** `/api/roles/{role_id}/market-summary`
* **Authentication:** None (Public)
* **Description:** Returns evidence-aware market summary. Uses only actual collected job descriptions with documented provenance (source, collection date, geography, sample size). When no statistically sufficient dataset is available (e.g. for emerging roles), returns transparent curated guidance with explicit disclaimers rather than fabricated counts or synthetic salaries.
* **Successful Response (`200 OK`) — Verified Dataset Case:**
  ```json
  {
    "role_id": "backend-engineer",
    "has_verified_data": true,
    "metadata": {
      "source": "US Tech Job Postings Public Archive (Q4 2024 - Q1 2025)",
      "collection_date": "2025-01-15",
      "geography": "US-Remote",
      "sample_size": 120,
      "skill_detection_method": "SkillGraph-Regex-v1.0"
    },
    "top_required_skills": [
      {"skill_id": "python", "canonical_name": "Python", "frequency_count": 96, "frequency_percent": 80.0},
      {"skill_id": "postgresql", "canonical_name": "PostgreSQL", "frequency_count": 84, "frequency_percent": 70.0}
    ],
    "top_preferred_skills": [
      {"skill_id": "kubernetes", "canonical_name": "Kubernetes", "frequency_count": 48, "frequency_percent": 40.0}
    ],
    "experience_distribution": {
      "entry_0_2_years": 18,
      "mid_3_5_years": 74,
      "senior_5_plus_years": 28
    },
    "data_notice": "Empirical summary calculated from 120 verified job descriptions collected on 2025-01-15 (US-Remote). No synthetic data."
  }
  ```
* **Successful Response (`200 OK`) — Curated Guidance Fallback (Emerging Roles):**
  ```json
  {
    "role_id": "ai-evaluation-engineer",
    "has_verified_data": false,
    "guidance_type": "curated_competency_framework",
    "data_notice": "Curated guidance: No statistically verified dataset of job postings with sufficient sample size is currently available for this role. SkillGraph strictly prohibits generating synthetic sample sizes, speculative percentages, or fabricated salary estimates.",
    "curated_skills": [...],
    "recommendation": "Treat the curated core skills and example projects as foundational learning benchmarks rather than empirical hiring statistics. Individual employer requirements vary significantly."
  }
  ```
* **Errors:** `404 Not Found` for invalid role ID.

---

## 6. Skills Extraction & Gap Analysis

### `POST /api/skills/analyze`
* **Method:** `POST`
* **Path:** `/api/skills/analyze`
* **Authentication:** Optional (`Bearer <token>`). If authenticated, persists `SkillAnalysisRecord`.
* **Request Schema (`AnalyzeRequest`):**
  ```json
  {
    "text": "Experienced Python and FastAPI engineer with PostgreSQL and Docker.",
    "role_id": "backend-engineer"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "role_id": "backend-engineer",
    "role_title": "Backend Engineer",
    "matched_skills": [
      {
        "skill_id": "python",
        "canonical_name": "Python",
        "category": "Programming Languages",
        "matched_via": "canonical"
      }
    ],
    "missing_skills": [
      {
        "skill_id": "system-design",
        "canonical_name": "System Design",
        "category": "Architecture",
        "importance": "critical",
        "estimated_hours": 30
      }
    ],
    "uncertain_skills": [],
    "coverage_percent": 66.7,
    "coverage_note": "Coverage reflects detected core competencies relative to curated industry standards.",
    "total_core_skills": 6,
    "matched_core_skills": 4,
    "priority_gaps": [...]
  }
  ```
* **Errors:** `404 Not Found` (unknown `role_id`), `422 Unprocessable Entity` (missing fields).

---

### `GET /api/skills/analyses`
* **Method:** `GET`
* **Path:** `/api/skills/analyses`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Returns historical skill analyses belonging to authenticated user.
* **Successful Response (`200 OK`):**
  ```json
  [
    {
      "id": 1,
      "role_id": "backend-engineer",
      "role_title": "Backend Engineer",
      "coverage_percent": 66.7,
      "matched_skills_count": 4,
      "missing_skills_count": 2,
      "created_at": "2026-11-03T18:15:00Z"
    }
  ]
  ```

---

### `GET /api/skills/analyses/{analysis_id}`
* **Method:** `GET`
* **Path:** `/api/skills/analyses/{analysis_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Access Control:** Enforces ownership check (`analysis.user_id == current_user.id`).
* **Successful Response (`200 OK`):** Complete analysis breakdown.
* **Errors:** `403 Forbidden` (IDOR prevention), `404 Not Found`.

---

### `DELETE /api/skills/analyses/{analysis_id}`
* **Method:** `DELETE`
* **Path:** `/api/skills/analyses/{analysis_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Successful Response (`200 OK`):** `{"ok": true, "message": "Skill analysis record 1 deleted."}`
* **Errors:** `403 Forbidden`, `404 Not Found`.

---

## 7. Job Description Matching

### `POST /api/job-descriptions/analyze` (Alias: `POST /jobs/match`)
* **Method:** `POST`
* **Path:** `/api/job-descriptions/analyze`
* **Authentication:** Optional (`Bearer <token>`). If authenticated, persists `JobDescriptionAnalysisRecord`.
* **Request Schema (`JobDescriptionAnalyzeRequest`):**
  ```json
  {
    "resume_text": "Experienced Python engineer with Docker and AWS.",
    "job_description_text": "Required: Python, Docker, CI/CD. Preferred: Kubernetes. 3+ years required."
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "extracted_skills": [...],
    "matched_skills": [...],
    "missing_skills": [...],
    "potentially_related_skills": [...],
    "required_skills": [...],
    "preferred_skills": [...],
    "experience_requirements": [
      {
        "raw_text": "3+ years required",
        "years": 3.0,
        "topic": null,
        "requirement_type": "tenure"
      }
    ],
    "coverage_percent": 66.7,
    "total_jd_skills": 4,
    "matched_count": 2,
    "missing_count": 2,
    "caveats": [
      "Job descriptions use heterogeneous phrasing. Unlisted skills may still be expected in interviews."
    ]
  }
  ```
* **Errors:** `422 Unprocessable Entity` (empty or whitespace-only job description).

---

### `GET /api/job-descriptions/analyses`
* **Method:** `GET`
* **Path:** `/api/job-descriptions/analyses`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Lists user's saved job description analyses.

---

### `GET /api/job-descriptions/analyses/{analysis_id}`
* **Method:** `GET`
* **Path:** `/api/job-descriptions/analyses/{analysis_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Errors:** `403 Forbidden` (IDOR prevention), `404 Not Found`.

---

### `DELETE /api/job-descriptions/analyses/{analysis_id}`
* **Method:** `DELETE`
* **Path:** `/api/job-descriptions/analyses/{analysis_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Errors:** `403 Forbidden`, `404 Not Found`.

---

## 8. Learning Roadmaps & Progress Tracking

### `POST /api/roadmaps/generate` (Alias: `POST /roadmap/generate`)
* **Method:** `POST`
* **Path:** `/api/roadmaps/generate`
* **Authentication:** Optional (`Bearer <token>`). If authenticated, persists `RoadmapRecord`, child `RoadmapTaskRecord`s, and initial `TaskProgressRecord`s.
* **Request Schema (`RoadmapGenerateRequest`):**
  ```json
  {
    "role_id": "harness-engineer",
    "existing_skills": ["python", "docker"],
    "missing_skills": null,
    "weekly_hours": 10,
    "resume_text": null
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "role_id": "harness-engineer",
    "role_title": "Harness Engineer",
    "total_weeks": 6,
    "target_weekly_hours": 10,
    "total_estimated_hours": 42,
    "weeks": [
      {
        "week_number": 1,
        "theme": "Foundations & Core Tooling",
        "weekly_hours_allocated": 7,
        "tasks": [
          {
            "id": "task_eval-harness_1",
            "title": "Build Evaluation Harness Framework",
            "description": "Implement automated evaluation pipelines...",
            "target_skill": "Eval Harness",
            "week": 1,
            "estimated_effort": 7,
            "prerequisites": ["Python"],
            "learning_resource": {
              "title": "Official Evaluation Framework Documentation",
              "url": "https://github.com/openai/evals",
              "is_verified": true,
              "verification_status": "Verified"
            },
            "completion_status": "pending"
          }
        ],
        "milestone_project": "Baseline Harness"
      }
    ],
    "tasks": [...],
    "capstone_project": "Build an end-to-end evaluation harness for agentic workflows...",
    "prerequisite_chains": {"Eval Harness": ["Python"]},
    "notes": [...]
  }
  ```
* **Errors:** `404 Not Found` (unknown `role_id`), `422 Unprocessable Entity` (weekly hours out of bounds).

---

### `GET /api/roadmaps`
* **Method:** `GET`
* **Path:** `/api/roadmaps`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Lists all roadmaps created for the authenticated caller with completion stats.
* **Successful Response (`200 OK`):**
  ```json
  [
    {
      "id": 1,
      "role_id": "harness-engineer",
      "role_title": "Harness Engineer",
      "total_weeks": 6,
      "target_weekly_hours": 10,
      "total_estimated_hours": 42,
      "total_tasks": 6,
      "completed_tasks": 1,
      "completion_percentage": 16.7,
      "created_at": "2026-11-03T18:20:00Z"
    }
  ]
  ```

---

### `GET /api/roadmaps/{roadmap_id}`
* **Method:** `GET`
* **Path:** `/api/roadmaps/{roadmap_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Access Control:** Enforces ownership check (`roadmap.user_id == current_user.id`).
* **Errors:** `403 Forbidden` (IDOR prevention), `404 Not Found`.

---

### `DELETE /api/roadmaps/{roadmap_id}`
* **Method:** `DELETE`
* **Path:** `/api/roadmaps/{roadmap_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Cascades deletion to child tasks and progress records.
* **Errors:** `403 Forbidden` (IDOR prevention), `404 Not Found`.

---

### `PATCH /api/roadmaps/{roadmap_id}/tasks/{task_id}` (Aliases: `/api/roadmaps/tasks/{task_id}`, `/roadmap/{task_id}`)
* **Method:** `PATCH`
* **Path:** `/api/roadmaps/{roadmap_id}/tasks/{task_id}`
* **Authentication:** Required (`Bearer <token>`)
* **Access Control:** Verifies that the task belongs to a roadmap owned by the authenticated caller.
* **Request Options:**
  1. **JSON Body (`TaskStatusUpdateRequest`):**
     ```json
     {
       "status": "completed",
       "notes": "Finished evaluation harness benchmark script."
     }
     ```
  2. **Boolean `done` parameter:** `{"done": true}` or query parameter `?done=true`.
* **Successful Response (`200 OK`):**
  ```json
  {
    "ok": true,
    "task_id": 1,
    "status": "completed",
    "completed_at": "2026-11-03T18:30:00Z"
  }
  ```
* **Errors:** `400 Bad Request` (task does not belong to specified roadmap), `403 Forbidden` (IDOR: user does not own task), `404 Not Found`.

---

### `GET /api/progress`
* **Method:** `GET`
* **Path:** `/api/progress`
* **Authentication:** Required (`Bearer <token>`)
* **Description:** Aggregates task progress metrics across all active roadmaps for the user.
* **Successful Response (`200 OK`):**
  ```json
  {
    "user_id": 1,
    "total_tasks": 6,
    "completed_tasks": 1,
    "in_progress_tasks": 1,
    "pending_tasks": 4,
    "completion_percentage": 16.7,
    "active_roadmaps_count": 1,
    "progress_items": [
      {
        "task_id": 1,
        "task_key": "task_eval-harness_1",
        "title": "Build Evaluation Harness Framework",
        "target_skill": "Eval Harness",
        "week": 1,
        "status": "completed",
        "completed_at": "2026-11-03T18:30:00Z",
        "notes": "Finished evaluation harness benchmark script."
      }
    ]
  }
  ```
* **Errors:** `401 Unauthorized` (unauthenticated).

---

## 8. Resume Advisor & Quality Critique Endpoints

### `POST /api/resume/critique`
* **Method:** `POST`
* **Path:** `/api/resume/critique`
* **Authentication:** Optional (authenticated users can critique saved resumes by `resume_id`)
* **Request Body (`ResumeCritiqueRequest`):**
  ```json
  {
    "text": "Architected Python FastAPI backend with PostgreSQL and Docker. Scaled to 10k users with 99.9% uptime.",
    "resume_id": 1
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "overall_score": 82,
    "rating_label": "Competitive",
    "dimension_scores": {
      "quantification": 21.0,
      "action_verbs": 21.0,
      "keyword_density": 21.0,
      "brevity_and_clarity": 19.0
    },
    "strengths": [
      "Strong quantification: detected 3 measurable impact metrics, percentages, or scale indicators.",
      "Solid technical vocabulary: recognized 4 verified engineering tools and skills."
    ],
    "things_to_add": [
      "Include a link to your public GitHub profile (github.com/yourusername) or live demonstration links."
    ],
    "things_to_remove": [
      "Eliminate generic buzzword 'team player' — demonstrate competence through shipped project outcomes instead."
    ],
    "bullet_improvements": [
      {
        "original": "Built backend APIs using FastAPI and connected to PostgreSQL database.",
        "improved": "Engineered 14 production REST endpoints in FastAPI with SQLAlchemy, handling 2,500 daily requests with sub-50ms p95 latency.",
        "reason": "Google XYZ Formula: Specifies what was built (endpoints), how it was measured (requests/latency), and tools used."
      }
    ],
    "summary": "Resume evaluated at 82/100 (Competitive). 2 positive signal areas detected. Action items: 1 high-priority additions and 1 fluff phrases flagged for removal."
  }
  ```
* **Errors:** `403 Forbidden` (user does not own specified resume), `404 Not Found`, `422 Unprocessable Entity` (empty text).

---

## 9. Coding Profiles (GitHub & LeetCode) Endpoints

### `POST /api/profiles/analyze`
* **Method:** `POST`
* **Path:** `/api/profiles/analyze`
* **Authentication:** None
* **Request Body (`CodingProfilesRequest`):**
  ```json
  {
    "github_username": "octocat",
    "leetcode_username": "tourist"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "github": {
      "username": "octocat",
      "name": "The Octocat",
      "avatar_url": "https://avatars.githubusercontent.com/u/583231",
      "profile_url": "https://github.com/octocat",
      "public_repos": 8,
      "followers": 25,
      "total_stars": 25,
      "primary_languages": {
        "Python": 66.7,
        "TypeScript": 33.3
      },
      "quality_score": 75,
      "summary": "Active GitHub profile with 8 public repositories and 25 total stargazers."
    },
    "leetcode": {
      "username": "tourist",
      "profile_url": "https://leetcode.com/tourist",
      "total_solved": 220,
      "easy_solved": 60,
      "medium_solved": 130,
      "hard_solved": 30,
      "acceptance_rate": 58.5,
      "ranking": 45000,
      "dsa_readiness_score": 85,
      "dsa_readiness_tier": "Interview Ready",
      "interview_recommendations": [
        "Strong algorithmic foundation: prioritize mock timed interviews and system design.",
        "Review edge cases and space complexity trade-offs for Hard-level dynamic programming and graph problems."
      ]
    },
    "combined_signal_score": 80,
    "strengths": [
      "GitHub: 8 public repos with 25 stars.",
      "LeetCode: 220 solved (130 Mediums, 30 Hards)."
    ],
    "recommendations": [
      "Strong algorithmic foundation: prioritize mock timed interviews and system design."
    ],
    "summary": "Technical interview readiness scored at 80/100 based on GitHub and LeetCode."
  }
  ```
* **Errors:** `422 Unprocessable Entity` (both handles empty or whitespace).

---

## 10. Job Market Analytics Endpoints

### `GET /api/job-descriptions/market-trends`
* **Method:** `GET`
* **Path:** `/api/job-descriptions/market-trends`
* **Authentication:** None
* **Query Parameters:**
  * `family` *(optional, string)*: Filter by role family (`Engineering`, `AI/ML`, `Data`).
* **Successful Response (`200 OK`):**
  ```json
  {
    "total_roles_analyzed": 11,
    "role_family_filter": "All Families",
    "top_in_demand_skills": [
      {
        "skill": "Python",
        "weighted_frequency": 22,
        "demand_index": 100.0
      },
      {
        "skill": "Docker",
        "weighted_frequency": 16,
        "demand_index": 72.7
      }
    ],
    "category_distribution": {
      "Engineering": 55.0,
      "AI/ML": 30.0,
      "Data": 15.0
    },
    "maturity_breakdown": {
      "established_roles": 4,
      "emerging_roles": 7
    },
    "skill_pairs": [
      {
        "pair": ["Python", "FastAPI"],
        "relevance": "API & Microservices Architecture",
        "overlap_pct": 92
      }
    ],
    "empirical_benchmarks": [
      {
        "role_id": "backend-engineer",
        "role_title": "Backend Engineer",
        "sample_size": 120,
        "provenance": {
          "source": "Curated Tech Job Postings Corpus",
          "collection_date": "2026-Q1",
          "geography": "Global Remote / US"
        },
        "top_demanded_skills": [
          {"name": "Python", "frequency_percent": 84.2}
        ]
      }
    ],
    "methodology_disclaimer": "Market trends are synthesized from verified empirical job-description corpora (where documented) and curated engineering role ontologies."
  }
  ```

---

## 11. Interactive Review, Selection Persistence & Progress Summary Endpoints

### `PUT /api/resume/skills`
* **Method:** `PUT`
* **Path:** `/api/resume/skills`
* **Authentication:** Required (`Authorization: Bearer <token>`)
* **Description:** Persists user-reviewed skills (additions and deletions) back to the user's latest active resume record.
* **Request Body:**
  ```json
  {
    "skills": ["Python", "Docker", "FastAPI", "SQLAlchemy", "PostgreSQL"]
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Skills updated successfully",
    "skills_count": 5,
    "skills": ["Python", "Docker", "FastAPI", "SQLAlchemy", "PostgreSQL"]
  }
  ```

---

### `POST /api/roles/save-selection`
* **Method:** `POST`
* **Path:** `/api/roles/save-selection`
* **Authentication:** Required (`Authorization: Bearer <token>`)
* **Description:** Saves the user's chosen primary target role and secondary comparison role to their persistent profile.
* **Request Body:**
  ```json
  {
    "target_role_id": "backend-engineer",
    "secondary_role_id": "ml-engineer"
  }
  ```
* **Successful Response (`200 OK`):**
  ```json
  {
    "status": "success",
    "message": "Role selection saved successfully",
    "target_role_id": "backend-engineer",
    "secondary_role_id": "ml-engineer"
  }
  ```

---

### `GET /api/roadmaps/summary`
* **Method:** `GET`
* **Path:** `/api/roadmaps/summary`
* **Authentication:** Required (`Authorization: Bearer <token>`)
* **Description:** Returns aggregate completion progress and task metrics for the authenticated user's active roadmap.
* **Successful Response (`200 OK`):**
  ```json
  {
    "has_roadmap": true,
    "roadmap_id": 1,
    "role_title": "Backend Engineer",
    "total_tasks": 18,
    "completed_tasks": 6,
    "progress_percentage": 33.3,
    "total_hours": 60,
    "completed_hours": 20
  }
  ```



