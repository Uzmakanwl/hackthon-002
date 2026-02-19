# Phase 2: Full-Stack Web Application — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a full-stack todo app with a Next.js frontend and FastAPI backend connected to Neon DB (PostgreSQL), supporting all CRUD, search/filter/sort, recurring tasks, due dates, and browser reminders.

**Architecture:** FastAPI backend with SQLModel ORM serving a RESTful API. Next.js 14 App Router frontend with Tailwind CSS. Alembic manages DB migrations. Service layer separates business logic from route handlers. Centralized API client on the frontend.

**Tech Stack:** Python 3.12+, FastAPI, SQLModel, Alembic, Neon DB (PostgreSQL), Next.js 14, TypeScript (strict), Tailwind CSS, pytest, httpx

---

## Task 1: Backend — Config and Database Connection

**Files:**
- Create: `phase-2-fullstack/backend/app/config.py`
- Create: `phase-2-fullstack/backend/app/db.py`
- Test: `phase-2-fullstack/backend/tests/test_db.py`

**Step 1: Write the failing test**

```python
# tests/test_db.py
import pytest
from app.config import get_settings


class TestConfig:
    def test_settings_loads(self):
        settings = get_settings()
        assert settings.DATABASE_URL is not None
        assert settings.CORS_ORIGINS is not None

    def test_database_url_is_string(self):
        settings = get_settings()
        assert isinstance(settings.DATABASE_URL, str)
```

**Step 2: Run test to verify it fails**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_db.py -v`
Expected: FAIL — ImportError

**Step 3: Implement config.py and db.py**

```python
# app/config.py
"""Application configuration loaded from environment variables."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment."""

    def __init__(self) -> None:
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
```

```python
# app/db.py
"""Database engine and session management."""

from collections.abc import AsyncGenerator

from sqlmodel import SQLModel, create_engine, Session

from app.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL, echo=False)


