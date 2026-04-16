"""Tests for task management tools (TaskCreate/Get/List/Update/Stop/Output)."""
from __future__ import annotations

import json
import pytest
from src.ai.tools._store import ToolStore, TaskStatus
from src.ai.tools.task import (
    build_task_create_tool, build_task_get_tool, build_task_list_tool,
    build_task_update_tool, build_task_stop_tool, build_task_output_tool,
)


@pytest.fixture()
def store() -> ToolStore:
    return ToolStore()


def test_task_create_returns_id_and_subject(store: ToolStore) -> None:
    tool = build_task_create_tool(store)
    result = json.loads(tool.invoke({"subject": "Run tests", "description": "Execute pytest"}))
    assert "id" in result["task"]
    assert result["task"]["subject"] == "Run tests"


def test_task_create_stores_in_store(store: ToolStore) -> None:
    tool = build_task_create_tool(store)
    result = json.loads(tool.invoke({"subject": "X", "description": "Y"}))
    assert store.get_task(result["task"]["id"]) is not None


def test_task_create_with_active_form(store: ToolStore) -> None:
    tool = build_task_create_tool(store)
    result = json.loads(tool.invoke({"subject": "Build", "description": "compile", "active_form": "Building..."}))
    record = store.get_task(result["task"]["id"])
    assert record.active_form == "Building..."


def test_task_get_existing(store: ToolStore) -> None:
    record = store.create_task(subject="S", description="D")
    tool = build_task_get_tool(store)
    result = json.loads(tool.invoke({"task_id": record.id}))
    assert result["id"] == record.id
    assert result["status"] == "pending"


def test_task_get_missing(store: ToolStore) -> None:
    tool = build_task_get_tool(store)
    result = tool.invoke({"task_id": "no-such-task"})
    assert "not found" in result.lower()


def test_task_list_empty(store: ToolStore) -> None:
    tool = build_task_list_tool(store)
    result = json.loads(tool.invoke({}))
    assert result["tasks"] == []


def test_task_list_returns_all(store: ToolStore) -> None:
    store.create_task(subject="A", description="a")
    store.create_task(subject="B", description="b")
    tool = build_task_list_tool(store)
    result = json.loads(tool.invoke({}))
    assert len(result["tasks"]) == 2


def test_task_update_status(store: ToolStore) -> None:
    record = store.create_task(subject="S", description="D")
    tool = build_task_update_tool(store)
    result = json.loads(tool.invoke({"task_id": record.id, "status": "in_progress"}))
    assert result["status"] == "in_progress"
    assert store.get_task(record.id).status == TaskStatus.IN_PROGRESS


def test_task_update_subject(store: ToolStore) -> None:
    record = store.create_task(subject="Old", description="D")
    tool = build_task_update_tool(store)
    result = json.loads(tool.invoke({"task_id": record.id, "subject": "New"}))
    assert result["subject"] == "New"


def test_task_update_deleted_removes_task(store: ToolStore) -> None:
    record = store.create_task(subject="Del", description="me")
    tool = build_task_update_tool(store)
    tool.invoke({"task_id": record.id, "status": "deleted"})
    assert store.get_task(record.id) is None


def test_task_update_missing(store: ToolStore) -> None:
    tool = build_task_update_tool(store)
    result = tool.invoke({"task_id": "ghost", "status": "completed"})
    assert "not found" in result.lower()


def test_task_stop_marks_stopped(store: ToolStore) -> None:
    record = store.create_task(subject="S", description="D")
    tool = build_task_stop_tool(store)
    result = json.loads(tool.invoke({"task_id": record.id}))
    assert result["stopped"] is True
    assert store.get_task(record.id).status == TaskStatus.STOPPED


def test_task_stop_missing(store: ToolStore) -> None:
    tool = build_task_stop_tool(store)
    result = tool.invoke({"task_id": "nope"})
    assert "not found" in result.lower()


def test_task_output_returns_accumulated(store: ToolStore) -> None:
    record = store.create_task(subject="Cmd", description="run it")
    store.append_output(record.id, "stdout line1\n")
    store.append_output(record.id, "stdout line2\n")
    tool = build_task_output_tool(store)
    result = tool.invoke({"task_id": record.id})
    assert "stdout line1" in result
    assert "stdout line2" in result


def test_task_output_missing_task(store: ToolStore) -> None:
    tool = build_task_output_tool(store)
    result = tool.invoke({"task_id": "x"})
    assert "not found" in result.lower()


def test_task_output_empty(store: ToolStore) -> None:
    record = store.create_task(subject="Q", description="quiet")
    tool = build_task_output_tool(store)
    result = tool.invoke({"task_id": record.id})
    assert result == "(no output yet)"

