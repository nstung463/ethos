"""structured_output tool — return machine-readable JSON output.

Mirrors SyntheticOutputTool (StructuredOutput) from claude-code-source.
Accepts any JSON-serializable dict and returns it serialized.
"""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class StructuredOutputInput(BaseModel):
    model_config = {"extra": "allow"}


class _StructuredOutputTool(StructuredTool):
    """StructuredTool subclass that serializes the raw input dict as JSON.

    LangChain strips unknown fields before calling the underlying func,
    so we intercept at the invoke level where the raw dict is still intact.
    """

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> str:  # type: ignore[override]
        if isinstance(input, dict):
            return json.dumps(input)
        return json.dumps({})


structured_output_tool = _StructuredOutputTool(
    name="structured_output",
    description=(
        "Return the final response as structured JSON. "
        "Call exactly once at the end of a task that requires machine-readable output. "
        "Pass all output fields as keyword arguments."
    ),
    args_schema=StructuredOutputInput,
    func=lambda **kw: json.dumps(kw),
)
