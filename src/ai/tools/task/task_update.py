"""task_update tool â€” update task fields or delete a task.

Status 'deleted' is a special action that removes the task (mirrors TS).
"""
from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.tools._store import TaskStatus, ToolStore


class TaskUpdateInput(BaseModel):
    task_id: str = Field(description="The ID of the task to update.")
    subject: Optional[str] = Field(default=None, description="New subject.")
    description: Optional[str] = Field(default=None, description="New description.")
    active_form: Optional[str] = Field(default=None, description="New active form text.")
    status: Optional[str] = Field(
        default=None,
        description="New status: 'pending', 'in_progress', 'completed', 'failed', 'stopped', or 'deleted'.",
    )
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Metadata to merge.")


def build_task_update_tool(store: ToolStore) -> StructuredTool:
    def _update(task_id: str, subject: Optional[str] = None,
                description: Optional[str] = None, active_form: Optional[str] = None,
                status: Optional[str] = None, metadata: Optional[dict[str, Any]] = None) -> str:
        if status == "deleted":
            deleted = store.delete_task(task_id)
            if not deleted:
                return f"Error: task '{task_id}' not found."
            return json.dumps({"deleted": True, "task_id": task_id})

        parsed_status: Optional[TaskStatus] = None
        if status is not None:
            try:
                parsed_status = TaskStatus(status)
            except ValueError:
                return f"Error: unknown status '{status}'."

        record = store.update_task(task_id, subject=subject, description=description,
                                    status=parsed_status, active_form=active_form, metadata=metadata)
        if record is None:
            return f"Error: task '{task_id}' not found."
        return json.dumps({"id": record.id, "subject": record.subject, "status": record.status.value})

    return StructuredTool.from_function(
        name="task_update", func=_update,
        description="Update a task's fields. Use status='deleted' to remove the task.",
        args_schema=TaskUpdateInput,
    )

