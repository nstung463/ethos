from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.ai.tools.filesystem.read_prompt import render_read_tool_description
from src.backends.protocol import FilesystemBackendProtocol


class ReadFileInput(BaseModel):
    path: str = Field(description="File path to read (relative to workspace root).")
    offset: int = Field(
        default=1,
        description="Line number to start reading from (1-indexed). Use for pagination of large files.",
    )
    limit: int | None = Field(
        default=None,
        description=(
            "Maximum number of lines to read. Omit to use the default of 2000 lines. "
            "Use with offset to paginate large files."
        ),
    )
    pages: str | None = Field(
        default=None,
        description=(
            'Page range for PDF files (e.g. "1-5", "3", "10-20"). '
            "Only applies to PDF files."
        ),
    )


def build_read_file_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
    filesystem: FilesystemService | None = None,
) -> StructuredTool:
    filesystem = filesystem or FilesystemService(root, backend=backend)

    def _tool(path: str, offset: int = 1, limit: int | None = None, pages: str | None = None) -> str:
        normalized_path = path.strip() or "."
        try:
            blocked = permission_error(filesystem, permission_context, PermissionSubject.READ, normalized_path)
        except PermissionError as exc:
            return str(exc)
        if blocked:
            return blocked
        return filesystem.read_file(normalized_path, offset=offset, limit=limit, pages=pages)

    return StructuredTool.from_function(
        name="read_file",
        func=_tool,
        description=render_read_tool_description(),
        args_schema=ReadFileInput,
    )


__all__ = ["ReadFileInput", "build_read_file_tool"]
