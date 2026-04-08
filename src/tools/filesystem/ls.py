"""ls tool — list directory contents."""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.filesystem._sandbox import resolve


class LsInput(BaseModel):
    path: str = Field(
        default=".",
        description="Directory path to list (relative to workspace root). Defaults to root.",
    )


def _ls(root: Path, path: str) -> str:
    target = resolve(root, path)
    if not target.exists():
        return f"Error: '{path}' does not exist."
    if target.is_file():
        return str(target.relative_to(root))

    entries = sorted(target.iterdir(), key=lambda p: (p.is_file(), p.name))
    if not entries:
        return "(empty directory)"

    lines = []
    for entry in entries:
        rel = entry.relative_to(root)
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{rel}{suffix}")
    return "\n".join(lines)


def build_ls_tool(root: Path) -> StructuredTool:
    return StructuredTool.from_function(
        name="ls",
        func=lambda path=".": _ls(root, path),
        description=(
            "List files and directories in the workspace. "
            "Use this before reading or editing files to explore the structure. "
            "Paths are relative to the workspace root."
        ),
        args_schema=LsInput,
    )
