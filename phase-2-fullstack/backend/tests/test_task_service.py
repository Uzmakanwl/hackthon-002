# tests/test_task_service.py
import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.models import Task, TaskStatus, TaskPriority
from app.services.task_service import (
    create_task, get_task, list_tasks, update_task, delete_task, toggle_complete,
)
from app.schemas import TaskCreate, TaskUpdate


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestCreateTask:
    def test_create_basic(self, session):
        data = TaskCreate(title="Buy groceries")
        task = create_task(session, data)
        assert task.title == "Buy groceries"
        assert task.status == TaskStatus.PENDING

    def test_create_with_all_fields(self, session):
        data = TaskCreate(
            title="Review PR",
            description="Auth module",
            priority=TaskPriority.HIGH,
            tags=["work"],
        )
        task = create_task(session, data)
        assert task.priority == TaskPriority.HIGH
        assert task.tags == ["work"]


class TestGetTask:
    def test_get_existing(self, session):
        data = TaskCreate(title="Test")
        created = create_task(session, data)
        task = get_task(session, created.id)
        assert task is not None
        assert task.title == "Test"

    def test_get_nonexistent_returns_none(self, session):
        assert get_task(session, "fake-id") is None


class TestListTasks:
    def test_list_empty(self, session):
        tasks, total = list_tasks(session)
        assert tasks == []
        assert total == 0

    def test_list_with_tasks(self, session):
        create_task(session, TaskCreate(title="Task 1"))
        create_task(session, TaskCreate(title="Task 2"))
        tasks, total = list_tasks(session)
        assert total == 2

    def test_filter_by_status(self, session):
        create_task(session, TaskCreate(title="Pending"))
        t = create_task(session, TaskCreate(title="Done"))
        toggle_complete(session, t.id)
        tasks, total = list_tasks(session, status=TaskStatus.COMPLETED)
        assert total == 1
        assert tasks[0].title == "Done"

    def test_filter_by_priority(self, session):
        create_task(session, TaskCreate(title="High", priority=TaskPriority.HIGH))
        create_task(session, TaskCreate(title="Low", priority=TaskPriority.LOW))
        tasks, total = list_tasks(session, priority=TaskPriority.HIGH)
        assert total == 1

    def test_search_by_keyword(self, session):
        create_task(session, TaskCreate(title="Buy groceries"))
        create_task(session, TaskCreate(title="Review PR"))
        tasks, total = list_tasks(session, search="groceries")
        assert total == 1

    def test_sort_by_title(self, session):
        create_task(session, TaskCreate(title="Charlie"))
        create_task(session, TaskCreate(title="Alpha"))
        tasks, _ = list_tasks(session, sort_by="title", sort_order="asc")
        assert tasks[0].title == "Alpha"


class TestUpdateTask:
    def test_update_title(self, session):
        t = create_task(session, TaskCreate(title="Original"))
        updated = update_task(session, t.id, TaskUpdate(title="Updated"))
        assert updated.title == "Updated"

    def test_update_nonexistent_returns_none(self, session):
        assert update_task(session, "fake-id", TaskUpdate(title="X")) is None


class TestDeleteTask:
    def test_delete_existing(self, session):
        t = create_task(session, TaskCreate(title="Delete me"))
        assert delete_task(session, t.id) is True
        assert get_task(session, t.id) is None

    def test_delete_nonexistent(self, session):
        assert delete_task(session, "fake-id") is False


class TestToggleComplete:
    def test_toggle_to_completed(self, session):
        t = create_task(session, TaskCreate(title="Toggle"))
        toggled = toggle_complete(session, t.id)
        assert toggled.status == TaskStatus.COMPLETED
        assert toggled.completed_at is not None

    def test_toggle_back_to_pending(self, session):
        t = create_task(session, TaskCreate(title="Toggle"))
        toggle_complete(session, t.id)
        toggled = toggle_complete(session, t.id)
        assert toggled.status == TaskStatus.PENDING
