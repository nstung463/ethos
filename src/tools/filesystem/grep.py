"""grep tool — search file contents with regex."""

import fnmatch
import re
from pathlib import Path
from typing import Literal, Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from src.tools.filesystem._sandbox import resolve

MAX_MATCHES = 500


class GrepInput(BaseModel):
    pattern: str = Field(description="Regex pattern to search for in file contents.")
    path: str = Field(
        default=".",
        description="File or directory to search in (relative to workspace root). Defaults to root.",
    )
    glob: Optional[str] = Field(
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


def _grep(
    root: Path,
    pattern: str,
    path: str = ".",
    glob: Optional[str] = None,
    output_mode: str = "content",
) -> str:
    target = resolve(root, path)
    if not target.exists():
        return f"Error: '{path}' does not exist."

    try:
        regex = re.compile(pattern)
    except re.error as e:
        return f"Error: invalid regex '{pattern}': {e}"

    def get_files() -> list[Path]:
        if target.is_file():
            return [target]
        files = sorted(f for f in target.rglob("*") if f.is_file())
        if glob:
            files = [f for f in files if fnmatch.fnmatch(f.name, glob)]
        return files

    files = get_files()
    results: list[str] = []

    for file_path in files:
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue

        rel = file_path.relative_to(root)

        if output_mode == "files_with_matches":
            if any(regex.search(line) for line in lines):
                results.append(str(rel))
        elif output_mode == "count":
            count = sum(1 for line in lines if regex.search(line))
            if count:
                results.append(f"{rel}: {count}")
        else:  # content
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    results.append(f"{rel}:{i}: {line}")
                    if len(results) >= MAX_MATCHES:
                        results.append(f"\n[Truncated at {MAX_MATCHES} matches]")
                        return "\n".join(results)

    if not results:
        return f"No matches found for '{pattern}'."
    return "\n".join(results)


def build_grep_tool(root: Path) -> StructuredTool:
    return StructuredTool.from_function(
        name="grep",
        func=lambda pattern, path=".", glob=None, output_mode="content": _grep(
            root, pattern, path, glob, output_mode
        ),
        description=(
            "Search file contents using a regex pattern. "
            "Returns matching lines in file:line: content format. "
            "Use glob to restrict which file types are searched."
        ),
        args_schema=GrepInput,
    )
