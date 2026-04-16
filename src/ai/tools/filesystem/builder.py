from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.ai.permissions.types import PermissionContext
from src.ai.tools.filesystem.edit_file import EditFileInput, build_edit_file_tool
from src.ai.tools.filesystem.glob import GlobInput, build_glob_tool
from src.ai.tools.filesystem.grep import GrepInput, build_grep_tool
from src.ai.tools.filesystem.ls import LsInput, build_ls_tool
from src.ai.tools.filesystem.read_file import ReadFileInput, build_read_file_tool
from src.ai.tools.filesystem.write_file import WriteFileInput, build_write_file_tool
from src.backends.protocol import SandboxProtocol as FilesystemBackendProtocol


class FilesystemToolBuilder:
    def __init__(
        self,
        root_dir: str | Path = "./workspace",
        *,
        backend: FilesystemBackendProtocol | None = None,
        permission_context: PermissionContext | None = None,
    ) -> None:
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.backend = backend
        self.permission_context = permission_context

    def build_tools(self) -> list[StructuredTool]:
        return [
            self.build_ls_tool(),
            self.build_read_file_tool(),
            self.build_write_file_tool(),
            self.build_edit_file_tool(),
            self.build_glob_tool(),
            self.build_grep_tool(),
        ]

    def build_tool(self, name: str) -> StructuredTool:
        builders = {
            "ls": self.build_ls_tool,
            "read_file": self.build_read_file_tool,
            "write_file": self.build_write_file_tool,
            "edit_file": self.build_edit_file_tool,
            "glob": self.build_glob_tool,
            "grep": self.build_grep_tool,
        }
        return builders[name]()

    def build_ls_tool(self) -> StructuredTool:
        return build_ls_tool(self.root, backend=self.backend, permission_context=self.permission_context)

    def build_read_file_tool(self) -> StructuredTool:
        return build_read_file_tool(self.root, backend=self.backend, permission_context=self.permission_context)

    def build_write_file_tool(self) -> StructuredTool:
        return build_write_file_tool(self.root, backend=self.backend, permission_context=self.permission_context)

    def build_edit_file_tool(self) -> StructuredTool:
        return build_edit_file_tool(self.root, backend=self.backend, permission_context=self.permission_context)

    def build_glob_tool(self) -> StructuredTool:
        return build_glob_tool(self.root, backend=self.backend, permission_context=self.permission_context)

    def build_grep_tool(self) -> StructuredTool:
        return build_grep_tool(self.root, backend=self.backend, permission_context=self.permission_context)


def build_filesystem_tools(
    root_dir: str = "./workspace",
    backend: FilesystemBackendProtocol | None = None,
    permission_context: PermissionContext | None = None,
) -> list[StructuredTool]:
    return FilesystemToolBuilder(
        root_dir=root_dir,
        backend=backend,
        permission_context=permission_context,
    ).build_tools()


__all__ = [
    "EditFileInput",
    "FilesystemToolBuilder",
    "GlobInput",
    "GrepInput",
    "LsInput",
    "ReadFileInput",
    "WriteFileInput",
    "build_filesystem_tools",
]
