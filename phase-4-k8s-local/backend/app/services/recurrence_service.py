# app/services/recurrence_service.py
"""Recurrence logic for auto-scheduling recurring tasks."""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from app.models import Task, TaskStatus


def calculate_next_occurrence(current_due: datetime | None, rule: str) -> datetime:
    """Calculate the next due date from a recurrence rule."""
    base = current_due or datetime.utcnow()
    match rule:
        case "daily":
            return base + timedelta(days=1)
        case "weekly":
            return base + timedelta(weeks=1)
        case "monthly":
            return base + relativedelta(months=1)
        case "yearly":
            return base + relativedelta(years=1)
        case _:
            raise ValueError(f"Unsupported recurrence rule: {rule}")


def handle_recurrence_on_complete(session: Session, task: Task) -> Task | None:
    """If task is recurring, create the next occurrence."""
    if not task.is_recurring or not task.recurrence_rule:
        return None

    next_due = calculate_next_occurrence(task.due_date, task.recurrence_rule)
    clone = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags) if task.tags else [],
        due_date=next_due,
        is_recurring=True,
        recurrence_rule=task.recurrence_rule,
    )
    session.add(clone)
    session.commit()
    session.refresh(clone)
    return clone
