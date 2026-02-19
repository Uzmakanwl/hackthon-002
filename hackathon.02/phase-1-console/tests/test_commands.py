# tests/test_commands.py
import pytest
from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule
from src.store import TaskStore
from src.commands import (
    add_task,
    view_all_tasks,
    view_task_detail,
    update_task,
    delete_task,
    toggle_complete,
)


class TestAddTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_add_basic_task(self):
        task = add_task(self.store, title="Buy groceries")
        assert task.title == "Buy groceries"
        assert self.store.count() == 1

    def test_add_task_with_all_fields(self):
        task = add_task(
            self.store,
            title="Review PR",
            description="Auth module changes",
            priority="high",
            tags="work, urgent",
            due_date="2025-12-25 10:00",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]
        assert task.due_date is not None
        assert task.is_recurring is True

    def test_add_task_empty_title_raises(self):
        with pytest.raises(ValueError):
            add_task(self.store, title="")


class TestDeleteTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_delete_existing(self):
        task = add_task(self.store, title="To delete")
        result = delete_task(self.store, task.id)
        assert result is True
        assert self.store.count() == 0

    def test_delete_nonexistent(self):
        result = delete_task(self.store, "fake-id")
        assert result is False


class TestUpdateTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_update_title(self):
        task = add_task(self.store, title="Original")
        updated = update_task(self.store, task.id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_priority(self):
        task = add_task(self.store, title="Test")
        updated = update_task(self.store, task.id, priority="high")
        assert updated.priority == Priority.HIGH

    def test_update_nonexistent_returns_none(self):
        result = update_task(self.store, "fake-id", title="Nope")
        assert result is None


class TestViewTasks:
    def setup_method(self):
        self.store = TaskStore()

    def test_view_all_empty(self):
        tasks = view_all_tasks(self.store)
        assert tasks == []

    def test_view_all_with_tasks(self):
        add_task(self.store, title="Task 1")
        add_task(self.store, title="Task 2")
        tasks = view_all_tasks(self.store)
        assert len(tasks) == 2

    def test_view_detail(self):
        task = add_task(self.store, title="Detailed task")
        detail = view_task_detail(self.store, task.id)
        assert detail is not None
        assert detail.title == "Detailed task"

    def test_view_detail_nonexistent(self):
        assert view_task_detail(self.store, "fake-id") is None


class TestToggleComplete:
    def setup_method(self):
        self.store = TaskStore()

    def test_toggle_to_completed(self):
        task = add_task(self.store, title="Toggle me")
        toggled = toggle_complete(self.store, task.id)
        assert toggled.status == Status.COMPLETED
        assert toggled.completed_at is not None

    def test_toggle_back_to_pending(self):
        task = add_task(self.store, title="Toggle me")
        toggle_complete(self.store, task.id)
        toggled = toggle_complete(self.store, task.id)
        assert toggled.status == Status.PENDING
        assert toggled.completed_at is None

    def test_toggle_nonexistent_returns_none(self):
        result = toggle_complete(self.store, "fake-id")
        assert result is None
