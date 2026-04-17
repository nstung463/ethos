"""Shared in-memory store for todo lists and task records.

Mirrors the session-scoped task/todo state in claude-code-source.
Inject one ToolStore per agent session; pass it to all tool builders.
"""
from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TaskRecord:
    id: str
    subject: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    active_form: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    output: str = ""
    stopped: bool = False


class ToolStore:
    """Thread-safe in-memory store for todos and tasks."""

    _counter = itertools.count(1)

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[str, TaskRecord] = {}
        self._todos: list[dict[str, str]] = []

    # ── Tasks ──────────────────────────────────────────────────────────────

    def create_task(
        self,
        subject: str,
        description: str,
        active_form: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> TaskRecord:
        task_id = f"task-{next(self._counter)}"
        record = TaskRecord(
            id=task_id,
            subject=subject,
            description=description,
            active_form=active_form,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[task_id] = record
        return record

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> list[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())

    def update_task(
        self,
        task_id: str,
        *,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        active_form: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Optional[TaskRecord]:
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return None
            if subject is not None:
                record.subject = subject
            if description is not None:
                record.description = description
            if status is not None:
                record.status = status
            if active_form is not None:
                record.active_form = active_form
            if metadata is not None:
                record.metadata.update(metadata)
            return record

    def delete_task(self, task_id: str) -> bool:
        with self._lock:
            return self._tasks.pop(task_id, None) is not None

    def stop_task(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            record = self._tasks.get(task_id)
            if record:
                record.stopped = True
                record.status = TaskStatus.STOPPED
            return record

    # ── Task output ────────────────────────────────────────────────────────

    def append_output(self, task_id: str, text: str) -> None:
        with self._lock:
            record = self._tasks.get(task_id)
            if record:
                record.output += text

    def get_output(self, task_id: str) -> str:
        with self._lock:
            record = self._tasks.get(task_id)
            return record.output if record else ""

    # ── Todos ──────────────────────────────────────────────────────────────

    def write_todos(self, todos: list[dict[str, str]]) -> None:
        with self._lock:
            self._todos = list(todos)

    def read_todos(self) -> list[dict[str, str]]:
        with self._lock:
            return list(self._todos)
