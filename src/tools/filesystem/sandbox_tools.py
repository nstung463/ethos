"""Filesystem tools backed by a BaseSandbox (local or remote).

When a sandbox backend is provided, these replace the local pathlib-based tools.
All operations delegate to the sandbox's shell-script implementations, meaning
they work identically for LocalSandbox and DaytonaSandbox.
"""

from langchain_core.tools import StructuredTool

from src.backends.sandbox import BaseSandbox
from src.tools.filesystem.edit_file import EditFileInput
from src.tools.filesystem.glob import GlobInput
from src.tools.filesystem.grep import GrepInput
from src.tools.filesystem.ls import LsInput
from src.tools.filesystem.read_file import ReadFileInput
from src.tools.filesystem.write_file import WriteFileInput


def build_sandbox_filesystem_tools(backend: BaseSandbox) -> list[StructuredTool]:
    """Build all six filesystem tools backed by a sandbox.

    Operations run as Python/shell scripts inside the sandbox via execute(),
    so they work identically for LocalSandbox and DaytonaSandbox.
    """

    def _ls(path: str = "/") -> str:
        result = backend.ls(path)
        if result.error:
            return f"Error: {result.error}"
        if not result.entries:
            return "(empty directory)"
        lines = [f"{e.path}{'/' if e.is_dir else ''}" for e in sorted(result.entries, key=lambda e: (not e.is_dir, e.path))]
        return "\n".join(lines)

    def _read(path: str, offset: int = 0, limit: int | None = None) -> str:
        result = backend.read(path, offset=offset, limit=limit or 200)
        if result.error:
            return f"Error: {result.error}"
        return result.content or "(empty file)"

    def _write(path: str, content: str) -> str:
        result = backend.write(path, content)
        if result.error:
            return f"Error: {result.error}"
        return f"Written {len(content)} characters to '{path}'."

    def _edit(path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        result = backend.edit(path, old_string, new_string, replace_all)
        if result.error:
            return result.error
        return f"Edited '{path}': replaced {result.occurrences} occurrence(s)."

    def _glob(pattern: str, path: str = "/") -> str:
        matches = backend.glob(pattern, path)
        if not matches:
            return f"No files matched '{pattern}' in '{path}'."
        return "\n".join(matches[:500])

    def _grep(pattern: str, path: str = ".", glob: str | None = None, output_mode: str = "content") -> str:
        matches = backend.grep(pattern, path, glob)
        if not matches:
            return f"No matches found for '{pattern}'."
        if output_mode == "files_with_matches":
            return "\n".join(dict.fromkeys(m["path"] for m in matches))
        if output_mode == "count":
            from collections import Counter
            counts = Counter(m["path"] for m in matches)
            return "\n".join(f"{p}: {c}" for p, c in counts.items())
        # content mode
        lines = [f"{m['path']}:{m['line']}: {m['text']}" for m in matches[:500]]
        return "\n".join(lines)

    return [
        StructuredTool.from_function(name="ls", func=_ls,
            description="List files and directories in the sandbox.",
            args_schema=LsInput),
        StructuredTool.from_function(name="read_file", func=_read,
            description="Read a file's contents with line numbers. Use offset/limit to paginate large files.",
            args_schema=ReadFileInput),
        StructuredTool.from_function(name="write_file", func=_write,
            description="Write content to a file in the sandbox, creating parent dirs as needed.",
            args_schema=WriteFileInput),
        StructuredTool.from_function(name="edit_file", func=_edit,
            description="Replace an exact string in a file. Read the file first. old_string must be unique.",
            args_schema=EditFileInput),
        StructuredTool.from_function(name="glob", func=_glob,
            description="Find files matching a glob pattern in the sandbox.",
            args_schema=GlobInput),
        StructuredTool.from_function(name="grep", func=_grep,
            description="Search file contents for a pattern in the sandbox.",
            args_schema=GrepInput),
    ]
