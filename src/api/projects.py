import logging
import json
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from src.database import get_db
from src.database.models import Project, TaskLog, User, TaskStatus
from src.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from src.services.web_task_processor import WebTaskProcessor

router = APIRouter(prefix="/api/projects", tags=["Projects"])
logger = logging.getLogger(__name__)


# Simple auth dependency (replace with JWT in production)
async def get_current_user_id(user_id: int = 1) -> int:
    """Temporary: Get user_id from query param. Replace with JWT."""
    return user_id


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """建立新專案並在背景執行任務"""
    try:
        # Create project
        new_project = Project(
            owner_id=user_id,
            name=project.name,
            description=project.description,
            task_prompt=project.task_prompt,
            status=TaskStatus.PENDING
        )
        db.add(new_project)
        db.commit()
        db.refresh(new_project)

        # Start task in background
        processor = WebTaskProcessor(db)
        background_tasks.add_task(processor.process_task, new_project.id)

        logger.info(f"Created project {new_project.id}: {new_project.name}")
        return new_project

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取得使用者的所有專案"""
    projects = (
        db.query(Project)
        .filter(Project.owner_id == user_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取得特定專案詳情"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    updates: ProjectUpdate,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """更新專案資訊"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields
    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    logger.info(f"Updated project {project_id}")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """刪除專案"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(project)
    db.commit()
    logger.info(f"Deleted project {project_id}")
    return None


@router.get("/{project_id}/logs")
async def get_project_logs(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """取得專案的執行日誌"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logs = (
        db.query(TaskLog)
        .filter(TaskLog.project_id == project_id)
        .order_by(TaskLog.created_at.asc())
        .all()
    )

    return [
        {
            "id": log.id,
            "message": log.message,
            "log_type": log.log_type,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


@router.get("/{project_id}/stream")
async def stream_project_progress(
    project_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """SSE 串流專案進度"""
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    async def event_generator():
        """Generate SSE events"""
        last_log_id = 0
        import asyncio

        while True:
            # Refresh project status
            db.refresh(project)

            # Get new logs
            new_logs = (
                db.query(TaskLog)
                .filter(
                    TaskLog.project_id == project_id,
                    TaskLog.id > last_log_id
                )
                .order_by(TaskLog.created_at.asc())
                .all()
            )

            # Send new logs
            for log in new_logs:
                data = {
                    "type": "log",
                    "log_id": log.id,
                    "message": log.message,
                    "log_type": log.log_type,
                    "timestamp": log.created_at.isoformat()
                }
                yield f"data: {json.dumps(data)}\n\n"
                last_log_id = log.id

            # Send status update
            status_data = {
                "type": "status",
                "status": project.status.value,
                "updated_at": project.updated_at.isoformat()
            }
            yield f"data: {json.dumps(status_data)}\n\n"

            # Check if completed
            if project.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                final_data = {
                    "type": "complete",
                    "status": project.status.value,
                    "result_summary": project.result_summary,
                    "error_message": project.error_message
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                break

            await asyncio.sleep(1)  # Poll every second

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
