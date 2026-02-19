"""Service layer for recurring task logic.

In Phase 5, recurrence is also handled as an event consumer that listens
to task.completed events and auto-creates the next occurrence.
"""

from datetime import datetime, timedelta
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from app.models import Task, TaskStatus


def calculate_next_occurrence(
    current_date: datetime,
    recurrence_rule: str,
) -> Optional[datetime]:
    """Calculate the next occurrence date based on a recurrence rule.

    Supports: daily, weekly, monthly, yearly.
    Returns the next datetime, or None if the rule is unrecognized.
    """
    base = current_date or datetime.utcnow()
    match recurrence_rule:
        case "daily":
            return base + timedelta(days=1)
        case "weekly":
            return base + timedelta(weeks=1)
        case "monthly":
            return base + relativedelta(months=1)
        case "yearly":
            return base + relativedelta(years=1)
        case _:
            return None


def handle_recurrence_on_complete(
    session: Session, task: Task
) -> Optional[Task]:
    """Handle recurrence when a recurring task is marked as complete.

    If the task is recurring, create a clone with the next due date.
    Returns the newly created task, or None if the task is not recurring.
    """
    if not task.is_recurring or not task.recurrence_rule:
        return None

    base_date = task.due_date or datetime.utcnow()
    next_due = calculate_next_occurrence(base_date, task.recurrence_rule)
    if next_due is None:
        return None

    clone = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags) if task.tags else [],
        due_date=next_due,
        is_recurring=True,
        recurrence_rule=task.recurrence_rule,
        status=TaskStatus.PENDING,
    )
    session.add(clone)
    session.commit()
    session.refresh(clone)
    return clone
