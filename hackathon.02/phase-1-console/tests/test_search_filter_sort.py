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
