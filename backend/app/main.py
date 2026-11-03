"""SkillGraph FastAPI Application Entrypoint."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.job_descriptions import router as job_descriptions_router
from app.api.resume import router as resume_router
from app.api.roadmap import router as roadmap_router
from app.api.roles import router as roles_router
from app.api.skills import router as skills_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initialize database tables on startup."""
    init_db()
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
async def root():
    """Root endpoint providing a friendly status greeting and documentation link."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
    }
