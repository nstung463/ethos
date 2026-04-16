from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.backends.protocol import FilesystemBackendProtocol


class WriteFileInput(BaseModel):
    path: str = Field(
        description="File path to write (relative to workspace root). Parent directories are created automatically."
    )
    content: str = Field(description="Full content to write to the file.")


def build_write_file_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(path: str, content: str) -> str:
        blocked = permission_error(filesystem, permission_context, PermissionSubject.EDIT, path)
        if blocked:
            return blocked
        return filesystem.write_file(path, content)

    return StructuredTool.from_function(
        name="write_file",
        func=_tool,
        description=(
            "Write content to a file, creating it and parent directories if needed. "
            "Prefer edit_file for modifying existing files - use write_file for new files "
            "or complete rewrites."
        ),
        args_schema=WriteFileInput,
    )


__all__ = ["WriteFileInput", "build_write_file_tool"]
