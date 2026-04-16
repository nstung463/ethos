from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext
from src.backends.protocol import SandboxProtocol as FilesystemBackendProtocol


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

    return StructuredTool.from_function(
        name="ls",
        func=filesystem.ls,
        description=(
            "List files and directories in the workspace. "
            "Use this before reading or editing files to explore the structure. "
            "Paths are relative to the workspace root."
        ),
        args_schema=LsInput,
    )


__all__ = ["LsInput", "build_ls_tool"]
