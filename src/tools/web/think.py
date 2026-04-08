"""think tool — explicit reasoning scratchpad before acting."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ThinkInput(BaseModel):
    thought: str = Field(
        description=(
            "Your reasoning, analysis, or step-by-step thinking. "
            "Use this to reason through complex problems, evaluate options, "
            "or plan an approach before calling other tools."
        )
    )


def _think(thought: str) -> str:
    """Return the thought unchanged — this is a reasoning scratchpad."""
    return thought


think_tool = StructuredTool.from_function(
    name="think",
    func=_think,
    description=(
        "Reason through a problem before acting. "
        "Write out your analysis or step-by-step logic. "
        "This tool takes no side effects — it is a scratchpad for structured thinking."
    ),
    args_schema=ThinkInput,
)
