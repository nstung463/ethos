"""read_file tool — read file contents with line numbers and optional pagination."""

from pathlib import Path
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.filesystem._sandbox import resolve

DEFAULT_LIMIT = 200


class ReadFileInput(BaseModel):
    path: str = Field(description="File path to read (relative to workspace root).")
    offset: int = Field(
        default=0,
        description="Line number to start reading from (0-indexed). Use for pagination of large files.",
    )
    limit: Optional[int] = Field(
        default=None,
        description=(
            f"Maximum number of lines to read (default: {DEFAULT_LIMIT}). "
            "Omit to read the entire file. Use with offset to paginate large files."
        ),
    )


def _read_file(root: Path, path: str, offset: int = 0, limit: Optional[int] = None) -> str:
    target = resolve(root, path)
    if not target.exists():
        return f"Error: '{path}' does not exist."
    if target.is_dir():
        return f"Error: '{path}' is a directory. Use ls to list its contents."

    try:
        all_lines = target.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return f"Error: '{path}' is not a text file (binary content)."

    total = len(all_lines)
    start = max(0, offset)
    end = total if limit is None else min(total, start + (limit or DEFAULT_LIMIT))
    selected = all_lines[start:end]

    if not selected and total > 0:
        return f"[File has {total} lines, but offset={offset} is past the end.]"
    if not selected:
        return "(empty file)"

    numbered = [f"{i + start + 1:>6}\t{line}" for i, line in enumerate(selected)]
    result = "\n".join(numbered)

    if end < total:
        result += (
            f"\n\n[Showing lines {start + 1}–{end} of {total}. "
            f"Use offset={end} to read more.]"
        )
    return result


def build_read_file_tool(root: Path) -> StructuredTool:
    return StructuredTool.from_function(
        name="read_file",
        func=lambda path, offset=0, limit=None: _read_file(root, path, offset, limit),
        description=(
            "Read a file's contents with line numbers. "
            "Always read a file before editing it. "
            "Use offset and limit to paginate large files. "
            "Paths are relative to the workspace root."
        ),
        args_schema=ReadFileInput,
    )
