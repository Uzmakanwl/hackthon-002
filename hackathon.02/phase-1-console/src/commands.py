# src/commands.py
"""Command handlers for CRUD operations, search, filter, and sort."""

from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule
from src.store import TaskStore
from src.utils import (
    validate_title,
    validate_priority_input,
    validate_status_input,
    parse_date_input,
    parse_tags_input,
)


def add_task(
    store: TaskStore,
    *,
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: str = "",
    due_date: str = "",
    reminder_at: str = "",
    is_recurring: bool = False,
    recurrence_rule: str = "",
) -> Task:
    """Create and store a new task.

    Args:
        store: The task store.
        title: Task title (required).
        description: Optional description.
        priority: Priority string ('low', 'medium', 'high').
        tags: Comma-separated tag string.
        due_date: Date string 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'.
        reminder_at: Reminder date string.
        is_recurring: Whether the task recurs.
        recurrence_rule: Recurrence frequency string.

    Returns:
        The created Task.

    Raises:
        ValueError: If title is empty or inputs are invalid.
    """
    clean_title = validate_title(title)
    parsed_priority = validate_priority_input(priority)
    parsed_tags = parse_tags_input(tags)
    parsed_due = parse_date_input(due_date)
    parsed_reminder = parse_date_input(reminder_at)
    parsed_rule = RecurrenceRule(recurrence_rule) if recurrence_rule else None

    task = Task(
        title=clean_title,
        description=description.strip(),
        priority=parsed_priority,
        tags=parsed_tags,
        due_date=parsed_due,
        reminder_at=parsed_reminder,
        is_recurring=is_recurring,
        recurrence_rule=parsed_rule,
    )
    store.add(task)
    return task


def view_all_tasks(store: TaskStore) -> list[Task]:
    """Return all tasks from the store."""
    return store.get_all()


def view_task_detail(store: TaskStore, task_id: str) -> Task | None:
    """Return a single task by ID, or None if not found."""
    return store.get(task_id)


def update_task(
    store: TaskStore,
    task_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    tags: str | None = None,
    due_date: str | None = None,
    reminder_at: str | None = None,
    status: str | None = None,
) -> Task | None:
    """Partially update a task's fields.

    Only non-None arguments are applied.
    Returns the updated Task, or None if not found.
    """
    task = store.get(task_id)
    if task is None:
        return None

    if title is not None:
        task.title = validate_title(title)
    if description is not None:
        task.description = description.strip()
    if priority is not None:
        task.priority = validate_priority_input(priority)
    if tags is not None:
        task.tags = parse_tags_input(tags)
    if due_date is not None:
        task.due_date = parse_date_input(due_date)
    if reminder_at is not None:
        task.reminder_at = parse_date_input(reminder_at)
    if status is not None:
        task.status = validate_status_input(status)

    store.update(task)
    return task


def delete_task(store: TaskStore, task_id: str) -> bool:
    """Delete a task by ID. Returns True if deleted, False if not found."""
    return store.delete(task_id)


def toggle_complete(store: TaskStore, task_id: str) -> Task | None:
    """Toggle a task between pending and completed.

    If the task is recurring and being completed, auto-creates
    the next occurrence.

    Returns the updated Task, or None if not found.
    """
    from src.recurrence import create_recurring_clone

    task = store.get(task_id)
    if task is None:
        return None

    if task.status == Status.COMPLETED:
        task.status = Status.PENDING
        task.completed_at = None
    else:
        task.status = Status.COMPLETED
        task.completed_at = datetime.now()

        # Auto-create next occurrence for recurring tasks
        if task.is_recurring and task.recurrence_rule:
            clone = create_recurring_clone(task)
            store.add(clone)

    store.update(task)
    return task


def search_tasks(store: TaskStore, *, keyword: str) -> list[Task]:
    """Search tasks by keyword in title and description (case-insensitive).

    Returns all tasks if keyword is empty.
    """
    if not keyword.strip():
        return store.get_all()
    keyword_lower = keyword.strip().lower()
    return [
        task for task in store.get_all()
        if keyword_lower in task.title.lower()
        or keyword_lower in task.description.lower()
    ]


def filter_tasks(
    store: TaskStore,
    *,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    due_before: str | None = None,
    due_after: str | None = None,
) -> list[Task]:
    """Filter tasks by status, priority, tag, and/or date range.

    All filters are AND-combined. Returns all tasks if no filters provided.
    """
    tasks = store.get_all()

    if status:
        parsed_status = validate_status_input(status)
        tasks = [t for t in tasks if t.status == parsed_status]

    if priority:
        parsed_priority = validate_priority_input(priority)
        tasks = [t for t in tasks if t.priority == parsed_priority]

    if tag:
        tag_lower = tag.strip().lower()
        tasks = [t for t in tasks if tag_lower in [tg.lower() for tg in t.tags]]

    if due_before:
        cutoff = parse_date_input(due_before)
        tasks = [t for t in tasks if t.due_date and t.due_date <= cutoff]

    if due_after:
        cutoff = parse_date_input(due_after)
        tasks = [t for t in tasks if t.due_date and t.due_date >= cutoff]

    return tasks


def sort_tasks(
    tasks: list[Task],
    *,
    sort_by: str = "created_at",
    descending: bool = False,
) -> list[Task]:
    """Sort a list of tasks by the given field.

    Supported sort_by values: 'title', 'priority', 'created_at', 'due_date', 'status'.
    None values (e.g., no due_date) sort last.
    """
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    max_date = datetime.max

    def sort_key(task: Task):
        if sort_by == "title":
            return task.title.lower()
        elif sort_by == "priority":
            return priority_order.get(task.priority, 99)
        elif sort_by == "due_date":
            return task.due_date or max_date
        elif sort_by == "status":
            return task.status.value
        else:  # created_at default
            return task.created_at

    return sorted(tasks, key=sort_key, reverse=descending)
