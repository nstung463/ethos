"""task_list tool — list all tasks in the store."""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel

from src.tools._store import ToolStore


class TaskListInput(BaseModel):
    pass


def build_task_list_tool(store: ToolStore) -> StructuredTool:
    def _list() -> str:
        records = store.list_tasks()
        tasks = [{"id": r.id, "subject": r.subject, "status": r.status.value} for r in records]
        return json.dumps({"tasks": tasks})

    return StructuredTool.from_function(
        name="task_list", func=_list,
        description="List all tasks in the current session.",
        args_schema=TaskListInput,
    )