def create_db_and_tables() -> None:
    """Create all SQLModel tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """Yield a database session for FastAPI dependency injection."""
    with Session(engine) as session:
        yield session
```

**Step 4: Run test to verify it passes**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_db.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add phase-2-fullstack/backend/app/config.py phase-2-fullstack/backend/app/db.py phase-2-fullstack/backend/tests/test_db.py
git commit -m "phase-2: feat: add config and database connection layer"
```

---

## Task 2: Backend — SQLModel Task Model

**Files:**
- Create: `phase-2-fullstack/backend/app/models.py`
- Test: `phase-2-fullstack/backend/tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from datetime import datetime
from app.models import Task, TaskStatus, TaskPriority


class TestTaskModel:
    def test_task_creation_defaults(self):
        task = Task(title="Test task")
        assert task.title == "Test task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.is_recurring is False

    def test_task_status_enum(self):
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.IN_PROGRESS == "in_progress"
        assert TaskStatus.COMPLETED == "completed"

    def test_task_priority_enum(self):
        assert TaskPriority.LOW == "low"
        assert TaskPriority.MEDIUM == "medium"
        assert TaskPriority.HIGH == "high"
```

**Step 2: Run test to verify it fails**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_models.py -v`
Expected: FAIL

**Step 3: Implement models.py**

```python
# app/models.py
"""SQLModel table definitions for the Task entity."""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON


class TaskStatus(str, Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, Enum):
    """Task priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(SQLModel, table=True):
    """Task database table model."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
    )
    title: str = Field(max_length=200, nullable=False)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM)
    tags: list[str] = Field(default=[], sa_column=Column(JSON, default=[]))
    due_date: Optional[datetime] = Field(default=None)
    reminder_at: Optional[datetime] = Field(default=None)
    is_recurring: bool = Field(default=False)
    recurrence_rule: Optional[str] = Field(default=None, max_length=20)
    next_occurrence: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = Field(default=None)
```

**Step 4: Run test to verify it passes**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_models.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add phase-2-fullstack/backend/app/models.py phase-2-fullstack/backend/tests/test_models.py
git commit -m "phase-2: feat: add SQLModel Task table with enums"
```

---

## Task 3: Backend — Pydantic Schemas

**Files:**
- Create: `phase-2-fullstack/backend/app/schemas.py`

**Step 1: Implement schemas.py**

```python
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
```

**Step 2: Commit**

```bash
git add phase-2-fullstack/backend/app/schemas.py
git commit -m "phase-2: feat: add Pydantic request/response schemas"
```

---

## Task 4: Backend — Task Service (Business Logic)

**Files:**
- Create: `phase-2-fullstack/backend/app/services/task_service.py`
- Create: `phase-2-fullstack/backend/app/services/recurrence_service.py`
- Test: `phase-2-fullstack/backend/tests/test_task_service.py`

**Step 1: Write the failing test**

```python
# tests/test_task_service.py
import pytest
from sqlmodel import SQLModel, create_engine, Session
from app.models import Task, TaskStatus, TaskPriority
from app.services.task_service import (
    create_task, get_task, list_tasks, update_task, delete_task, toggle_complete,
)
from app.schemas import TaskCreate, TaskUpdate


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


class TestCreateTask:
    def test_create_basic(self, session):
        data = TaskCreate(title="Buy groceries")
        task = create_task(session, data)
        assert task.title == "Buy groceries"
        assert task.status == TaskStatus.PENDING

    def test_create_with_all_fields(self, session):
        data = TaskCreate(
            title="Review PR",
            description="Auth module",
            priority=TaskPriority.HIGH,
            tags=["work"],
        )
        task = create_task(session, data)
        assert task.priority == TaskPriority.HIGH
        assert task.tags == ["work"]


class TestGetTask:
    def test_get_existing(self, session):
        data = TaskCreate(title="Test")
        created = create_task(session, data)
        task = get_task(session, created.id)
        assert task is not None
        assert task.title == "Test"

    def test_get_nonexistent_returns_none(self, session):
        assert get_task(session, "fake-id") is None


class TestListTasks:
    def test_list_empty(self, session):
        tasks, total = list_tasks(session)
        assert tasks == []
        assert total == 0

    def test_list_with_tasks(self, session):
        create_task(session, TaskCreate(title="Task 1"))
        create_task(session, TaskCreate(title="Task 2"))
        tasks, total = list_tasks(session)
        assert total == 2

    def test_filter_by_status(self, session):
        create_task(session, TaskCreate(title="Pending"))
        t = create_task(session, TaskCreate(title="Done"))
        toggle_complete(session, t.id)
        tasks, total = list_tasks(session, status=TaskStatus.COMPLETED)
        assert total == 1
        assert tasks[0].title == "Done"

    def test_filter_by_priority(self, session):
        create_task(session, TaskCreate(title="High", priority=TaskPriority.HIGH))
        create_task(session, TaskCreate(title="Low", priority=TaskPriority.LOW))
        tasks, total = list_tasks(session, priority=TaskPriority.HIGH)
        assert total == 1

    def test_search_by_keyword(self, session):
        create_task(session, TaskCreate(title="Buy groceries"))
        create_task(session, TaskCreate(title="Review PR"))
        tasks, total = list_tasks(session, search="groceries")
        assert total == 1

    def test_sort_by_title(self, session):
        create_task(session, TaskCreate(title="Charlie"))
        create_task(session, TaskCreate(title="Alpha"))
        tasks, _ = list_tasks(session, sort_by="title", sort_order="asc")
        assert tasks[0].title == "Alpha"


class TestUpdateTask:
    def test_update_title(self, session):
        t = create_task(session, TaskCreate(title="Original"))
        updated = update_task(session, t.id, TaskUpdate(title="Updated"))
        assert updated.title == "Updated"

    def test_update_nonexistent_returns_none(self, session):
        assert update_task(session, "fake-id", TaskUpdate(title="X")) is None


class TestDeleteTask:
    def test_delete_existing(self, session):
        t = create_task(session, TaskCreate(title="Delete me"))
        assert delete_task(session, t.id) is True
        assert get_task(session, t.id) is None

    def test_delete_nonexistent(self, session):
        assert delete_task(session, "fake-id") is False


class TestToggleComplete:
    def test_toggle_to_completed(self, session):
        t = create_task(session, TaskCreate(title="Toggle"))
        toggled = toggle_complete(session, t.id)
        assert toggled.status == TaskStatus.COMPLETED
        assert toggled.completed_at is not None

    def test_toggle_back_to_pending(self, session):
        t = create_task(session, TaskCreate(title="Toggle"))
        toggle_complete(session, t.id)
        toggled = toggle_complete(session, t.id)
        assert toggled.status == TaskStatus.PENDING
```

**Step 2: Run test to verify it fails**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_task_service.py -v`
Expected: FAIL — ImportError

**Step 3: Implement task_service.py**

```python
# app/services/task_service.py
"""Business logic for task CRUD operations."""

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from app.models import Task, TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate


def create_task(session: Session, data: TaskCreate) -> Task:
    """Create a new task and persist to DB."""
    task = Task(**data.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_task(session: Session, task_id: str) -> Task | None:
    """Retrieve a task by ID."""
    return session.get(Task, task_id)


def list_tasks(
    session: Session,
    *,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    search: Optional[str] = None,
    tag: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[Task], int]:
    """List tasks with filtering, searching, and sorting.

    Returns (tasks, total_count).
    """
    statement = select(Task)

    if status:
        statement = statement.where(Task.status == status)
    if priority:
        statement = statement.where(Task.priority == priority)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(
            Task.title.ilike(pattern) | Task.description.ilike(pattern)
        )

    # Sorting
    sort_column = getattr(Task, sort_by, Task.created_at)
    if sort_order == "asc":
        statement = statement.order_by(sort_column.asc())
    else:
        statement = statement.order_by(sort_column.desc())

    tasks = session.exec(statement).all()

    # Tag filtering (post-query since tags is JSON)
    if tag:
        tasks = [t for t in tasks if tag.lower() in [tg.lower() for tg in (t.tags or [])]]

    return list(tasks), len(tasks)


def update_task(
    session: Session,
    task_id: str,
    data: TaskUpdate,
) -> Task | None:
    """Partially update a task."""
    task = session.get(Task, task_id)
    if not task:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: str) -> bool:
    """Delete a task by ID."""
    task = session.get(Task, task_id)
    if not task:
        return False
    session.delete(task)
    session.commit()
    return True


def toggle_complete(session: Session, task_id: str) -> Task | None:
    """Toggle task completion status."""
    task = session.get(Task, task_id)
    if not task:
        return None

    if task.status == TaskStatus.COMPLETED:
        task.status = TaskStatus.PENDING
        task.completed_at = None
    else:
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task
```

**Step 4: Implement recurrence_service.py**

```python
# app/services/recurrence_service.py
"""Recurrence logic for auto-scheduling recurring tasks."""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from app.models import Task, TaskStatus


def calculate_next_occurrence(current_due: datetime | None, rule: str) -> datetime:
    """Calculate the next due date from a recurrence rule."""
    base = current_due or datetime.utcnow()
    match rule:
        case "daily":
            return base + timedelta(days=1)
        case "weekly":
            return base + timedelta(weeks=1)
        case "monthly":
            return base + relativedelta(months=1)
        case "yearly":
            return base + relativedelta(years=1)
        case _:
            raise ValueError(f"Unsupported recurrence rule: {rule}")


def handle_recurrence_on_complete(session: Session, task: Task) -> Task | None:
    """If task is recurring, create the next occurrence."""
    if not task.is_recurring or not task.recurrence_rule:
        return None

    next_due = calculate_next_occurrence(task.due_date, task.recurrence_rule)
    clone = Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags) if task.tags else [],
        due_date=next_due,
        is_recurring=True,
        recurrence_rule=task.recurrence_rule,
    )
    session.add(clone)
    session.commit()
    session.refresh(clone)
    return clone
```

**Step 5: Run test to verify it passes**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_task_service.py -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add phase-2-fullstack/backend/app/services/
git add phase-2-fullstack/backend/tests/test_task_service.py
git commit -m "phase-2: feat: add task service with CRUD, filter, sort, search"
```

---

## Task 5: Backend — FastAPI Routes

**Files:**
- Create: `phase-2-fullstack/backend/app/routers/tasks.py`
- Create: `phase-2-fullstack/backend/app/main.py`
- Test: `phase-2-fullstack/backend/tests/test_tasks_api.py`

**Step 1: Write the failing test**

```python
# tests/test_tasks_api.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from app.main import app
from app.db import get_session


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestCreateTask:
    def test_create_task(self, client):
        response = client.post("/api/tasks", json={"title": "Buy groceries"})
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Buy groceries"
        assert data["status"] == "pending"

    def test_create_task_missing_title(self, client):
        response = client.post("/api/tasks", json={})
        assert response.status_code == 422


class TestGetTasks:
    def test_list_empty(self, client):
        response = client.get("/api/tasks")
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []
        assert data["total"] == 0

    def test_list_with_tasks(self, client):
        client.post("/api/tasks", json={"title": "Task 1"})
        client.post("/api/tasks", json={"title": "Task 2"})
        response = client.get("/api/tasks")
        assert response.json()["total"] == 2

    def test_get_single_task(self, client):
        create_resp = client.post("/api/tasks", json={"title": "Test"})
        task_id = create_resp.json()["id"]
        response = client.get(f"/api/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Test"

    def test_get_nonexistent_404(self, client):
        response = client.get("/api/tasks/fake-id")
        assert response.status_code == 404


class TestUpdateTask:
    def test_patch_title(self, client):
        resp = client.post("/api/tasks", json={"title": "Original"})
        task_id = resp.json()["id"]
        response = client.patch(f"/api/tasks/{task_id}", json={"title": "Updated"})
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_patch_nonexistent_404(self, client):
        response = client.patch("/api/tasks/fake-id", json={"title": "X"})
        assert response.status_code == 404


class TestDeleteTask:
    def test_delete_existing(self, client):
        resp = client.post("/api/tasks", json={"title": "Delete me"})
        task_id = resp.json()["id"]
        response = client.delete(f"/api/tasks/{task_id}")
        assert response.status_code == 204

    def test_delete_nonexistent_404(self, client):
        response = client.delete("/api/tasks/fake-id")
        assert response.status_code == 404


class TestToggleComplete:
    def test_toggle_complete(self, client):
        resp = client.post("/api/tasks", json={"title": "Toggle"})
        task_id = resp.json()["id"]
        response = client.post(f"/api/tasks/{task_id}/complete")
        assert response.status_code == 200
        assert response.json()["status"] == "completed"


class TestHealthCheck:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
```

**Step 2: Run test to verify it fails**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_tasks_api.py -v`
Expected: FAIL

**Step 3: Implement routers/tasks.py and main.py**

```python
# app/routers/tasks.py
"""Task CRUD API endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from app.db import get_session
from app.models import TaskStatus, TaskPriority
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
from app.services.task_service import (
    create_task, get_task, list_tasks, update_task, delete_task, toggle_complete,
)

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=201)
def create(data: TaskCreate, session: Session = Depends(get_session)):
    """Create a new task."""
    task = create_task(session, data)
    return task


