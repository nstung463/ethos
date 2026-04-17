from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.backends.protocol import FilesystemBackendProtocol


class GlobInput(BaseModel):
    pattern: str = Field(
        description=(
            "Glob pattern to match files. Examples: '**/*.py' (all Python files), "
            "'src/**/*.ts' (TypeScript in src/), '*.json' (JSON in root)."
        )
    )
    path: str = Field(
        default=".",
        description="Base directory to search from (relative to workspace root). Defaults to root.",
    )


def build_glob_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(pattern: str, path: str = ".") -> str:
        blocked = permission_error(filesystem, permission_context, PermissionSubject.READ, path)
        if blocked:
            return blocked

        result = filesystem.glob_search(pattern, path)
        if result.error:
            return result.error

        matches = [
            match
            for match in result.matches
            if permission_error(filesystem, permission_context, PermissionSubject.READ, match) is None
        ]
        return filesystem.format_glob_matches(pattern, path, matches)

    return StructuredTool.from_function(
        name="glob",
        func=_tool,
        description=(
            "Find files matching a glob pattern. "
            "Supports ** for recursive search. "
            "Returns paths relative to workspace root."
        ),
        args_schema=GlobInput,
    )


__all__ = ["GlobInput", "build_glob_tool"]
