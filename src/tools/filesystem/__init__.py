"""Filesystem tools — sandboxed to workspace root_dir.

Each tool lives in its own module; this package exports the builder function.
"""

from pathlib import Path

from langchain_core.tools import StructuredTool

from src.tools.filesystem.edit_file import build_edit_file_tool
from src.tools.filesystem.glob import build_glob_tool
from src.tools.filesystem.grep import build_grep_tool
from src.tools.filesystem.ls import build_ls_tool
from src.tools.filesystem.notebook_edit import build_notebook_edit_tool
from src.tools.filesystem.read_file import build_read_file_tool
from src.tools.filesystem.write_file import build_write_file_tool


def build_filesystem_tools(root_dir: str = "./workspace") -> list[StructuredTool]:
    """Build the six core filesystem tools sandboxed to root_dir.

    Note: notebook_edit is exported separately via build_notebook_edit_tool
    because it requires the optional nbformat dependency.

    Creates the workspace directory if it doesn't exist.

    Returns:
        [ls, read_file, write_file, edit_file, glob, grep]
    """
    root = Path(root_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)

    return [
        build_ls_tool(root),
        build_read_file_tool(root),
        build_write_file_tool(root),
        build_edit_file_tool(root),
        build_glob_tool(root),
        build_grep_tool(root),
    ]


__all__ = ["build_filesystem_tools", "build_notebook_edit_tool"]
