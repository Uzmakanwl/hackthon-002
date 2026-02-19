"""Tests for MCP tool plain functions and their integration with task services."""

import re

import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.mcp.server import (
    mcp_create_task,
    mcp_list_tasks,
    mcp_get_task,
    mcp_update_task,
    mcp_delete_task,
    mcp_complete_task,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def _extract_id(result: str) -> str:
    """Extract a full UUID from the MCP tool result string."""
    match = re.search(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        result,
    )
    return match.group(0) if match else ""


class TestMCPCreateTask:
    """Tests for the mcp_create_task plain function."""

    def test_create_basic(self, session):
        """Creating a task with only a title should succeed."""
        result = mcp_create_task(session, title="Buy groceries")
        assert "Buy groceries" in result
        assert "created" in result.lower()
        assert _extract_id(result), "Result should contain a UUID"

    def test_create_with_priority(self, session):
        """Creating a task with a specific priority should reflect it."""
        result = mcp_create_task(session, title="Urgent fix", priority="high")
        assert "Urgent fix" in result
        assert "high" in result.lower()

    def test_create_with_tags(self, session):
        """Creating a task with tags should persist them."""
        result = mcp_create_task(
            session, title="Tagged task", tags=["work", "dev"]
        )
        task_id = _extract_id(result)
        detail = mcp_get_task(session, task_id=task_id)
        assert "work" in detail
        assert "dev" in detail

    def test_create_with_recurrence(self, session):
        """Creating a recurring task should set is_recurring."""
        result = mcp_create_task(
            session, title="Daily standup", recurrence_rule="daily"
        )
        task_id = _extract_id(result)
        detail = mcp_get_task(session, task_id=task_id)
        assert "daily" in detail.lower()

    def test_create_with_description(self, session):
        """Creating a task with a description should persist it."""
        result = mcp_create_task(
            session, title="Write report", description="Q4 financial report"
        )
        task_id = _extract_id(result)
        detail = mcp_get_task(session, task_id=task_id)
        assert "Q4 financial report" in detail


class TestMCPListTasks:
    """Tests for the mcp_list_tasks plain function."""

    def test_list_empty(self, session):
        """Listing with no tasks should indicate nothing found."""
        result = mcp_list_tasks(session)
        assert "no tasks" in result.lower()

    def test_list_with_tasks(self, session):
        """Listing after creating tasks should show them all."""
        mcp_create_task(session, title="Task 1")
        mcp_create_task(session, title="Task 2")
        result = mcp_list_tasks(session)
        assert "Task 1" in result
        assert "Task 2" in result
        assert "2" in result  # total count

    def test_list_filter_by_priority(self, session):
        """Filtering by priority should only return matching tasks."""
        mcp_create_task(session, title="Low task", priority="low")
        mcp_create_task(session, title="High task", priority="high")
        result = mcp_list_tasks(session, priority="high")
        assert "High task" in result
        assert "Low task" not in result

    def test_list_filter_by_status(self, session):
        """Filtering by status should only return matching tasks."""
        create_result = mcp_create_task(session, title="Done task")
        task_id = _extract_id(create_result)
        mcp_complete_task(session, task_id=task_id)
        mcp_create_task(session, title="Pending task")

        result = mcp_list_tasks(session, status="completed")
        assert "Done task" in result
        assert "Pending task" not in result

    def test_list_search(self, session):
        """Searching by keyword should match title/description."""
        mcp_create_task(session, title="Buy groceries")
        mcp_create_task(session, title="Read a book")
        result = mcp_list_tasks(session, search="groceries")
        assert "Buy groceries" in result
        assert "Read a book" not in result

    def test_list_filter_by_tag(self, session):
        """Filtering by tag should only return tasks with that tag."""
        mcp_create_task(session, title="Work item", tags=["work"])
        mcp_create_task(session, title="Home item", tags=["home"])
        result = mcp_list_tasks(session, tag="work")
        assert "Work item" in result
        assert "Home item" not in result


class TestMCPGetTask:
    """Tests for the mcp_get_task plain function."""

    def test_get_existing(self, session):
        """Getting an existing task should return its details."""
        create_result = mcp_create_task(session, title="Test task")
        task_id = _extract_id(create_result)
        result = mcp_get_task(session, task_id=task_id)
        assert "Test task" in result
        assert task_id in result
        assert "pending" in result.lower()

    def test_get_nonexistent(self, session):
        """Getting a nonexistent task should return not found."""
        result = mcp_get_task(
            session, task_id="00000000-0000-0000-0000-000000000000"
        )
        assert "not found" in result.lower()

    def test_get_shows_all_fields(self, session):
        """Getting a task should display all key fields."""
        create_result = mcp_create_task(
            session,
            title="Detailed task",
            description="A thorough description",
            priority="high",
            tags=["urgent", "work"],
        )
        task_id = _extract_id(create_result)
        result = mcp_get_task(session, task_id=task_id)
        assert "Detailed task" in result
        assert "A thorough description" in result
        assert "high" in result.lower()
        assert "urgent" in result
        assert "work" in result


class TestMCPUpdateTask:
    """Tests for the mcp_update_task plain function."""

    def test_update_title(self, session):
        """Updating a task's title should reflect in the result."""
        create_result = mcp_create_task(session, title="Original")
        task_id = _extract_id(create_result)
        result = mcp_update_task(session, task_id=task_id, title="Updated")
        assert "Updated" in result
        assert "updated" in result.lower()

    def test_update_priority(self, session):
        """Updating a task's priority should reflect in the result."""
        create_result = mcp_create_task(session, title="Change prio")
        task_id = _extract_id(create_result)
        result = mcp_update_task(session, task_id=task_id, priority="high")
        assert "high" in result.lower()

    def test_update_status(self, session):
        """Updating a task's status via update_task should work."""
        create_result = mcp_create_task(session, title="Status task")
        task_id = _extract_id(create_result)
        result = mcp_update_task(
            session, task_id=task_id, status="in_progress"
        )
        assert "in_progress" in result.lower()

    def test_update_nonexistent(self, session):
        """Updating a nonexistent task should return not found."""
        result = mcp_update_task(
            session,
            task_id="00000000-0000-0000-0000-000000000000",
            title="X",
        )
        assert "not found" in result.lower()


class TestMCPDeleteTask:
    """Tests for the mcp_delete_task plain function."""

    def test_delete_existing(self, session):
        """Deleting an existing task should confirm deletion."""
        create_result = mcp_create_task(session, title="Delete me")
        task_id = _extract_id(create_result)
        result = mcp_delete_task(session, task_id=task_id)
        assert "deleted" in result.lower()

    def test_delete_confirms_gone(self, session):
        """After deletion, the task should not be retrievable."""
        create_result = mcp_create_task(session, title="Delete me")
        task_id = _extract_id(create_result)
        mcp_delete_task(session, task_id=task_id)
        result = mcp_get_task(session, task_id=task_id)
        assert "not found" in result.lower()

    def test_delete_nonexistent(self, session):
        """Deleting a nonexistent task should return not found."""
        result = mcp_delete_task(
            session, task_id="00000000-0000-0000-0000-000000000000"
        )
        assert "not found" in result.lower()


class TestMCPCompleteTask:
    """Tests for the mcp_complete_task plain function."""

    def test_complete_pending_task(self, session):
        """Completing a pending task should mark it as completed."""
        create_result = mcp_create_task(session, title="Complete me")
        task_id = _extract_id(create_result)
        result = mcp_complete_task(session, task_id=task_id)
        assert "completed" in result.lower()

    def test_toggle_back_to_pending(self, session):
        """Toggling a completed task should revert to pending."""
        create_result = mcp_create_task(session, title="Toggle back")
        task_id = _extract_id(create_result)
        mcp_complete_task(session, task_id=task_id)
        result = mcp_complete_task(session, task_id=task_id)
        assert "pending" in result.lower()

    def test_complete_nonexistent(self, session):
        """Completing a nonexistent task should return not found."""
        result = mcp_complete_task(
            session, task_id="00000000-0000-0000-0000-000000000000"
        )
        assert "not found" in result.lower()

    def test_complete_recurring_creates_next(self, session):
        """Completing a recurring task should auto-create the next occurrence."""
        create_result = mcp_create_task(
            session,
            title="Daily standup",
            recurrence_rule="daily",
            due_date="2026-03-01T09:00:00",
        )
        task_id = _extract_id(create_result)
        mcp_complete_task(session, task_id=task_id)
        # List all tasks -- should now have 2 (original completed + new clone)
        result = mcp_list_tasks(session)
        assert "2" in result  # total count includes both
        assert "Daily standup" in result
