"""FastAPI application entry point with Dapr sidecar integration."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlmodel import SQLModel

from app.config import get_settings
from app.db import engine
from app.routers.tasks import router as tasks_router
from app.events.consumer import router as events_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    logger.info("Starting application...")
    import app.models  # noqa: F401 — ensure models are registered
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created")
    yield
    logger.info("Application shut down")


app = FastAPI(
    title="Todo List API — Phase 5 (Cloud)",
    description=(
        "Event-driven task management API with Kafka, Dapr, "
        "and DigitalOcean DOKS deployment."
    ),
    version="0.5.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router)
app.include_router(events_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {"status": "healthy"}


@app.get("/dapr/subscribe")
async def dapr_subscriptions() -> list[dict[str, Any]]:
    """Return Dapr subscription configuration.

    Dapr calls this endpoint to discover which topics
    this application subscribes to and their handler routes.
    """
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task-events",
        },
    ]
