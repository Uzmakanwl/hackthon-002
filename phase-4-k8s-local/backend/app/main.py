# app/main.py
"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import create_db_and_tables
from app.routers.tasks import router as tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: startup and shutdown events."""
    create_db_and_tables()
    yield


app = FastAPI(
    title="Todo App API",
    description="Phase 4: Kubernetes-deployed Todo Application",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return {"status": "healthy", "service": "todo-backend"}