@router.get("", response_model=TaskListResponse)
def list_all(
    status: Optional[TaskStatus] = Query(None),
    priority: Optional[TaskPriority] = Query(None),
    search: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    session: Session = Depends(get_session),
):
    """List tasks with optional filtering, search, and sort."""
    tasks, total = list_tasks(
        session,
        status=status,
        priority=priority,
        search=search,
        tag=tag,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return TaskListResponse(tasks=tasks, total=total)


@router.get("/{task_id}", response_model=TaskResponse)
def get_one(task_id: str, session: Session = Depends(get_session)):
    """Get a single task by ID."""
    task = get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update(task_id: str, data: TaskUpdate, session: Session = Depends(get_session)):
    """Partially update a task."""
    task = update_task(session, task_id, data)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=204)
def delete(task_id: str, session: Session = Depends(get_session)):
    """Delete a task."""
    success = delete_task(session, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return Response(status_code=204)


@router.post("/{task_id}/complete", response_model=TaskResponse)
def complete(task_id: str, session: Session = Depends(get_session)):
    """Toggle task completion status."""
    task = toggle_complete(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
```

```python
# app/main.py
"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db import create_db_and_tables
from app.routers.tasks import router as tasks_router

settings = get_settings()

app = FastAPI(title="Todo API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)


@app.on_event("startup")
def on_startup():
    """Create tables on app startup."""
    create_db_and_tables()


@app.get("/health")
def health_check():
    """Health check endpoint for K8s probes."""
    return {"status": "ok"}
```

**Step 4: Run test to verify it passes**

Run: `cd phase-2-fullstack/backend && python -m pytest tests/test_tasks_api.py -v`
Expected: All tests PASS

**Step 5: Commit**

```bash
git add phase-2-fullstack/backend/app/routers/tasks.py phase-2-fullstack/backend/app/main.py
git add phase-2-fullstack/backend/tests/test_tasks_api.py
git commit -m "phase-2: feat: add FastAPI routes with full CRUD + health check"
```

---

## Task 6: Backend — Alembic Migration Setup

**Files:**
- Create: `phase-2-fullstack/backend/alembic.ini`
- Create: `phase-2-fullstack/backend/alembic/env.py`

**Step 1: Initialize Alembic**

Run: `cd phase-2-fullstack/backend && alembic init alembic`

**Step 2: Configure env.py to use SQLModel metadata**

Update `alembic/env.py` to import `app.models` and set `target_metadata = SQLModel.metadata`.

**Step 3: Create initial migration**

Run: `cd phase-2-fullstack/backend && alembic revision --autogenerate -m "create task table"`

**Step 4: Apply migration**

Run: `cd phase-2-fullstack/backend && alembic upgrade head`

**Step 5: Commit**

```bash
git add phase-2-fullstack/backend/alembic* phase-2-fullstack/backend/alembic.ini
git commit -m "phase-2: chore: add Alembic migration for task table"
```

---

## Task 7: Frontend — TypeScript Types and API Client

**Files:**
- Create: `phase-2-fullstack/frontend/src/types/task.ts`
- Create: `phase-2-fullstack/frontend/src/lib/api.ts`

**Step 1: Implement types/task.ts**

```typescript
// src/types/task.ts

export type TaskStatus = "pending" | "in_progress" | "completed";
export type TaskPriority = "low" | "medium" | "high";

export interface Task {
  id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  tags: string[];
  due_date: string | null;
  reminder_at: string | null;
  is_recurring: boolean;
  recurrence_rule: string | null;
  next_occurrence: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: TaskPriority;
  tags?: string[];
  due_date?: string;
  reminder_at?: string;
  is_recurring?: boolean;
  recurrence_rule?: string;
}

export interface UpdateTaskInput {
  title?: string;
  description?: string;
  status?: TaskStatus;
  priority?: TaskPriority;
  tags?: string[];
  due_date?: string | null;
  reminder_at?: string | null;
  is_recurring?: boolean;
  recurrence_rule?: string | null;
}

export interface TaskListResponse {
  tasks: Task[];
  total: number;
}

export interface TaskFilters {
  status?: TaskStatus;
  priority?: TaskPriority;
  search?: string;
  tag?: string;
  sort_by?: string;
  sort_order?: "asc" | "desc";
}
```

**Step 2: Implement lib/api.ts**

```typescript
// src/lib/api.ts

import type {
  Task,
  CreateTaskInput,
  UpdateTaskInput,
  TaskListResponse,
  TaskFilters,
} from "@/types/task";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}

export async function fetchTasks(filters?: TaskFilters): Promise<TaskListResponse> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== "") params.set(key, value);
    });
  }
  const query = params.toString();
  return fetchAPI<TaskListResponse>(`/api/tasks${query ? `?${query}` : ""}`);
}

