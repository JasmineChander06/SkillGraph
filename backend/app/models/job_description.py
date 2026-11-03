"""Job description comparison persistence model."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class JobDescriptionAnalysisRecord(Base):
    """Persisted comparative analysis between a resume and a pasted job description."""

    __tablename__ = "job_description_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    job_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    job_description_text: Mapped[str] = mapped_column(Text, nullable=False)
    coverage_percent: Mapped[float] = mapped_column(Float, nullable=False)

    # Serialized analysis structures
    extracted_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    matched_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    missing_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    required_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    preferred_skills_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    experience_requirements_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    caveats_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship("User", back_populates="job_analyses")

    def get_extracted_skills(self) -> List[dict]:
        return json.loads(self.extracted_skills_json) if self.extracted_skills_json else []

    def get_matched_skills(self) -> List[dict]:
        return json.loads(self.matched_skills_json) if self.matched_skills_json else []

    def get_missing_skills(self) -> List[dict]:
        return json.loads(self.missing_skills_json) if self.missing_skills_json else []

    def get_experience_requirements(self) -> List[dict]:
        return json.loads(self.experience_requirements_json) if self.experience_requirements_json else []

