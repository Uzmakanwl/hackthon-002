"""Tests for the OpenAI agent configuration, tool definitions, and tool execution."""

import pytest
from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — ensure Task table is registered with SQLModel metadata


class TestAgentConfig:
    """Tests for the agent system prompt and tool definitions."""

    def test_system_prompt_exists(self):
        """System prompt should be a non-trivial string mentioning tasks."""
        from app.agents.todo_agent import SYSTEM_PROMPT

        assert SYSTEM_PROMPT is not None
        assert "task" in SYSTEM_PROMPT.lower()
        assert len(SYSTEM_PROMPT) > 50

    def test_tools_defined(self):
        """All six CRUD tool definitions should be present."""
        from app.agents.todo_agent import get_agent_tools

        tools = get_agent_tools()
        tool_names = [t["function"]["name"] for t in tools]
        assert "create_task" in tool_names
        assert "list_tasks" in tool_names
        assert "get_task" in tool_names
        assert "update_task" in tool_names
        assert "delete_task" in tool_names
        assert "complete_task" in tool_names
        assert len(tools) == 6

    def test_all_tools_have_required_fields(self):
        """Every tool definition must have type, name, description, and parameters."""
        from app.agents.todo_agent import get_agent_tools

        tools = get_agent_tools()
        for tool in tools:
            assert tool["type"] == "function"
            assert "name" in tool["function"]
            assert "description" in tool["function"]
            assert "parameters" in tool["function"]

    def test_create_task_requires_title(self):
        """The create_task tool should require 'title' as a parameter."""
        from app.agents.todo_agent import get_agent_tools

        tools = get_agent_tools()
        create_tool = next(t for t in tools if t["function"]["name"] == "create_task")
        assert "title" in create_tool["function"]["parameters"].get("required", [])

    def test_get_task_requires_task_id(self):
        """The get_task tool should require 'task_id' as a parameter."""
        from app.agents.todo_agent import get_agent_tools

        tools = get_agent_tools()
        get_tool = next(t for t in tools if t["function"]["name"] == "get_task")
        assert "task_id" in get_tool["function"]["parameters"].get("required", [])


class TestToolExecution:
    """Tests for the _execute_tool function against a real in-memory DB."""

    @pytest.fixture(autouse=True)
    def patch_db(self, monkeypatch):
        """Patch get_session_sync to return sessions from an in-memory SQLite engine."""
        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        SQLModel.metadata.create_all(engine)
        self._engine = engine

        def fake_get_session_sync():
            return Session(engine)

        monkeypatch.setattr(
            "app.agents.todo_agent.get_session_sync", fake_get_session_sync
        )

    def test_execute_create_task(self):
        """_execute_tool should create a task and return confirmation."""
        from app.agents.todo_agent import _execute_tool

        result = _execute_tool("create_task", {"title": "Agent test task"})
        assert "Agent test task" in result
        assert "created" in result.lower()

    def test_execute_list_tasks_empty(self):
        """_execute_tool for list_tasks on empty DB should indicate no tasks."""
        from app.agents.todo_agent import _execute_tool

        result = _execute_tool("list_tasks", {})
        assert "no tasks" in result.lower()

    def test_execute_unknown_tool(self):
        """_execute_tool with unknown tool name should return error message."""
        from app.agents.todo_agent import _execute_tool

        result = _execute_tool("nonexistent_tool", {})
        assert "unknown" in result.lower()
