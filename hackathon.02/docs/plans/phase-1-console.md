# Phase 1: In-Memory Console Todo App — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a fully-featured Python CLI todo app with in-memory storage, supporting CRUD, search/filter/sort, recurring tasks, and due dates.

**Architecture:** Menu-driven CLI loop dispatching to command handlers. Tasks stored in a dict keyed by UUID string. Dataclass-based model with enums for status/priority. Recurrence logic in a dedicated module calculates next occurrence using dateutil.

**Tech Stack:** Python 3.12+, dataclasses, enum, uuid, datetime, python-dateutil, pytest

---

## Task 1: Models — Task Dataclass and Enums

**Files:**
- Create: `phase-1-console/src/models.py`
- Test: `phase-1-console/tests/test_models.py`

**Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule


class TestTaskModel:
    def test_task_creation_defaults(self):
        task = Task(title="Buy groceries")
        assert task.title == "Buy groceries"
        assert task.description == ""
        assert task.status == Status.PENDING
        assert task.priority == Priority.MEDIUM
        assert task.tags == []
        assert task.due_date is None
        assert task.reminder_at is None
        assert task.is_recurring is False
        assert task.recurrence_rule is None
        assert task.next_occurrence is None
        assert task.completed_at is None
        assert task.id is not None
        assert task.created_at is not None
        assert task.updated_at is not None

    def test_task_creation_full(self):
        now = datetime.now()
        task = Task(
            title="Review PR",
            description="Check the auth module PR",
            status=Status.IN_PROGRESS,
            priority=Priority.HIGH,
            tags=["work", "urgent"],
            due_date=now,
            is_recurring=True,
            recurrence_rule=RecurrenceRule.WEEKLY,
        )
        assert task.title == "Review PR"
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]
        assert task.is_recurring is True
        assert task.recurrence_rule == RecurrenceRule.WEEKLY

    def test_task_id_is_unique(self):
        t1 = Task(title="Task 1")
        t2 = Task(title="Task 2")
        assert t1.id != t2.id

    def test_status_enum_values(self):
        assert Status.PENDING.value == "pending"
        assert Status.IN_PROGRESS.value == "in_progress"
        assert Status.COMPLETED.value == "completed"

    def test_priority_enum_values(self):
        assert Priority.LOW.value == "low"
        assert Priority.MEDIUM.value == "medium"
        assert Priority.HIGH.value == "high"

    def test_recurrence_rule_enum_values(self):
        assert RecurrenceRule.DAILY.value == "daily"
        assert RecurrenceRule.WEEKLY.value == "weekly"
        assert RecurrenceRule.MONTHLY.value == "monthly"
        assert RecurrenceRule.YEARLY.value == "yearly"
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_models.py -v`
Expected: FAIL — ImportError (models not implemented yet)

**Step 3: Implement models.py**

```python
# src/models.py
"""Task model and enums for the Todo console app."""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Status(Enum):
    """Task completion status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class Priority(Enum):
    """Task priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecurrenceRule(Enum):
    """Supported recurrence frequencies."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


@dataclass
class Task:
    """Represents a single todo task.

    Args:
        title: Task title (required, max 200 chars).
        description: Optional detailed description (max 2000 chars).
        status: Current status (default: pending).
        priority: Priority level (default: medium).
        tags: Free-form labels.
        due_date: Optional deadline.
        reminder_at: Optional reminder timestamp.
        is_recurring: Whether this task recurs.
        recurrence_rule: Frequency if recurring.
        next_occurrence: Auto-calculated next due date.
    """
    title: str
    description: str = ""
    status: Status = Status.PENDING
    priority: Priority = Priority.MEDIUM
    tags: list[str] = field(default_factory=list)
    due_date: datetime | None = None
    reminder_at: datetime | None = None
    is_recurring: bool = False
    recurrence_rule: RecurrenceRule | None = None
    next_occurrence: datetime | None = None
    completed_at: datetime | None = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_models.py -v`
Expected: All 6 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/models.py phase-1-console/tests/test_models.py
git commit -m "phase-1: feat: add Task dataclass with Status, Priority, RecurrenceRule enums"
```

---

## Task 2: Store — In-Memory Task Storage

**Files:**
- Create: `phase-1-console/src/store.py`
- Test: `phase-1-console/tests/test_store.py`

**Step 1: Write the failing test**

```python
# tests/test_store.py
import pytest
from src.models import Task, Status, Priority
from src.store import TaskStore


class TestTaskStore:
    def setup_method(self):
        self.store = TaskStore()

    def test_add_and_get(self):
        task = Task(title="Test task")
        self.store.add(task)
        retrieved = self.store.get(task.id)
        assert retrieved is not None
        assert retrieved.title == "Test task"

    def test_get_nonexistent_returns_none(self):
        assert self.store.get("nonexistent-id") is None

    def test_get_all_empty(self):
        assert self.store.get_all() == []

    def test_get_all_returns_all(self):
        t1 = Task(title="Task 1")
        t2 = Task(title="Task 2")
        self.store.add(t1)
        self.store.add(t2)
        all_tasks = self.store.get_all()
        assert len(all_tasks) == 2

    def test_delete_existing(self):
        task = Task(title="To delete")
        self.store.add(task)
        result = self.store.delete(task.id)
        assert result is True
        assert self.store.get(task.id) is None

    def test_delete_nonexistent(self):
        result = self.store.delete("nonexistent-id")
        assert result is False

    def test_update_existing(self):
        task = Task(title="Original")
        self.store.add(task)
        task.title = "Updated"
        self.store.update(task)
        retrieved = self.store.get(task.id)
        assert retrieved.title == "Updated"

    def test_update_nonexistent_returns_false(self):
        task = Task(title="Ghost")
        result = self.store.update(task)
        assert result is False

    def test_count(self):
        self.store.add(Task(title="One"))
        self.store.add(Task(title="Two"))
        assert self.store.count() == 2
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_store.py -v`
Expected: FAIL — ImportError

**Step 3: Implement store.py**

```python
# src/store.py
"""In-memory task storage using a dictionary."""

from datetime import datetime
from src.models import Task


class TaskStore:
    """Stores tasks in memory, keyed by task ID.

    Args:
        None — initializes with an empty dict.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def add(self, task: Task) -> Task:
        """Add a task to the store. Returns the added task."""
        self._tasks[task.id] = task
        return task

    def get(self, task_id: str) -> Task | None:
        """Retrieve a task by ID. Returns None if not found."""
        return self._tasks.get(task_id)

    def get_all(self) -> list[Task]:
        """Return all tasks as a list."""
        return list(self._tasks.values())

    def update(self, task: Task) -> bool:
        """Update an existing task. Returns False if task not found."""
        if task.id not in self._tasks:
            return False
        task.updated_at = datetime.now()
        self._tasks[task.id] = task
        return True

    def delete(self, task_id: str) -> bool:
        """Delete a task by ID. Returns False if not found."""
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True

    def count(self) -> int:
        """Return the number of tasks in the store."""
        return len(self._tasks)
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_store.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/store.py phase-1-console/tests/test_store.py
git commit -m "phase-1: feat: add in-memory TaskStore with CRUD operations"
```

---

## Task 3: Utils — Validators, Formatters, Parsers

**Files:**
- Create: `phase-1-console/src/utils.py`
- Test: `phase-1-console/tests/test_utils.py`

**Step 1: Write the failing test**

```python
# tests/test_utils.py
import pytest
from datetime import datetime
from src.models import Task, Status, Priority
from src.utils import (
    validate_title,
    validate_priority_input,
    validate_status_input,
    format_task_summary,
    format_task_detail,
    parse_date_input,
    parse_tags_input,
)


