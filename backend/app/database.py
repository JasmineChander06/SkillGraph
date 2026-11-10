"""Database configuration and session management using SQLAlchemy."""

from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

logger = logging.getLogger("skillgraph.database")


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 base class for all SkillGraph database models."""
    pass


# SQLite-specific connect args (check_same_thread=False for FastAPI concurrency)
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a transactional SQLAlchemy session.
    Automatically closes session upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(bind_engine=None) -> None:
    """Create all configured database tables."""
    # Import all models to ensure they are registered with Base.metadata
    from app.models.user import User  # noqa: F401
    from app.models.resume import ResumeRecord  # noqa: F401
    from app.models.analysis import SkillAnalysisRecord  # noqa: F401
    from app.models.roadmap import RoadmapRecord, RoadmapTaskRecord  # noqa: F401
    from app.models.progress import TaskProgressRecord  # noqa: F401
    from app.models.job_description import JobDescriptionAnalysisRecord  # noqa: F401

    target = bind_engine or engine
    Base.metadata.create_all(bind=target)

    # Seamlessly add onboarding columns to existing sqlite users table if missing
    try:
        from sqlalchemy import text
        with target.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(users)"))
            cols = {row[1] for row in result.fetchall()}
            if cols:
                if "education_stage" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN education_stage VARCHAR(100)"))
                if "career_interests" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN career_interests VARCHAR(255)"))
                if "skill_level" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN skill_level VARCHAR(50)"))
                if "target_role" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN target_role VARCHAR(100)"))
                if "github_username" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN github_username VARCHAR(100)"))
                if "leetcode_username" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN leetcode_username VARCHAR(100)"))
                if "onboarding_completed" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN onboarding_completed BOOLEAN DEFAULT 0"))
                conn.commit()
    except Exception as exc:
        logger.debug("Migration check note: %s", exc)

    logger.info("Database tables initialized successfully.")


def drop_db(bind_engine=None) -> None:
    """Drop all tables (primarily for test teardown)."""
    target = bind_engine or engine
    Base.metadata.drop_all(bind=target)

