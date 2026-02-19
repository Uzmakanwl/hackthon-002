"""Task CRUD and filter/sort API endpoints with event publishing."""

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.db import get_session
from app.models import TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskListResponse, TaskResponse, TaskUpdate
from app.services import task_service, recurrence_service
from app.events.schemas import EventType, TaskEvent
from app.events.producer import publish_event

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task_in: TaskCreate,
    session: Session = Depends(get_session),
) -> TaskResponse:
    """Create a new task and publish task.created event."""
    task = task_service.create_task(session, task_in)

    # Fire-and-forget: publish event
    try:
        event = TaskEvent(
            event_type=EventType.TASK_CREATED,
            task_id=str(task.id),
            payload={"title": task.title, "priority": task.priority.value},
        )
        await publish_event(event)
    except Exception as exc:
        logger.error("Failed to publish task.created event: %s", exc)

    return TaskResponse.model_validate(task)


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    status: Optional[TaskStatus] = Query(default=None),
    priority: Optional[TaskPriority] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    sort_by: Optional[str] = Query(
        default=None, pattern="^(due_date|priority|created_at|title)$"
    ),
    sort_order: Optional[str] = Query(default="asc", pattern="^(asc|desc)$"),
    session: Session = Depends(get_session),
) -> TaskListResponse:
    """List tasks with optional filtering, searching, and sorting."""
    tasks, total = task_service.list_tasks(
        session,
        status=status,
        priority=priority,
        tag=tag,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order or "asc",
    )
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(t) for t in tasks],
        total=total,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> TaskResponse:
    """Get a single task by ID."""
    task = task_service.get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskResponse.model_validate(task)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID,
    task_in: TaskUpdate,
    session: Session = Depends(get_session),
) -> TaskResponse:
    """Partially update a task and publish task.updated event."""
    task = task_service.update_task(session, task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Fire-and-forget: publish event
    try:
        event = TaskEvent(
            event_type=EventType.TASK_UPDATED,
            task_id=str(task.id),
            payload=task_in.model_dump(exclude_unset=True, mode="json"),
        )
        await publish_event(event)
    except Exception as exc:
        logger.error("Failed to publish task.updated event: %s", exc)

    return TaskResponse.model_validate(task)


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> None:
    """Delete a task by ID and publish task.deleted event."""
    deleted = task_service.delete_task(session, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    # Fire-and-forget: publish event
    try:
        event = TaskEvent(
            event_type=EventType.TASK_DELETED,
            task_id=str(task_id),
        )
        await publish_event(event)
    except Exception as exc:
        logger.error("Failed to publish task.deleted event: %s", exc)


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def toggle_complete(
    task_id: uuid.UUID,
    session: Session = Depends(get_session),
) -> TaskResponse:
    """Toggle a task's completion status and publish task.completed event.

    If the task is recurring, also triggers recurrence handling.
    """
    task = task_service.toggle_complete(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Handle recurrence if completing a recurring task
    new_task = None
    if task.status == TaskStatus.COMPLETED and task.is_recurring:
        new_task = recurrence_service.handle_recurrence_on_complete(session, task)

    # Fire-and-forget: publish event
    try:
        event = TaskEvent(
            event_type=EventType.TASK_COMPLETED,
            task_id=str(task.id),
            payload={
                "status": task.status.value,
                "is_recurring": task.is_recurring,
                "recurrence_rule": task.recurrence_rule,
            },
        )
        await publish_event(event)

        if new_task:
            recurring_event = TaskEvent(
                event_type=EventType.RECURRING_TRIGGERED,
                task_id=str(new_task.id),
                payload={
                    "original_task_id": str(task.id),
                    "recurrence_rule": task.recurrence_rule,
                    "next_due_date": new_task.due_date.isoformat() if new_task.due_date else None,
                },
            )
            await publish_event(recurring_event)
    except Exception as exc:
        logger.error("Failed to publish task.completed event: %s", exc)

    return TaskResponse.model_validate(task)
