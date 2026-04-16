"""team_create tool — register a new agent team."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TeamCreateInput(BaseModel):
    name: str = Field(description="Unique team name.")
    description: str = Field(description="What this team does.")


def build_team_create_tool(registry: dict[str, Any]) -> StructuredTool:
    def _create(name: str, description: str) -> str:
        registry[name] = {"name": name, "description": description}
        return json.dumps({"created": True, "name": name})

    return StructuredTool.from_function(
        name="team_create", func=_create,
        description="Create a new agent team.",
        args_schema=TeamCreateInput,
    )
