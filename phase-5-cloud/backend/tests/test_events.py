"""Tests for event schemas, producer, and consumer."""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

from app.events.schemas import EventType, TaskEvent
from app.events.consumer import DaprEvent
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


# ---------------------------------------------------------------------------
# EventType Enum
# ---------------------------------------------------------------------------


class TestEventType:
    """Tests for EventType enum values."""

    def test_event_type_values(self) -> None:
        """Verify all expected event types are defined with correct values."""
        assert EventType.TASK_CREATED == "task.created"
        assert EventType.TASK_UPDATED == "task.updated"
        assert EventType.TASK_COMPLETED == "task.completed"
        assert EventType.TASK_DELETED == "task.deleted"
        assert EventType.REMINDER_DUE == "task.reminder.due"
        assert EventType.RECURRING_TRIGGERED == "task.recurring.triggered"

    def test_event_type_count(self) -> None:
        """Verify the total number of event types."""
        assert len(EventType) == 6


# ---------------------------------------------------------------------------
# TaskEvent Schema
# ---------------------------------------------------------------------------


class TestTaskEventSchema:
    """Tests for TaskEvent schema."""

    def test_task_event_creation(self) -> None:
        """Verify TaskEvent can be constructed with valid data."""
        event = TaskEvent(
            event_type=EventType.TASK_CREATED,
            task_id=str(uuid.uuid4()),
            payload={"title": "Test"},
        )
        assert event.event_type == EventType.TASK_CREATED
        assert event.payload == {"title": "Test"}
        assert isinstance(event.timestamp, datetime)

    def test_task_event_serialization(self) -> None:
        """Verify TaskEvent serializes to JSON correctly."""
        task_id = str(uuid.uuid4())
        event = TaskEvent(
            event_type=EventType.TASK_DELETED,
            task_id=task_id,
        )
        data = event.model_dump(mode="json")
        assert data["event_type"] == "task.deleted"
        assert data["task_id"] == task_id
        assert data["payload"] == {}
        assert "timestamp" in data

    def test_task_event_default_payload(self) -> None:
        """Verify TaskEvent defaults to empty payload."""
        event = TaskEvent(
            event_type=EventType.TASK_UPDATED,
            task_id="abc",
        )
        assert event.payload == {}


# ---------------------------------------------------------------------------
# Consumer Router
# ---------------------------------------------------------------------------


class TestEventConsumer:
    """Tests for the Dapr event consumer endpoint."""

    def test_handle_task_event_created(self, client: TestClient) -> None:
        """Verify the consumer endpoint handles task.created events."""
        cloud_event = {
            "data": {
                "event_type": "task.created",
                "task_id": str(uuid.uuid4()),
                "payload": {"title": "New Task"},
            },
            "datacontenttype": "application/json",
            "id": "event-1",
            "source": "test",
            "specversion": "1.0",
            "type": "com.dapr.event.sent",
        }
        response = client.post("/events/task-events", json=cloud_event)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_handle_task_event_completed(self, client: TestClient) -> None:
        """Verify the consumer endpoint handles task.completed events."""
        cloud_event = {
            "data": {
                "event_type": "task.completed",
                "task_id": str(uuid.uuid4()),
                "payload": {
                    "is_recurring": True,
                    "recurrence_rule": "weekly",
                },
            },
            "datacontenttype": "application/json",
            "id": "event-2",
            "source": "test",
            "specversion": "1.0",
            "type": "com.dapr.event.sent",
        }
        response = client.post("/events/task-events", json=cloud_event)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_handle_task_event_reminder(self, client: TestClient) -> None:
        """Verify the consumer endpoint handles reminder events."""
        cloud_event = {
            "data": {
                "event_type": "task.reminder.due",
                "task_id": str(uuid.uuid4()),
                "payload": {"title": "Meeting"},
            },
            "datacontenttype": "application/json",
            "id": "event-3",
            "source": "test",
            "specversion": "1.0",
            "type": "com.dapr.event.sent",
        }
        response = client.post("/events/task-events", json=cloud_event)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_dapr_event_model(self) -> None:
        """Verify DaprEvent model parses correctly."""
        event = DaprEvent(
            data={"event_type": "task.created", "task_id": "123"},
            id="evt-1",
            source="test-source",
        )
        assert event.data["event_type"] == "task.created"
        assert event.specversion == "1.0"
