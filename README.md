# SkillGraph

**Career-readiness analysis through evidence-based skill-gap detection.**

> 🚀 **Live Production Deployment:** [https://skillgraph-1-yfq4.onrender.com](https://skillgraph-1-yfq4.onrender.com)

SkillGraph is a local-first web application that quantifies the distance between a candidate's demonstrated technical skills and the requirements of specific engineering roles. It parses resumes, identifies skill overlaps and gaps against curated role profiles, compares candidates against job descriptions, and generates personalised six-week learning roadmaps.

> **Important disclaimer:** Skill coverage percentages measure *detected keyword overlap* between a resume and a role profile. They are **not** a hiring probability, a proof of proficiency, or a guarantee of job readiness. Actual hiring decisions depend on experience depth, system-design ability, communication, cultural fit, and many factors that keyword matching cannot assess.

---

## Table of Contents

- [Problem Statement](#problem-statement)
- [Why This Project Was Built](#why-this-project-was-built)
- [Target Audience](#target-audience)
- [Solution and Workflow](#solution-and-workflow)
- [Role Catalogue](#role-catalogue)
  - [Traditional Roles](#traditional-roles)
  - [Emerging Roles](#emerging-roles)
  - [Harness Engineer](#harness-engineer)
  - [Forward Deployed Engineer](#forward-deployed-engineer)
- [Skill-Gap Methodology](#skill-gap-methodology)
- [Job-Description Analysis](#job-description-analysis)
- [Six-Week Roadmap Generation](#six-week-roadmap-generation)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Folder Structure](#folder-structure)
- [Database Design](#database-design)
- [API Reference](#api-reference)
- [Installation](#installation)
- [Running the Backend](#running-the-backend)
- [Running the Frontend](#running-the-frontend)
- [Running Tests](#running-tests)
- [Example Workflow](#example-workflow)
- [Implemented vs Planned Features](#implemented-vs-planned-features)
- [Known Limitations](#known-limitations)
- [Future Improvements](#future-improvements)
- [Documentation](#documentation)
- [Licence](#licence)

---

## Problem Statement

Engineers exploring new roles or preparing for interviews face a common question: *"How ready am I for this position?"* Answering it typically involves manually comparing resume bullet points against job postings — a tedious, subjective, and inconsistent process.

The problem becomes harder with emerging titles like AI Agent Engineer, LLMOps Engineer, or Harness Engineer, where role definitions are still forming and reliable public data is scarce. Candidates risk either overestimating their readiness or missing skills they already possess under different terminology.

## Why This Project Was Built

SkillGraph was built to:

1. **Automate skill extraction** from PDF and DOCX resumes using deterministic pattern matching rather than manual self-assessment.
2. **Provide structured role profiles** for both traditional and emerging engineering titles, with honest maturity labels that distinguish established career paths from nascent specialisations.
3. **Generate actionable learning plans** rather than vague recommendations, so candidates know exactly what to study and in what order.
4. **Avoid fabricated statistics** — where verified market data exists, it is presented with sources, geography, and sample sizes; where it does not, the system displays curated guidance with clear disclaimers.

## Target Audience

- Software engineers assessing readiness for a career transition (e.g., backend engineer → ML engineer).
- Recent graduates evaluating which roles match their existing coursework and project experience.
- Self-taught developers identifying specific skill gaps before applying to positions.
- Career advisors looking for a structured framework to discuss role requirements with candidates.

---

## Solution and Workflow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Upload      │     │  Select      │     │  View Gap    │     │  Generate    │
│  Resume      │────▶│  Target Role │────▶│  Analysis    │────▶│  Roadmap     │
│  (PDF/DOCX)  │     │              │     │              │     │  (6 weeks)   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                     │
       ▼                    ▼                    ▼                     ▼
  Text extracted       Role profiles       Matched, missing,     Prerequisite-
  via PyMuPDF or       loaded from         and uncertain         ordered tasks
  python-docx          curated JSON        skills displayed      with weekly
                                                                 hour limits
```

1. **Register and log in** — JWT-authenticated sessions with PBKDF2-HMAC-SHA256 password hashing.
2. **Upload a resume** — PDF or DOCX (up to 5 MB). Binary files are parsed in memory and discarded; only extracted text is stored.
3. **Select a target role** — Choose from 11 curated role profiles spanning traditional and emerging titles.
4. **View skill-gap analysis** — See matched skills, missing skills, uncertain matches, and an overall coverage percentage.
5. **Compare against a job description** — Paste a specific job posting to see how your resume compares, with required vs preferred skill breakdowns.
6. **Generate a six-week roadmap** — Receive a personalised study plan with prerequisite ordering, estimated effort, learning resources, and a capstone project.
7. **Track progress** — Mark tasks as completed; progress persists across browser refreshes and backend restarts.
8. **Explore roles** — Browse, filter, compare roles, and view evidence-aware market summaries.

---

## Role Catalogue

SkillGraph includes 11 curated role profiles, each specifying responsibilities, prerequisites, core skills (7 per role), optional skills, example projects, and related roles.

### Traditional Roles

| Role | Description |
|------|-------------|
| **Backend Engineer** | Server-side architecture, API design, database management, and system scalability. |
| **Machine Learning Engineer** | Production ML pipelines, model training, evaluation, and deployment at scale. |
| **Data Engineer** | Data pipeline architecture, ETL/ELT processes, warehouse design, and data quality. |
| **Data Analyst** | Statistical analysis, data visualisation, business intelligence, and reporting. |

### Emerging Roles

| Role | Maturity | Entry-Level Accessible |
|------|----------|----------------------|
| **Harness Engineer** | Emerging | No — requires CI/CD platform experience |
| **Forward Deployed Engineer** | Emerging | No — requires customer-facing delivery experience |
| **Forward Deployed AI Engineer** | Emerging | No — combines FDE and ML skills |
| **AI Agent Engineer** | Emerging | Partially — growing demand but role still forming |
| **LLMOps Engineer** | Emerging | No — requires MLOps foundation |
| **AI Evaluation Engineer** | Emerging | Partially — benefits from testing background |
| **AI Infrastructure Engineer** | Emerging | No — requires distributed systems experience |

> **Note:** Emerging roles are labelled honestly. Not every new title is equally established, equally compensated, or equally accessible to entry-level candidates. The maturity labels reflect the current state of industry adoption, not a value judgement about the roles themselves.

### Harness Engineer

A **Harness Engineer** specialises in building and maintaining the infrastructure that enables continuous integration, continuous deployment, and automated quality assurance at scale.

**Responsibilities:**
- Design and implement CI/CD pipeline architectures
- Build deployment harnesses supporting canary releases and blue-green deployments
- Create evaluation harnesses for automated testing and validation
- Maintain infrastructure-as-code configurations
- Implement observability and monitoring for deployment pipelines

**Prerequisites:** Prior experience with CI/CD platforms, container orchestration, and infrastructure automation. This is not typically an entry-level role.

**Core skills:** CI/CD Pipelines, Docker, Kubernetes, Terraform, Python, Git, Monitoring & Observability.

### Forward Deployed Engineer

A **Forward Deployed Engineer (FDE)** is embedded with customers to deliver tailored technical solutions, bridging the gap between a product's general capabilities and each client's specific requirements.

**Responsibilities:**
- Work on-site or embedded with enterprise customers
- Build custom integrations against client infrastructure
- Translate customer requirements into engineering specifications
- Navigate enterprise security, compliance, and data governance constraints
- Provide technical leadership during implementation engagements

**Prerequisites:** Strong software engineering fundamentals combined with client-facing communication skills, comfort with ambiguity, and experience working within enterprise environments. This is not typically an entry-level role.

**Core skills:** Python, SQL, REST APIs, System Design, Technical Communication, Data Analysis, Cloud Platforms.

---

## Skill-Gap Methodology

SkillGraph uses **deterministic regex-based pattern matching** to extract skills from resume text:

1. **Skill dictionary** — A curated catalogue of ~60 skills, each with canonical names, aliases, categories, and importance weights (stored in `skill_aliases.json`).
2. **Extraction** — Whole-word boundary matching with custom regex patterns scans the extracted resume text. Each alias maps back to its canonical skill.
3. **Matching** — Extracted skills are compared against a target role's 7 core skills. Skills are classified as:
   - **Matched** — Detected in the resume and required by the role.
   - **Missing** — Required by the role but not detected in the resume.
   - **Uncertain** — Partial or ambiguous matches requiring human review.
4. **Coverage formula:**

$$
\text{Coverage \%} = \frac{\text{Matched Core Skills}}{\text{Total Core Skills}} \times 100
$$

> **What coverage is not:**
> - It is not a hiring probability.
> - It is not a proof of proficiency or depth of experience.
> - It does not account for years of experience, project complexity, system-design ability, or soft skills.
> - A 100% coverage score means every core keyword was detected — it does not mean the candidate is fully qualified.

---

## Job-Description Analysis

Candidates can paste a specific job posting to compare their resume against it:

1. **Section segmentation** — The job description is split into required skills, preferred skills, and general content sections using keyword-based heuristics.
2. **Skill extraction** — The same regex engine extracts skills from the job description text.
3. **Experience extraction** — Patterns like "3+ years of experience with X" are identified and listed separately.
4. **Comparison** — Extracted job-description skills are compared against the candidate's resume skills to produce matched/missing breakdowns and a coverage percentage.
5. **Caveats** — The analysis includes caveats noting that job descriptions often list aspirational requirements and that missing keywords do not necessarily indicate missing competence.

---

## Six-Week Roadmap Generation

When a skill-gap analysis reveals missing skills, SkillGraph generates a structured six-week learning roadmap:

1. **Prerequisite ordering** — Skills with dependencies are scheduled after their prerequisites (e.g., "Docker" before "Kubernetes").
2. **Weekly hour budget** — Tasks are distributed across 6 weeks with a default target of 10 hours per week.
3. **Task structure** — Each task includes a title, description, target skill, estimated effort in hours, and a learning resource reference.
4. **Capstone project** — Week 6 includes a capstone project that integrates the skills learned throughout the roadmap.
5. **Progress tracking** — Each task can be marked as `pending`, `in_progress`, or `completed`. Progress is persisted in the database and survives browser refreshes and backend restarts.

---

## Technology Stack

| Layer | Technology | Version | Purpose |
|-------|-----------|---------|---------|
| **Backend framework** | FastAPI | 0.162.0 | Async REST API with automatic OpenAPI documentation |
| **ORM** | SQLAlchemy | 2.1.6 | Database models with mapped column types |
| **Validation** | Pydantic | 2.14.2 | Request/response schema validation |
| **Configuration** | pydantic-settings | 2.16.2 | Environment-based configuration loading |
| **Database** | SQLite | (stdlib) | Development database with WAL mode |
| **Authentication** | PyJWT | 2.15.1 | JWT HS256 token generation and verification |
| **Password hashing** | hashlib (PBKDF2) | (stdlib) | PBKDF2-HMAC-SHA256 with 100,000 iterations |
| **PDF parsing** | PyMuPDF | 2.1 | Text extraction from PDF documents |
| **DOCX parsing** | python-docx | 1.2.0 | Text extraction from Word documents |
| **HTTP client** | httpx | 0.28.1 | Test client for API integration tests |
| **Testing** | pytest | 9.2.0 | Test runner with FastAPI TestClient |
| **ASGI server** | uvicorn | 0.54.0 | Development and production ASGI server |
| **Runtime** | Python | 3.13.7 | Backend runtime |
| **Frontend** | HTML5, CSS3, vanilla JavaScript (ES2022+) | — | No frameworks, no build step |
| **Fonts** | Fraunces, Inter, JetBrains Mono | — | Display, sans-serif, and monospace typography |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Vanilla JS)                  │
│  index.html │ dashboard.html │ roles.html │ roadmap.html    │
│         api.js ──── config.js ──── app.js                   │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP (JSON + FormData)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Application                       │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │ Auth API │ │Skills API│ │Resume API│ │Job Desc API   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘  │
│       │             │            │               │          │
│  ┌────┴─────┐ ┌─────┴────┐ ┌────┴─────┐ ┌──────┴────────┐ │
│  │Roles API │ │Roadmap   │ │Resume    │ │JD Analyzer    │ │
│  │          │ │API       │ │Parser    │ │               │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └──────┬────────┘ │
│       │             │            │               │          │
│  ┌────┴─────────────┴────────────┴───────────────┴────────┐ │
│  │                   Service Layer                        │ │
│  │  skill_extractor │ skill_analyzer │ roadmap_generator  │ │
│  │  role_discovery  │ market_insights│ auth               │ │
│  └────────────────────────┬──────────────────────────────┘  │
│                           │                                 │
│  ┌────────────────────────┴──────────────────────────────┐  │
│  │              SQLAlchemy ORM + SQLite                   │  │
│  │  users │ resumes │ skill_analyses │ roadmaps          │  │
│  │  roadmap_tasks │ task_progress │ job_description_…    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │          Static Data (JSON)                           │  │
│  │  role_profiles.json │ skill_aliases.json              │  │
│  │  verified_market_data.json                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key architectural decisions:**

- **No ML embeddings at runtime** — Skill matching uses deterministic regex rather than vector similarity. This keeps the system predictable, fast, and auditable.
- **Static role profiles** — Role definitions are stored as curated JSON files, not in the database. This makes them version-controllable and reviewable.
- **No binary file storage** — Uploaded PDFs and DOCXs are parsed in transient memory. Only extracted plain text is persisted to the database.
- **JWT authentication** — Stateless tokens with configurable expiry. No server-side session storage.
- **Frontend served by FastAPI** — The `frontend/` directory is mounted as static files at `/frontend/`, eliminating the need for a separate web server during development.

---

## Folder Structure

```
SkillGraph/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                      # FastAPI entrypoint, CORS, routers, static mount
│   │   ├── config.py                    # Pydantic Settings (env-based configuration)
│   │   ├── database.py                  # SQLAlchemy engine, session, Base, init_db()
│   │   ├── api/
│   │   │   ├── auth.py                  # POST /api/auth/register, /login, GET /me
│   │   │   ├── resume.py               # POST /api/resume/parse, /upload
│   │   │   ├── roles.py                # GET /api/roles/, /compare, /{id}, /{id}/related, /market-summary
│   │   │   ├── skills.py               # POST /api/skills/analyze, GET /api/skills/analyses
│   │   │   ├── job_descriptions.py     # POST /api/job-descriptions/analyze
│   │   │   └── roadmap.py              # POST /api/roadmaps/generate, GET, PATCH progress
│   │   ├── data/
│   │   │   ├── role_profiles.json       # 11 curated role definitions (7 core skills each)
│   │   │   ├── skill_aliases.json       # ~60 skill definitions with aliases and categories
│   │   │   └── verified_market_data.json # Empirical market data (3 roles with sources)
│   │   ├── models/
│   │   │   ├── user.py                  # User entity + PBKDF2 password utilities
│   │   │   ├── resume.py               # ResumeRecord (extracted text, no binary storage)
│   │   │   ├── analysis.py             # SkillAnalysisRecord (matched/missing/uncertain)
│   │   │   ├── roadmap.py              # RoadmapRecord + RoadmapTaskRecord
│   │   │   ├── progress.py             # TaskProgressRecord (per-user task completion)
│   │   │   └── job_description.py      # JobDescriptionAnalysisRecord
│   │   ├── schemas/
│   │   │   ├── auth.py                  # Register, login, token, user response schemas
│   │   │   ├── resume.py               # Upload and parse response schemas
│   │   │   ├── analysis.py             # Skill analysis request/response schemas
│   │   │   ├── roadmap.py              # Roadmap generation and progress schemas
│   │   │   └── job_description.py      # JD analysis request/response schemas
│   │   └── services/
│   │       ├── auth.py                  # Registration, login, JWT, get_current_user
│   │       ├── resume_parser.py         # PyMuPDF + python-docx text extraction
│   │       ├── skill_extractor.py       # Regex-based whole-word skill matching
│   │       ├── skill_analyzer.py        # Coverage calculation against role profiles
│   │       ├── roadmap_generator.py     # 6-week prerequisite-ordered curriculum
│   │       ├── job_description_analyzer.py # Section segmentation + skill comparison
│   │       ├── role_discovery.py        # Role browsing, comparison, Jaccard overlap
│   │       └── market_insights.py       # Evidence-aware market summaries
│   ├── tests/
│   │   ├── conftest.py                  # Test database fixtures (in-memory SQLite)
│   │   ├── test_auth.py                 # Registration, login, token, authorisation tests
│   │   ├── test_database.py             # Table creation, persistence, cascade tests
│   │   ├── test_health.py               # Health endpoint and CORS tests
│   │   ├── test_resume.py               # Upload validation, PDF/DOCX parsing tests
│   │   ├── test_skills.py               # Skill extraction, analysis, coverage tests
│   │   ├── test_roadmap.py              # Roadmap generation, progress tracking tests
│   │   ├── test_job_description.py      # JD analysis, section segmentation tests
│   │   ├── test_role_discovery.py       # Role listing, comparison, market summary tests
│   │   ├── test_workflow.py             # End-to-end workflow integration tests
│   │   └── test_frontend_integration.py # Frontend file structure and content tests
│   ├── requirements.txt                 # Python dependency specifications
│   ├── .env.example                     # Example environment configuration
│   └── .gitignore
├── frontend/
│   ├── index.html                       # Landing page with role ticker
│   ├── dashboard.html                   # Resume upload, skill analysis, JD comparison
│   ├── roles.html                       # Role explorer, detail modals, comparison tool
│   ├── roadmap.html                     # 6-week timeline with progress checkboxes
│   ├── css/
│   │   ├── variables.css                # OKLCH design tokens and CSS custom properties
│   │   ├── style.css                    # Global layout, typography, navigation
│   │   ├── components.css               # Reusable UI components (cards, badges, modals)
│   │   ├── dashboard.css                # Dashboard-specific styles
│   │   └── roadmap.css                  # Roadmap timeline styles
│   ├── js/
│   │   ├── config.js                    # API base URL configuration
│   │   ├── api.js                       # HTTP client module (auth, resume, skills, roles, roadmap, JD)
│   │   ├── app.js                       # Shared navigation, auth state, mobile menu
│   │   ├── dashboard.js                 # Resume upload, analysis display, JD matcher
│   │   ├── roadmap.js                   # Roadmap rendering, task completion updates
│   │   └── roles.js                     # Role explorer, filtering, comparison, modals
│   └── assets/
│       ├── icons/                       # SVG icons (file-text, route, shield, target, upload)
│       └── images/                      # Image assets placeholder
├── docs/
│   ├── architecture.md                  # System architecture documentation
│   ├── api-reference.md                 # Complete API endpoint reference
│   ├── testing.md                       # Test suite inventory and results
│   ├── implementation-plan.md           # Phased development plan
│   ├── market-data-methodology.md       # Market data collection methodology
│   └── ui-reference.md                  # UI design specification
├── README.md
├── .gitignore
└── pyrightconfig.json
```

---

## Database Design

SkillGraph uses SQLite (with WAL mode) for development storage. The schema is managed by SQLAlchemy 2.0+ with mapped column types.

```
┌──────────────────┐
│      users       │
├──────────────────┤
│ id (PK)          │
│ email (UNIQUE)   │
│ hashed_password  │
│ full_name        │
│ is_active        │
│ created_at       │
│ updated_at       │
└────────┬─────────┘
         │ 1:N
    ┌────┴────┬──────────────┬────────────────┬──────────────────┐
    ▼         ▼              ▼                ▼                  ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐ ┌────────────────┐
│resumes │ │  skill   │ │ roadmaps │ │ job_desc      │ │ task_progress  │
│        │ │ analyses │ │          │ │ _analyses     │ │                │
├────────┤ ├──────────┤ ├──────────┤ ├───────────────┤ ├────────────────┤
│id (PK) │ │id (PK)   │ │id (PK)   │ │id (PK)        │ │id (PK)         │
│user_id │ │user_id   │ │user_id   │ │user_id        │ │user_id (FK)    │
│filename│ │resume_id │ │role_id   │ │job_title      │ │task_id (FK)    │
│file_typ│ │role_id   │ │role_title│ │company_name   │ │status          │
│file_siz│ │role_title│ │total_wks │ │jd_text        │ │notes           │
│extract │ │coverage_%│ │target_hrs│ │coverage_%     │ │completed_at    │
│_text   │ │matched_… │ │total_hrs │ │extracted_…    │ │updated_at      │
│extract │ │missing_… │ │capstone  │ │matched_…      │ └────────────────┘
│_skills │ │uncertain…│ │notes_json│ │missing_…      │
│is_del  │ │priority… │ │created_at│ │required_…     │
│created │ │created_at│ │updated_at│ │preferred_…    │
│_at     │ └──────────┘ └────┬─────┘ │experience_…   │
└────┬───┘                   │ 1:N   │caveats_json   │
     │ 1:N              ┌────┴─────┐ │created_at     │
     └──────────────▶   │ roadmap  │ └───────────────┘
       (resume_id FK)   │ _tasks   │
                        ├──────────┤
                        │id (PK)   │
                        │roadmap_id│
                        │task_key  │
                        │title     │
                        │descript. │
                        │target_sk │
                        │week (1-6)│
                        │est_effort│
                        │prereqs…  │
                        │resource… │
                        │completion│
                        │_status   │
                        │created_at│
                        │updated_at│
                        └──────────┘
```

**Key constraints:**
- `task_progress` has a unique constraint on `(user_id, task_id)` — one progress record per user per task.
- Deleting a user cascades to all their resumes, analyses, roadmaps, progress records, and JD analyses.
- Deleting a resume sets `resume_id` to NULL on associated analyses (SET NULL) rather than deleting them.
- Deleting a roadmap cascades to its tasks and their progress records.

---

## API Reference

All endpoints are prefixed with `/api`. Authentication is via `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | No | Create a new account |
| `POST` | `/api/auth/login` | No | Authenticate and receive a JWT token |
| `POST` | `/api/auth/forgot-password` | No | Request secure password reset email (enumeration protected) |
| `POST` | `/api/auth/reset-password` | No | Reset password using single-use cryptographic token |
| `GET` | `/api/auth/me` | Yes | Retrieve current user profile |

### Resume

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/resume/parse` | No | Parse a resume file and return extracted text |
| `POST` | `/api/resume/upload` | Yes | Upload and persist a resume with skill extraction |
| `POST` | `/api/resume/critique` | No/Yes | Audit resume text, score 0-100, suggest additions/removals and Google XYZ bullet rewrites |

### Coding Profiles

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/profiles/analyze` | No | Fetch and score GitHub and LeetCode engineering & interview readiness signals |

### Skills Analysis

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/skills/analyze` | Yes | Run skill-gap analysis against a target role |
| `GET` | `/api/skills/analyses` | Yes | Retrieve all saved analyses for the current user |

### Roles

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/roles/` | No | List and filter role profiles |
| `GET` | `/api/roles/compare` | No | Compare two roles (Jaccard skill overlap) |
| `GET` | `/api/roles/{role_id}` | No | Get detailed role profile |
| `GET` | `/api/roles/{role_id}/related` | No | Get related role suggestions |
| `GET` | `/api/roles/market-summary` | No | Get evidence-aware market summary for a role |

### Job Descriptions

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/job-descriptions/analyze` | Yes | Compare resume against a pasted job description |
| `GET` | `/api/job-descriptions/market-trends` | No | Get aggregate cross-role skill demand, category distributions, and skill pairs |

### Roadmaps

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/roadmaps/generate` | Yes | Generate a 6-week learning roadmap |
| `GET` | `/api/roadmaps` | Yes | List all roadmaps for the current user |
| `GET` | `/api/roadmaps/{roadmap_id}` | Yes | Retrieve a specific roadmap with tasks |
| `GET` | `/api/roadmaps/{roadmap_id}/progress` | Yes | Get progress for all tasks in a roadmap |
| `PATCH` | `/api/roadmaps/{roadmap_id}/tasks/{task_id}/progress` | Yes | Update task completion status |

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/health` | No | Application health check |

Full endpoint documentation with request/response schemas is available in [`docs/api-reference.md`](docs/api-reference.md) and at `/docs` (Swagger UI) when the server is running.

---

## Installation

### Prerequisites

- **Python 3.12+** (tested with 3.13.7)
- **Git**
- **Windows PowerShell** (the commands below use PowerShell syntax)

### Step-by-Step Setup

**1. Clone the repository:**

```powershell
git clone https://github.com/YOUR_USERNAME/SkillGraph.git
cd SkillGraph
```

**2. Create and activate a Python virtual environment:**

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

> If you receive an execution policy error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

**3. Install dependencies:**

```powershell
pip install -r requirements.txt
```

The `requirements.txt` specifies:
```
fastapi>=0.115.0
uvicorn[standard]>=0.30.0
pydantic>=2.9.0
pydantic-settings>=2.5.0
python-dotenv>=1.0.0
httpx>=0.27.0
pytest>=8.0.0
pymupdf>=2.0.0
python-docx>=1.0.0
python-multipart>=0.0.12
sqlalchemy>=2.0.0
pyjwt[crypto]>=2.8.0
```

**4. Configure environment variables:**

```powershell
Copy-Item .env.example .env
```

Edit `.env` and replace the `SECRET_KEY` with a cryptographically secure random string:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

Copy the output into the `SECRET_KEY` field in `.env`.

---

## Running the Backend

From the `backend/` directory with the virtual environment activated:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server starts at `http://127.0.0.1:8000`. Key URLs:

| URL | Purpose |
|-----|---------|
| `http://127.0.0.1:8000/api/health` | Health check |
| `http://127.0.0.1:8000/docs` | Swagger UI (interactive API docs) |
| `http://127.0.0.1:8000/redoc` | ReDoc (alternative API docs) |
| `http://127.0.0.1:8000/frontend/index.html` | Frontend landing page |

The database (`skillgraph.db`) is created automatically on first startup.

---

## Running the Frontend

The frontend is served automatically by the FastAPI backend as static files. Once the backend is running, open:

```
http://127.0.0.1:8000/frontend/index.html
```

**Pages:**

| Page | URL | Description |
|------|-----|-------------|
| Landing | `/frontend/index.html` | Hero section with role ticker and navigation |
| Dashboard | `/frontend/dashboard.html` | Resume upload, skill analysis, JD comparison |
| Roles | `/frontend/roles.html` | Role explorer, detail views, comparison tool |
| Roadmap | `/frontend/roadmap.html` | 6-week timeline with progress tracking |
| Resume Review | `/frontend/resume-review.html` | Resume quality rating, things to add/remove, and Google XYZ bullet optimizer |
| Coding Signal | `/frontend/coding.html` | Public GitHub & LeetCode profile analysis and DSA interview readiness |
| Market Analytics | `/frontend/analytics.html` | Cross-role market demand signals, top recurring skills, and empirical benchmarks |

No build step, no npm install, and no Node.js required. The frontend uses vanilla JavaScript modules loaded directly by the browser.

---

## Running Tests

From the `backend/` directory:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

Or without activating the venv:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest tests -v
```

**Test suite summary (172 tests):**

| Test File | Count | Coverage Area |
|-----------|-------|---------------|
| `test_auth.py` | 16 | Registration, login, tokens, authorisation |
| `test_database.py` | 11 | Table creation, persistence, cascades |
| `test_health.py` | 5 | Health endpoint, CORS headers |
| `test_resume.py` | 10 | Upload validation, PDF/DOCX parsing |
| `test_resume_advisor.py` | 9 | Resume rating, metric quantification, fluff elimination, bullet rewrites |
| `test_coding_profiles.py` | 5 | GitHub repos & stars, LeetCode Easy/Med/Hard, DSA interview readiness score |
| `test_job_market_analytics.py` | 3 | Cross-role market trends, skill co-occurrence pairs, category distributions |
| `test_skills.py` | 36 | Skill extraction boundaries, case-insensitivity, aliases, gap analysis |
| `test_roadmap.py` | 16 | Roadmap generation, progress tracking, prerequisite chains |
| `test_job_description.py` | 17 | JD analysis, section segmentation, experience extraction |
| `test_role_discovery.py` | 31 | Role listing, comparison, market summaries, taxonomy |
| `test_workflow.py` | 11 | End-to-end workflow integration, IDOR protection |
| `test_frontend_integration.py` | 2 | Static file verification (21 assets) and 15-step lifecycle integration |

All tests use an in-memory SQLite database and do not require network access.

Detailed test documentation is available in [`docs/testing.md`](docs/testing.md).

---

## Example Workflow

Below is a complete workflow using `curl` (or any HTTP client) against the running backend.

**1. Register:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com", "password": "SecurePass123!", "full_name": "Jane Dev"}'
```

**2. Log in:**
```bash
curl -X POST http://127.0.0.1:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "dev@example.com", "password": "SecurePass123!"}'
```
Response includes `access_token`. Use it in subsequent requests.

**3. Upload a resume:**
```bash
curl -X POST http://127.0.0.1:8000/api/resume/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@resume.pdf"
```

**4. Run skill-gap analysis:**
```bash
curl -X POST http://127.0.0.1:8000/api/skills/analyze \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_id": "backend-engineer", "resume_id": 1}'
```

**5. Browse available roles:**
```bash
curl http://127.0.0.1:8000/api/roles/
```

**6. Compare two roles:**
```bash
curl "http://127.0.0.1:8000/api/roles/compare?role_a=backend-engineer&role_b=data-engineer"
```

**7. Generate a roadmap:**
```bash
curl -X POST http://127.0.0.1:8000/api/roadmaps/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role_id": "backend-engineer", "missing_skills": ["Docker", "Kubernetes"]}'
```

**8. Mark a task as completed:**
```bash
curl -X PATCH http://127.0.0.1:8000/api/roadmaps/1/tasks/1/progress \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "completed"}'
```

---

## Implemented vs Planned Features

### ✅ Implemented

- **User Authentication & Session Security:** Salted PBKDF2-HMAC-SHA256 password hashing, stateless signed JWT access tokens, and strict IDOR user isolation.
- **Password Recovery & Email System:** Secure token-based password reset supporting transactional Resend API (HTTPS) and authenticated SMTP (STARTTLS/SSL) with sliding-window rate limiting.
- **In-Memory Resume Parsing:** Zero-storage PDF and DOCX extraction via PyMuPDF and python-docx. Binary files are parsed in RAM and discarded immediately for candidate privacy.
- **Deterministic Skill-Gap Engine:** Pattern-based extraction from curated skill taxonomies across 11 role profiles (4 traditional, 7 emerging).
- **Dynamic Resume Content Advisor:** Real-time resume-grounded recommendations including *Things to Add* (missing algorithms, metrics, datasets), *Things to Remove* (generic soft skills, outdated tools), and an interactive *Google XYZ Formula Bullet Point Optimizer*.
- **Multi-Signal Coding Profile Proofs:** Public GitHub REST and LeetCode GraphQL verification classifying candidate skills into 3 evidence tiers (🟢 Verified Repo, 🟡 Resume Mention, ⚪ Needs Demonstration).
- **Job Description Matcher:** Paste any live job posting to calculate match rate, critical core gaps, and secondary bonuses.
- **Six-Week Roadmap Generation:** Personalized weekly study plans with prerequisite dependency ordering and hour-budget bin packing.
- **Role Explorer & Comparison:** Multi-role comparison with Jaccard skill overlap matrices and evidence-backed market data.
- **Cloud Production Deployment:** Hosted live on Render at [https://skillgraph-1-yfq4.onrender.com](https://skillgraph-1-yfq4.onrender.com) with automatic root browser redirection and CORS-isolated endpoints.
- **Automated Test Suite:** 201 backend integration, security, and edge-case tests with 100% pass rate.

### 🔮 Planned (Future Roadmap)

- **Semantic Skill Matching:** NLP vector embeddings (Sentence Transformers / spaCy) to infer technical competencies from project narratives without exact keyword matches.
- **Production PostgreSQL Migration with pgvector:** Hosted PostgreSQL migration with vector extensions for semantic role retrieval at scale.
- **OAuth 2.0 / SSO:** Google and GitHub one-click login alongside email/password credentials.
- **Live Job Market Aggregation:** Periodic ingestion of real-time market demand signals via public job board APIs with source attribution.
- **Export Capabilities:** Client-side vector PDF and JSON export of generated roadmaps and gap analyses.
- **Account Email Verification:** Mandatory confirmation links for new account registrations.
- **Collaborative Engineering Dashboards:** Team roadmaps, peer benchmarking, and mentorship gap tracking.

---

## Known Limitations

1. **Regex-Based Skill Extraction:** Skill matching relies on deterministic keyword patterns and does not analyze semantic context. For example, a resume stating *"no prior experience with Docker"* would still trigger a keyword match for Docker.

2. **No Semantic Skill Inference:** The parser cannot deduce underlying skills from descriptive prose without explicit terminology. A bullet describing a *"containerized microservices cluster with automated failover"* will not register Docker or Kubernetes unless explicitly stated by name.

3. **Curated Role Catalogue Scope:** The role taxonomy consists of 11 curated engineering roles in a versioned JSON schema. Adding new roles currently requires defining core skills, optional skills, and project blueprints in `role_profiles.json`.

4. **Dual Database Architecture (SQLite Default):** Local development uses SQLite in WAL mode for lightweight zero-dependency setup. Production supports PostgreSQL via `DATABASE_URL`, but automatic multi-region database replication is not implemented.

5. **Curated Market Data Coverage:** Only 3 of the 11 roles (Backend Engineer, Machine Learning Engineer, Data Engineer) contain empirical salary and demand data with documented sample sizes and geographies. The remaining 8 emerging roles provide qualitative guidance with transparent disclaimers.

6. **No Live Web Scraping:** Market demand indicators are statically curated and verified to avoid unverified scraping or rate-limit fragility. The system does not dynamically scrape external job portals.

7. **No Social OAuth/SSO:** Authentication currently supports secure email and password login only; third-party identity providers (Google/GitHub OAuth) are not yet integrated.

8. **English Language Only:** Extraction regex patterns, ontology dictionaries, and role profiles are optimized exclusively for English-language resumes.

9. **Zero Raw File Persistence by Design:** Uploaded PDF and DOCX binaries are parsed in volatile memory and purged immediately. Original source files cannot be re-downloaded from the platform.

10. **Unverified Registration Emails:** While password recovery dispatches verified reset links via Resend/SMTP, initial account creation does not mandate email address verification prior to first login.

---

## Future Improvements

- **Semantic Embedding Matching:** Integrate lightweight Sentence Transformers to score semantic similarity between resume project descriptions and target role competencies.
- **Full PostgreSQL + pgvector Migration:** Shift permanent production data storage to PostgreSQL with pgvector for fast cosine-similarity search across resumes and role ontologies.
- **OAuth 2.0 Authentication:** Add GitHub and Google single sign-on buttons to simplify onboarding.
- **Dynamic Role Management Interface:** Provide an administrative interface allowing verified curriculum leads to add, modify, or deprecate roles without manual JSON editing.
- **Real-Time Market Data Feeds:** Ingest verified job data through approved employment APIs (such as Adzuna or GitHub Jobs archives) with proper geographic filtering and source citations.
- **Roadmap & Analysis PDF Export:** Generate branded, downloadable PDF summary cards of the 6-Week Roadmap and Skill Gap Matrix for offline study.
- **Collaborative Mentorship Spaces:** Allow candidates to share their 6-week roadmaps and progress with mentors or study groups.

---

## Documentation

| Document | Description |
|----------|-------------|
| [`docs/architecture.md`](docs/architecture.md) | System architecture, component design, data flow |
| [`docs/api-reference.md`](docs/api-reference.md) | Complete API endpoint documentation with schemas |
| [`docs/testing.md`](docs/testing.md) | Test suite inventory, 155-test breakdown, run instructions |
| [`docs/implementation-plan.md`](docs/implementation-plan.md) | Phased development plan |
| [`docs/market-data-methodology.md`](docs/market-data-methodology.md) | Market data collection methodology and standards |
| [`docs/ui-reference.md`](docs/ui-reference.md) | UI design specification |

---

## Licence

This project is provided for educational and portfolio purposes.
