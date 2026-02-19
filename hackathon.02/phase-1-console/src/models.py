"""Task model and enums for the Todo console app."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Status(Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Priority(Enum):
    """Task priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceRule(Enum):
    """Supported recurrence frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Task:
    """Represents a single todo task."""
    title: str
    description: str = ""
    status: Status = Status.PENDING
    priority: Priority = Priority.MEDIUM
    tags: list[str] = field(default_factory=list)
    due_date: datetime | None = None
    reminder_at: datetime | None = None
    is_recurring: bool = False
    recurrence_rule: RecurrenceRule | None = None
    next_occurrence: datetime | None = None
    completed_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
