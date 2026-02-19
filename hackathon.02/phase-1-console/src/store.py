"""In-memory task storage using a dictionary."""

from datetime import datetime
from src.models import Task


class TaskStore:
    """Stores tasks in memory, keyed by task ID."""

    def __init__(self) -> None:
        """Initialize an empty task store."""
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
