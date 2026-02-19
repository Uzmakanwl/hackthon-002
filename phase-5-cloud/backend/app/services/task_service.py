"""Service layer for task CRUD operations."""

import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Task, TaskPriority, TaskStatus
from app.schemas import TaskCreate, TaskUpdate


def create_task(session: Session, task_in: TaskCreate) -> Task:
    """Create a new task and persist it to the database."""
    task = Task(**task_in.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Retrieve a single task by its ID. Returns None if not found."""
    return session.get(Task, task_id)


def list_tasks(
    session: Session,
    *,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    tag: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> tuple[list[Task], int]:
    """List tasks with optional filtering, searching, and sorting.

    Returns a tuple of (tasks, total_count).
    """
    statement = select(Task)

    # Apply filters
    if status:
        statement = statement.where(Task.status == status)
    if priority:
        statement = statement.where(Task.priority == priority)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            Task.title.ilike(pattern) | Task.description.ilike(pattern)  # type: ignore[union-attr]
        )

    # Apply sorting
    if sort_by:
        sort_column = getattr(Task, sort_by, Task.created_at)
    else:
        sort_column = Task.created_at

    if sort_order == "desc":
        statement = statement.order_by(sort_column.desc())  # type: ignore[union-attr]
    else:
        statement = statement.order_by(sort_column.asc())  # type: ignore[union-attr]

    tasks = list(session.exec(statement).all())

    # Tag filtering (post-query since tags is a JSON column)
    if tag:
        tasks = [
            t for t in tasks
            if tag.lower() in [tg.lower() for tg in (t.tags or [])]
        ]

    return tasks, len(tasks)


def update_task(
    session: Session, task_id: uuid.UUID, task_in: TaskUpdate
) -> Optional[Task]:
    """Partially update a task. Returns None if the task is not found."""
    task = session.get(Task, task_id)
    if not task:
        return None

    update_data = task_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: uuid.UUID) -> bool:
    """Delete a task by ID. Returns True if deleted, False if not found."""
    task = session.get(Task, task_id)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True


def toggle_complete(session: Session, task_id: uuid.UUID) -> Optional[Task]:
    """Toggle a task between completed and pending status.

    Returns the updated task, or None if not found.
    """
    task = session.get(Task, task_id)
    if not task:
        return None

    if task.status == TaskStatus.COMPLETED:
        task.status = TaskStatus.PENDING
        task.completed_at = None
    else:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
