# tests/test_tasks_api.py
"""Integration tests for the Task API endpoints."""

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

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "todo-backend"


class TestCreateTask:
    """Tests for POST /api/tasks."""

    def test_create_task(self, client):
        response = client.post("/api/tasks", json={"title": "Buy groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["status"] == "pending"

    def test_create_task_with_all_fields(self, client):
        response = client.post("/api/tasks", json={
            "title": "Review PRs",
            "description": "Check open pull requests",
            "priority": "high",
            "tags": ["work", "dev"],
            "due_date": "2026-03-01T10:00:00",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Review PRs"
        assert data["priority"] == "high"
        assert data["tags"] == ["work", "dev"]

    def test_create_task_missing_title(self, client):
        response = client.post("/api/tasks", json={})
        assert response.status_code == 422


class TestGetTasks:
    """Tests for GET /api/tasks."""

    def test_list_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0

    def test_list_with_tasks(self, client):
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        response = client.get("/api/tasks")
        assert response.json()["total"] == 2

    def test_get_single_task(self, client):
        create_resp = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_resp.json()["id"]
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test"

    def test_get_nonexistent_404(self, client):
        response = client.get("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_filter_by_status(self, client):
        client.post("/api/tasks", json={"title": "Pending task"})
        resp2 = client.post("/api/tasks", json={"title": "Done task"})
        task_id = resp2.json()["id"]
        client.post(f"/api/tasks/{task_id}/complete")
        response = client.get("/api/tasks?status=completed")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Done task"

    def test_filter_by_priority(self, client):
        client.post("/api/tasks", json={"title": "Low", "priority": "low"})
        client.post("/api/tasks", json={"title": "High", "priority": "high"})
        response = client.get("/api/tasks?priority=high")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "High"

    def test_search_by_keyword(self, client):
        client.post("/api/tasks", json={"title": "Buy groceries"})
        client.post("/api/tasks", json={"title": "Read a book"})
        response = client.get("/api/tasks?search=groceries")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Buy groceries"

    def test_filter_by_tag(self, client):
        client.post("/api/tasks", json={"title": "Work task", "tags": ["work"]})
        client.post("/api/tasks", json={"title": "Home task", "tags": ["home"]})
        response = client.get("/api/tasks?tag=work")
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Work task"

    def test_sort_by_title_asc(self, client):
        client.post("/api/tasks", json={"title": "Zebra"})
        client.post("/api/tasks", json={"title": "Apple"})
        response = client.get("/api/tasks?sort_by=title&sort_order=asc")
        data = response.json()
        assert data["tasks"][0]["title"] == "Apple"
        assert data["tasks"][1]["title"] == "Zebra"


class TestUpdateTask:
    """Tests for PATCH /api/tasks/{id}."""

    def test_patch_title(self, client):
        resp = client.post("/api/tasks", json={"title": "Original"})
        task_id = resp.json()["id"]
        response = client.patch(f"/api/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_patch_priority(self, client):
        resp = client.post("/api/tasks", json={"title": "Task"})
        task_id = resp.json()["id"]
        response = client.patch(f"/api/tasks/{task_id}", json={"priority": "high"})
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    def test_patch_nonexistent_404(self, client):
        response = client.patch(
            "/api/tasks/00000000-0000-0000-0000-000000000000",
            json={"title": "X"},
        )
        assert response.status_code == 404


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{id}."""

    def test_delete_existing(self, client):
        resp = client.post("/api/tasks", json={"title": "Delete me"})
        task_id = resp.json()["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

    def test_delete_confirms_gone(self, client):
        resp = client.post("/api/tasks", json={"title": "Delete me"})
        task_id = resp.json()["id"]
        client.delete(f"/api/tasks/{task_id}")
        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_404(self, client):
        response = client.delete("/api/tasks/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestToggleComplete:
    """Tests for POST /api/tasks/{id}/complete."""

    def test_toggle_pending_to_completed(self, client):
        resp = client.post("/api/tasks", json={"title": "Toggle"})
        task_id = resp.json()["id"]
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_toggle_completed_back_to_pending(self, client):
        resp = client.post("/api/tasks", json={"title": "Toggle back"})
        task_id = resp.json()["id"]
        client.post(f"/api/tasks/{task_id}/complete")
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["completed_at"] is None

    def test_toggle_nonexistent_404(self, client):
        response = client.post(
            "/api/tasks/00000000-0000-0000-0000-000000000000/complete"
        )
        assert response.status_code == 404

    def test_recurring_task_creates_clone(self, client):
        resp = client.post("/api/tasks", json={
            "title": "Weekly standup",
            "is_recurring": True,
            "recurrence_rule": "weekly",
            "due_date": "2026-02-01T09:00:00",
        })
        task_id = resp.json()["id"]
        client.post(f"/api/tasks/{task_id}/complete")
        # List all tasks -- should have original (completed) + clone (pending)
        response = client.get("/api/tasks")
        data = response.json()
        assert data["total"] == 2
        statuses = {t["status"] for t in data["tasks"]}
        assert "completed" in statuses
        assert "pending" in statuses
