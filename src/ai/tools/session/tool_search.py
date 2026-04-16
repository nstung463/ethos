"""tool_search tool — search available tools by keyword or name."""
from __future__ import annotations

import json

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class ToolSearchInput(BaseModel):
    query: str = Field(
        description="Search query. Use 'select:<tool_name>' for exact match, or keywords to search."
    )
    max_results: int = Field(default=5, description="Maximum number of results to return.")


def build_tool_search_tool(available_tools: list[StructuredTool]) -> StructuredTool:
    def _search(query: str, max_results: int = 5) -> str:
        if query.startswith("select:"):
            names = {n.strip() for n in query[len("select:"):].split(",")}
            matches = [
                {"name": t.name, "description": t.description or ""}
                for t in available_tools if t.name in names
            ]
            return json.dumps({"matches": matches[:max_results], "query": query, "total_tools": len(available_tools)})

        q_lower = query.lower()
        scored: list[tuple[int, dict]] = []
        for t in available_tools:
            name_score = 2 if q_lower in t.name.lower() else 0
            desc_score = 1 if (t.description and q_lower in t.description.lower()) else 0
            score = name_score + desc_score
            if score > 0:
                scored.append((score, {"name": t.name, "description": t.description or ""}))

        scored.sort(key=lambda x: -x[0])
        matches = [item for _, item in scored[:max_results]]
        return json.dumps({"matches": matches, "query": query, "total_tools": len(available_tools)})

    return StructuredTool.from_function(
        name="tool_search",
        func=_search,
        description="Search available tools by keyword or exact name. Use 'select:<name>' for exact lookup.",
        args_schema=ToolSearchInput,
    )
