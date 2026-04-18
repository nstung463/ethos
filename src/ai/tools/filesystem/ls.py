from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.ai.tools.filesystem.ls_prompt import render_ls_tool_description
from src.backends.protocol import FilesystemBackendProtocol


class LsInput(BaseModel):
    path: str = Field(
        default=".",
        description="Directory path to list (relative to workspace root). Defaults to root.",
    )


def build_ls_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(path: str = ".") -> str:
        try:
            blocked = permission_error(filesystem, permission_context, PermissionSubject.READ, path.strip() or ".")
        except PermissionError as exc:
            return str(exc)
        if blocked:
            return blocked
        return filesystem.ls(path)

    return StructuredTool.from_function(
        name="ls",
        func=_tool,
        description=render_ls_tool_description(),
        args_schema=LsInput,
    )


__all__ = ["LsInput", "build_ls_tool"]
