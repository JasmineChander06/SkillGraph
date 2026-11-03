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

## 5. Curated Role Ontologies

### `GET /api/roles/`
* **Method:** `GET`
* **Path:** `/api/roles/`
* **Authentication:** None (Public)
* **Description:** Returns the complete catalog of 11 industry role profiles.
* **Successful Response (`200 OK`):**
  ```json
  [
    {
      "id": "harness-engineer",
      "canonical_title": "Harness Engineer",
      "role_family": "AI Engineering",
      "description": "Designs deterministic and agentic evaluation harnesses...",
      "experience_level": "Mid to Senior",
      "entry_level_accessible": false,
      "core_skills": ["python", "docker", "eval-harness", "pytest"]
    }
  ]
  ```

---

### `GET /api/roles/{role_id}`
* **Method:** `GET`
* **Path:** `/api/roles/{role_id}`
* **Authentication:** None (Public)
* **Description:** Returns full profile including responsibilities, prerequisites, example projects, learning resources, and market evidence.
* **Path Parameter:** `role_id` (e.g. `harness-engineer`, `backend-engineer`, `llmops-engineer`).
* **Successful Response (`200 OK`):** Full profile schema including `core_skills`, `recommended_skills`, `optional_skills`, and `market_evidence`.
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