class TestValidators:
    def test_validate_title_valid(self):
        assert validate_title("Buy groceries") == "Buy groceries"

    def test_validate_title_strips_whitespace(self):
        assert validate_title("  Buy groceries  ") == "Buy groceries"

    def test_validate_title_empty_raises(self):
        with pytest.raises(ValueError, match="Title cannot be empty"):
            validate_title("")

    def test_validate_title_too_long_raises(self):
        with pytest.raises(ValueError, match="Title cannot exceed 200 characters"):
            validate_title("a" * 201)

    def test_validate_priority_valid(self):
        assert validate_priority_input("high") == Priority.HIGH
        assert validate_priority_input("LOW") == Priority.LOW
        assert validate_priority_input("Medium") == Priority.MEDIUM

    def test_validate_priority_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid priority"):
            validate_priority_input("urgent")

    def test_validate_status_valid(self):
        assert validate_status_input("pending") == Status.PENDING
        assert validate_status_input("IN_PROGRESS") == Status.IN_PROGRESS
        assert validate_status_input("completed") == Status.COMPLETED

    def test_validate_status_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid status"):
            validate_status_input("done")


class TestParsers:
    def test_parse_date_valid(self):
        result = parse_date_input("2025-12-25 10:00")
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 12

    def test_parse_date_date_only(self):
        result = parse_date_input("2025-12-25")
        assert isinstance(result, datetime)

    def test_parse_date_empty_returns_none(self):
        assert parse_date_input("") is None

    def test_parse_date_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid date format"):
            parse_date_input("not-a-date")

    def test_parse_tags_comma_separated(self):
        assert parse_tags_input("work, home, urgent") == ["work", "home", "urgent"]

    def test_parse_tags_strips_whitespace(self):
        assert parse_tags_input("  work ,  home  ") == ["work", "home"]

    def test_parse_tags_empty_returns_empty(self):
        assert parse_tags_input("") == []

    def test_parse_tags_deduplicates(self):
        assert parse_tags_input("work, work, home") == ["work", "home"]


class TestFormatters:
    def test_format_task_summary(self):
        task = Task(title="Buy groceries", priority=Priority.HIGH, status=Status.PENDING)
        summary = format_task_summary(task)
        assert "Buy groceries" in summary
        assert "HIGH" in summary.upper() or "high" in summary
        assert "PENDING" in summary.upper() or "pending" in summary

    def test_format_task_detail(self):
        task = Task(
            title="Buy groceries",
            description="Milk, eggs, bread",
            priority=Priority.HIGH,
            tags=["home", "errand"],
        )
        detail = format_task_detail(task)
        assert "Buy groceries" in detail
        assert "Milk, eggs, bread" in detail
        assert "home" in detail
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_utils.py -v`
Expected: FAIL — ImportError

**Step 3: Implement utils.py**

```python
# src/utils.py
"""Validators, formatters, and input parsers for the CLI."""

from datetime import datetime
from src.models import Task, Status, Priority


def validate_title(title: str) -> str:
    """Validate and clean a task title.

    Raises:
        ValueError: If title is empty or exceeds 200 chars.
    """
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")
    if len(title) > 200:
        raise ValueError("Title cannot exceed 200 characters")
    return title


def validate_priority_input(value: str) -> Priority:
    """Parse a priority string into a Priority enum.

    Raises:
        ValueError: If value is not a valid priority.
    """
    try:
        return Priority(value.strip().lower())
    except ValueError:
        valid = ", ".join(p.value for p in Priority)
        raise ValueError(f"Invalid priority: '{value}'. Choose from: {valid}")


def validate_status_input(value: str) -> Status:
    """Parse a status string into a Status enum.

    Raises:
        ValueError: If value is not a valid status.
    """
    try:
        return Status(value.strip().lower())
    except ValueError:
        valid = ", ".join(s.value for s in Status)
        raise ValueError(f"Invalid status: '{value}'. Choose from: {valid}")


