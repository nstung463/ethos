from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.backends.protocol import FilesystemBackendProtocol

DEFAULT_LIMIT = 200


class ReadFileInput(BaseModel):
    path: str = Field(description="File path to read (relative to workspace root).")
    offset: int = Field(
        default=0,
        description="Line number to start reading from (0-indexed). Use for pagination of large files.",
    )
    limit: int | None = Field(
        default=None,
        description=(
            f"Maximum number of lines to read (default: {DEFAULT_LIMIT}). "
            "Omit to read the entire file. Use with offset to paginate large files."
        ),
    )


def build_read_file_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(path: str, offset: int = 0, limit: int | None = None) -> str:
        blocked = permission_error(filesystem, permission_context, PermissionSubject.READ, path)
        if blocked:
            return blocked
        return filesystem.read_file(path, offset=offset, limit=limit)

    return StructuredTool.from_function(
        name="read_file",
        func=_tool,
        description=(
            "Read a file's contents with line numbers. "
            "Always read a file before editing it. "
            "Use offset and limit to paginate large files. "
            "Paths are relative to the workspace root."
        ),
        args_schema=ReadFileInput,
    )


__all__ = ["ReadFileInput", "build_read_file_tool"]
