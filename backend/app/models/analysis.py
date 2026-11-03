"""Skill-gap analysis persistence model."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.resume import ResumeRecord
    from app.models.user import User


class SkillAnalysisRecord(Base):
    """Persisted skill-gap analysis comparing a candidate profile against a curated role."""

    __tablename__ = "skill_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    resume_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, nullable=False)

    # Serialized JSON structures
    matched_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    missing_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    uncertain_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    priority_gaps_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship("User", back_populates="analyses")
    resume: Mapped[Optional[ResumeRecord]] = relationship("ResumeRecord", back_populates="analyses")

    def get_matched_skills(self) -> List[dict]:
        return json.loads(self.matched_skills_json) if self.matched_skills_json else []

    def get_missing_skills(self) -> List[dict]:
        return json.loads(self.missing_skills_json) if self.missing_skills_json else []

    def get_uncertain_skills(self) -> List[dict]:
        return json.loads(self.uncertain_skills_json) if self.uncertain_skills_json else []

    def get_priority_gaps(self) -> List[dict]:
        return json.loads(self.priority_gaps_json) if self.priority_gaps_json else []

