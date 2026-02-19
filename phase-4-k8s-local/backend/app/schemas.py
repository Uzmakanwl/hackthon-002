# app/schemas.py
"""Pydantic request/response schemas for the Task API."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    tags: list[str] = []
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None


class TaskUpdate(BaseModel):
    """Schema for partially updating a task. All fields optional."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    tags: Optional[list[str]] = None
    due_date: Optional[datetime] = None
    reminder_at: Optional[datetime] = None
    is_recurring: Optional[bool] = None
    recurrence_rule: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for a single task in responses."""
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    tags: list[str]
    due_date: Optional[datetime]
    reminder_at: Optional[datetime]
    is_recurring: bool
    recurrence_rule: Optional[str]
    next_occurrence: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for paginated task list responses."""
    tasks: list[TaskResponse]
    total: int
