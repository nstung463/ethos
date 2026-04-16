"""Tests for todo_write tool (TodoWriteTool port)."""
from __future__ import annotations

import json
from src.ai.tools._store import ToolStore
from src.ai.tools.todo.todo_write import build_todo_write_tool


ITEM_A = {"content": "Write tests", "status": "pending", "priority": "high"}
ITEM_B = {"content": "Run CI", "status": "completed", "priority": "medium"}


def test_todo_write_stores_todos() -> None:
    store = ToolStore()
    tool = build_todo_write_tool(store)
    tool.invoke({"todos": [ITEM_A, ITEM_B]})
    assert store.read_todos() == [ITEM_A, ITEM_B]


def test_todo_write_clears_when_all_completed() -> None:
    store = ToolStore()
    tool = build_todo_write_tool(store)
    all_done = [{"content": "A", "status": "completed", "priority": "low"}]
    tool.invoke({"todos": all_done})
    assert store.read_todos() == []


def test_todo_write_returns_old_and_new() -> None:
    store = ToolStore()
    store.write_todos([ITEM_A])
    tool = build_todo_write_tool(store)
    result = json.loads(tool.invoke({"todos": [ITEM_B]}))
    assert "old_todos" in result
    assert "new_todos" in result


def test_todo_write_replaces_previous() -> None:
    store = ToolStore()
    tool = build_todo_write_tool(store)
    item_pending_b = {"content": "Run CI", "status": "pending", "priority": "medium"}
    tool.invoke({"todos": [ITEM_A]})
    tool.invoke({"todos": [item_pending_b]})
    todos = store.read_todos()
    assert len(todos) == 1
    assert todos[0]["content"] == "Run CI"

