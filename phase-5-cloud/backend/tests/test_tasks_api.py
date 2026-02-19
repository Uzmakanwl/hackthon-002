"""Integration tests for the Task API endpoints."""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
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


@pytest.fixture(name="sample_task_data")
def sample_task_data_fixture() -> dict:
    """Return sample task data for creating a task."""
    return {
        "title": "Test Task",
        "description": "A test task description",
        "priority": "medium",
        "tags": ["test", "sample"],
    }


# ---------------------------------------------------------------------------
# Health Check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    """Tests for the health check endpoint."""

    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


# ---------------------------------------------------------------------------
# Create Task
# ---------------------------------------------------------------------------


class TestCreateTask:
    """Tests for POST /api/tasks."""

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_create_task_success(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        response = client.post("/api/tasks/", json=sample_task_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Task"
        assert data["description"] == "A test task description"
        assert data["priority"] == "medium"
        assert data["status"] == "pending"
        assert data["tags"] == ["test", "sample"]
        assert data["id"] is not None

    def test_create_task_missing_title(self, client: TestClient) -> None:
        response = client.post("/api/tasks/", json={"description": "no title"})
        assert response.status_code == 422

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_create_task_with_due_date(
        self, mock_publish, client: TestClient
    ) -> None:
        due = (datetime.utcnow() + timedelta(days=3)).isoformat()
        data = {"title": "Due Date Task", "due_date": due}
        response = client.post("/api/tasks/", json=data)
        assert response.status_code == 201
        assert response.json()["due_date"] is not None

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_create_task_with_recurrence(
        self, mock_publish, client: TestClient
    ) -> None:
        data = {
            "title": "Recurring Task",
            "is_recurring": True,
            "recurrence_rule": "daily",
        }
        response = client.post("/api/tasks/", json=data)
        assert response.status_code == 201
        body = response.json()
        assert body["is_recurring"] is True
        assert body["recurrence_rule"] == "daily"


# ---------------------------------------------------------------------------
# List Tasks
# ---------------------------------------------------------------------------


class TestListTasks:
    """Tests for GET /api/tasks."""

    def test_list_tasks_empty(self, client: TestClient) -> None:
        response = client.get("/api/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_list_tasks_with_filter(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        # Create a task
        client.post("/api/tasks/", json=sample_task_data)
        # Create a high priority task
        client.post(
            "/api/tasks/",
            json={"title": "High Task", "priority": "high"},
        )

        response = client.get("/api/tasks/?priority=high")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["priority"] == "high"

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_list_tasks_with_search(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        client.post("/api/tasks/", json=sample_task_data)
        client.post("/api/tasks/", json={"title": "Buy groceries"})

        response = client.get("/api/tasks/?search=groceries")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "groceries" in data["tasks"][0]["title"].lower()

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_list_tasks_with_sort(
        self, mock_publish, client: TestClient
    ) -> None:
        client.post("/api/tasks/", json={"title": "Banana"})
        client.post("/api/tasks/", json={"title": "Apple"})

        response = client.get("/api/tasks/?sort_by=title&sort_order=asc")
        assert response.status_code == 200
        titles = [t["title"] for t in response.json()["tasks"]]
        assert titles == sorted(titles)

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_list_tasks_with_tag_filter(
        self, mock_publish, client: TestClient
    ) -> None:
        client.post(
            "/api/tasks/",
            json={"title": "Work Task", "tags": ["work"]},
        )
        client.post(
            "/api/tasks/",
            json={"title": "Home Task", "tags": ["home"]},
        )

        response = client.get("/api/tasks/?tag=work")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["tasks"][0]["title"] == "Work Task"


# ---------------------------------------------------------------------------
# Get Task
# ---------------------------------------------------------------------------


class TestGetTask:
    """Tests for GET /api/tasks/{id}."""

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_get_task_success(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        create_resp = client.post("/api/tasks/", json=sample_task_data)
        task_id = create_resp.json()["id"]

        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["id"] == task_id
        assert response.json()["title"] == "Test Task"

    def test_get_task_not_found(self, client: TestClient) -> None:
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/tasks/{fake_id}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update Task
# ---------------------------------------------------------------------------


class TestUpdateTask:
    """Tests for PATCH /api/tasks/{id}."""

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_update_task_partial(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        create_resp = client.post("/api/tasks/", json=sample_task_data)
        task_id = create_resp.json()["id"]

        response = client.patch(
            f"/api/tasks/{task_id}",
            json={"title": "Updated Title"},
        )
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
        # Unchanged fields remain
        assert response.json()["description"] == "A test task description"

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_update_task_not_found(
        self, mock_publish, client: TestClient
    ) -> None:
        fake_id = str(uuid.uuid4())
        response = client.patch(
            f"/api/tasks/{fake_id}",
            json={"title": "Nope"},
        )
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete Task
# ---------------------------------------------------------------------------


class TestDeleteTask:
    """Tests for DELETE /api/tasks/{id}."""

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_delete_task_success(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        create_resp = client.post("/api/tasks/", json=sample_task_data)
        task_id = create_resp.json()["id"]

        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_resp = client.get(f"/api/tasks/{task_id}")
        assert get_resp.status_code == 404

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_delete_task_not_found(
        self, mock_publish, client: TestClient
    ) -> None:
        fake_id = str(uuid.uuid4())
        response = client.delete(f"/api/tasks/{fake_id}")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Toggle Complete
# ---------------------------------------------------------------------------


class TestToggleComplete:
    """Tests for POST /api/tasks/{id}/complete."""

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_toggle_complete_pending_to_completed(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        create_resp = client.post("/api/tasks/", json=sample_task_data)
        task_id = create_resp.json()["id"]

        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_toggle_complete_completed_to_pending(
        self, mock_publish, client: TestClient, sample_task_data: dict
    ) -> None:
        create_resp = client.post("/api/tasks/", json=sample_task_data)
        task_id = create_resp.json()["id"]

        # Complete it
        client.post(f"/api/tasks/{task_id}/complete")
        # Toggle back to pending
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["completed_at"] is None

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_toggle_complete_recurring_task(
        self, mock_publish, client: TestClient
    ) -> None:
        due = (datetime.utcnow() + timedelta(days=1)).isoformat()
        data = {
            "title": "Recurring Daily",
            "is_recurring": True,
            "recurrence_rule": "daily",
            "due_date": due,
        }
        create_resp = client.post("/api/tasks/", json=data)
        task_id = create_resp.json()["id"]

        # Complete the recurring task
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        # Verify a new task was created (total should be 2 now)
        list_resp = client.get("/api/tasks/")
        assert list_resp.json()["total"] == 2

    @patch("app.routers.tasks.publish_event", new_callable=AsyncMock)
    def test_toggle_complete_not_found(
        self, mock_publish, client: TestClient
    ) -> None:
        fake_id = str(uuid.uuid4())
        response = client.post(f"/api/tasks/{fake_id}/complete")
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Dapr Subscriptions
# ---------------------------------------------------------------------------


class TestDaprSubscriptions:
    """Tests for Dapr subscription endpoint."""

    def test_dapr_subscribe_returns_subscriptions(
        self, client: TestClient
    ) -> None:
        response = client.get("/dapr/subscribe")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["pubsubname"] == "pubsub"
        assert data[0]["topic"] == "task-events"
        assert data[0]["route"] == "/events/task-events"
