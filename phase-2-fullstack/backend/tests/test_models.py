# tests/test_models.py
import pytest
from datetime import datetime
from app.models import Task, TaskStatus, TaskPriority


class TestTaskModel:
    def test_task_creation_defaults(self):
        task = Task(title="Test task")
        assert task.title == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.is_recurring is False

    def test_task_status_enum(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"

    def test_task_priority_enum(self):
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
