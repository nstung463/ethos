"""task_output tool — get accumulated output from a task."""
from __future__ import annotations

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools._store import ToolStore


class TaskOutputInput(BaseModel):
    task_id: str = Field(description="The ID of the task whose output to retrieve.")


def build_task_output_tool(store: ToolStore) -> StructuredTool:
    def _output(task_id: str) -> str:
        record = store.get_task(task_id)
        if record is None:
            return f"Error: task '{task_id}' not found."
        return record.output or "(no output yet)"

    return StructuredTool.from_function(
        name="task_output", func=_output,
        description="Get the accumulated stdout/stderr output of a task.",
        args_schema=TaskOutputInput,
    )