def parse_date_input(value: str) -> datetime | None:
    """Parse a date string into a datetime object.

    Supports: 'YYYY-MM-DD' and 'YYYY-MM-DD HH:MM'.
    Returns None for empty string.

    Raises:
        ValueError: If the date format is not recognized.
    """
    value = value.strip()
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: '{value}'. Use YYYY-MM-DD or YYYY-MM-DD HH:MM")


def parse_tags_input(value: str) -> list[str]:
    """Parse comma-separated tags into a deduplicated list."""
    value = value.strip()
    if not value:
        return []
    seen: set[str] = set()
    tags: list[str] = []
    for tag in value.split(","):
        tag = tag.strip()
        if tag and tag not in seen:
            seen.add(tag)
            tags.append(tag)
    return tags


def format_task_summary(task: Task) -> str:
    """Format a single-line summary of a task for list views."""
    status_icon = {"pending": "○", "in_progress": "◑", "completed": "●"}
    icon = status_icon.get(task.status.value, "?")
    due = f" | Due: {task.due_date.strftime('%Y-%m-%d')}" if task.due_date else ""
    return f"  {icon} [{task.priority.value.upper()}] {task.title}{due}  (ID: {task.id[:8]})"


def format_task_detail(task: Task) -> str:
    """Format a full detail view of a task."""
    lines = [
        f"{'=' * 50}",
        f"  Title:       {task.title}",
        f"  ID:          {task.id}",
        f"  Status:      {task.status.value}",
        f"  Priority:    {task.priority.value}",
        f"  Description: {task.description or '(none)'}",
        f"  Tags:        {', '.join(task.tags) if task.tags else '(none)'}",
        f"  Due Date:    {task.due_date.strftime('%Y-%m-%d %H:%M') if task.due_date else '(none)'}",
        f"  Reminder:    {task.reminder_at.strftime('%Y-%m-%d %H:%M') if task.reminder_at else '(none)'}",
        f"  Recurring:   {task.recurrence_rule.value if task.is_recurring and task.recurrence_rule else 'No'}",
        f"  Created:     {task.created_at.strftime('%Y-%m-%d %H:%M')}",
        f"  Updated:     {task.updated_at.strftime('%Y-%m-%d %H:%M')}",
        f"  Completed:   {task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else '(none)'}",
        f"{'=' * 50}",
    ]
    return "\n".join(lines)
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_utils.py -v`
Expected: All 17 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/utils.py phase-1-console/tests/test_utils.py
git commit -m "phase-1: feat: add validators, parsers, and formatters"
```

---

## Task 4: Commands — CRUD Operations (Add, View, Update, Delete, Toggle)

**Files:**
- Create: `phase-1-console/src/commands.py`
- Test: `phase-1-console/tests/test_commands.py`

**Step 1: Write the failing test**

```python
# tests/test_commands.py
import pytest
from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule
from src.store import TaskStore
from src.commands import (
    add_task,
    view_all_tasks,
    view_task_detail,
    update_task,
    delete_task,
    toggle_complete,
)


class TestAddTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_add_basic_task(self):
        task = add_task(self.store, title="Buy groceries")
        assert task.title == "Buy groceries"
        assert self.store.count() == 1

    def test_add_task_with_all_fields(self):
        task = add_task(
            self.store,
            title="Review PR",
            description="Auth module changes",
            priority="high",
            tags="work, urgent",
            due_date="2025-12-25 10:00",
            is_recurring=True,
            recurrence_rule="weekly",
        )
        assert task.priority == Priority.HIGH
        assert task.tags == ["work", "urgent"]
        assert task.due_date is not None
        assert task.is_recurring is True

    def test_add_task_empty_title_raises(self):
        with pytest.raises(ValueError):
            add_task(self.store, title="")


class TestDeleteTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_delete_existing(self):
        task = add_task(self.store, title="To delete")
        result = delete_task(self.store, task.id)
        assert result is True
        assert self.store.count() == 0

    def test_delete_nonexistent(self):
        result = delete_task(self.store, "fake-id")
        assert result is False


class TestUpdateTask:
    def setup_method(self):
        self.store = TaskStore()

    def test_update_title(self):
        task = add_task(self.store, title="Original")
        updated = update_task(self.store, task.id, title="Updated")
        assert updated is not None
        assert updated.title == "Updated"

    def test_update_priority(self):
        task = add_task(self.store, title="Test")
        updated = update_task(self.store, task.id, priority="high")
        assert updated.priority == Priority.HIGH

    def test_update_nonexistent_returns_none(self):
        result = update_task(self.store, "fake-id", title="Nope")
        assert result is None


class TestViewTasks:
    def setup_method(self):
        self.store = TaskStore()

    def test_view_all_empty(self):
        tasks = view_all_tasks(self.store)
        assert tasks == []

    def test_view_all_with_tasks(self):
        add_task(self.store, title="Task 1")
        add_task(self.store, title="Task 2")
        tasks = view_all_tasks(self.store)
        assert len(tasks) == 2

    def test_view_detail(self):
        task = add_task(self.store, title="Detailed task")
        detail = view_task_detail(self.store, task.id)
        assert detail is not None
        assert detail.title == "Detailed task"

    def test_view_detail_nonexistent(self):
        assert view_task_detail(self.store, "fake-id") is None


class TestToggleComplete:
    def setup_method(self):
        self.store = TaskStore()

    def test_toggle_to_completed(self):
        task = add_task(self.store, title="Toggle me")
        toggled = toggle_complete(self.store, task.id)
        assert toggled.status == Status.COMPLETED
        assert toggled.completed_at is not None

    def test_toggle_back_to_pending(self):
        task = add_task(self.store, title="Toggle me")
        toggle_complete(self.store, task.id)
        toggled = toggle_complete(self.store, task.id)
        assert toggled.status == Status.PENDING
        assert toggled.completed_at is None

    def test_toggle_nonexistent_returns_none(self):
        result = toggle_complete(self.store, "fake-id")
        assert result is None
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_commands.py -v`
Expected: FAIL — ImportError