export async function fetchTask(id: string): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}`);
}

export async function createTask(data: CreateTaskInput): Promise<Task> {
  return fetchAPI<Task>("/api/tasks", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateTask(id: string, data: UpdateTaskInput): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteTask(id: string): Promise<void> {
  return fetchAPI<void>(`/api/tasks/${id}`, { method: "DELETE" });
}

export async function toggleComplete(id: string): Promise<Task> {
  return fetchAPI<Task>(`/api/tasks/${id}/complete`, { method: "POST" });
}
```

**Step 3: Commit**

```bash
git add phase-2-fullstack/frontend/src/types/task.ts phase-2-fullstack/frontend/src/lib/api.ts
git commit -m "phase-2: feat: add TypeScript types and API client"
```

---

## Task 8: Frontend — Custom Hooks

**Files:**
- Create: `phase-2-fullstack/frontend/src/hooks/useTasks.ts`
- Create: `phase-2-fullstack/frontend/src/hooks/useDebounce.ts`

**Step 1: Implement hooks**

```typescript
// src/hooks/useDebounce.ts
"use client";
import { useState, useEffect } from "react";

export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedValue(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debouncedValue;
}
```

```typescript
// src/hooks/useTasks.ts
"use client";
import { useState, useEffect, useCallback } from "react";
import type { Task, TaskFilters, TaskListResponse } from "@/types/task";
import { fetchTasks } from "@/lib/api";

export function useTasks(filters?: TaskFilters) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadTasks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: TaskListResponse = await fetchTasks(filters);
      setTasks(data.tasks);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadTasks();
  }, [loadTasks]);

  return { tasks, total, loading, error, refetch: loadTasks };
}
```

