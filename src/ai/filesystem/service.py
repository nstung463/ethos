from __future__ import annotations

import fnmatch
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from src.ai.tools.filesystem._sandbox import resolve
from src.backends.protocol import (
    EditResult,
    FileDownloadResponse,
    FileUploadResponse,
    LsEntry,
    LsResult,
    PathInfo,
    ReadResult,
    SandboxProtocol as FilesystemBackendProtocol,
    WriteResult,
)

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


class FilesystemService:
    def __init__(
        self,
        root_dir: str | Path,
        *,
        backend: FilesystemBackendProtocol | None = None,
    ) -> None:
        self.root = Path(root_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.backend = backend

    def resolve_permission_target(self, path: str, *, base: str | None = None) -> tuple[str, Path]:
        target = self._resolve_workspace_path(path, base=base)
        return self._to_display_path(target), target

    def normalize_path(self, path: str, *, base: str | None = None) -> str:
        return self._to_display_path(self._resolve_workspace_path(path, base=base))

    def format_glob_matches(self, pattern: str, path: str, matches: list[str]) -> str:
        if not matches:
            return f"No files matched '{pattern}' in '{path}'."
        if len(matches) <= MAX_MATCHES:
            return "\n".join(matches)
        visible = "\n".join(matches[:MAX_MATCHES])
        return f"{visible}\n\n[Truncated: showing {MAX_MATCHES} of {len(matches)} matches]"

    def format_grep_matches(self, pattern: str, output_mode: str, matches: list[dict[str, object]]) -> str:
        if not matches:
            return f"No matches found for '{pattern}'."
        if output_mode == "files_with_matches":
            return "\n".join(dict.fromkeys(str(match["path"]) for match in matches))
        if output_mode == "count":
            counts = Counter(str(match["path"]) for match in matches)
            return "\n".join(f"{path}: {count}" for path, count in counts.items())

        visible = [f"{match['path']}:{match['line']}: {match['text']}" for match in matches[:MAX_MATCHES]]
        result = "\n".join(visible)
        if len(matches) > MAX_MATCHES:
            result += f"\n\n[Truncated at {MAX_MATCHES} matches]"
        return result

    def ls(self, path: str = ".") -> str:
        info = self._stat_path(path)
        if not info.exists:
            return f"Error: '{path}' does not exist."
        if info.is_file:
            return self.normalize_path(path)

        result = self._list_dir(path)
        if result.error:
            return f"Error: {result.error}"
        if not result.entries:
            return "(empty directory)"

        lines = [
            f"{self.normalize_path(entry.path)}{'/' if entry.is_dir else ''}"
            for entry in sorted(result.entries, key=lambda entry: (not entry.is_dir, entry.path))
        ]
        return "\n".join(lines)

    def read_file(self, path: str, offset: int = 0, limit: int | None = None) -> str:
        info = self._stat_path(path)
        if not info.exists:
            return f"Error: '{path}' does not exist."
        if info.is_dir:
            return f"Error: '{path}' is a directory. Use ls to list its contents."

        response = self._read_bytes(path, offset=offset, limit=limit)
        if response.error or response.content is None:
            return f"Error: '{path}' does not exist."

        try:
            all_lines = response.content.decode("utf-8").splitlines()
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
            result += f"\n\n[Showing lines {start + 1}-{end} of {total}. Use offset={end} to read more.]"
        return result

    def write_file(self, path: str, content: str) -> str:
        result = self._write_bytes(path, content.encode("utf-8"))
        if result.error:
            return f"Error: {result.error}"
        lines = content.count("\n") + 1
        return f"Written {len(content)} characters ({lines} lines) to '{path}'."

    def edit_file(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        info = self._stat_path(path)
        if not info.exists:
            return f"Error: '{path}' does not exist. Read the file before editing."
        if info.is_dir:
            return f"Error: '{path}' is a directory. Use ls to list its contents."

        response = self._read_bytes(path)
        if response.error or response.content is None:
            return f"Error: '{path}' does not exist. Read the file before editing."

        try:
            content = response.content.decode("utf-8")
        except UnicodeDecodeError:
            return f"Error: '{path}' is not a text file."

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

        updated = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        write_result = self._write_bytes(path, updated.encode("utf-8"))
        if write_result.error:
            return f"Error: {write_result.error}"
        replaced = count if replace_all else 1
        return f"Edited '{path}': replaced {replaced} occurrence(s)."

    def glob_search(self, pattern: str, path: str = ".") -> GlobSearchResult:
        info = self._stat_path(path)
        if not info.exists:
            return GlobSearchResult(error=f"Error: '{path}' does not exist.")

        if info.is_file:
            candidates = [self.normalize_path(path)]
        else:
            candidates = [
                self.normalize_path(entry.path)
                for entry in self._walk(path)
            ]

        matches = [
            candidate for candidate in candidates
            if self._matches_glob(pattern, self._relative_to_base(candidate, path))
        ]
        return GlobSearchResult(matches=sorted(matches))

    def grep_search(self, pattern: str, path: str = ".", glob: str | None = None) -> GrepSearchResult:
        info = self._stat_path(path)
        if not info.exists:
            return GrepSearchResult(error=f"Error: '{path}' does not exist.")

        try:
            regex = re.compile(pattern)
        except re.error as exc:
            return GrepSearchResult(error=f"Error: invalid regex '{pattern}': {exc}")

        entries: list[LsEntry]
        if info.is_file:
            entries = [LsEntry(path=path, is_dir=False)]
        else:
            entries = [entry for entry in self._walk(path) if not entry.is_dir]

        matches: list[dict[str, object]] = []
        for entry in entries:
            display_path = self.normalize_path(entry.path)
            if glob and not fnmatch.fnmatch(PurePosixPath(display_path).name, glob):
                continue

            response = self._read_bytes(entry.path)
            if response.error or response.content is None:
                continue
            try:
                lines = response.content.decode("utf-8").splitlines()
            except UnicodeDecodeError:
                continue

            for line_number, line in enumerate(lines, start=1):
                if regex.search(line):
                    matches.append({"path": display_path, "line": line_number, "text": line})

        return GrepSearchResult(matches=matches)

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

    def _relative_to_base(self, display_path: str, base: str) -> str:
        if base == ".":
            return display_path
        base_display = self.normalize_path(base)
        if display_path == base_display:
            return "."
        prefix = f"{base_display}/"
        return display_path[len(prefix):] if display_path.startswith(prefix) else display_path

    def _matches_glob(self, pattern: str, relative_path: str) -> bool:
        if relative_path == ".":
            return False
        pure = PurePosixPath(relative_path)
        if pure.match(pattern):
            return True
        if pattern.startswith("**/"):
            return pure.match(pattern[3:])
        return False

    def _stat_path(self, path: str) -> PathInfo:
        if self.backend is None:
            target = self._resolve_workspace_path(path)
            exists = target.exists()
            return PathInfo(
                path=path,
                exists=exists,
                is_file=exists and target.is_file(),
                is_dir=exists and target.is_dir(),
                size=target.stat().st_size if exists and target.is_file() else 0,
            )

        stat_path = getattr(self.backend, "stat_path", None)
        if callable(stat_path):
            return stat_path(path)

        read_method = getattr(self.backend, "read", None)
        ls_method = getattr(self.backend, "ls", None)
        if callable(read_method):
            read_result: ReadResult = read_method(path, offset=0, limit=1)
            if read_result.error is None:
                return PathInfo(path=path, exists=True, is_file=True, is_dir=False)
        if callable(ls_method):
            ls_result: LsResult = ls_method(path)
            if ls_result.error is None:
                return PathInfo(path=path, exists=True, is_file=False, is_dir=True)
        return PathInfo(path=path, exists=False, is_file=False, is_dir=False)

    def _list_dir(self, path: str) -> LsResult:
        if self.backend is None:
            target = self._resolve_workspace_path(path)
            if not target.exists():
                return LsResult(error=f"'{path}' does not exist.")
            if target.is_file():
                return LsResult(entries=[LsEntry(path=self._to_display_path(target), is_dir=False)])
            return LsResult(
                entries=[
                    LsEntry(path=self._to_display_path(entry), is_dir=entry.is_dir())
                    for entry in target.iterdir()
                ]
            )

        list_dir = getattr(self.backend, "list_dir", None)
        if callable(list_dir):
            return list_dir(path)

        ls_method = getattr(self.backend, "ls", None)
        if callable(ls_method):
            return ls_method(path)
        return LsResult(error=f"'{path}' does not exist.")

    def _walk(self, path: str) -> list[LsEntry]:
        if self.backend is None:
            target = self._resolve_workspace_path(path)
            if not target.exists():
                return []
            if target.is_file():
                return [LsEntry(path=self._to_display_path(target), is_dir=False)]
            return [
                LsEntry(path=self._to_display_path(entry), is_dir=entry.is_dir())
                for entry in target.rglob("*")
            ]

        walk = getattr(self.backend, "walk", None)
        if callable(walk):
            return walk(path)

        glob_method = getattr(self.backend, "glob", None)
        if callable(glob_method):
            return [LsEntry(path=match, is_dir=False) for match in glob_method("**/*", path)]
        return []

    def _read_bytes(self, path: str, offset: int = 0, limit: int | None = None) -> FileDownloadResponse:
        if self.backend is None:
            target = self._resolve_workspace_path(path)
            if not target.exists() or target.is_dir():
                return FileDownloadResponse(path=path, error="file_not_found")
            return FileDownloadResponse(path=path, content=target.read_bytes())

        read_bytes = getattr(self.backend, "read_bytes", None)
        if callable(read_bytes):
            return read_bytes(path)

        read_method = getattr(self.backend, "read", None)
        if callable(read_method):
            read_result: ReadResult = read_method(path, offset=offset, limit=limit or DEFAULT_READ_LIMIT)
            if read_result.error:
                return FileDownloadResponse(path=path, error=read_result.error)
            return FileDownloadResponse(path=path, content=(read_result.content or "").encode("utf-8"))
        return FileDownloadResponse(path=path, error="file_not_found")

    def _write_bytes(self, path: str, content: bytes) -> FileUploadResponse:
        if self.backend is None:
            target = self._resolve_workspace_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            return FileUploadResponse(path=path)

        write_bytes = getattr(self.backend, "write_bytes", None)
        if callable(write_bytes):
            return write_bytes(path, content)

        write_method = getattr(self.backend, "write", None)
        if callable(write_method):
            write_result: WriteResult = write_method(path, content.decode("utf-8"))
            return FileUploadResponse(path=path, error=write_result.error)
        return FileUploadResponse(path=path, error="write_not_supported")