**Step 3: Implement commands.py (CRUD portion)**

```python
# src/commands.py
"""Command handlers for CRUD operations, search, filter, and sort."""

from datetime import datetime
from src.models import Task, Status, Priority, RecurrenceRule
from src.store import TaskStore
from src.utils import (
    validate_title,
    validate_priority_input,
    validate_status_input,
    parse_date_input,
    parse_tags_input,
)


def add_task(
    store: TaskStore,
    *,
    title: str,
    description: str = "",
    priority: str = "medium",
    tags: str = "",
    due_date: str = "",
    reminder_at: str = "",
    is_recurring: bool = False,
    recurrence_rule: str = "",
) -> Task:
    """Create and store a new task.

    Args:
        store: The task store.
        title: Task title (required).
        description: Optional description.
        priority: Priority string ('low', 'medium', 'high').
        tags: Comma-separated tag string.
        due_date: Date string 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'.
        reminder_at: Reminder date string.
        is_recurring: Whether the task recurs.
        recurrence_rule: Recurrence frequency string.

    Returns:
        The created Task.

    Raises:
        ValueError: If title is empty or inputs are invalid.
    """
    clean_title = validate_title(title)
    parsed_priority = validate_priority_input(priority)
    parsed_tags = parse_tags_input(tags)
    parsed_due = parse_date_input(due_date)
    parsed_reminder = parse_date_input(reminder_at)
    parsed_rule = RecurrenceRule(recurrence_rule) if recurrence_rule else None

    task = Task(
        title=clean_title,
        description=description.strip(),
        priority=parsed_priority,
        tags=parsed_tags,
        due_date=parsed_due,
        reminder_at=parsed_reminder,
        is_recurring=is_recurring,
        recurrence_rule=parsed_rule,
    )
    store.add(task)
    return task


def view_all_tasks(store: TaskStore) -> list[Task]:
    """Return all tasks from the store."""
    return store.get_all()


def view_task_detail(store: TaskStore, task_id: str) -> Task | None:
    """Return a single task by ID, or None if not found."""
    return store.get(task_id)


def update_task(
    store: TaskStore,
    task_id: str,
    *,
    title: str | None = None,
    description: str | None = None,
    priority: str | None = None,
    tags: str | None = None,
    due_date: str | None = None,
    reminder_at: str | None = None,
    status: str | None = None,
) -> Task | None:
    """Partially update a task's fields.

    Only non-None arguments are applied.
    Returns the updated Task, or None if not found.
    """
    task = store.get(task_id)
    if task is None:
        return None

    if title is not None:
        task.title = validate_title(title)
    if description is not None:
        task.description = description.strip()
    if priority is not None:
        task.priority = validate_priority_input(priority)
    if tags is not None:
        task.tags = parse_tags_input(tags)
    if due_date is not None:
        task.due_date = parse_date_input(due_date)
    if reminder_at is not None:
        task.reminder_at = parse_date_input(reminder_at)
    if status is not None:
        task.status = validate_status_input(status)

    store.update(task)
    return task


def delete_task(store: TaskStore, task_id: str) -> bool:
    """Delete a task by ID. Returns True if deleted, False if not found."""
    return store.delete(task_id)


def toggle_complete(store: TaskStore, task_id: str) -> Task | None:
    """Toggle a task between pending and completed.

    Returns the updated Task, or None if not found.
    """
    task = store.get(task_id)
    if task is None:
        return None

    if task.status == Status.COMPLETED:
        task.status = Status.PENDING
        task.completed_at = None
    else:
        task.status = Status.COMPLETED
        task.completed_at = datetime.now()

    store.update(task)
    return task
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_commands.py -v`
Expected: All 14 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/commands.py phase-1-console/tests/test_commands.py
git commit -m "phase-1: feat: add CRUD command handlers (add, view, update, delete, toggle)"
```

---

## Task 5: Commands — Search, Filter, Sort

**Files:**
- Modify: `phase-1-console/src/commands.py`
- Test: `phase-1-console/tests/test_search_filter_sort.py`

**Step 1: Write the failing test**

```python
# tests/test_search_filter_sort.py
import pytest
from datetime import datetime, timedelta
from src.models import Task, Status, Priority
from src.store import TaskStore
from src.commands import add_task, search_tasks, filter_tasks, sort_tasks


class TestSearchTasks:
    def setup_method(self):
        self.store = TaskStore()
        add_task(self.store, title="Buy groceries", description="Milk and eggs")
        add_task(self.store, title="Review PR", description="Check auth module")
        add_task(self.store, title="Buy birthday gift", description="For mom")

    def test_search_by_title(self):
        results = search_tasks(self.store, keyword="Buy")
        assert len(results) == 2

    def test_search_by_description(self):
        results = search_tasks(self.store, keyword="auth")
        assert len(results) == 1

    def test_search_case_insensitive(self):
        results = search_tasks(self.store, keyword="buy")
        assert len(results) == 2

    def test_search_no_results(self):
        results = search_tasks(self.store, keyword="xyz123")
        assert len(results) == 0

    def test_search_empty_keyword_returns_all(self):
        results = search_tasks(self.store, keyword="")
        assert len(results) == 3


