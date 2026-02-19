# app/services/task_service.py
"""Business logic for task CRUD operations."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Task, TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate
from app.services.recurrence_service import handle_recurrence_on_complete


def create_task(session: Session, data: TaskCreate) -> Task:
    """Create a new task and persist to DB."""
    task = Task(**data.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: str) -> Task | None:
    """Retrieve a task by ID."""
    return session.get(Task, task_id)


def list_tasks(
    session: Session,
    *,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Task], int]:
    """List tasks with filtering, searching, and sorting.

    Returns (tasks, total_count).
    """
    statement = select(Task)

    if status:
        statement = statement.where(Task.status == status)
    if priority:
        statement = statement.where(Task.priority == priority)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            Task.title.ilike(pattern) | Task.description.ilike(pattern)
        )

    # Sorting
    sort_column = getattr(Task, sort_by, Task.created_at)
    if sort_order == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())

    tasks = session.exec(statement).all()

    # Tag filtering (post-query since tags is JSON)
    if tag:
        tasks = [t for t in tasks if tag.lower() in [tg.lower() for tg in (t.tags or [])]]

    return list(tasks), len(tasks)


def update_task(
    session: Session,
    task_id: str,
    data: TaskUpdate,
) -> Task | None:
    """Partially update a task."""
    task = session.get(Task, task_id)
    if not task:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: str) -> bool:
    """Delete a task by ID."""
    task = session.get(Task, task_id)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True


def toggle_complete(session: Session, task_id: str) -> Task | None:
    """Toggle task completion status."""
    task = session.get(Task, task_id)
    if not task:
        return None

    if task.status == TaskStatus.COMPLETED:
        task.status = TaskStatus.PENDING
        task.completed_at = None
    else:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        # Handle recurrence when completing a recurring task
        if task.is_recurring and task.recurrence_rule:
            handle_recurrence_on_complete(session, task)

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
