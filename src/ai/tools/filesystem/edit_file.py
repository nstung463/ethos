from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.backends.protocol import FilesystemBackendProtocol


class EditFileInput(BaseModel):
    path: str = Field(description="File path to edit (relative to workspace root).")
    old_string: str = Field(
        description=(
            "Exact string to find and replace. Must appear exactly once in the file "
            "unless replace_all=True. Include enough surrounding context to make it unique."
        )
    )
    new_string: str = Field(description="Replacement string. Must be different from old_string.")
    replace_all: bool = Field(
        default=False,
        description="If True, replace all occurrences. If False (default), old_string must be unique.",
    )


def build_edit_file_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        blocked = permission_error(filesystem, permission_context, PermissionSubject.EDIT, path)
        if blocked:
            return blocked
        return filesystem.edit_file(path, old_string, new_string, replace_all)

    return StructuredTool.from_function(
        name="edit_file",
        func=_tool,
        description=(
            "Replace an exact string in a file. "
            "You MUST read the file first. "
            "old_string must be unique in the file (or use replace_all=True). "
            "Preserve exact indentation from the read output."
        ),
        args_schema=EditFileInput,
    )


__all__ = ["EditFileInput", "build_edit_file_tool"]
