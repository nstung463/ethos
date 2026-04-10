"""think tool - strategic reflection scratchpad for research workflows."""

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ThinkInput(BaseModel):
    reflection: str = Field(
        description=(
            "Your detailed reflection on progress, findings, gaps, and next steps. "
            "Use this after gathering information to analyze what you learned, "
            "what is still missing, and whether to continue or conclude."
        )
    )


def _think(reflection: str) -> str:
    """Record a strategic reflection for deliberate decision-making."""
    return f"Reflection recorded: {reflection}"


think_tool = StructuredTool.from_function(
    name="think",
    func=_think,
    description=(
        "Tool for strategic reflection on research progress and decision-making. "
        "Use after searches or document reads to assess findings, identify gaps, "
        "evaluate evidence quality, and decide the next step."
    ),
    args_schema=ThinkInput,
)
