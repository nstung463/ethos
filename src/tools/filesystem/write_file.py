"""write_file tool — create or overwrite a file."""

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.filesystem._sandbox import resolve


class WriteFileInput(BaseModel):
    path: str = Field(description="File path to write (relative to workspace root). Parent directories are created automatically.")
    content: str = Field(description="Full content to write to the file.")


def _write_file(root: Path, path: str, content: str) -> str:
    target = resolve(root, path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    lines = content.count("\n") + 1
    return f"Written {len(content)} characters ({lines} lines) to '{path}'."


def build_write_file_tool(root: Path) -> StructuredTool:
    return StructuredTool.from_function(
        name="write_file",
        func=lambda path, content: _write_file(root, path, content),
        description=(
            "Write content to a file, creating it and parent directories if needed. "
            "Prefer edit_file for modifying existing files — use write_file for new files "
            "or complete rewrites."
        ),
        args_schema=WriteFileInput,
    )
