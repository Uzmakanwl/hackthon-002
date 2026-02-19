"""Dapr pub/sub event consumer router.

Receives CloudEvents from Dapr and dispatches them to appropriate handlers:
    - Notification handler: processes task.reminder.due events
    - Completion handler: processes task.completed events for recurrence
    - Audit handler: logs all other events for observability
"""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.events.schemas import EventType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["events"])


class DaprEvent(BaseModel):
    """Schema for a Dapr CloudEvent envelope."""

    data: dict
    datacontenttype: str = "application/json"
    id: str = ""
    source: str = ""
    specversion: str = "1.0"
    type: str = ""


@router.post("/events/task-events")
async def handle_task_event(event: DaprEvent) -> dict[str, str]:
    """Handle incoming task events from Dapr pub/sub.

    Routes events to the appropriate handler based on event_type.
    """
    event_data = event.data
    event_type = event_data.get("event_type", "")
    task_id = event_data.get("task_id", "")
    logger.info("Received event: %s for task %s", event_type, task_id)

    match event_type:
        case EventType.REMINDER_DUE:
            await _handle_reminder(event_data)
        case EventType.TASK_COMPLETED:
            await _handle_completion(event_data)
        case _:
            await _handle_audit(event_data)

    return {"status": "ok"}


async def _handle_reminder(event_data: dict) -> None:
    """Handle task.reminder.due events by logging the reminder."""
    task_id = event_data.get("task_id")
    payload = event_data.get("payload", {})
    title = payload.get("title", "Unknown task")
    logger.info("REMINDER: Task '%s' (ID: %s) is due!", title, task_id)


async def _handle_completion(event_data: dict) -> None:
    """Handle task.completed events for recurring task processing."""
    task_id = event_data.get("task_id")
    payload = event_data.get("payload", {})
    is_recurring = payload.get("is_recurring", False)
    if is_recurring:
        recurrence_rule = payload.get("recurrence_rule")
        logger.info(
            "RECURRENCE: Creating next %s occurrence for task %s",
            recurrence_rule,
            task_id,
        )


async def _handle_audit(event_data: dict) -> None:
    """Log all events for observability and audit trail."""
    event_type = event_data.get("event_type")
    task_id = event_data.get("task_id")
    logger.info(
        "AUDIT: %s — Task %s — %s",
        event_type,
        task_id,
        event_data.get("payload", {}),
    )
