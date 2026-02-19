"""OpenAI Agent for natural language task management via function calling.

Uses the standard openai library with the tools parameter for function
calling, routing tool invocations to the MCP plain functions that perform
actual CRUD operations against the database.
"""

import json
from typing import Optional

from openai import OpenAI

from app.config import get_settings
from app.db import get_session_sync

SYSTEM_PROMPT = """You are a personal task management assistant. Help the user manage their todos using natural language.

When the user says things like 'remind me to buy groceries tomorrow', create a task with appropriate due date and priority.

You have access to the following tools for managing tasks:
- create_task: Create a new task with title, description, priority, tags, due date
- list_tasks: List tasks with optional filtering by status, priority, search keyword
- get_task: Get full details of a specific task
- update_task: Update any field of an existing task
- delete_task: Remove a task permanently
- complete_task: Toggle a task's completion status

When creating tasks:
- Infer priority from context (e.g., "urgent" -> high, "sometime" -> low)
- Extract due dates from natural language when possible (use ISO 8601 format)
- Add relevant tags based on context (e.g., "groceries" -> ["shopping", "home"])

Always confirm actions with the user and show the result clearly."""


# ---------------------------------------------------------------------------
# OpenAI function-calling tool definitions (JSON Schema)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new todo task",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Task title (required)",
                    },
                    "description": {
                        "type": "string",
                        "description": "Task description",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Task priority level",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tag labels",
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Due date in ISO 8601 format",
                    },
                    "recurrence_rule": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly", "yearly"],
                        "description": "Recurrence rule for repeating tasks",
                    },
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List all tasks, optionally filtered by status, priority, or search keyword",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                        "description": "Filter by task status",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Filter by priority level",
                    },
                    "search": {
                        "type": "string",
                        "description": "Keyword to search in title/description",
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["created_at", "due_date", "priority", "title"],
                        "description": "Field to sort results by",
                    },
                    "tag": {
                        "type": "string",
                        "description": "Filter by a specific tag",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task",
            "description": "Get detailed information about a specific task by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task UUID",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update fields of an existing task",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task UUID",
                    },
                    "title": {"type": "string", "description": "New title"},
                    "description": {
                        "type": "string",
                        "description": "New description",
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "New priority",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tag list",
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "in_progress", "completed"],
                        "description": "New status",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete a task by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task UUID",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Toggle a task's completion status",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "The task UUID",
                    },
                },
                "required": ["task_id"],
            },
        },
    },
]


def get_agent_tools() -> list[dict]:
    """Return the list of OpenAI function-calling tool definitions.

    Returns:
        A list of tool definition dicts in OpenAI's expected schema.
    """
    return TOOL_DEFINITIONS


def _execute_tool(tool_name: str, arguments: dict) -> str:
    """Execute an MCP tool function and return the result string.

    Opens a database session, dispatches to the matching mcp_* plain
    function, and ensures the session is always closed.

    Args:
        tool_name: The name of the tool to execute (e.g. 'create_task').
        arguments: The keyword arguments parsed from the model's function call.

    Returns:
        A human-readable result string from the tool, or an error message.
    """
    from app.mcp.server import (
        mcp_create_task,
        mcp_list_tasks,
        mcp_get_task,
        mcp_update_task,
        mcp_delete_task,
        mcp_complete_task,
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
        handler = handlers.get(tool_name)
        if not handler:
            return f"Unknown tool: {tool_name}"
        return handler(session, **arguments)
    finally:
        session.close()


async def run_agent(
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> str:
    """Run the OpenAI agent with function calling.

    Sends the conversation to the OpenAI Chat Completions API with tool
    definitions.  If the model requests tool calls, executes them against the
    database via the MCP plain functions and feeds the results back, looping
    until the model produces a final text response.

    Args:
        user_message: The user's latest message.
        conversation_history: List of prior messages [{"role": ..., "content": ...}].

    Returns:
        The agent's final response text.
    """
    settings = get_settings()
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_message})

    # Loop to handle multiple rounds of tool calls
    max_iterations = 10
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=TOOL_DEFINITIONS,
        )

        choice = response.choices[0]

        # If the model wants to call one or more tools
        if choice.finish_reason == "tool_calls" and choice.message.tool_calls:
            # Append the assistant message (contains tool_calls metadata)
            messages.append(choice.message)

            # Execute each tool call and feed the result back
            for tool_call in choice.message.tool_calls:
                arguments = json.loads(tool_call.function.arguments)
                result = _execute_tool(tool_call.function.name, arguments)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    }
                )
        else:
            # Model returned a final text response
            return choice.message.content or "I processed your request."

    return "I'm having trouble processing this request. Please try again."
