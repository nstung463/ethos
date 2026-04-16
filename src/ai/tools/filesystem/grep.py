from __future__ import annotations

from pathlib import Path
from typing import Literal

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.ai.filesystem import FilesystemService
from src.ai.permissions.types import PermissionContext, PermissionSubject
from src.ai.tools.filesystem._shared import permission_error
from src.backends.protocol import FilesystemBackendProtocol


class GrepInput(BaseModel):
    pattern: str = Field(description="Regex pattern to search for in file contents.")
    path: str = Field(
        default=".",
        description="File or directory to search in (relative to workspace root). Defaults to root.",
    )
    glob: str | None = Field(
        default=None,
        description="Glob filter to restrict which files are searched (e.g. '*.py', '*.ts').",
    )
    output_mode: Literal["files_with_matches", "content", "count"] = Field(
        default="content",
        description=(
            "'content' (default): show matching lines with file:line format. "
            "'files_with_matches': show only file paths. "
            "'count': show match count per file."
        ),
    )


def build_grep_tool(
    root: Path,
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> StructuredTool:
    filesystem = FilesystemService(root, backend=backend)

    def _tool(
        pattern: str,
        path: str = ".",
        glob: str | None = None,
        output_mode: str = "content",
    ) -> str:
        blocked = permission_error(filesystem, permission_context, PermissionSubject.READ, path)
        if blocked:
            return blocked

        result = filesystem.grep_search(pattern, path, glob)
        if result.error:
            return result.error

        matches = [
            match
            for match in result.matches
            if permission_error(filesystem, permission_context, PermissionSubject.READ, str(match["path"])) is None
        ]
        return filesystem.format_grep_matches(pattern, output_mode, matches)

    return StructuredTool.from_function(
        name="grep",
        func=_tool,
        description=(
            "Search file contents using a regex pattern. "
            "Returns matching lines in file:line: content format. "
            "Use glob to restrict which file types are searched."
        ),
        args_schema=GrepInput,
    )


__all__ = ["GrepInput", "build_grep_tool"]
