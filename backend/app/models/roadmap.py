"""Roadmap and task persistence models."""

from __future__ import annotations

import json
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.progress import TaskProgressRecord
    from app.models.user import User


class RoadmapRecord(Base):
    """Persisted 6-week learning roadmap."""

    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    role_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    total_weeks: Mapped[int] = mapped_column(Integer, default=6, nullable=False)
    target_weekly_hours: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    total_estimated_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    capstone_project: Mapped[str] = mapped_column(Text, nullable=False)
    notes_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)

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
    user: Mapped[Optional[User]] = relationship("User", back_populates="roadmaps")
    tasks: Mapped[List[RoadmapTaskRecord]] = relationship(
        "RoadmapTaskRecord",
        back_populates="roadmap",
        cascade="all, delete-orphan",
        order_by="RoadmapTaskRecord.week",
    )


class RoadmapTaskRecord(Base):
    """Persisted individual task within a roadmap."""

    __tablename__ = "roadmap_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    roadmap_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roadmaps.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_key: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_skill: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 1 to 6
    estimated_effort: Mapped[int] = mapped_column(Integer, nullable=False)
    prerequisites_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    learning_resource_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    completion_status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )

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
    roadmap: Mapped[RoadmapRecord] = relationship("RoadmapRecord", back_populates="tasks")
    progress_records: Mapped[List[TaskProgressRecord]] = relationship(
        "TaskProgressRecord",
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def get_prerequisites(self) -> List[str]:
        return json.loads(self.prerequisites_json) if self.prerequisites_json else []

    def get_learning_resource(self) -> dict:
        return json.loads(self.learning_resource_json) if self.learning_resource_json else {}

