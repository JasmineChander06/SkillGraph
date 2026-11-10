"""SkillGraph FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.auth import router as auth_router
from app.api.job_descriptions import router as job_descriptions_router
from app.api.profiles import router as profiles_router
from app.api.resume import router as resume_router
from app.api.roadmap import router as roadmap_router
from app.api.roles import router as roles_router
from app.api.skills import router as skills_router
from app.config import settings
from app.database import init_db

logger = logging.getLogger("skillgraph.main")

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initialize database tables on startup and audit security settings."""
    init_db()
    if settings.ENVIRONMENT.lower() == "production" and settings.SECRET_KEY.startswith("CHANGE-ME"):
        logger.warning(
            "SECURITY WARNING: Default SECRET_KEY is in use in production mode. "
            "Configure a cryptographically secure SECRET_KEY in environment variables."
        )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SkillGraph API — Career readiness graph, skills gap analysis, learning roadmaps, and authentication.",
    debug=settings.DEBUG,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS explicitly for authorized local origins (no wildcard with credentials)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(roles_router)
app.include_router(skills_router)
app.include_router(job_descriptions_router)
app.include_router(roadmap_router)
app.include_router(profiles_router)

# Serve Frontend static assets if available
if FRONTEND_DIR.is_dir():
    app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.get("/api/health", tags=["Health"])
async def health_check():
    """Health check endpoint confirming that the backend application is running."""
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Root"])
async def root(request: Request):
    """Root endpoint: redirects browser requests to frontend landing page, returns JSON for API clients."""
    accept = request.headers.get("accept", "")
    # Browsers requesting HTML are redirected to the frontend landing page
    if "text/html" in accept:
        return RedirectResponse(url="/frontend/index.html")
    # API clients, tests, or tools requesting root receive the JSON API description
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
        "frontend": "/frontend/index.html",
    }
