"""task_get tool â€” retrieve a task by ID."""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.tools._store import ToolStore


class TaskGetInput(BaseModel):
    task_id: str = Field(description="The ID of the task to retrieve.")


def build_task_get_tool(store: ToolStore) -> StructuredTool:
    def _get(task_id: str) -> str:
        record = store.get_task(task_id)
        if record is None:
            return f"Error: task '{task_id}' not found."
        return json.dumps({
            "id": record.id, "subject": record.subject,
            "description": record.description, "status": record.status.value,
            "active_form": record.active_form, "metadata": record.metadata,
            "stopped": record.stopped,
        })

    return StructuredTool.from_function(
        name="task_get", func=_get,
        description="Get the current state of a task by its ID.",
        args_schema=TaskGetInput,
    )

