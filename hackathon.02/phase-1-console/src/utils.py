"""Validators, formatters, and input parsers for the CLI."""

from datetime import datetime
from src.models import Task, Status, Priority


def validate_title(title: str) -> str:
    """Validate and clean a task title."""
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")
    if len(title) > 200:
        raise ValueError("Title cannot exceed 200 characters")
    return title


def validate_priority_input(value: str) -> Priority:
    """Parse a priority string into a Priority enum."""
    try:
        return Priority(value.strip().lower())
    except ValueError:
        valid = ", ".join(p.value for p in Priority)
        raise ValueError(f"Invalid priority: '{value}'. Choose from: {valid}")


def validate_status_input(value: str) -> Status:
    """Parse a status string into a Status enum."""
    try:
        return Status(value.strip().lower())
    except ValueError:
        valid = ", ".join(s.value for s in Status)
        raise ValueError(f"Invalid status: '{value}'. Choose from: {valid}")


def parse_date_input(value: str) -> datetime | None:
    """Parse a date string. Supports 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM'. Returns None for empty."""
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{value}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")


def parse_tags_input(value: str) -> list[str]:
    """Parse comma-separated tags into a deduplicated list."""
    value = value.strip()
    if not value:
        return []
    seen: set[str] = set()
    tags: list[str] = []
    for tag in value.split(","):
        tag = tag.strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def format_task_summary(task: Task) -> str:
    """Format a single-line summary of a task for list views."""
    status_icon = {"pending": "○", "in_progress": "◑", "completed": "●"}
    icon = status_icon.get(task.status.value, "?")
    due = f" | Due: {task.due_date.strftime('%Y-%m-%d')}" if task.due_date else ""
    return f"  {icon} [{task.priority.value.upper()}] [{task.status.value}] {task.title}{due}  (ID: {task.id[:8]})"


def format_task_detail(task: Task) -> str:
    """Format a full detail view of a task."""
    lines = [
        f"{'=' * 50}",
        f"  Title:       {task.title}",
        f"  ID:          {task.id}",
        f"  Status:      {task.status.value}",
        f"  Priority:    {task.priority.value}",
        f"  Description: {task.description or '(none)'}",
        f"  Tags:        {', '.join(task.tags) if task.tags else '(none)'}",
        f"  Due Date:    {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '(none)'}",
        f"  Reminder:    {task.reminder_at.strftime('%Y-%m-%d %H:%M') if task.reminder_at else '(none)'}",
        f"  Recurring:   {task.recurrence_rule.value if task.is_recurring and task.recurrence_rule else 'No'}",
        f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M')}",
        f"  Completed:   {task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else '(none)'}",
        f"{'=' * 50}",
    ]
    return "\n".join(lines)
