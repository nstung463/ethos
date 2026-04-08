"""glob tool — find files matching a glob pattern."""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.filesystem._sandbox import resolve


class GlobInput(BaseModel):
    pattern: str = Field(
        description=(
            "Glob pattern to match files. Examples: '**/*.py' (all Python files), "
            "'src/**/*.ts' (TypeScript in src/), '*.json' (JSON in root)."
        )
    )
    path: str = Field(
        default=".",
        description="Base directory to search from (relative to workspace root). Defaults to root.",
    )


def _glob(root: Path, pattern: str, path: str = ".") -> str:
    search_root = resolve(root, path)
    if not search_root.exists():
        return f"Error: '{path}' does not exist."

    matches = sorted(search_root.glob(pattern))
    if not matches:
        return f"No files matched '{pattern}' in '{path}'."

    lines = [str(m.relative_to(root)) for m in matches]
    result = "\n".join(lines)
    if len(lines) > 500:
        result = "\n".join(lines[:500]) + f"\n\n[Truncated: showing 500 of {len(lines)} matches]"
    return result


def build_glob_tool(root: Path) -> StructuredTool:
    return StructuredTool.from_function(
        name="glob",
        func=lambda pattern, path=".": _glob(root, pattern, path),
        description=(
            "Find files matching a glob pattern. "
            "Supports ** for recursive search. "
            "Returns paths relative to workspace root."
        ),
        args_schema=GlobInput,
    )
