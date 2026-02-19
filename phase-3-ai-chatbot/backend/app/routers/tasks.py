"""Task CRUD and filter/sort REST API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from app.db import get_session
from app.models import TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services.task_service import (
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
    toggle_complete,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
def create(data: TaskCreate, session: Session = Depends(get_session)):
    """Create a new task."""
    task = create_task(session, data)
    return task


@router.get("", response_model=TaskListResponse)
def list_all(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    """List tasks with optional filtering, search, and sort."""
    tasks, total = list_tasks(
        session,
        status=status,
        priority=priority,
        search=search,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TaskListResponse(tasks=tasks, total=total)


@router.get("/{task_id}", response_model=TaskResponse)
def get_one(task_id: str, session: Session = Depends(get_session)):
    """Get a single task by ID."""
    task = get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update(task_id: str, data: TaskUpdate, session: Session = Depends(get_session)):
    """Partially update a task."""
    task = update_task(session, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
def delete(task_id: str, session: Session = Depends(get_session)):
    """Delete a task by ID."""
    success = delete_task(session, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete(task_id: str, session: Session = Depends(get_session)):
    """Toggle task completion status."""
    task = toggle_complete(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
