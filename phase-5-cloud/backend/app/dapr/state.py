"""Dapr state store helper for Redis-backed caching.

Uses Dapr's state management building block to get/set/delete state.
The underlying store is configured as Redis in dapr-components/statestore.yaml.
"""

import logging
from typing import Any, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

STATE_STORE_NAME = "statestore"  # Matches the Dapr component name


async def get_state(
    key: str,
    store_name: str = STATE_STORE_NAME,
) -> Optional[Any]:
    """Retrieve a value from the Dapr state store.

    Args:
        key: The state key to look up.
        store_name: The Dapr state store component name.

    Returns:
        The stored value, or None if the key does not exist.
    """
    settings = get_settings()
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{store_name}/{key}"

    async with httpx.AsyncClient() as client:
        response = await client.get(dapr_url)
        if response.status_code == 204:
            return None
        response.raise_for_status()
        return response.json()


async def save_state(
    key: str,
    value: Any,
    store_name: str = STATE_STORE_NAME,
) -> None:
    """Save a value to the Dapr state store.

    Args:
        key: The state key.
        value: The value to store (must be JSON-serializable).
        store_name: The Dapr state store component name.
    """
    settings = get_settings()
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{store_name}"

    payload = [{"key": key, "value": value}]

    async with httpx.AsyncClient() as client:
        response = await client.post(dapr_url, json=payload)
        response.raise_for_status()

    logger.info("Saved state key '%s' to store '%s'", key, store_name)


async def delete_state(
    key: str,
    store_name: str = STATE_STORE_NAME,
) -> None:
    """Delete a value from the Dapr state store.

    Args:
        key: The state key to delete.
        store_name: The Dapr state store component name.
    """
    settings = get_settings()
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/state/{store_name}/{key}"

    async with httpx.AsyncClient() as client:
        response = await client.delete(dapr_url)
        response.raise_for_status()

    logger.info("Deleted state key '%s' from store '%s'", key, store_name)
