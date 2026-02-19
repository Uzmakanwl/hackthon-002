"""Event schemas for Dapr pub/sub message payloads."""

from enum import Enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Constants for task event types."""

    TASK_CREATED = "task.created"
    TASK_UPDATED = "task.updated"
    TASK_COMPLETED = "task.completed"
    TASK_DELETED = "task.deleted"
    REMINDER_DUE = "task.reminder.due"
    RECURRING_TRIGGERED = "task.recurring.triggered"


class TaskEvent(BaseModel):
    """Schema for a task lifecycle event published via Dapr pub/sub.

    Attributes:
        event_type: The type of event (e.g., EventType.TASK_CREATED).
        task_id: The string representation of the task UUID.
        timestamp: When the event occurred (defaults to now).
        payload: Additional event data (task fields, diff, etc.).
    """

    event_type: EventType
    task_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = {}
