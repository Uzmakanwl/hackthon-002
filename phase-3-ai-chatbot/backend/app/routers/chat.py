"""Chat endpoint for AI-powered task management via natural language."""

import logging

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.agents.todo_agent import run_agent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


class ChatMessage(BaseModel):
    """A single message in a chat conversation."""

    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="The message text content")


class ChatRequest(BaseModel):
    """Request schema for the chat endpoint."""

    message: str = Field(..., min_length=1, description="The user's message")
    history: list[ChatMessage] = Field(
        default=[], description="Previous conversation messages for context"
    )


class ChatResponse(BaseModel):
    """Response schema from the chat endpoint."""

    reply: str = Field(..., description="The assistant's response message")


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a natural language message through the AI todo agent.

    Accepts a user message and optional conversation history, runs the
    OpenAI agent with MCP tools, and returns the agent's response.

    Args:
        request: The chat request containing the user message and history.

    Returns:
        A ChatResponse with the agent's reply.

    Raises:
        HTTPException: 500 if the agent encounters an error.
    """
    try:
        history_dicts = [msg.model_dump() for msg in request.history]
        reply = await run_agent(request.message, conversation_history=history_dicts)
        return ChatResponse(reply=reply)
    except Exception as exc:
        logger.exception("Agent error processing chat message")
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {exc}",
        ) from exc
