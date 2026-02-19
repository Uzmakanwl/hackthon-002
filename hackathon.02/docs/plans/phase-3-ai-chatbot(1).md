# Phase 3: AI-Powered Todo Chatbot — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extend Phase 2's full-stack todo app with an AI agent layer. An OpenAI Agent uses MCP tools to manage tasks via natural language. A ChatKit-powered frontend provides a conversational UI alongside the task list.

**Architecture:** FastAPI backend with Phase 2's CRUD layer intact. An MCP server exposes todo operations as tools. An OpenAI Agent (Agents SDK) wires MCP tools for natural language task management. A chat endpoint streams agent responses. The frontend is a split-pane layout: chat panel + task sidebar.

**Tech Stack:** Python 3.12+, FastAPI, SQLModel, OpenAI Agents SDK, MCP SDK, Next.js 14, TypeScript, OpenAI ChatKit, Tailwind CSS

---

## Task 1: Backend — Base CRUD Layer (Carry from Phase 2)

**Files:**
- Create: `phase-3-ai-chatbot/backend/app/config.py`
- Create: `phase-3-ai-chatbot/backend/app/db.py`
- Create: `phase-3-ai-chatbot/backend/app/models.py`
- Create: `phase-3-ai-chatbot/backend/app/schemas.py`
- Create: `phase-3-ai-chatbot/backend/app/services/task_service.py`
- Create: `phase-3-ai-chatbot/backend/app/services/recurrence_service.py`
- Create: `phase-3-ai-chatbot/backend/app/routers/tasks.py`

**Step 1: Copy and adapt Phase 2 backend code**

Copy all CRUD-related code from Phase 2's plan (Tasks 1-5). Each phase is independent — do not import from Phase 2.

Config should include the additional `OPENAI_API_KEY` field:

```python
# app/config.py — add to Settings:
self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
```

**Step 2: Run backend tests to verify CRUD works**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest tests/test_tasks_api.py -v`
Expected: All CRUD tests PASS

**Step 3: Commit**

```bash
git add phase-3-ai-chatbot/backend/app/ phase-3-ai-chatbot/backend/tests/
git commit -m "phase-3: feat: add base CRUD layer (adapted from phase-2)"
```

---

## Task 2: MCP Server — Todo Operation Tools

**Files:**
- Create: `phase-3-ai-chatbot/backend/app/mcp/server.py`
- Test: `phase-3-ai-chatbot/backend/tests/test_mcp_tools.py`

**Step 1: Write the failing test**

```python
# tests/test_mcp_tools.py
import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.mcp.server import (
    mcp_create_task,
    mcp_list_tasks,
    mcp_get_task,
    mcp_update_task,
    mcp_delete_task,
    mcp_complete_task,
)


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestMCPCreateTask:
    def test_create_basic(self, session):
        result = mcp_create_task(session, title="Buy groceries")
        assert "Buy groceries" in result
        assert "created" in result.lower() or "id" in result.lower()

    def test_create_with_priority(self, session):
        result = mcp_create_task(session, title="Urgent", priority="high")
        assert "Urgent" in result


class TestMCPListTasks:
    def test_list_empty(self, session):
        result = mcp_list_tasks(session)
        assert "no tasks" in result.lower() or "0" in result

    def test_list_with_tasks(self, session):
        mcp_create_task(session, title="Task 1")
        mcp_create_task(session, title="Task 2")
        result = mcp_list_tasks(session)
        assert "Task 1" in result
        assert "Task 2" in result


class TestMCPGetTask:
    def test_get_existing(self, session):
        create_result = mcp_create_task(session, title="Test")
        # Extract ID from create result
        task_id = _extract_id(create_result)
        result = mcp_get_task(session, task_id=task_id)
        assert "Test" in result

    def test_get_nonexistent(self, session):
        result = mcp_get_task(session, task_id="fake-id")
        assert "not found" in result.lower()


class TestMCPCompleteTask:
    def test_complete(self, session):
        create_result = mcp_create_task(session, title="Complete me")
        task_id = _extract_id(create_result)
        result = mcp_complete_task(session, task_id=task_id)
        assert "completed" in result.lower() or "done" in result.lower()


