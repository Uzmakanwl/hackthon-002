"""Dapr HTTP event producer for publishing task lifecycle events."""

import logging

import httpx

from app.config import get_settings
from app.events.schemas import TaskEvent

logger = logging.getLogger(__name__)

PUBSUB_NAME = "pubsub"
TOPIC_NAME = "task-events"


async def publish_event(event: TaskEvent) -> bool:
    """Publish a task event to Dapr pub/sub via HTTP.

    Args:
        event: The TaskEvent to publish.

    Returns:
        True if the event was published successfully, False otherwise.
    """
    settings = get_settings()
    dapr_url = (
        f"http://localhost:{settings.DAPR_HTTP_PORT}"
        f"/v1.0/publish/{PUBSUB_NAME}/{TOPIC_NAME}"
    )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                dapr_url,
                json=event.model_dump(mode="json"),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            logger.info(
                "Published event: %s for task %s",
                event.event_type.value,
                event.task_id,
            )
            return True
    except Exception as exc:
        logger.error("Failed to publish event: %s", exc)
        return False
