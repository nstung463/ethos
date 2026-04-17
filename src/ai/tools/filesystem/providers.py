from __future__ import annotations

import fnmatch
import re
from abc import ABC, abstractmethod
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from src.ai.tools.filesystem._sandbox import resolve

DEFAULT_READ_LIMIT = 200
MAX_MATCHES = 500


@dataclass(frozen=True)
class GlobSearchResult:
    matches: list[str] = field(default_factory=list)
    error: str | None = None


@dataclass(frozen=True)
class GrepSearchResult:
    matches: list[dict[str, object]] = field(default_factory=list)
    error: str | None = None


class BaseFilesystemToolProvider(ABC):
    def __init__(self, root_dir: str | Path) -> None:
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve_permission_target(self, path: str, *, base: str | None = None) -> tuple[str, Path]:
        target = self._resolve_workspace_path(path, base=base)
        return self._to_permission_candidate(target), target

    def normalize_path(self, path: str, *, base: str | None = None) -> str:
        return self._to_display_path(self._resolve_workspace_path(path, base=base))

    def format_glob_matches(self, pattern: str, path: str, matches: list[str]) -> str:
        if not matches:
            return f"No files matched '{pattern}' in '{path}'."
        if len(matches) <= MAX_MATCHES:
            return "\n".join(matches)
        visible = "\n".join(matches[:MAX_MATCHES])
        return f"{visible}\n\n[Truncated: showing {MAX_MATCHES} of {len(matches)} matches]"

    def format_grep_matches(
        self,
        pattern: str,
        output_mode: str,
        matches: list[dict[str, object]],
    ) -> str:
        if not matches:
            return f"No matches found for '{pattern}'."
        if output_mode == "files_with_matches":
            return "\n".join(dict.fromkeys(str(match["path"]) for match in matches))
        if output_mode == "count":
            counts = Counter(str(match["path"]) for match in matches)
            return "\n".join(f"{path}: {count}" for path, count in counts.items())

        visible = [
            f"{match['path']}:{match['line']}: {match['text']}"
            for match in matches[:MAX_MATCHES]
        ]
        result = "\n".join(visible)
        if len(matches) > MAX_MATCHES:
            result += f"\n\n[Truncated at {MAX_MATCHES} matches]"
        return result

    @abstractmethod
    def ls(self, path: str = ".") -> str: ...

    @abstractmethod
    def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> str: ...

    @abstractmethod
    def write_file(self, path: str, content: str) -> str: ...

    @abstractmethod
    def edit_file(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str: ...

    @abstractmethod
    def glob_search(self, pattern: str, path: str = ".") -> GlobSearchResult: ...

    @abstractmethod
    def grep_search(
        self,
        pattern: str,
        path: str = ".",
        glob: str | None = None,
    ) -> GrepSearchResult: ...

    def _resolve_workspace_path(self, path: str, *, base: str | None = None) -> Path:
        if not base or path.startswith("/"):
            return resolve(self.root, path)

        base_target = resolve(self.root, base)
        target = (base_target / path).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as exc:
            raise PermissionError(
                f"Path '{path}' resolves outside the workspace root '{self.root}'. Access denied."
            ) from exc
        return target

    def _to_display_path(self, target: Path) -> str:
        relative = target.relative_to(self.root)
        return "." if relative == Path(".") else relative.as_posix()

    def _to_permission_candidate(self, target: Path) -> str:
        relative = target.relative_to(self.root)
        return "." if relative == Path(".") else relative.as_posix()


class LocalFilesystemToolProvider(BaseFilesystemToolProvider):
    def ls(self, path: str = ".") -> str:
        target = resolve(self.root, path)
        if not target.exists():
            return f"Error: '{path}' does not exist."
        if target.is_file():
            return self._to_display_path(target)

        entries = sorted(
            target.iterdir(),
            key=lambda entry: (entry.is_file(), entry.name),
        )
        if not entries:
            return "(empty directory)"

        lines = [
            f"{self._to_display_path(entry)}{'/' if entry.is_dir() else ''}"
            for entry in entries
        ]
        return "\n".join(lines)

    def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> str:
        target = resolve(self.root, path)
        if not target.exists():
            return f"Error: '{path}' does not exist."
        if target.is_dir():
            return f"Error: '{path}' is a directory. Use ls to list its contents."

        try:
            all_lines = target.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            return f"Error: '{path}' is not a text file (binary content)."

        total = len(all_lines)
        start = max(0, offset)
        end = total if limit is None else min(total, start + (limit or DEFAULT_READ_LIMIT))
        selected = all_lines[start:end]

        if not selected and total > 0:
            return f"[File has {total} lines, but offset={offset} is past the end.]"
        if not selected:
            return "(empty file)"

        numbered = [f"{i + start + 1:>6}\t{line}" for i, line in enumerate(selected)]
        result = "\n".join(numbered)
        if end < total:
            result += (
                f"\n\n[Showing lines {start + 1}-{end} of {total}. "
                f"Use offset={end} to read more.]"
            )
        return result

    def write_file(self, path: str, content: str) -> str:
        target = resolve(self.root, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        lines = content.count("\n") + 1
        return f"Written {len(content)} characters ({lines} lines) to '{path}'."

    def edit_file(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        target = resolve(self.root, path)
        if not target.exists():
            return f"Error: '{path}' does not exist. Read the file before editing."

        content = target.read_text(encoding="utf-8")
        count = content.count(old_string)

        if count == 0:
            return (
                f"Error: old_string not found in '{path}'. "
                "Make sure the string matches exactly (including indentation and whitespace)."
            )
        if count > 1 and not replace_all:
            return (
                f"Error: old_string appears {count} times in '{path}'. "
                "Provide more surrounding context to make it unique, or set replace_all=True."
            )

        new_content = content.replace(old_string, new_string)
        target.write_text(new_content, encoding="utf-8")
        replaced = count if replace_all else 1
        return f"Edited '{path}': replaced {replaced} occurrence(s)."

    def glob_search(self, pattern: str, path: str = ".") -> GlobSearchResult:
        search_root = resolve(self.root, path)
        if not search_root.exists():
            return GlobSearchResult(error=f"Error: '{path}' does not exist.")

        matches = [
            self._to_display_path(match)
            for match in sorted(search_root.glob(pattern))
        ]
        return GlobSearchResult(matches=matches)

    def grep_search(
        self,
        pattern: str,
        path: str = ".",
        glob: str | None = None,
    ) -> GrepSearchResult:
        target = resolve(self.root, path)
        if not target.exists():
            return GrepSearchResult(error=f"Error: '{path}' does not exist.")

        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return GrepSearchResult(error=f"Error: invalid regex '{pattern}': {exc}")

        if target.is_file():
            files = [target]
        else:
            files = sorted(file_path for file_path in target.rglob("*") if file_path.is_file())
            if glob:
                files = [file_path for file_path in files if fnmatch.fnmatch(file_path.name, glob)]

        matches: list[dict[str, object]] = []
        for file_path in files:
            try:
                lines = file_path.read_text(encoding="utf-8").splitlines()
            except (UnicodeDecodeError, OSError):
                continue

            display_path = self._to_display_path(file_path)
            for line_number, line in enumerate(lines, 1):
                if regex.search(line):
                    matches.append(
                        {"path": display_path, "line": line_number, "text": line}
                    )

        return GrepSearchResult(matches=matches)


class SandboxFilesystemToolProvider(BaseFilesystemToolProvider):
    def __init__(self, root_dir: str | Path, backend: object) -> None:
        super().__init__(root_dir)
        self.backend = backend

    def ls(self, path: str = ".") -> str:
        result = self.backend.ls(path)
        if result.error:
            return f"Error: {result.error}"
        if not result.entries:
            return "(empty directory)"

        lines = [
            f"{self.normalize_path(entry.path, base=path)}{'/' if entry.is_dir else ''}"
            for entry in sorted(result.entries, key=lambda entry: (not entry.is_dir, entry.path))
        ]
        return "\n".join(lines)

    def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> str:
        result = self.backend.read(path, offset=offset, limit=limit)
        if result.error:
            return f"Error: {result.error}"
        return result.content or "(empty file)"

    def write_file(self, path: str, content: str) -> str:
        result = self.backend.write(path, content)
        if result.error:
            return f"Error: {result.error}"
        lines = content.count("\n") + 1
        return f"Written {len(content)} characters ({lines} lines) to '{path}'."

    def edit_file(
        self,
        path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        result = self.backend.edit(path, old_string, new_string, replace_all)
        if result.error:
            return result.error
        return f"Edited '{path}': replaced {result.occurrences} occurrence(s)."

    def glob_search(self, pattern: str, path: str = ".") -> GlobSearchResult:
        matches = [
            self.normalize_path(match, base=path)
            for match in self.backend.glob(pattern, path)
        ]
        return GlobSearchResult(matches=matches)

    def grep_search(
        self,
        pattern: str,
        path: str = ".",
        glob: str | None = None,
    ) -> GrepSearchResult:
        matches = [
            {
                "path": self.normalize_path(str(match["path"]), base=path),
                "line": match["line"],
                "text": match["text"],
            }
            for match in self.backend.grep(pattern, path, glob)
        ]
        return GrepSearchResult(matches=matches)

