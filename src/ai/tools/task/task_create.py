"""task_create tool â€” create a new task record in the store."""
from __future__ import annotations

import json
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.tools._store import ToolStore


class TaskCreateInput(BaseModel):
    subject: str = Field(description="A brief title for the task.")
    description: str = Field(description="What needs to be done.")
    active_form: Optional[str] = Field(default=None, description="Present continuous form shown while in_progress.")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Arbitrary metadata to attach.")


def build_task_create_tool(store: ToolStore) -> StructuredTool:
    def _create(subject: str, description: str,
                active_form: Optional[str] = None,
                metadata: Optional[dict[str, Any]] = None) -> str:
        record = store.create_task(subject=subject, description=description,
                                    active_form=active_form, metadata=metadata)
        return json.dumps({"task": {"id": record.id, "subject": record.subject}})

    return StructuredTool.from_function(
        name="task_create",
        func=_create,
        description="Create a new task to track a unit of work. Returns the task ID.",
        args_schema=TaskCreateInput,
    )