class TestFilterTasks:
    def setup_method(self):
        self.store = TaskStore()
        add_task(self.store, title="High pending", priority="high")
        add_task(self.store, title="Low pending", priority="low")
        add_task(self.store, title="High tagged", priority="high", tags="work")
        t = add_task(self.store, title="Completed", priority="medium")
        from src.commands import toggle_complete
        toggle_complete(self.store, t.id)

    def test_filter_by_status(self):
        results = filter_tasks(self.store, status="completed")
        assert len(results) == 1
        assert results[0].title == "Completed"

    def test_filter_by_priority(self):
        results = filter_tasks(self.store, priority="high")
        assert len(results) == 2

    def test_filter_by_tag(self):
        results = filter_tasks(self.store, tag="work")
        assert len(results) == 1

    def test_filter_combined(self):
        results = filter_tasks(self.store, status="pending", priority="high")
        assert len(results) == 2

    def test_filter_no_criteria_returns_all(self):
        results = filter_tasks(self.store)
        assert len(results) == 4


class TestSortTasks:
    def setup_method(self):
        self.store = TaskStore()
        add_task(self.store, title="Charlie", priority="low")
        add_task(self.store, title="Alpha", priority="high")
        add_task(self.store, title="Bravo", priority="medium")

    def test_sort_alphabetical(self):
        tasks = self.store.get_all()
        sorted_tasks = sort_tasks(tasks, sort_by="title")
        assert sorted_tasks[0].title == "Alpha"
        assert sorted_tasks[1].title == "Bravo"
        assert sorted_tasks[2].title == "Charlie"

    def test_sort_by_priority(self):
        tasks = self.store.get_all()
        sorted_tasks = sort_tasks(tasks, sort_by="priority")
        assert sorted_tasks[0].priority == Priority.HIGH
        assert sorted_tasks[-1].priority == Priority.LOW

    def test_sort_by_created_date(self):
        tasks = self.store.get_all()
        sorted_tasks = sort_tasks(tasks, sort_by="created_at")
        for i in range(len(sorted_tasks) - 1):
            assert sorted_tasks[i].created_at <= sorted_tasks[i + 1].created_at

    def test_sort_descending(self):
        tasks = self.store.get_all()
        sorted_tasks = sort_tasks(tasks, sort_by="title", descending=True)
        assert sorted_tasks[0].title == "Charlie"

    def test_sort_by_due_date_none_last(self):
        add_task(self.store, title="Due task", due_date="2025-12-01")
        tasks = self.store.get_all()
        sorted_tasks = sort_tasks(tasks, sort_by="due_date")
        assert sorted_tasks[0].due_date is not None
        assert sorted_tasks[-1].due_date is None or sorted_tasks[-2].due_date is None
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_search_filter_sort.py -v`
Expected: FAIL — ImportError (search_tasks, filter_tasks, sort_tasks not defined)

**Step 3: Add search/filter/sort to commands.py**

Append to `src/commands.py`:

```python
def search_tasks(store: TaskStore, *, keyword: str) -> list[Task]:
    """Search tasks by keyword in title and description (case-insensitive).

    Returns all tasks if keyword is empty.
    """
    if not keyword.strip():
        return store.get_all()
    keyword_lower = keyword.strip().lower()
    return [
        task for task in store.get_all()
        if keyword_lower in task.title.lower()
        or keyword_lower in task.description.lower()
    ]


def filter_tasks(
    store: TaskStore,
    *,
    status: str | None = None,
    priority: str | None = None,
    tag: str | None = None,
    due_before: str | None = None,
    due_after: str | None = None,
) -> list[Task]:
    """Filter tasks by status, priority, tag, and/or date range.

    All filters are AND-combined. Returns all tasks if no filters provided.
    """
    tasks = store.get_all()

    if status:
        parsed_status = validate_status_input(status)
        tasks = [t for t in tasks if t.status == parsed_status]

    if priority:
        parsed_priority = validate_priority_input(priority)
        tasks = [t for t in tasks if t.priority == parsed_priority]

    if tag:
        tag_lower = tag.strip().lower()
        tasks = [t for t in tasks if tag_lower in [tg.lower() for tg in t.tags]]

    if due_before:
        cutoff = parse_date_input(due_before)
        tasks = [t for t in tasks if t.due_date and t.due_date <= cutoff]

    if due_after:
        cutoff = parse_date_input(due_after)
        tasks = [t for t in tasks if t.due_date and t.due_date >= cutoff]

    return tasks


def sort_tasks(
    tasks: list[Task],
    *,
    sort_by: str = "created_at",
    descending: bool = False,
) -> list[Task]:
    """Sort a list of tasks by the given field.

    Supported sort_by values: 'title', 'priority', 'created_at', 'due_date', 'status'.
    None values (e.g., no due_date) sort last.
    """
    priority_order = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    max_date = datetime.max

    def sort_key(task: Task):
        if sort_by == "title":
            return task.title.lower()
        elif sort_by == "priority":
            return priority_order.get(task.priority, 99)
        elif sort_by == "due_date":
            return task.due_date or max_date
        elif sort_by == "status":
            return task.status.value
        else:  # created_at default
            return task.created_at

    return sorted(tasks, key=sort_key, reverse=descending)
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_search_filter_sort.py -v`
Expected: All 15 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/commands.py phase-1-console/tests/test_search_filter_sort.py
git commit -m "phase-1: feat: add search, filter, and sort command handlers"
```

---

## Task 6: Recurrence — Auto-Scheduling Logic

**Files:**
- Create: `phase-1-console/src/recurrence.py`
- Test: `phase-1-console/tests/test_recurrence.py`

**Step 1: Write the failing test**

