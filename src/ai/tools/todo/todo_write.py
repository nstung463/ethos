"""todo_write tool â€” manage the session task checklist.

Mirrors TodoWriteTool from claude-code-source.
Input: list of todo items (content, status, priority).
Behavior: replaces the current todo list. If all items are 'completed',
the list resets to empty (the session is done).
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.tools._store import ToolStore


class TodoItem(BaseModel):
    content: str = Field(description="Description of the todo item.")
    status: str = Field(description="One of: 'pending', 'in_progress', 'completed'.")
    priority: str = Field(default="medium", description="One of: 'high', 'medium', 'low'.")


class TodoWriteInput(BaseModel):
    todos: list[TodoItem] = Field(description="The updated todo list. Replaces the current list.")


def _todo_write(store: ToolStore, todos: list[TodoItem]) -> str:
    old = store.read_todos()
    items = [t.model_dump() for t in todos]
    all_done = all(t["status"] == "completed" for t in items)
    new = [] if all_done else items
    store.write_todos(new)
    return json.dumps({"old_todos": old, "new_todos": items})


def build_todo_write_tool(store: ToolStore) -> StructuredTool:
    """Build the todo_write tool bound to the given ToolStore."""
    return StructuredTool.from_function(
        name="todo_write",
        func=lambda todos: _todo_write(store, todos),
        description=(
            "Manage the session task checklist. "
            "Pass the complete updated list of todos. "
            "When all items are 'completed', the list resets to empty. "
            "Always include every item â€” partial updates are not supported."
        ),
        args_schema=TodoWriteInput,
    )