**Step 2: Commit**

```bash
git add phase-2-fullstack/frontend/src/hooks/
git commit -m "phase-2: feat: add useTasks and useDebounce hooks"
```

---

## Task 9: Frontend — UI Components

**Files:**
- Create: `phase-2-fullstack/frontend/src/components/TaskCard.tsx`
- Create: `phase-2-fullstack/frontend/src/components/TaskForm.tsx`
- Create: `phase-2-fullstack/frontend/src/components/TaskList.tsx`
- Create: `phase-2-fullstack/frontend/src/components/FilterBar.tsx`
- Create: `phase-2-fullstack/frontend/src/components/SearchInput.tsx`

**Step 1: Implement components**

Build each component with Tailwind CSS styling:

- **TaskCard**: Displays task title, status icon, priority badge, tags, due date. Has toggle complete button and delete button.
- **TaskForm**: Modal/form for creating/editing tasks. Fields: title, description, priority select, tags input, due date picker, reminder picker, recurring checkbox + rule select.
- **TaskList**: Maps over tasks and renders TaskCard components. Shows loading/empty states.
- **FilterBar**: Dropdowns for status, priority, tag. Sort selector.
- **SearchInput**: Text input with debounced onChange using useDebounce hook.

Each component should be a `"use client"` component with proper TypeScript types.