```python
# tests/test_recurrence.py
import pytest
from datetime import datetime, timedelta
from src.models import Task, Status, Priority, RecurrenceRule
from src.recurrence import calculate_next_occurrence, create_recurring_clone


class TestCalculateNextOccurrence:
    def test_daily(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.DAILY)
        assert next_date == datetime(2025, 6, 16, 10, 0)

    def test_weekly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.WEEKLY)
        assert next_date == datetime(2025, 6, 22, 10, 0)

    def test_monthly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.MONTHLY)
        assert next_date == datetime(2025, 7, 15, 10, 0)

    def test_yearly(self):
        due = datetime(2025, 6, 15, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.YEARLY)
        assert next_date == datetime(2026, 6, 15, 10, 0)

    def test_monthly_end_of_month(self):
        due = datetime(2025, 1, 31, 10, 0)
        next_date = calculate_next_occurrence(due, RecurrenceRule.MONTHLY)
        assert next_date.month == 2
        assert next_date.day == 28  # Feb 2025 has 28 days

    def test_no_due_date_uses_now(self):
        next_date = calculate_next_occurrence(None, RecurrenceRule.DAILY)
        assert next_date is not None
        assert next_date > datetime.now()


class TestCreateRecurringClone:
    def test_clone_basic(self):
        original = Task(
            title="Daily standup",
            description="Team sync",
            priority=Priority.HIGH,
            tags=["work"],
            due_date=datetime(2025, 6, 15, 9, 0),
            is_recurring=True,
            recurrence_rule=RecurrenceRule.DAILY,
        )
        clone = create_recurring_clone(original)
        assert clone.id != original.id
        assert clone.title == original.title
        assert clone.description == original.description
        assert clone.priority == original.priority
        assert clone.tags == original.tags
        assert clone.is_recurring is True
        assert clone.recurrence_rule == RecurrenceRule.DAILY
        assert clone.status == Status.PENDING
        assert clone.completed_at is None
        assert clone.due_date == datetime(2025, 6, 16, 9, 0)

    def test_clone_not_recurring_raises(self):
        task = Task(title="Not recurring", is_recurring=False)
        with pytest.raises(ValueError, match="not a recurring task"):
            create_recurring_clone(task)

    def test_clone_preserves_tags(self):
        original = Task(
            title="Weekly review",
            tags=["work", "planning"],
            due_date=datetime(2025, 6, 15),
            is_recurring=True,
            recurrence_rule=RecurrenceRule.WEEKLY,
        )
        clone = create_recurring_clone(original)
        assert clone.tags == ["work", "planning"]
        # Verify it's a copy, not a reference
        clone.tags.append("modified")
        assert "modified" not in original.tags
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_recurrence.py -v`
Expected: FAIL — ImportError

**Step 3: Implement recurrence.py**

```python
# src/recurrence.py
"""Recurrence logic for auto-scheduling recurring tasks."""

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from src.models import Task, Status, RecurrenceRule


def calculate_next_occurrence(
    current_due: datetime | None,
    rule: RecurrenceRule,
) -> datetime:
    """Calculate the next occurrence based on a recurrence rule.

    Args:
        current_due: The current due date. Uses now() if None.
        rule: The recurrence frequency.

    Returns:
        The next due datetime.
    """
    base = current_due or datetime.now()

    if rule == RecurrenceRule.DAILY:
        return base + timedelta(days=1)
    elif rule == RecurrenceRule.WEEKLY:
        return base + timedelta(weeks=1)
    elif rule == RecurrenceRule.MONTHLY:
        return base + relativedelta(months=1)
    elif rule == RecurrenceRule.YEARLY:
        return base + relativedelta(years=1)
    else:
        raise ValueError(f"Unsupported recurrence rule: {rule}")


def create_recurring_clone(task: Task) -> Task:
    """Create a new pending task from a completed recurring task.

    The clone inherits all properties except:
    - Gets a new UUID
    - Status reset to PENDING
    - completed_at set to None
    - due_date advanced to next occurrence
    - Fresh created_at and updated_at timestamps

    Args:
        task: The completed recurring task to clone.

    Returns:
        A new Task with the next due date.

    Raises:
        ValueError: If the task is not recurring.
    """
    if not task.is_recurring or not task.recurrence_rule:
        raise ValueError(f"Task '{task.title}' is not a recurring task")

    next_due = calculate_next_occurrence(task.due_date, task.recurrence_rule)

    return Task(
        title=task.title,
        description=task.description,
        priority=task.priority,
        tags=list(task.tags),  # copy to avoid shared reference
        due_date=next_due,
        reminder_at=None,
        is_recurring=True,
        recurrence_rule=task.recurrence_rule,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_recurrence.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add phase-1-console/src/recurrence.py phase-1-console/tests/test_recurrence.py
git commit -m "phase-1: feat: add recurrence logic with auto-scheduling"
```

---

## Task 7: Toggle Complete — Wire Recurrence Into Toggle

**Files:**
- Modify: `phase-1-console/src/commands.py` (update `toggle_complete`)
- Test: `phase-1-console/tests/test_recurrence_toggle.py`

**Step 1: Write the failing test**

```python
# tests/test_recurrence_toggle.py
import pytest
from datetime import datetime
from src.models import Task, Status, RecurrenceRule
from src.store import TaskStore
from src.commands import add_task, toggle_complete


class TestRecurrenceOnToggle:
    def setup_method(self):
        self.store = TaskStore()

    def test_completing_recurring_task_creates_clone(self):
        task = add_task(
            self.store,
            title="Daily standup",
            due_date="2025-06-15 09:00",
            is_recurring=True,
            recurrence_rule="daily",
        )
        original_count = self.store.count()
        toggle_complete(self.store, task.id)

        assert self.store.count() == original_count + 1

        all_tasks = self.store.get_all()
        clones = [t for t in all_tasks if t.id != task.id]
        assert len(clones) == 1

        clone = clones[0]
        assert clone.title == "Daily standup"
        assert clone.status == Status.PENDING
        assert clone.due_date == datetime(2025, 6, 16, 9, 0)

    def test_uncompleting_does_not_create_clone(self):
        task = add_task(
            self.store,
            title="Daily standup",
            due_date="2025-06-15 09:00",
            is_recurring=True,
            recurrence_rule="daily",
        )
        toggle_complete(self.store, task.id)  # complete → creates clone
        count_after_complete = self.store.count()

        toggle_complete(self.store, task.id)  # uncomplete → no new clone
        assert self.store.count() == count_after_complete

    def test_non_recurring_does_not_create_clone(self):
        task = add_task(self.store, title="One-off task")
        toggle_complete(self.store, task.id)
        assert self.store.count() == 1
```

