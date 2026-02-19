"""MCP (Model Context Protocol) server exposing todo CRUD operations as tools."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session
from mcp.server.fastmcp import FastMCP

from app.models import TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate
from app.services.task_service import (
    create_task as svc_create_task,
    get_task as svc_get_task,
    list_tasks as svc_list_tasks,
    update_task as svc_update_task,
    delete_task as svc_delete_task,
    toggle_complete as svc_toggle_complete,
)

mcp_server = FastMCP("Todo MCP Server")


# ---------------------------------------------------------------------------
# Plain testable functions (accept a Session, return human-readable strings)
# ---------------------------------------------------------------------------


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
    """Create a new task and return a human-readable confirmation.

    Args:
        session: The database session.
        title: The task title (required).
        description: Optional description text.
        priority: Priority level ('low', 'medium', 'high').
        tags: Optional list of tag labels.
        due_date: Optional due date in ISO 8601 format.
        recurrence_rule: Optional recurrence rule ('daily', 'weekly', etc.).

    Returns:
        A string confirming task creation with key details.
    """
    parsed_due: Optional[datetime] = None
    if due_date:
        parsed_due = datetime.fromisoformat(due_date)

    data = TaskCreate(
        title=title,
        description=description,
        priority=TaskPriority(priority),
        tags=tags or [],
        due_date=parsed_due,
        is_recurring=bool(recurrence_rule),
        recurrence_rule=recurrence_rule,
    )
    task = svc_create_task(session, data)
    due_info = f", Due: {task.due_date}" if task.due_date else ""
    recurring_info = f", Recurring: {task.recurrence_rule}" if task.recurrence_rule else ""
    return (
        f"Task created: '{task.title}' "
        f"(ID: {task.id}, Priority: {task.priority.value}"
        f"{due_info}{recurring_info})"
    )


def mcp_list_tasks(
    session: Session,
    *,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    tag: Optional[str] = None,
) -> str:
    """List tasks with optional filtering and return a formatted summary.

    Args:
        session: The database session.
        status: Filter by status ('pending', 'in_progress', 'completed').
        priority: Filter by priority ('low', 'medium', 'high').
        search: Keyword search across title and description.
        sort_by: Field to sort by (default: 'created_at').
        tag: Filter by tag name.

    Returns:
        A formatted multi-line string listing matching tasks.
    """
    parsed_status = TaskStatus(status) if status else None
    parsed_priority = TaskPriority(priority) if priority else None
    tasks, total = svc_list_tasks(
        session,
        status=parsed_status,
        priority=parsed_priority,
        search=search,
        tag=tag,
        sort_by=sort_by,
    )
    if not tasks:
        return "No tasks found matching the criteria."

    status_icons = {
        "pending": "○",
        "in_progress": "◑",
        "completed": "●",
    }
    lines = [f"Found {total} task(s):"]
    for task in tasks:
        icon = status_icons.get(task.status.value, "?")
        due = f" | Due: {task.due_date}" if task.due_date else ""
        tags_str = f" | Tags: {', '.join(task.tags)}" if task.tags else ""
        lines.append(
            f"  {icon} [{task.priority.value}] {task.title}"
            f"{due}{tags_str} (ID: {task.id[:8]})"
        )
    return "\n".join(lines)


def mcp_get_task(session: Session, *, task_id: str) -> str:
    """Retrieve a single task by ID and return a detailed description.

    Args:
        session: The database session.
        task_id: The UUID of the task.

    Returns:
        A formatted string with the task details, or a not-found message.
    """
    task = svc_get_task(session, task_id)
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
    """Update an existing task and return confirmation.

    Args:
        session: The database session.
        task_id: The UUID of the task to update.
        title: New title (optional).
        description: New description (optional).
        priority: New priority (optional).
        tags: New tag list (optional).
        due_date: New due date in ISO 8601 (optional).
        status: New status (optional).

    Returns:
        A string confirming the update, or a not-found message.
    """
    # Build kwargs dict with only the fields that were explicitly provided,
    # so that TaskUpdate.model_dump(exclude_unset=True) works correctly.
    update_kwargs: dict = {}
    if title is not None:
        update_kwargs["title"] = title
    if description is not None:
        update_kwargs["description"] = description
    if priority is not None:
        update_kwargs["priority"] = TaskPriority(priority)
    if tags is not None:
        update_kwargs["tags"] = tags
    if due_date is not None:
        update_kwargs["due_date"] = datetime.fromisoformat(due_date)
    if status is not None:
        update_kwargs["status"] = TaskStatus(status)

    data = TaskUpdate(**update_kwargs)
    task = svc_update_task(session, task_id, data)
    if not task:
        return f"Task not found with ID: {task_id}"
    return (
        f"Task updated: '{task.title}' "
        f"(Status: {task.status.value}, Priority: {task.priority.value})"
    )


def mcp_delete_task(session: Session, *, task_id: str) -> str:
    """Delete a task by ID and return confirmation.

    Args:
        session: The database session.
        task_id: The UUID of the task to delete.

    Returns:
        A string confirming deletion, or a not-found message.
    """
    success = svc_delete_task(session, task_id)
    if not success:
        return f"Task not found with ID: {task_id}"
    return f"Task deleted successfully (ID: {task_id})"


def mcp_complete_task(session: Session, *, task_id: str) -> str:
    """Toggle a task's completion status and return confirmation.

    For recurring tasks, completing them auto-creates the next occurrence.

    Args:
        session: The database session.
        task_id: The UUID of the task to toggle.

    Returns:
        A string describing the new status, or a not-found message.
    """
    task = svc_toggle_complete(session, task_id)
    if not task:
        return f"Task not found with ID: {task_id}"
    return f"Task '{task.title}' marked as {task.status.value}"


# ---------------------------------------------------------------------------
# FastMCP decorated tools (manage their own DB session via get_session_sync)
# ---------------------------------------------------------------------------


@mcp_server.tool()
async def create_task(
    title: str,
    description: Optional[str] = None,
    priority: Optional[str] = "medium",
    tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
) -> str:
    """Create a new task with the given details.

    Args:
        title: The task title (required, max 200 chars).
        description: Optional detailed description of the task.
        priority: Task priority level - 'low', 'medium', or 'high'.
        tags: Optional list of tag labels (e.g., ['work', 'urgent']).
        due_date: Optional due date in ISO 8601 format.
        recurrence_rule: Optional recurrence rule ('daily', 'weekly', 'monthly', 'yearly').

    Returns:
        A human-readable string confirming task creation.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_create_task(
            session,
            title=title,
            description=description or "",
            priority=priority or "medium",
            tags=tags,
            due_date=due_date,
            recurrence_rule=recurrence_rule,
        )
    finally:
        session.close()


