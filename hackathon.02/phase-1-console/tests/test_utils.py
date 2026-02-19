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