**Step 2: Run test to verify it fails**

Run: `cd phase-1-console && python -m pytest tests/test_recurrence_toggle.py -v`
Expected: FAIL — `test_completing_recurring_task_creates_clone` fails (no clone created)

**Step 3: Modify toggle_complete in commands.py**

Replace the `toggle_complete` function:

```python
def toggle_complete(store: TaskStore, task_id: str) -> Task | None:
    """Toggle a task between pending and completed.

    If the task is recurring and being completed, auto-creates
    the next occurrence.

    Returns the updated Task, or None if not found.
    """
    from src.recurrence import create_recurring_clone

    task = store.get(task_id)
    if task is None:
        return None

    if task.status == Status.COMPLETED:
        task.status = Status.PENDING
        task.completed_at = None
    else:
        task.status = Status.COMPLETED
        task.completed_at = datetime.now()

        # Auto-create next occurrence for recurring tasks
        if task.is_recurring and task.recurrence_rule:
            clone = create_recurring_clone(task)
            store.add(clone)

    store.update(task)
    return task
```

**Step 4: Run test to verify it passes**

Run: `cd phase-1-console && python -m pytest tests/test_recurrence_toggle.py -v`
Expected: All 3 tests PASS

**Step 5: Run ALL tests to ensure nothing broke**

Run: `cd phase-1-console && python -m pytest -v`
Expected: All tests PASS (across all test files)

**Step 6: Commit**

```bash
git add phase-1-console/src/commands.py phase-1-console/tests/test_recurrence_toggle.py
git commit -m "phase-1: feat: wire recurrence auto-scheduling into toggle_complete"
```

---

## Task 8: Main — CLI Menu Loop

**Files:**
- Create: `phase-1-console/src/main.py`

**Step 1: Implement main.py**

