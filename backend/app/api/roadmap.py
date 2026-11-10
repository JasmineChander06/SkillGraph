"""Roadmap and Progress API — personalized 6-week learning roadmaps and tracking."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.progress import TaskProgressRecord
from app.models.resume import ResumeRecord
from app.models.roadmap import RoadmapRecord, RoadmapTaskRecord
from app.models.user import User
from app.schemas.auth import ProgressSummaryResponse, TaskProgressItem, TaskStatusUpdateRequest
from app.schemas.roadmap import Roadmap, RoadmapGenerateRequest
from app.services import roadmap_generator
from app.services.auth import get_current_user, get_optional_current_user

logger = logging.getLogger("skillgraph.api.roadmap")

router = APIRouter(tags=["Roadmaps & Progress"])


@router.post(
    "/api/roadmaps/generate",
    response_model=Roadmap,
    summary="Generate a personalized 6-week learning roadmap",
)
@router.post(
    "/roadmap/generate",
    response_model=Roadmap,
    include_in_schema=False,
)
async def generate_roadmap(
    request: RoadmapGenerateRequest,
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> Roadmap:
    """Generate an actionable 6-week study roadmap based on target role, existing skills,
    missing skill gaps, prerequisite chains, and weekly study availability.

    Persists the generated roadmap and tasks when called by an authenticated user.
    """
    existing_skills = request.existing_skills or []
    resume_text = request.resume_text

    # If authenticated and existing_skills was not passed, load from user's latest resume
    if current_user and not existing_skills:
        latest_resume = (
            db.query(ResumeRecord)
            .filter(ResumeRecord.user_id == current_user.id, ResumeRecord.is_deleted == False)
            .order_by(ResumeRecord.created_at.desc())
            .first()
        )
        if latest_resume:
            if not resume_text:
                resume_text = latest_resume.extracted_text
            if latest_resume.extracted_skills_json:
                try:
                    existing_skills = json.loads(latest_resume.extracted_skills_json)
                except Exception:
                    pass

    try:
        roadmap = roadmap_generator.generate_roadmap(
            role_id=request.role_id,
            existing_skills=existing_skills,
            missing_skills=request.missing_skills,
            weekly_hours=request.weekly_hours or 10,
            resume_text=resume_text,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Role '{request.role_id}' not found. Use GET /api/roles to list valid IDs.",
        ) from exc

    if current_user:
        try:
            roadmap_rec = RoadmapRecord(
                user_id=current_user.id,
                role_id=roadmap.role_id,
                role_title=roadmap.role_title,
                total_weeks=roadmap.total_weeks,
                target_weekly_hours=roadmap.target_weekly_hours,
                total_estimated_hours=roadmap.total_estimated_hours,
                capstone_project=roadmap.capstone_project,
                notes_json=json.dumps(roadmap.notes),
            )
            db.add(roadmap_rec)
            db.flush()

            for task in roadmap.tasks:
                task_rec = RoadmapTaskRecord(
                    roadmap_id=roadmap_rec.id,
                    task_key=task.id,
                    title=task.title,
                    description=task.description,
                    target_skill=task.target_skill,
                    week=task.week,
                    estimated_effort=task.estimated_effort,
                    prerequisites_json=json.dumps(task.prerequisites),
                    learning_resource_json=json.dumps(task.learning_resource.model_dump()),
                    completion_status="pending",
                )
                db.add(task_rec)
                db.flush()

                # Seed initial task progress
                progress = TaskProgressRecord(
                    user_id=current_user.id,
                    task_id=task_rec.id,
                    status="pending",
                )
                db.add(progress)

            db.commit()
            db.refresh(roadmap_rec)
            logger.info("Persisted RoadmapRecord ID %s for User ID %s", roadmap_rec.id, current_user.id)
        except Exception as exc:
            logger.warning("Failed to persist RoadmapRecord: %s", exc)
            db.rollback()

    return roadmap


@router.get(
    "/api/roadmaps",
    status_code=status.HTTP_200_OK,
    summary="List Authenticated User's Roadmaps",
)
async def list_user_roadmaps(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """Return all roadmaps created for the authenticated user."""
    roadmaps = (
        db.query(RoadmapRecord)
        .filter(RoadmapRecord.user_id == current_user.id)
        .order_by(RoadmapRecord.created_at.desc())
        .all()
    )

    results = []
    for r in roadmaps:
        total_tasks = len(r.tasks)
        completed_tasks = sum(1 for t in r.tasks if t.completion_status == "completed")
        results.append({
            "id": r.id,
            "role_id": r.role_id,
            "role_title": r.role_title,
            "total_weeks": r.total_weeks,
            "target_weekly_hours": r.target_weekly_hours,
            "total_estimated_hours": r.total_estimated_hours,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "completion_percentage": round((completed_tasks / total_tasks * 100), 1) if total_tasks > 0 else 0.0,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return results


@router.get(
    "/api/roadmaps/{roadmap_id}",
    status_code=status.HTTP_200_OK,
    summary="Get Specific Roadmap Details",
)
async def get_user_roadmap(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retrieve full roadmap details with tasks. Enforces ownership check (IDOR protection)."""
    roadmap = db.query(RoadmapRecord).filter(RoadmapRecord.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found.")

    if roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this roadmap.",
        )

    tasks_data = []
    for t in roadmap.tasks:
        tasks_data.append({
            "id": t.id,
            "task_key": t.task_key,
            "title": t.title,
            "description": t.description,
            "target_skill": t.target_skill,
            "week": t.week,
            "estimated_effort": t.estimated_effort,
            "prerequisites": t.get_prerequisites(),
            "learning_resource": t.get_learning_resource(),
            "completion_status": t.completion_status,
        })

    return {
        "id": roadmap.id,
        "role_id": roadmap.role_id,
        "role_title": roadmap.role_title,
        "total_weeks": roadmap.total_weeks,
        "target_weekly_hours": roadmap.target_weekly_hours,
        "total_estimated_hours": roadmap.total_estimated_hours,
        "capstone_project": roadmap.capstone_project,
        "notes": json.loads(roadmap.notes_json) if roadmap.notes_json else [],
        "tasks": tasks_data,
        "created_at": roadmap.created_at.isoformat() if roadmap.created_at else None,
    }


