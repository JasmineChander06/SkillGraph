"""User entity model and cryptographic password hashing utilities."""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.analysis import SkillAnalysisRecord
    from app.models.job_description import JobDescriptionAnalysisRecord
    from app.models.progress import TaskProgressRecord
    from app.models.resume import ResumeRecord
    from app.models.roadmap import RoadmapRecord


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-HMAC-SHA256 with 100,000 iterations and a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its salt-delimited hash."""
    try:
        salt_hex, key_hex = hashed_password.split("$")
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return secrets.compare_digest(key.hex(), key_hex)
    except Exception:
        return False


class User(Base):
    """User account entity representing a candidate or developer."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    education_stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    career_interests: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skill_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    github_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    leetcode_username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    resumes: Mapped[List[ResumeRecord]] = relationship(
        "ResumeRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    analyses: Mapped[List[SkillAnalysisRecord]] = relationship(
        "SkillAnalysisRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    roadmaps: Mapped[List[RoadmapRecord]] = relationship(
        "RoadmapRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    job_analyses: Mapped[List[JobDescriptionAnalysisRecord]] = relationship(
        "JobDescriptionAnalysisRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    progress_records: Mapped[List[TaskProgressRecord]] = relationship(
        "TaskProgressRecord",
        back_populates="user",
        cascade="all, delete-orphan",
    )