**Step 2: Commit**

```bash
git add phase-2-fullstack/frontend/src/components/
git commit -m "phase-2: feat: add TaskCard, TaskForm, TaskList, FilterBar, SearchInput components"
```

---

## Task 10: Frontend — Main Page Assembly

**Files:**
- Modify: `phase-2-fullstack/frontend/src/app/page.tsx`
- Modify: `phase-2-fullstack/frontend/src/app/layout.tsx`

**Step 1: Wire everything together in page.tsx**

The main page should:
- Use `useTasks` hook with filter state
- Render SearchInput + FilterBar at top
- Render TaskList in the center
- Have a "Add Task" button that opens TaskForm
- Show toast notifications on CRUD actions
- Responsive layout with Tailwind

**Step 2: Manual smoke test**

Run backend: `cd phase-2-fullstack/backend && uvicorn app.main:app --reload`
Run frontend: `cd phase-2-fullstack/frontend && npm run dev`
Test: Create, view, update, delete, toggle, search, filter, sort tasks

**Step 3: Commit**

```bash
git add phase-2-fullstack/frontend/src/app/
git commit -m "phase-2: feat: assemble main page with all components"
```

---

## Task 11: README and Final Polish

**Files:**
- Create: `phase-2-fullstack/README.md`

**Step 1: Write comprehensive README**

Cover:
- Architecture diagram (Mermaid: Frontend → API → Service → DB)
- Backend setup (venv, pip install, .env, alembic upgrade head, uvicorn)
- Frontend setup (npm install, .env.local, npm run dev)
- API documentation (link to /docs Swagger)
- Environment variables table
- Testing instructions
- Feature checklist

**Step 2: Run all backend tests**

Run: `cd phase-2-fullstack/backend && python -m pytest -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add phase-2-fullstack/README.md
git commit -m "phase-2: docs: add README with setup, API docs, and architecture"
```

---

## Summary

| Task | What | Tests |
|------|------|-------|
| 1 | Config + DB connection | 2 |
| 2 | SQLModel Task model | 3 |
| 3 | Pydantic schemas | — |
| 4 | Task service (business logic) | 14 |
| 5 | FastAPI routes + main | 12 |
| 6 | Alembic migrations | — |
| 7 | TS types + API client | — |
| 8 | Custom hooks | — |
| 9 | UI components | — |
| 10 | Main page assembly | Manual |
| 11 | README + polish | — |

**Total: ~31 automated backend tests + manual frontend testing across 11 tasks.**
