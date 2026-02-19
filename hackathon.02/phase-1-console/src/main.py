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
        print(f"\n  Task added: {task.title} (ID: {task.id[:8]})")
    except ValueError as exc:
        print(f"\n  Error: {exc}")


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
        print("\n  Task not found.")


def handle_update(store: TaskStore) -> None:
    """Gather fields to update and apply."""
    task_id = prompt("Task ID to update")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  Task not found.")
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
            print(f"\n  Task updated: {updated.title}")
    except ValueError as exc:
        print(f"\n  Error: {exc}")


def handle_delete(store: TaskStore) -> None:
    """Delete a task by ID."""
    task_id = prompt("Task ID to delete")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  Task not found.")
        return
    confirm = prompt(f"Delete '{task.title}'? (yes/no)").lower()
    if confirm in ("yes", "y"):
        delete_task(store, task.id)
        print(f"\n  Task deleted.")
    else:
        print("\n  Cancelled.")


def handle_toggle(store: TaskStore) -> None:
    """Toggle task completion status."""
    task_id = prompt("Task ID to toggle")
    task = _resolve_task(store, task_id)
    if not task:
        print("\n  Task not found.")
        return
    toggled = toggle_complete(store, task.id)
    print(f"\n  '{toggled.title}' -> {toggled.status.value}")
    if toggled.status.value == "completed" and toggled.is_recurring:
        print("  Next recurring instance created automatically.")


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
        print(f"\n  Error: {exc}")


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


def _resolve_task(store: TaskStore, partial_id: str):
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
            print("\n  Goodbye!\n")
            break

        handler = handlers.get(choice)
        if handler:
            print()
            handler(store)
            print()
        else:
            print("\n  Invalid choice. Please enter 1-10.\n")


if __name__ == "__main__":
    main()