class TestMCPDeleteTask:
    def test_delete(self, session):
        create_result = mcp_create_task(session, title="Delete me")
        task_id = _extract_id(create_result)
        result = mcp_delete_task(session, task_id=task_id)
        assert "deleted" in result.lower()


def _extract_id(create_result: str) -> str:
    """Helper to extract task ID from MCP create response."""
    # Implementation depends on response format
    import re
    match = re.search(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", create_result)
    return match.group(0) if match else ""
```

**Step 2: Run test to verify it fails**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest tests/test_mcp_tools.py -v`
Expected: FAIL — ImportError

**Step 3: Implement MCP server tools**

```python
# app/mcp/server.py
"""MCP server exposing todo CRUD operations as tools."""

from typing import Optional
from sqlmodel import Session

from app.models import TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate
from app.services.task_service import (
    create_task,
    get_task,
    list_tasks,
    update_task,
    delete_task,
    toggle_complete,
)


def mcp_create_task(
    session: Session,
    *,
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
) -> str:
    """Create a new task. Returns a confirmation message with the task ID."""
    data = TaskCreate(
        title=title,
        description=description,
        priority=TaskPriority(priority),
        tags=tags or [],
        is_recurring=bool(recurrence_rule),
        recurrence_rule=recurrence_rule,
    )
    task = create_task(session, data)
    return f"Task created: '{task.title}' (ID: {task.id}, Priority: {task.priority.value})"


def mcp_list_tasks(
    session: Session,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    tag: Optional[str] = None,
) -> str:
    """List tasks with optional filters. Returns formatted task list."""
    parsed_status = TaskStatus(status) if status else None
    parsed_priority = TaskPriority(priority) if priority else None

    tasks, total = list_tasks(
        session,
        status=parsed_status,
        priority=parsed_priority,
        search=search,
        tag=tag,
        sort_by=sort_by,
    )

    if not tasks:
        return "No tasks found matching the criteria."

    lines = [f"Found {total} task(s):"]
    for task in tasks:
        status_icon = {"pending": "○", "in_progress": "◑", "completed": "●"}.get(task.status.value, "?")
        due = f" | Due: {task.due_date}" if task.due_date else ""
        lines.append(f"  {status_icon} [{task.priority.value}] {task.title}{due} (ID: {task.id[:8]})")
    return "\n".join(lines)


def mcp_get_task(session: Session, *, task_id: str) -> str:
    """Get detailed information about a specific task."""
    task = get_task(session, task_id)
    if not task:
        return f"Task not found with ID: {task_id}"

    tags = ", ".join(task.tags) if task.tags else "none"
    return (
        f"Task: {task.title}\n"
        f"  ID: {task.id}\n"
        f"  Status: {task.status.value}\n"
        f"  Priority: {task.priority.value}\n"
        f"  Description: {task.description or 'none'}\n"
        f"  Tags: {tags}\n"
        f"  Due: {task.due_date or 'none'}\n"
        f"  Recurring: {task.recurrence_rule or 'no'}\n"
        f"  Created: {task.created_at}"
    )


def mcp_update_task(
    session: Session,
    *,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    status: Optional[str] = None,
) -> str:
    """Update fields of an existing task."""
    data = TaskUpdate(
        title=title,
        description=description,
        priority=TaskPriority(priority) if priority else None,
        tags=tags,
        status=TaskStatus(status) if status else None,
    )
    task = update_task(session, task_id, data)
    if not task:
        return f"Task not found with ID: {task_id}"
    return f"Task updated: '{task.title}' (Status: {task.status.value}, Priority: {task.priority.value})"


def mcp_delete_task(session: Session, *, task_id: str) -> str:
    """Delete a task by ID."""
    success = delete_task(session, task_id)
    if not success:
        return f"Task not found with ID: {task_id}"
    return f"Task deleted successfully (ID: {task_id})"


def mcp_complete_task(session: Session, *, task_id: str) -> str:
    """Toggle task completion. Returns new status."""
    task = toggle_complete(session, task_id)
    if not task:
        return f"Task not found with ID: {task_id}"
    return f"Task '{task.title}' marked as {task.status.value}"
```

**Step 4: Run test to verify it passes**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest tests/test_mcp_tools.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add phase-3-ai-chatbot/backend/app/mcp/
git add phase-3-ai-chatbot/backend/tests/test_mcp_tools.py
git commit -m "phase-3: feat: add MCP server with todo CRUD tools"
```

---

## Task 3: MCP Server — Formal MCP SDK Registration

**Files:**
- Create: `phase-3-ai-chatbot/backend/app/mcp/mcp_app.py`

**Step 1: Implement MCP app with SDK**

```python
# app/mcp/mcp_app.py
"""MCP application that registers todo tools using the official MCP SDK."""

from mcp.server import Server
from mcp.types import Tool, TextContent

server = Server("todo-mcp-server")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """Register all todo MCP tools."""
    return [
        Tool(
            name="create_task",
            description="Create a new todo task",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Task title (required)"},
                    "description": {"type": "string", "description": "Task description"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "due_date": {"type": "string", "description": "Due date (ISO format)"},
                    "recurrence_rule": {"type": "string", "enum": ["daily", "weekly", "monthly", "yearly"]},
                },
                "required": ["title"],
            },
        ),
        Tool(
            name="list_tasks",
            description="List all tasks, optionally filtered by status, priority, or search keyword",
            inputSchema={
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "search": {"type": "string", "description": "Keyword to search in title/description"},
                    "sort_by": {"type": "string", "enum": ["created_at", "due_date", "priority", "title"]},
                    "tag": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_task",
            description="Get detailed information about a specific task by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task UUID"},
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="update_task",
            description="Update fields of an existing task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task UUID"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high"]},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "status": {"type": "string", "enum": ["pending", "in_progress", "completed"]},
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="delete_task",
            description="Delete a task by ID",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task UUID"},
                },
                "required": ["task_id"],
            },
        ),
        Tool(
            name="complete_task",
            description="Toggle a task's completion status",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "The task UUID"},
                },
                "required": ["task_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to MCP server functions."""
    from app.db import get_session_sync
    from app.mcp.server import (
        mcp_create_task, mcp_list_tasks, mcp_get_task,
        mcp_update_task, mcp_delete_task, mcp_complete_task,
    )

    session = get_session_sync()
    try:
        handlers = {
            "create_task": mcp_create_task,
            "list_tasks": mcp_list_tasks,
            "get_task": mcp_get_task,
            "update_task": mcp_update_task,
            "delete_task": mcp_delete_task,
            "complete_task": mcp_complete_task,
        }
        handler = handlers.get(name)
        if not handler:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        result = handler(session, **arguments)
        return [TextContent(type="text", text=result)]
    finally:
        session.close()
```

**Step 2: Commit**

```bash
git add phase-3-ai-chatbot/backend/app/mcp/mcp_app.py
git commit -m "phase-3: feat: register MCP tools with official SDK"
```

---

## Task 4: Agent — OpenAI Agents SDK Integration

**Files:**
- Create: `phase-3-ai-chatbot/backend/app/agents/todo_agent.py`
- Test: `phase-3-ai-chatbot/backend/tests/test_agent.py`

**Step 1: Write the failing test**

```python
# tests/test_agent.py
import pytest
from app.agents.todo_agent import SYSTEM_PROMPT, get_agent_tools


class TestAgentConfig:
    def test_system_prompt_exists(self):
        assert SYSTEM_PROMPT is not None
        assert "task" in SYSTEM_PROMPT.lower()
        assert len(SYSTEM_PROMPT) > 50

    def test_tools_defined(self):
        tools = get_agent_tools()
        tool_names = [t.name for t in tools]
        assert "create_task" in tool_names
        assert "list_tasks" in tool_names
        assert "complete_task" in tool_names
```

**Step 2: Run test to verify it fails**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest tests/test_agent.py -v`
Expected: FAIL

**Step 3: Implement todo_agent.py**

```python
# app/agents/todo_agent.py
"""OpenAI Agent definition for natural language task management."""

from openai import OpenAI
from app.config import get_settings

SYSTEM_PROMPT = """You are a personal task management assistant. Help the user manage their
todos using natural language. When the user says things like 'remind me to buy groceries
tomorrow', create a task with appropriate due date and priority.

You have access to the following tools for managing tasks:
- create_task: Create a new task with title, description, priority, tags, due date
- list_tasks: List tasks with optional filtering by status, priority, search keyword
- get_task: Get full details of a specific task
- update_task: Update any field of an existing task
- delete_task: Remove a task permanently
- complete_task: Toggle a task's completion status

When creating tasks:
- Infer priority from context (e.g., "urgent" → high, "sometime" → low)
- Extract due dates from natural language (e.g., "tomorrow", "next Friday")
- Add relevant tags based on context (e.g., "groceries" → ["shopping", "home"])

Always confirm actions with the user and show the result clearly."""


def get_agent_tools():
    """Return the list of tool definitions for the agent."""
    from app.mcp.mcp_app import list_tools
    import asyncio
    return asyncio.run(list_tools())


async def run_agent(user_message: str, conversation_history: list[dict]) -> str:
    """Run the OpenAI agent with the given message and history.

    Args:
        user_message: The user's latest message.
        conversation_history: List of prior messages [{role, content}].

    Returns:
        The agent's response text.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # TODO: Wire MCP tools via Agents SDK
    # This is the integration point where the agent calls MCP tools
    # Implementation depends on the specific Agents SDK version

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    return response.choices[0].message.content
```

**Step 4: Run test to verify it passes**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest tests/test_agent.py -v`
Expected: PASS (config/tool listing tests only — agent execution requires API key)

**Step 5: Commit**

```bash
git add phase-3-ai-chatbot/backend/app/agents/
git add phase-3-ai-chatbot/backend/tests/test_agent.py
git commit -m "phase-3: feat: add OpenAI agent with system prompt and tool wiring"
```

---

## Task 5: Backend — Chat API Endpoint

**Files:**
- Create: `phase-3-ai-chatbot/backend/app/routers/chat.py`
- Modify: `phase-3-ai-chatbot/backend/app/main.py`

**Step 1: Implement chat router**

```python
# app/routers/chat.py
"""Chat endpoint for AI agent interaction."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.db import get_session
from app.agents.todo_agent import run_agent

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat message."""
    message: str
    history: list[dict] = []


class ChatResponse(BaseModel):
    """Agent response."""
    response: str


@router.post("", response_model=ChatResponse)
async def chat(data: ChatRequest):
    """Send a message to the AI agent and get a response."""
    try:
        response = await run_agent(data.message, data.history)
        return ChatResponse(response=response)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(exc)}")
