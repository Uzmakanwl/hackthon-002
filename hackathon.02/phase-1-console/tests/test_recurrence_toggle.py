# tests/test_recurrence_toggle.py
import pytest
from datetime import datetime
from src.models import Task, Status, RecurrenceRule
from src.store import TaskStore
from src.commands import add_task, toggle_complete


class TestRecurrenceOnToggle:
    def setup_method(self):
        self.store = TaskStore()

    def test_completing_recurring_task_creates_clone(self):
        task = add_task(
            self.store,
            title="Daily standup",
            due_date="2025-06-15 09:00",
            is_recurring=True,
            recurrence_rule="daily",
        )
        original_count = self.store.count()
        toggle_complete(self.store, task.id)

        assert self.store.count() == original_count + 1

        all_tasks = self.store.get_all()
        clones = [t for t in all_tasks if t.id != task.id]
        assert len(clones) == 1

        clone = clones[0]
        assert clone.title == "Daily standup"
        assert clone.status == Status.PENDING
        assert clone.due_date == datetime(2025, 6, 16, 9, 0)

    def test_uncompleting_does_not_create_clone(self):
        task = add_task(
            self.store,
            title="Daily standup",
            due_date="2025-06-15 09:00",
            is_recurring=True,
            recurrence_rule="daily",
        )
        toggle_complete(self.store, task.id)  # complete -> creates clone
        count_after_complete = self.store.count()

        toggle_complete(self.store, task.id)  # uncomplete -> no new clone
        assert self.store.count() == count_after_complete

    def test_non_recurring_does_not_create_clone(self):
        task = add_task(self.store, title="One-off task")
        toggle_complete(self.store, task.id)
        assert self.store.count() == 1
