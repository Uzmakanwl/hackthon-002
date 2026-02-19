"""Dapr pub/sub helper for publishing and subscribing to events.

Uses Dapr's pub/sub building block backed by Kafka. This provides an
abstraction layer over direct Kafka access, allowing Dapr to manage
broker connections, serialization, and retries.
"""

import logging
from typing import Any

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

PUBSUB_NAME = "pubsub"  # Matches the Dapr component name in dapr-components/pubsub.yaml


async def publish_to_topic(
    topic: str,
    data: dict[str, Any],
    pubsub_name: str = PUBSUB_NAME,
) -> None:
    """Publish a message to a Dapr pub/sub topic.

    Args:
        topic: The topic name to publish to (e.g., "tasks", "task-reminders").
        data: The message payload to publish.
        pubsub_name: The Dapr pub/sub component name. Defaults to "pubsub".
    """
    settings = get_settings()
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/publish/{pubsub_name}/{topic}"

    async with httpx.AsyncClient() as client:
        response = await client.post(dapr_url, json=data)
        response.raise_for_status()

    logger.info("Published to Dapr topic '%s' via '%s'", topic, pubsub_name)


async def subscribe_to_topic(
    topic: str,
    route: str,
    pubsub_name: str = PUBSUB_NAME,
) -> dict[str, Any]:
    """Return a Dapr subscription configuration for a topic.

    This is used to register a subscription endpoint with Dapr.
    The FastAPI app should expose a POST endpoint at the specified route
    to receive messages from the topic.

    Args:
        topic: The topic name to subscribe to.
        route: The local route path that handles incoming messages.
        pubsub_name: The Dapr pub/sub component name. Defaults to "pubsub".

    Returns:
        A subscription configuration dictionary for Dapr.
    """
    return {
        "pubsubname": pubsub_name,
        "topic": topic,
        "route": route,
    }