@router.delete(
    "/api/roadmaps/{roadmap_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete User Roadmap",
)
async def delete_user_roadmap(
    roadmap_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Delete a roadmap and its tasks owned by the authenticated user."""
    roadmap = db.query(RoadmapRecord).filter(RoadmapRecord.id == roadmap_id).first()
    if not roadmap:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Roadmap not found.")

    if roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this roadmap.",
        )

    db.delete(roadmap)
    db.commit()
    return {"ok": True, "message": f"Roadmap {roadmap_id} deleted successfully."}


@router.patch(
    "/api/roadmaps/{roadmap_id}/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Update Roadmap Task Completion Status",
)
@router.patch(
    "/api/roadmaps/tasks/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Update Task Status (Direct)",
)
@router.patch(
    "/roadmap/{task_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_task_status(
    task_id: int,
    request: Optional[TaskStatusUpdateRequest] = None,
    done: Optional[bool] = Query(None, description="Query parameter done flag"),
    roadmap_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update task completion status and persist progress for the authenticated user.

    Strictly enforces that the task belongs to a roadmap owned by the authenticated user.
    """
    task = db.query(RoadmapTaskRecord).filter(RoadmapTaskRecord.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    # Ownership check: verify that task's roadmap is owned by current_user
    if not task.roadmap or task.roadmap.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: you do not own this roadmap task.",
        )

    if roadmap_id is not None and task.roadmap_id != roadmap_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Task {task_id} does not belong to Roadmap {roadmap_id}.",
        )

    # Determine desired status
    target_status = "pending"
    notes = None
    if request:
        notes = request.notes
        if request.status:
            target_status = request.status
        elif request.done is not None:
            target_status = "completed" if request.done else "pending"
    elif done is not None:
        target_status = "completed" if done else "pending"

    # Find or create user progress record
    progress = (
        db.query(TaskProgressRecord)
        .filter(
            TaskProgressRecord.user_id == current_user.id,
            TaskProgressRecord.task_id == task.id,
        )
        .first()
    )
    if not progress:
        progress = TaskProgressRecord(
            user_id=current_user.id,
            task_id=task.id,
            status=target_status,
            notes=notes,
        )
        db.add(progress)

    if target_status == "completed":
        progress.mark_completed()
    elif target_status == "in_progress":
        progress.mark_in_progress()
    else:
        progress.reset_status()

    if notes is not None:
        progress.notes = notes

    task.completion_status = target_status
    db.commit()

    return {
        "ok": True,
        "task_id": task.id,
        "status": task.completion_status,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }


@router.get(
    "/api/progress",
    response_model=ProgressSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve Authenticated User's Overall Learning Progress",
)
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProgressSummaryResponse:
    """Retrieve aggregate progress metrics across all roadmaps for the authenticated user."""
    # Find all roadmaps for user
    roadmaps = db.query(RoadmapRecord).filter(RoadmapRecord.user_id == current_user.id).all()
    roadmap_ids = [r.id for r in roadmaps]

    all_tasks = (
        db.query(RoadmapTaskRecord)
        .filter(RoadmapTaskRecord.roadmap_id.in_(roadmap_ids))
        .all()
        if roadmap_ids
        else []
    )

    # Query progress records
    progress_map = {
        p.task_id: p
        for p in db.query(TaskProgressRecord).filter(TaskProgressRecord.user_id == current_user.id).all()
    }

    total_tasks = len(all_tasks)
    completed_count = 0
    in_progress_count = 0
    pending_count = 0
    progress_items = []

    for t in all_tasks:
        prog = progress_map.get(t.id)
        effective_status = prog.status if prog else t.completion_status
        if effective_status == "completed":
            completed_count += 1
        elif effective_status == "in_progress":
            in_progress_count += 1
        else:
            pending_count += 1

        progress_items.append(
            TaskProgressItem(
                task_id=t.id,
                task_key=t.task_key,
                title=t.title,
                target_skill=t.target_skill,
                week=t.week,
                status=effective_status,
                completed_at=prog.completed_at if prog else None,
                notes=prog.notes if prog else None,
            )
        )

    completion_pct = round((completed_count / total_tasks * 100), 1) if total_tasks > 0 else 0.0

    return ProgressSummaryResponse(
        user_id=current_user.id,
        total_tasks=total_tasks,
        completed_tasks=completed_count,
        in_progress_tasks=in_progress_count,
        pending_tasks=pending_count,
        completion_percentage=completion_pct,
        active_roadmaps_count=len(roadmaps),
        progress_items=progress_items,
    )


# Architecture.md compatibility endpoint
@router.get("/roadmap/", include_in_schema=False)
async def get_roadmap_compat(
    current_user: Optional[User] = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    """Architecture doc compatibility endpoint."""
    if not current_user:
        return []
    latest_roadmap = (
        db.query(RoadmapRecord)
        .filter(RoadmapRecord.user_id == current_user.id)
        .order_by(RoadmapRecord.created_at.desc())
        .first()
    )
    if not latest_roadmap:
        return []

    return [
        {
            "id": str(t.id),
            "week": t.week,
            "focus": f"Week {t.week} Core",
            "item": t.title,
            "done": t.completion_status == "completed",
        }
        for t in latest_roadmap.tasks
    ]
