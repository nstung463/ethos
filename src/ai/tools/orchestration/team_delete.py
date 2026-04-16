"""team_delete tool — remove an agent team."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TeamDeleteInput(BaseModel):
    name: str = Field(description="Name of the team to delete.")


def build_team_delete_tool(registry: dict[str, Any]) -> StructuredTool:
    def _delete(name: str) -> str:
        if name not in registry:
            return f"Error: team '{name}' not found."
        del registry[name]
        return json.dumps({"deleted": True, "name": name})

    return StructuredTool.from_function(
        name="team_delete", func=_delete,
        description="Delete an agent team by name.",
        args_schema=TeamDeleteInput,
    )
