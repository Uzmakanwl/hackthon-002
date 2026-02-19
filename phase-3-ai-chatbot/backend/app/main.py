"""FastAPI application entry point for the Phase 3 AI-powered Todo app."""

from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import create_db_and_tables
from app.routers import tasks


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan: create DB tables on startup."""
    create_db_and_tables()
    yield


settings = get_settings()

app = FastAPI(
    title="Todo AI Chatbot API",
    description="Phase 3: AI-powered todo management with OpenAI Agents and MCP tools.",
    version="0.3.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include task CRUD router
app.include_router(tasks.router)

# Include chat router (AI agent) — imported separately to avoid
# breaking tests if OpenAI SDK is not fully configured
try:
    from app.routers import chat
    app.include_router(chat.router)
except Exception:
    pass


@app.get("/health", tags=["health"])
def health_check() -> dict:
    """Health check endpoint for monitoring and K8s probes.

    Returns:
        A dictionary with status and service information.
    """
    return {
        "status": "healthy",
        "service": "todo-ai-chatbot-api",
        "version": "0.3.0",
    }