@mcp_server.tool()
async def list_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: Optional[str] = None,
    tag: Optional[str] = None,
) -> str:
    """List tasks with optional filtering and sorting.

    Args:
        status: Filter by status ('pending', 'in_progress', 'completed').
        priority: Filter by priority ('low', 'medium', 'high').
        search: Keyword search across title and description.
        sort_by: Sort field ('due_date', 'priority', 'created_at', 'title').
        tag: Filter by a specific tag name.

    Returns:
        A formatted string listing matching tasks with their details.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_list_tasks(
            session,
            status=status,
            priority=priority,
            search=search,
            sort_by=sort_by or "created_at",
            tag=tag,
        )
    finally:
        session.close()


@mcp_server.tool()
async def get_task(task_id: str) -> str:
    """Retrieve a single task by its ID.

    Args:
        task_id: The UUID of the task to retrieve.

    Returns:
        A detailed string with the task's fields, or a not-found message.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_get_task(session, task_id=task_id)
    finally:
        session.close()


@mcp_server.tool()
async def update_task(
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[list[str]] = None,
    due_date: Optional[str] = None,
    recurrence_rule: Optional[str] = None,
) -> str:
    """Update an existing task with the provided fields.

    Args:
        task_id: The UUID of the task to update.
        title: New title for the task.
        description: New description for the task.
        status: New status ('pending', 'in_progress', 'completed').
        priority: New priority ('low', 'medium', 'high').
        tags: New list of tag labels.
        due_date: New due date in ISO 8601 format.
        recurrence_rule: New recurrence rule.

    Returns:
        A string confirming the update, or a not-found message.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_update_task(
            session,
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            due_date=due_date,
            status=status,
        )
    finally:
        session.close()


@mcp_server.tool()
async def delete_task(task_id: str) -> str:
    """Delete a task by its ID.

    Args:
        task_id: The UUID of the task to delete.

    Returns:
        A string confirming deletion, or a not-found message.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_delete_task(session, task_id=task_id)
    finally:
        session.close()


@mcp_server.tool()
async def complete_task(task_id: str) -> str:
    """Toggle the completion status of a task.

    If the task is pending/in-progress, marks it as completed.
    If already completed, reverts it to pending.
    For recurring tasks, auto-creates the next occurrence upon completion.

    Args:
        task_id: The UUID of the task to toggle.

    Returns:
        A string describing the new status, or a not-found message.
    """
    from app.db import get_session_sync

    session = get_session_sync()
    try:
        return mcp_complete_task(session, task_id=task_id)
    finally:
        session.close()
