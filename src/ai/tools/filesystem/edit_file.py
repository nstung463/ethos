from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.ai.tools.filesystem.edit_prompt import render_edit_tool_description
from src.backends.protocol import FilesystemBackendProtocol


class EditFileInput(BaseModel):
    path: str = Field(description="File path to edit (relative to workspace root).")
    old_string: str = Field(
        description=(
            "The text to replace. Must appear exactly once in the file unless replace_all=True. "
            "Include enough surrounding context to make it unique."
        )
    )
    new_string: str = Field(description="The text to replace it with (must be different from old_string).")
    replace_all: bool = Field(
        default=False,
        description="Replace all occurrences of old_string (default false).",
    )


def build_edit_file_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
    filesystem: FilesystemService | None = None,
) -> StructuredTool:
    filesystem = filesystem or FilesystemService(root, backend=backend)

    def _tool(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        normalized_path = path.strip() or "."
        try:
            blocked = permission_error(filesystem, permission_context, PermissionSubject.EDIT, normalized_path)
        except PermissionError as exc:
            return str(exc)
        if blocked:
            return blocked
        return filesystem.edit_file(normalized_path, old_string, new_string, replace_all)

    return StructuredTool.from_function(
        name="edit_file",
        func=_tool,
        description=render_edit_tool_description(),
        args_schema=EditFileInput,
    )


__all__ = ["EditFileInput", "build_edit_file_tool"]