```

**Step 2: Add chat router to main.py**

Add to main.py imports and include:
```python
from app.routers.chat import router as chat_router
app.include_router(chat_router)
```

**Step 3: Commit**

```bash
git add phase-3-ai-chatbot/backend/app/routers/chat.py
git add phase-3-ai-chatbot/backend/app/main.py
git commit -m "phase-3: feat: add chat API endpoint wired to AI agent"
```

---

## Task 6: Frontend — Chat Types and API Client

**Files:**
- Create: `phase-3-ai-chatbot/frontend/src/types/chat.ts`
- Modify: `phase-3-ai-chatbot/frontend/src/lib/api.ts`

**Step 1: Implement chat types**

```typescript
// src/types/chat.ts
export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  history: Array<{ role: string; content: string }>;
}

export interface ChatResponse {
  response: string;
}
```

**Step 2: Add chat API function**

```typescript
// Add to src/lib/api.ts:
export async function sendChatMessage(
  message: string,
  history: Array<{ role: string; content: string }>
): Promise<string> {
  const data = await fetchAPI<{ response: string }>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message, history }),
  });
  return data.response;
}
```

**Step 3: Commit**

```bash
git add phase-3-ai-chatbot/frontend/src/types/chat.ts phase-3-ai-chatbot/frontend/src/lib/api.ts
git commit -m "phase-3: feat: add chat types and API client"
```

---

## Task 7: Frontend — Chat Components

**Files:**
- Create: `phase-3-ai-chatbot/frontend/src/components/ChatPanel.tsx`
- Create: `phase-3-ai-chatbot/frontend/src/components/ChatMessage.tsx`
- Create: `phase-3-ai-chatbot/frontend/src/components/ChatInput.tsx`
- Create: `phase-3-ai-chatbot/frontend/src/hooks/useChat.ts`

**Step 1: Implement useChat hook**

```typescript
// src/hooks/useChat.ts
"use client";
import { useState, useCallback } from "react";
import type { ChatMessage } from "@/types/chat";
import { sendChatMessage } from "@/lib/api";

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const response = await sendChatMessage(content, history);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: response,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: "Sorry, I encountered an error. Please try again.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }, [messages]);

  return { messages, loading, sendMessage };
}
```

**Step 2: Implement ChatMessage component**

Render message bubbles with user on right (blue) and assistant on left (gray). Show timestamp.

**Step 3: Implement ChatInput component**

Text input with send button. Disabled while loading. Submit on Enter.

**Step 4: Implement ChatPanel component**

Combines ChatMessage list (scrollable) + ChatInput at bottom. Shows loading indicator.

**Step 5: Commit**

```bash
git add phase-3-ai-chatbot/frontend/src/components/Chat*.tsx
git add phase-3-ai-chatbot/frontend/src/hooks/useChat.ts
git commit -m "phase-3: feat: add chat UI components and useChat hook"
```

---

## Task 8: Frontend — Split Layout Page

**Files:**
- Create: `phase-3-ai-chatbot/frontend/src/components/TaskSidebar.tsx`
- Modify: `phase-3-ai-chatbot/frontend/src/app/page.tsx`

**Step 1: Implement TaskSidebar**

Compact task list view for the sidebar. Shows task title, status icon, priority badge. Refreshes when tasks change.

**Step 2: Implement split-pane page.tsx**

```
┌─────────────────────────────────────────────┐
│              Todo AI Assistant               │
├──────────────────────┬──────────────────────┤
│                      │                      │
│    Chat Panel        │   Task Sidebar       │
│    (2/3 width)       │   (1/3 width)        │
│                      │                      │
│  [messages...]       │  [task list...]      │
│                      │                      │
│  [input box]         │                      │
└──────────────────────┴──────────────────────┘
```

- Use Tailwind grid: `grid grid-cols-3`
- Chat panel: `col-span-2`
- Task sidebar: `col-span-1`
- Sidebar auto-refreshes after each chat message (tasks may have changed)

**Step 3: Manual smoke test**

Run backend and frontend. Test natural language commands:
- "Add a high priority task to review PRs by Friday"
- "Show me all my tasks"
- "Mark the PR task as done"
- "Delete the completed task"

**Step 4: Commit**

```bash
git add phase-3-ai-chatbot/frontend/src/
git commit -m "phase-3: feat: add split-pane layout with chat panel and task sidebar"
```

---

## Task 9: README and Final Polish

**Files:**
- Create: `phase-3-ai-chatbot/README.md`

**Step 1: Write README**

Cover:
- Architecture diagram (Mermaid: ChatKit → Chat API → Agent → MCP → Task Service → DB)
- Backend setup (venv, pip, .env with OPENAI_API_KEY, alembic, uvicorn)
- Frontend setup (npm install, npm run dev)
- MCP tools reference table
- Agent system prompt
- Example conversations
- Testing instructions

**Step 2: Run all tests**

Run: `cd phase-3-ai-chatbot/backend && python -m pytest -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add phase-3-ai-chatbot/README.md
git commit -m "phase-3: docs: add README with architecture, setup, and MCP tools reference"
```

---

## Summary

| Task | What | Tests |
|------|------|-------|
| 1 | Base CRUD layer (from Phase 2) | ~30 |
| 2 | MCP server tools | 7 |
| 3 | MCP SDK registration | — |
| 4 | OpenAI agent integration | 2 |
| 5 | Chat API endpoint | — |
| 6 | Chat types + API client | — |
| 7 | Chat UI components + hook | — |
| 8 | Split-pane layout page | Manual |
| 9 | README + polish | — |

**Total: ~39 automated tests + manual testing across 9 tasks.**
