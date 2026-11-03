"""Progress tracking entity ensuring state survives application restarts."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.roadmap import RoadmapTaskRecord
    from app.models.user import User


class TaskProgressRecord(Base):
    """User-specific progress and completion status for a roadmap task."""

    __tablename__ = "task_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_user_task_progress"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("roadmap_tasks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # "pending", "in_progress", "completed"
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped[User] = relationship("User", back_populates="progress_records")
    task: Mapped[RoadmapTaskRecord] = relationship("RoadmapTaskRecord", back_populates="progress_records")

    def mark_completed(self) -> None:
        """Mark task as completed with current timestamp."""
        self.status = "completed"
        self.completed_at = datetime.now()
        if self.task:
            self.task.completion_status = "completed"

    def mark_in_progress(self) -> None:
        """Mark task as currently in progress."""
        self.status = "in_progress"
        self.completed_at = None
        if self.task:
            self.task.completion_status = "in_progress"

    def reset_status(self) -> None:
        """Reset task status to pending."""
        self.status = "pending"
        self.completed_at = None
        if self.task:
            self.task.completion_status = "pending"

