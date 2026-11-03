# SkillGraph

SkillGraph is an evidence-based career readiness platform. It quantifies the distance between a candidate's verified technical capabilities (derived from resumes, GitHub activity, and self-assessments) and industry expectations (derived from curated role ontologies and parsed job postings).

## Project Structure

```
SkillGraph/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Backend application package
│   │   ├── main.py              # FastAPI entrypoint, middleware, and route registration
│   │   ├── config.py            # Pydantic Settings configuration
│   │   ├── api/                 # API route controllers
│   │   │   ├── __init__.py
│   │   │   └── resume.py        # POST /api/resume/parse endpoint
│   │   ├── schemas/             # Pydantic v2 validation models
│   │   │   ├── __init__.py
│   │   │   └── resume.py        # DocumentMetadata & ResumeParseResponse
│   │   └── services/            # Core business logic
│   │       ├── __init__.py
│   │       └── resume_parser.py # PyMuPDF & python-docx extraction engine
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py          # Pytest path and environment fixtures
│   │   ├── test_health.py       # Automated tests for GET /api/health and CORS
│   │   └── test_resume.py       # Automated tests for POST /api/resume/parse
│   ├── requirements.txt         # Backend Python dependencies
│   ├── .env.example             # Example environment variables
│   └── .gitignore               # Backend-specific ignore rules
├── frontend/                    # Pure Vanilla HTML5/CSS3/JS client (upcoming)
├── docs/
│   ├── architecture.md          # Full-stack system architecture
│   ├── implementation-plan.md   # Phased development sequence and roadmap
│   └── ui-reference.md          # Paper & Ink UI design specification
├── README.md
└── .gitignore
```

## Getting Started

### 1. Backend Setup

From the `backend` directory:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the Development Server

```powershell
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

* **API Health Check:** `http://127.0.0.1:8000/api/health`
* **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
* **ReDoc Documentation:** `http://127.0.0.1:8000/redoc`

### 3. Running Automated Tests

From the `backend` directory:

```powershell
cd backend
python -m pytest tests -v
```

Or from the repository root:

```powershell
python -m pytest backend/tests -v
```

