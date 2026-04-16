"""tavily_search tool — web search via Tavily API."""

import os

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field


class TavilySearchInput(BaseModel):
    query: str = Field(description="The search query.")
    max_results: int = Field(
        default=5,
        description="Maximum number of results to return (1–10).",
    )


def _search(query: str, max_results: int = 5) -> str:
    try:
        from tavily import TavilyClient
    except ImportError:
        return "Error: tavily-python not installed. Run: pip install tavily-python"

    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return "Error: TAVILY_API_KEY environment variable not set."

    client = TavilyClient(api_key=api_key)
    max_results = max(1, min(10, max_results))

    try:
        response = client.search(query, max_results=max_results)
    except Exception as e:
        return f"Search error: {e}"

    results = response.get("results", [])
    if not results:
        return f"No results found for '{query}'."

    parts = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "No title")
        url = r.get("url", "")
        content = r.get("content", "").strip()[:600]
        parts.append(f"[{i}] {title}\n    URL: {url}\n    {content}")

    return "\n\n".join(parts)


tavily_search = StructuredTool.from_function(
    name="tavily_search",
    func=_search,
    description=(
        "Search the web for current information. "
        "Returns titles, URLs, and content snippets. "
        "Use for facts, documentation, news, or anything not in the codebase."
    ),
    args_schema=TavilySearchInput,
)
