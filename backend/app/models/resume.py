"""Resume persistence model and data retention policies.

Data Retention & Privacy Policy:
--------------------------------
1. File Storage Policy:
   SkillGraph NEVER stores raw binary document uploads (PDF/DOCX byte streams) on disk
   or in the database. Binary payloads are parsed in transient memory and discarded immediately.
2. What is Persisted:
   Only sanitized plain text (`extracted_text`), document metadata (filename, file size,
   detected format), and cached skill tags (`extracted_skills_json`) are stored.
3. How to Delete Resume Data:
   Deleting a `ResumeRecord` (or its parent `User`) triggers a cascading purge that
   permanently removes the extracted text and associated skill analyses from the database.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.analysis import SkillAnalysisRecord
    from app.models.user import User


class ResumeRecord(Base):
    """Persisted resume metadata and extracted plain-text content."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "pdf" or "docx"
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_skills_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[Optional[User]] = relationship("User", back_populates="resumes")
    analyses: Mapped[List[SkillAnalysisRecord]] = relationship(
        "SkillAnalysisRecord",
        back_populates="resume",
        cascade="all, delete-orphan",
    )

    def get_extracted_skills(self) -> List[dict]:
        """Return cached skill extractions as a deserialized list of dicts."""
        if not self.extracted_skills_json:
            return []
        try:
            return json.loads(self.extracted_skills_json)
        except Exception:
            return []

    def set_extracted_skills(self, skills: List[dict]) -> None:
        """Serialize skill extractions into JSON text for storage."""
        self.extracted_skills_json = json.dumps(skills)

