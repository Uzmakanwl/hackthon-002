# tests/test_recurrence.py
import pytest
from datetime import datetime, timedelta
from src.models import Task, Status, Priority, RecurrenceRule
from src.recurrence import calculate_next_occurrence, create_recurring_clone


class TestCalculateNextOccurrence:
    def test_daily(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.DAILY)
        assert next_date == datetime(2025, 6, 16, 10, 0)

    def test_weekly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.WEEKLY)
        assert next_date == datetime(2025, 6, 22, 10, 0)

    def test_monthly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.MONTHLY)
        assert next_date == datetime(2025, 7, 15, 10, 0)

    def test_yearly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.YEARLY)
        assert next_date == datetime(2026, 6, 15, 10, 0)

    def test_monthly_end_of_month(self):
        due = datetime(2025, 1, 31, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.MONTHLY)
        assert next_date.month == 2
        assert next_date.day == 28  # Feb 2025 has 28 days

    def test_no_due_date_uses_now(self):
        next_date = calculate_next_occurrence(None, RecurrenceRule.DAILY)
        assert next_date is not None
        assert next_date > datetime.now()


class TestCreateRecurringClone:
    def test_clone_basic(self):
        original = Task(
            title="Daily standup",
            description="Team sync",
            priority=Priority.HIGH,
            tags=["work"],
            due_date=datetime(2025, 6, 15, 9, 0),
            is_recurring=True,
            recurrence_rule=RecurrenceRule.DAILY,
        )
        clone = create_recurring_clone(original)
        assert clone.id != original.id
        assert clone.title == original.title
        assert clone.description == original.description
        assert clone.priority == original.priority
        assert clone.tags == original.tags
        assert clone.is_recurring is True
        assert clone.recurrence_rule == RecurrenceRule.DAILY
        assert clone.status == Status.PENDING
        assert clone.completed_at is None
        assert clone.due_date == datetime(2025, 6, 16, 9, 0)

    def test_clone_not_recurring_raises(self):
        task = Task(title="Not recurring", is_recurring=False)
        with pytest.raises(ValueError, match="not a recurring task"):
            create_recurring_clone(task)

    def test_clone_preserves_tags(self):
        original = Task(
            title="Weekly review",
            tags=["work", "planning"],
            due_date=datetime(2025, 6, 15),
            is_recurring=True,
            recurrence_rule=RecurrenceRule.WEEKLY,
        )
        clone = create_recurring_clone(original)
        assert clone.tags == ["work", "planning"]
        # Verify it's a copy, not a reference
        clone.tags.append("modified")
        assert "modified" not in original.tags
