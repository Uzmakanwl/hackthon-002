import pytest
from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule


class TestTaskModel:
    def test_task_creation_defaults(self):
        task = Task(title="Buy groceries")
        assert task.title == "Buy groceries"
        assert task.description == ""
        assert task.status == Status.PENDING
        assert task.priority == Priority.MEDIUM
        assert task.tags == []
        assert task.due_date is None
        assert task.reminder_at is None
        assert task.is_recurring is False
        assert task.recurrence_rule is None
        assert task.next_occurrence is None
        assert task.completed_at is None
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_creation_full(self):
        now = datetime.now()
        task = Task(
            title="Review PR",
            description="Check the auth module PR",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=["work", "urgent"],
            due_date=now,
            is_recurring=True,
            recurrence_rule=RecurrenceRule.WEEKLY,
        )
        assert task.title == "Review PR"
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]
        assert task.is_recurring is True
        assert task.recurrence_rule == RecurrenceRule.WEEKLY

    def test_task_id_is_unique(self):
        t1 = Task(title="Task 1")
        t2 = Task(title="Task 2")
        assert t1.id != t2.id

    def test_status_enum_values(self):
        assert Status.PENDING.value == "pending"
        assert Status.IN_PROGRESS.value == "in_progress"
        assert Status.COMPLETED.value == "completed"

    def test_priority_enum_values(self):
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"

    def test_recurrence_rule_enum_values(self):
        assert RecurrenceRule.DAILY.value == "daily"
        assert RecurrenceRule.WEEKLY.value == "weekly"
        assert RecurrenceRule.MONTHLY.value == "monthly"
        assert RecurrenceRule.YEARLY.value == "yearly"
