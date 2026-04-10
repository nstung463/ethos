"""skill tool — invoke a named skill by name."""
from __future__ import annotations

from typing import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class SkillInput(BaseModel):
    skill: str = Field(description="Name of the skill to invoke.")
    args: str = Field(default="", description="Optional arguments to pass to the skill.")


def build_skill_tool(skill_runner: Callable[[str, str], str]) -> StructuredTool:
    def _invoke(skill: str, args: str = "") -> str:
        try:
            return skill_runner(skill, args)
        except FileNotFoundError as exc:
            return f"Error: {exc}"
        except Exception as exc:
            return f"Error invoking skill '{skill}': {exc}"

    return StructuredTool.from_function(
        name="skill", func=_invoke,
        description="Invoke a named skill. Skills provide specialized workflows and guidance.",
        args_schema=SkillInput,
    )
