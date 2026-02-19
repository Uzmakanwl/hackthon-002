import pytest
from src.models import Task, Status, Priority
from src.store import TaskStore


class TestTaskStore:
    def setup_method(self):
        self.store = TaskStore()

    def test_add_and_get(self):
        task = Task(title="Test task")
        self.store.add(task)
        retrieved = self.store.get(task.id)
        assert retrieved is not None
        assert retrieved.title == "Test task"

    def test_get_nonexistent_returns_none(self):
        assert self.store.get("nonexistent-id") is None

    def test_get_all_empty(self):
        assert self.store.get_all() == []

    def test_get_all_returns_all(self):
        t1 = Task(title="Task 1")
        t2 = Task(title="Task 2")
        self.store.add(t1)
        self.store.add(t2)
        all_tasks = self.store.get_all()
        assert len(all_tasks) == 2

    def test_delete_existing(self):
        task = Task(title="To delete")
        self.store.add(task)
        result = self.store.delete(task.id)
        assert result is True
        assert self.store.get(task.id) is None

    def test_delete_nonexistent(self):
        result = self.store.delete("nonexistent-id")
        assert result is False

    def test_update_existing(self):
        task = Task(title="Original")
        self.store.add(task)
        task.title = "Updated"
        self.store.update(task)
        retrieved = self.store.get(task.id)
        assert retrieved.title == "Updated"

    def test_update_nonexistent_returns_false(self):
        task = Task(title="Ghost")
        result = self.store.update(task)
        assert result is False

    def test_count(self):
        self.store.add(Task(title="One"))
        self.store.add(Task(title="Two"))
        assert self.store.count() == 2
