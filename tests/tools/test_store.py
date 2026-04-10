"""Tests for ToolStore."""
from __future__ import annotations

from src.tools._store import TaskRecord, TaskStatus, ToolStore


def test_store_create_task() -> None:
    store = ToolStore()
    task = store.create_task(subject="Do something", description="Details here")
    assert task.id.startswith("task-")
    assert task.subject == "Do something"
    assert task.status == TaskStatus.PENDING
    assert task in store.list_tasks()


def test_store_get_task() -> None:
    store = ToolStore()
    task = store.create_task(subject="X", description="Y")
    found = store.get_task(task.id)
    assert found is task


def test_store_get_missing_task() -> None:
    store = ToolStore()
    assert store.get_task("no-such-id") is None


def test_store_update_task_status() -> None:
    store = ToolStore()
    task = store.create_task(subject="A", description="B")
    store.update_task(task.id, status=TaskStatus.IN_PROGRESS)
    assert store.get_task(task.id).status == TaskStatus.IN_PROGRESS


def test_store_delete_task() -> None:
    store = ToolStore()
    task = store.create_task(subject="Del", description="me")
    store.delete_task(task.id)
    assert store.get_task(task.id) is None


def test_store_todo_write_and_read() -> None:
    store = ToolStore()
    todos = [{"content": "Task A", "status": "pending"}, {"content": "Task B", "status": "completed"}]
    store.write_todos(todos)
    assert store.read_todos() == todos


def test_store_append_task_output() -> None:
    store = ToolStore()
    task = store.create_task(subject="Run", description="cmd")
    store.append_output(task.id, "line1\n")
    store.append_output(task.id, "line2\n")
    assert store.get_output(task.id) == "line1\nline2\n"
