"""task_stop tool — stop a running task."""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools._store import ToolStore


class TaskStopInput(BaseModel):
    task_id: str = Field(description="The ID of the task to stop.")


def build_task_stop_tool(store: ToolStore) -> StructuredTool:
    def _stop(task_id: str) -> str:
        record = store.stop_task(task_id)
        if record is None:
            return f"Error: task '{task_id}' not found."
        return json.dumps({"stopped": True, "task_id": record.id, "status": record.status.value})

    return StructuredTool.from_function(
        name="task_stop", func=_stop,
        description="Stop a running task. Sets its status to 'stopped'.",
        args_schema=TaskStopInput,
    )
