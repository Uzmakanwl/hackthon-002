"""Integration tests for the Task CRUD API endpoints."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import get_session


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


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a test client with overridden DB session."""

    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_returns_200(self, client):
        """Health check should return 200 with status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestCreateTask:
    """Tests for POST /api/tasks."""

    def test_create_task_with_required_fields(self, client):
        """Creating a task with only a title should succeed with defaults."""
        response = client.post("/api/tasks", json={"title": "Buy groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["status"] == "pending"
        assert data["priority"] == "medium"
        assert data["id"] is not None

    def test_create_task_with_all_fields(self, client):
        """Creating a task with all optional fields should succeed."""
        response = client.post("/api/tasks", json={
            "title": "Review PRs",
            "description": "Check open pull requests",
            "priority": "high",
            "tags": ["work", "dev"],
            "due_date": "2026-03-01T10:00:00",
            "is_recurring": True,
            "recurrence_rule": "weekly",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Review PRs"
        assert data["description"] == "Check open pull requests"
        assert data["priority"] == "high"
        assert data["tags"] == ["work", "dev"]
        assert data["is_recurring"] is True
        assert data["recurrence_rule"] == "weekly"

    def test_create_task_missing_title(self, client):
        """Creating a task without a title should return 422."""
        response = client.post("/api/tasks", json={})
        assert response.status_code == 422

    def test_create_task_empty_title(self, client):
        """Creating a task with an empty title should return 422."""
        response = client.post("/api/tasks", json={"title": ""})
        assert response.status_code == 422


class TestListTasks:
    """Tests for GET /api/tasks."""

    def test_list_tasks_empty(self, client):
        """Listing tasks when none exist should return empty list."""
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0

    def test_list_tasks_with_tasks(self, client):
        """Listing tasks should return all created tasks."""
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2

    def test_filter_by_status(self, client):
        """Filtering by status should return only matching tasks."""
        client.post("/api/tasks", json={"title": "Pending task"})
        resp2 = client.post("/api/tasks", json={"title": "Done task"})
        task_id = resp2.json()["id"]
        client.post(f"/api/tasks/{task_id}/complete")
        response = client.get("/api/tasks?status=completed")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Done task"

    def test_filter_by_priority(self, client):
        """Filtering by priority should return only matching tasks."""
        client.post("/api/tasks", json={"title": "Low", "priority": "low"})
        client.post("/api/tasks", json={"title": "High", "priority": "high"})
        response = client.get("/api/tasks?priority=high")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "High"

    def test_search_by_keyword(self, client):
        """Searching by keyword should match title and description."""
        client.post("/api/tasks", json={"title": "Buy groceries"})
        client.post("/api/tasks", json={"title": "Read a book"})
        response = client.get("/api/tasks?search=groceries")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Buy groceries"


class TestGetTask:
    """Tests for GET /api/tasks/{id}."""

    def test_get_existing_task(self, client):
        """Getting an existing task by ID should return the task."""
        create_resp = client.post("/api/tasks", json={"title": "Test task"})
        task_id = create_resp.json()["id"]
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test task"

    def test_get_nonexistent_task(self, client):
        """Getting a task with an unknown ID should return 404."""
        response = client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestUpdateTask:
    """Tests for PATCH /api/tasks/{id}."""

    def test_patch_title(self, client):
        """Updating only the title should leave other fields unchanged."""
        resp = client.post("/api/tasks", json={"title": "Original", "priority": "low"})
        task_id = resp.json()["id"]
        response = client.patch(f"/api/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == "low"

    def test_patch_nonexistent_task(self, client):
        """Updating a nonexistent task should return 404."""
        response = client.patch(
            "/api/tasks/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert response.status_code == 404


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{id}."""

    def test_delete_existing_task(self, client):
        """Deleting an existing task should return 204."""
        resp = client.post("/api/tasks", json={"title": "Delete me"})
        task_id = resp.json()["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

    def test_delete_confirms_gone(self, client):
        """After deletion, the task should no longer be retrievable."""
        resp = client.post("/api/tasks", json={"title": "Delete me"})
        task_id = resp.json()["id"]
        client.delete(f"/api/tasks/{task_id}")
        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_task(self, client):
        """Deleting a nonexistent task should return 404."""
        response = client.delete("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestToggleComplete:
    """Tests for POST /api/tasks/{id}/complete."""

    def test_complete_pending_task(self, client):
        """Completing a pending task should set status to completed."""
        resp = client.post("/api/tasks", json={"title": "Toggle"})
        task_id = resp.json()["id"]
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_uncomplete_completed_task(self, client):
        """Toggling a completed task should revert to pending."""
        resp = client.post("/api/tasks", json={"title": "Toggle back"})
        task_id = resp.json()["id"]
        client.post(f"/api/tasks/{task_id}/complete")
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["completed_at"] is None

    def test_toggle_nonexistent_task(self, client):
        """Toggling a nonexistent task should return 404."""
        response = client.post(
            "/api/tasks/00000000-0000-0000-0000-000000000000/complete"
        )
        assert response.status_code == 404