```python
# src/main.py
"""Entry point — CLI menu loop for the Todo console app."""

from src.store import TaskStore
from src.commands import (
    add_task,
    view_all_tasks,
    view_task_detail,
    update_task,
    delete_task,
    toggle_complete,
    search_tasks,
    filter_tasks,
    sort_tasks,
)
from src.utils import format_task_summary, format_task_detail


MENU = """
=== Todo App ===
1.  Add Task
2.  View All Tasks
3.  View Task Details
4.  Update Task
5.  Delete Task
6.  Mark Complete/Incomplete
7.  Search Tasks
8.  Filter Tasks
9.  Sort Tasks
10. Exit
"""


def prompt(message: str) -> str:
    """Prompt user for input with a message."""
    return input(f"  {message}: ").strip()


def handle_add(store: TaskStore) -> None:
    """Gather input and add a task."""
    title = prompt("Title (required)")
    description = prompt("Description (optional, press Enter to skip)")
    priority = prompt("Priority (low/medium/high, default: medium)") or "medium"
    tags = prompt("Tags (comma-separated, optional)")
    due_date = prompt("Due date (YYYY-MM-DD or YYYY-MM-DD HH:MM, optional)")
    reminder_at = prompt("Reminder (YYYY-MM-DD HH:MM, optional)")

    is_recurring_input = prompt("Recurring? (yes/no, default: no)").lower()
    is_recurring = is_recurring_input in ("yes", "y")
    recurrence_rule = ""
    if is_recurring:
        recurrence_rule = prompt("Recurrence (daily/weekly/monthly/yearly)")

    try:
        task = add_task(
            store,
            title=title,
            description=description,
            priority=priority,
            tags=tags,
            due_date=due_date,
            reminder_at=reminder_at,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
        )
        print(f"\n  ✓ Task added: {task.title} (ID: {task.id[:8]})")
    except ValueError as exc:
        print(f"\n  ✗ Error: {exc}")


def handle_view_all(store: TaskStore) -> None:
    """Display all tasks."""
    tasks = view_all_tasks(store)
    if not tasks:
        print("\n  No tasks yet.")
        return
    print(f"\n  --- All Tasks ({len(tasks)}) ---")
    for task in tasks:
        print(format_task_summary(task))


def handle_view_detail(store: TaskStore) -> None:
    """Display a single task's full details."""
    task_id = prompt("Task ID (or first 8 chars)")
    task = _resolve_task(store, task_id)
    if task:
        print(format_task_detail(task))
    else:
        print("\n  ✗ Task not found.")


def handle_update(store: TaskStore) -> None:
    """Gather fields to update and apply."""
    task_id = prompt("Task ID to update")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  ✗ Task not found.")
        return

    print("  (Press Enter to keep current value)")
    title = prompt(f"Title [{task.title}]") or None
    description = prompt(f"Description [{task.description}]") or None
    priority = prompt(f"Priority [{task.priority.value}]") or None
    tags = prompt(f"Tags [{', '.join(task.tags)}]") or None
    due_date = prompt(f"Due date [{task.due_date}]") or None
    status = prompt(f"Status [{task.status.value}]") or None

    try:
        updated = update_task(
            store, task.id,
            title=title, description=description,
            priority=priority, tags=tags,
            due_date=due_date, status=status,
        )
        if updated:
            print(f"\n  ✓ Task updated: {updated.title}")
    except ValueError as exc:
        print(f"\n  ✗ Error: {exc}")


def handle_delete(store: TaskStore) -> None:
    """Delete a task by ID."""
    task_id = prompt("Task ID to delete")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  ✗ Task not found.")
        return
    confirm = prompt(f"Delete '{task.title}'? (yes/no)").lower()
    if confirm in ("yes", "y"):
        delete_task(store, task.id)
        print(f"\n  ✓ Task deleted.")
    else:
        print("\n  Cancelled.")


def handle_toggle(store: TaskStore) -> None:
    """Toggle task completion status."""
    task_id = prompt("Task ID to toggle")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  ✗ Task not found.")
        return
    toggled = toggle_complete(store, task.id)
    print(f"\n  ✓ '{toggled.title}' → {toggled.status.value}")
    if toggled.status.value == "completed" and toggled.is_recurring:
        print("  ↻ Next recurring instance created automatically.")


def handle_search(store: TaskStore) -> None:
    """Search tasks by keyword."""
    keyword = prompt("Search keyword")
    results = search_tasks(store, keyword=keyword)
    if not results:
        print("\n  No matching tasks.")
        return
    print(f"\n  --- Search Results ({len(results)}) ---")
    for task in results:
        print(format_task_summary(task))


def handle_filter(store: TaskStore) -> None:
    """Filter tasks by criteria."""
    print("  (Press Enter to skip a filter)")
    status = prompt("Status (pending/in_progress/completed)") or None
    priority = prompt("Priority (low/medium/high)") or None
    tag = prompt("Tag") or None
    due_before = prompt("Due before (YYYY-MM-DD)") or None
    due_after = prompt("Due after (YYYY-MM-DD)") or None

    try:
        results = filter_tasks(
            store, status=status, priority=priority,
            tag=tag, due_before=due_before, due_after=due_after,
        )
        if not results:
            print("\n  No matching tasks.")
            return
        print(f"\n  --- Filtered Results ({len(results)}) ---")
        for task in results:
            print(format_task_summary(task))
    except ValueError as exc:
        print(f"\n  ✗ Error: {exc}")


def handle_sort(store: TaskStore) -> None:
    """Sort and display tasks."""
    sort_by = prompt("Sort by (title/priority/due_date/created_at)") or "created_at"
    order = prompt("Order (asc/desc, default: asc)").lower()
    descending = order in ("desc", "descending", "d")

    tasks = view_all_tasks(store)
    if not tasks:
        print("\n  No tasks to sort.")
        return

    sorted_list = sort_tasks(tasks, sort_by=sort_by, descending=descending)
    print(f"\n  --- Sorted by {sort_by} ({'desc' if descending else 'asc'}) ---")
    for task in sorted_list:
        print(format_task_summary(task))


def _resolve_task(store: TaskStore, partial_id: str) -> object:
    """Find a task by full ID or partial (first 8 chars) match."""
    task = store.get(partial_id)
    if task:
        return task
    # Try partial match
    for t in store.get_all():
        if t.id.startswith(partial_id):
            return t
    return None


def main() -> None:
    """Main CLI loop."""
    store = TaskStore()
    handlers = {
        "1": handle_add,
        "2": handle_view_all,
        "3": handle_view_detail,
        "4": handle_update,
        "5": handle_delete,
        "6": handle_toggle,
        "7": handle_search,
        "8": handle_filter,
        "9": handle_sort,
    }

    print("\n  Welcome to the Todo App! (In-memory — data is lost on exit)\n")

    while True:
        print(MENU)
        choice = prompt("Choose an option (1-10)")

        if choice == "10":
            print("\n  Goodbye! 👋\n")
            break

        handler = handlers.get(choice)
        if handler:
            print()
            handler(store)
            print()
        else:
            print("\n  ✗ Invalid choice. Please enter 1-10.\n")


if __name__ == "__main__":
    main()
```

**Step 2: Manual smoke test**

Run: `cd phase-1-console && python src/main.py`
- Add a task, view it, toggle complete, search, filter, sort
- Add a recurring task, complete it, verify clone appears

**Step 3: Run all tests**

Run: `cd phase-1-console && python -m pytest -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add phase-1-console/src/main.py
git commit -m "phase-1: feat: add CLI menu loop with all 10 operations"
```

---

## Task 9: README and Final Polish

**Files:**
- Create: `phase-1-console/README.md`

**Step 1: Write README.md**

Write a README covering:
- Title & overview
- Features (Basic + Intermediate + Advanced checklists)
- Setup instructions (venv, pip install, python src/main.py)
- Architecture diagram (Mermaid: main.py → commands.py → store.py, with models.py and recurrence.py)
- File structure tree
- Testing instructions (`python -m pytest -v`)
- Usage examples (sample CLI session)

**Step 2: Final test run**

Run: `cd phase-1-console && python -m pytest -v --tb=short`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add phase-1-console/README.md
git commit -m "phase-1: docs: add README with setup, architecture, and usage"
```

---

## Summary

| Task | What | Tests |
|------|------|-------|
| 1 | Models (Task, enums) | 6 tests |
| 2 | Store (in-memory CRUD) | 9 tests |
| 3 | Utils (validators, formatters, parsers) | 17 tests |
| 4 | Commands — CRUD (add, view, update, delete, toggle) | 14 tests |
| 5 | Commands — Search, filter, sort | 15 tests |
| 6 | Recurrence logic | 9 tests |
| 7 | Wire recurrence into toggle | 3 tests |
| 8 | CLI menu loop (main.py) | Manual smoke test |
| 9 | README + final polish | — |

**Total: ~73 automated tests across 9 tasks.**
