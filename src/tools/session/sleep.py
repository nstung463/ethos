"""sleep tool — pause execution for a specified duration."""
from __future__ import annotations

import time

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SleepInput(BaseModel):
    duration_ms: int = Field(description="Duration to sleep in milliseconds.", ge=0)


def _sleep(duration_ms: int) -> str:
    time.sleep(duration_ms / 1000.0)
    return f"Slept {duration_ms}ms."


sleep_tool = StructuredTool.from_function(
    name="sleep",
    func=_sleep,
    description="Pause execution for the specified number of milliseconds.",
    args_schema=SleepInput,
)
