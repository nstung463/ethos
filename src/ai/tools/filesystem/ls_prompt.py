from __future__ import annotations

DESCRIPTION = "List files and directories in the workspace."


def render_ls_tool_description() -> str:
    return (
        "List files and directories in the workspace.\n\n"
        "Usage:\n"
        "- Use this tool to explore directory structure before reading or editing files.\n"
        "- Paths are relative to the workspace root. Defaults to the root if no path is provided.\n"
        "- Directories are shown with a trailing '/'. Directories are listed before files.\n"
        "- If a file path is given instead of a directory, the path of that file is returned.\n"
        "- This tool cannot list paths outside the workspace root.\n"
        "- If the path does not exist, an error is returned."
    )


__all__ = ["DESCRIPTION", "render_ls_tool_description"]
