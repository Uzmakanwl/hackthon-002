"""Business logic for task CRUD operations, filtering, sorting, and search."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Task, TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate
from app.services.recurrence_service import handle_recurrence_on_complete


def create_task(session: Session, data: TaskCreate) -> Task:
    """Create a new task and persist to DB.

    Args:
        session: The database session.
        data: Validated task creation data.

    Returns:
        The newly created Task instance.
    """
    task = Task(**data.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: str) -> Task | None:
    """Retrieve a single task by its ID.

    Args:
        session: The database session.
        task_id: The string UUID of the task.

    Returns:
        The Task if found, otherwise None.
    """
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
    """List tasks with optional filtering, searching, and sorting.

    Args:
        session: The database session.
        status: Filter by task status.
        priority: Filter by task priority.
        search: Keyword search in title and description.
        tag: Filter by tag name.
        sort_by: Field name to sort by.
        sort_order: Sort direction ('asc' or 'desc').

    Returns:
        A tuple of (tasks list, total count).
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
    """Partially update an existing task.

    Args:
        session: The database session.
        task_id: The string UUID of the task to update.
        data: Validated partial update data.

    Returns:
        The updated Task if found, otherwise None.
    """
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
    """Delete a task by its ID.

    Args:
        session: The database session.
        task_id: The string UUID of the task to delete.

    Returns:
        True if the task was deleted, False if not found.
    """
    task = session.get(Task, task_id)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True


def toggle_complete(session: Session, task_id: str) -> Task | None:
    """Toggle the completion status of a task.

    When completing a recurring task, auto-creates the next occurrence.

    Args:
        session: The database session.
        task_id: The string UUID of the task to toggle.

    Returns:
        The updated Task if found, otherwise None.
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
        # Auto-create next occurrence for recurring tasks
        if task.is_recurring and task.recurrence_rule:
            handle_recurrence_on_complete(session, task)

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
