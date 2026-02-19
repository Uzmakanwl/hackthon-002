# src/recurrence.py
"""Recurrence logic for auto-scheduling recurring tasks."""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.models import Task, Status, RecurrenceRule


def calculate_next_occurrence(
    current_due: datetime | None,
    rule: RecurrenceRule,
) -> datetime:
    """Calculate the next occurrence based on a recurrence rule.

    Args:
        current_due: The current due date. Uses now() if None.
        rule: The recurrence frequency.

    Returns:
        The next due datetime.
    """
    base = current_due or datetime.now()

    if rule == RecurrenceRule.DAILY:
        return base + timedelta(days=1)
    elif rule == RecurrenceRule.WEEKLY:
        return base + timedelta(weeks=1)
    elif rule == RecurrenceRule.MONTHLY:
        return base + relativedelta(months=1)
    elif rule == RecurrenceRule.YEARLY:
        return base + relativedelta(years=1)
    else:
        raise ValueError(f"Unsupported recurrence rule: {rule}")


def create_recurring_clone(task: Task) -> Task:
    """Create a new pending task from a completed recurring task.

    The clone inherits all properties except:
    - Gets a new UUID
    - Status reset to PENDING
    - completed_at set to None
    - due_date advanced to next occurrence
    - Fresh created_at and updated_at timestamps

    Args:
        task: The completed recurring task to clone.

    Returns:
        A new Task with the next due date.

    Raises:
        ValueError: If the task is not recurring.
    """
    if not task.is_recurring or not task.recurrence_rule:
        raise ValueError(f"Task '{task.title}' is not a recurring task")

    next_due = calculate_next_occurrence(task.due_date, task.recurrence_rule)

    return Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags),  # copy to avoid shared reference
        due_date=next_due,
        reminder_at=None,
        is_recurring=True,
        recurrence_rule=task.recurrence_rule,
    )
