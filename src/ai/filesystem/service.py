from __future__ import annotations

import fnmatch
import hashlib
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from src.ai.filesystem.read import read_path, render_bytes_read
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


@dataclass(frozen=True)
class FileReadState:
    path: str
    is_full_read: bool
    content_hash: str | None = None


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
        self._read_states: dict[str, FileReadState] = {}

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
        path = self._sanitize_input_path(path)
        try:
            info = self._stat_path(path)
        except PermissionError as exc:
            return str(exc)
        if not info.exists:
            return f"Error: '{path}' does not exist."
        if info.is_file:
            try:
                return self.normalize_path(path)
            except PermissionError as exc:
                return str(exc)

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

    def read_file(
        self,
        path: str,
        offset: int = 1,
        limit: int | None = None,
        pages: str | None = None,
    ) -> str:
        path = self._sanitize_input_path(path)
        try:
            if self.backend is None:
                target = self._resolve_workspace_path(path)
                rendered = read_path(target, display_path=path, offset=offset, limit=limit, pages=pages)
                self._remember_successful_read(path, rendered, limit=limit, pages=pages)
                return rendered

            info = self._stat_path(path)
            if not info.exists:
                return f"Error: '{path}' does not exist."
            if info.is_dir:
                return f"Error: '{path}' is a directory. Use ls to list its contents."

            response = self._read_bytes(path, offset=offset, limit=limit)
            if response.error or response.content is None:
                return f"Error reading '{path}': {response.error or 'no content returned'}."
            rendered = render_bytes_read(
                response.content,
                display_path=path,
                suffix=Path(path).suffix.lower(),
                offset=offset,
                limit=limit,
                pages=pages,
            )
            self._remember_successful_read(path, rendered, limit=limit, pages=pages, content=response.content)
            return rendered
        except PermissionError as exc:
            return str(exc)

    def write_file(self, path: str, content: str) -> str:
        path = self._sanitize_input_path(path)
        try:
            validation_error = self._validate_write_preconditions(path)
        except PermissionError as exc:
            return str(exc)
        if validation_error:
            return validation_error

        result = self._write_bytes(path, content.encode("utf-8"))
        if result.error:
            return f"Error: {result.error}"
        self._read_states[self.normalize_path(path)] = FileReadState(
            path=self.normalize_path(path),
            is_full_read=True,
            content_hash=self._hash_bytes(content.encode("utf-8")),
        )
        lines = content.count("\n") + 1
        return f"Written {len(content)} characters ({lines} lines) to '{path}'."

    def edit_file(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        path = self._sanitize_input_path(path)
        try:
            return self._edit_file_inner(path, old_string, new_string, replace_all)
        except PermissionError as exc:
            return str(exc)

    def _edit_file_inner(self, path: str, old_string: str, new_string: str, replace_all: bool) -> str:
        if old_string == new_string:
            return "No changes to make: old_string and new_string are exactly the same."

        info = self._stat_path(path)

        if info.is_dir:
            return f"Error: '{path}' is a directory. Use ls to list its contents."

        # Create-file path: empty old_string means "write new_string to file".
        # This check must come before the .ipynb guard so that creating a new
        # .ipynb file with old_string="" is allowed (matches Claude Code behaviour).
        if old_string == "":
            if info.exists:
                response = self._read_bytes(path)
                if response.error:
                    return f"Error reading '{path}': {response.error}."
                existing = response.content or b""
                if existing.strip():
                    return "Cannot create new file - file already exists."
            write_result = self._write_bytes(path, new_string.encode("utf-8"))
            if write_result.error:
                return f"Error: {write_result.error}"
            normalized = self.normalize_path(path)
            self._read_states[normalized] = FileReadState(
                path=normalized,
                is_full_read=True,
                content_hash=self._hash_bytes(new_string.encode("utf-8")),
            )
            return f"The file '{path}' has been updated successfully."

        if not info.exists:
            return f"Error: '{path}' does not exist. Read the file before editing."

        if Path(path).suffix.lower() == ".ipynb":
            return "File is a Jupyter Notebook. Use the notebook_edit tool to edit this file."

        # Must have a full read on record before editing
        normalized = self.normalize_path(path)
        read_state = self._read_states.get(normalized)
        if read_state is None or not read_state.is_full_read:
            return "File has not been read yet. Read it first before editing it."

        response = self._read_bytes(path)
        if response.error or response.content is None:
            return f"Error: '{path}' does not exist."

        # Stale-read check
        if read_state.content_hash != self._hash_bytes(response.content):
            return "File has been modified since read. Read it again before attempting to edit it."

        try:
            content = response.content.decode("utf-8")
        except UnicodeDecodeError:
            return f"Error: '{path}' is not a text file."

        count = content.count(old_string)
        if count == 0:
            return f"String to replace not found in file.\nString: {old_string}"
        if count > 1 and not replace_all:
            return (
                f"Found {count} matches of the string to replace, but replace_all is false. "
                "To replace all occurrences, set replace_all to true. "
                "To replace only one occurrence, provide more context to uniquely identify the instance.\n"
                f"String: {old_string}"
            )

        updated = content.replace(old_string, new_string) if replace_all else content.replace(old_string, new_string, 1)
        write_result = self._write_bytes(path, updated.encode("utf-8"))
        if write_result.error:
            return f"Error: {write_result.error}"

        updated_bytes = updated.encode("utf-8")
        self._read_states[normalized] = FileReadState(
            path=normalized,
            is_full_read=True,
            content_hash=self._hash_bytes(updated_bytes),
        )

        if replace_all:
            return f"The file '{path}' has been updated. All occurrences were successfully replaced."
        return f"The file '{path}' has been updated successfully."

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
        path = self._sanitize_input_path(path)
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

    def _sanitize_input_path(self, path: str) -> str:
        stripped = path.strip()
        return stripped or "."

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

    def _remember_successful_read(
        self,
        path: str,
        rendered: str,
        *,
        limit: int | None,
        pages: str | None,
        content: bytes | None = None,
    ) -> None:
        if (
            rendered.startswith("Error:")
            or rendered.startswith("Cannot read ")
            or rendered.startswith("File content (")
            or rendered.startswith("This PDF has ")
            or rendered.startswith("Invalid pages parameter:")
            or rendered.startswith("This tool cannot read binary files.")
            or rendered.startswith("File is not a valid PDF")
            or rendered.startswith("PDF is password-protected.")
            or rendered.startswith("PDF file is corrupted or invalid.")
            or rendered.startswith("pdftoppm failed:")
            or rendered.startswith("pdftoppm is not installed.")
        ):
            return

        normalized_path = self.normalize_path(path)
        is_full_read = limit is None and pages is None and not self._is_partial_read_output(rendered)
        if not is_full_read:
            self._read_states[normalized_path] = FileReadState(path=normalized_path, is_full_read=False)
            return

        payload = content if content is not None else self._read_current_bytes(path)
        if payload is None:
            return
        self._read_states[normalized_path] = FileReadState(
            path=normalized_path,
            is_full_read=True,
            content_hash=self._hash_bytes(payload),
        )

    def _validate_write_preconditions(self, path: str) -> str | None:
        info = self._stat_path(path)
        if not info.exists:
            return None
        if info.is_dir:
            return f"Error: '{path}' is a directory. Use ls to list its contents."

        read_state = self._read_states.get(self.normalize_path(path))
        if read_state is None or not read_state.is_full_read:
            return "File has not been read yet. Read it first before writing to it."

        current_content = self._read_current_bytes(path)
        if current_content is None:
            return f"Error: '{path}' does not exist."
        if read_state.content_hash != self._hash_bytes(current_content):
            return "File has been modified since read. Read it again before attempting to write it."
        return None

    def _read_current_bytes(self, path: str) -> bytes | None:
        response = self._read_bytes(path)
        if response.error or response.content is None:
            return None
        return response.content

    def _hash_bytes(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    def _is_partial_read_output(self, rendered: str) -> bool:
        return rendered.startswith("[Showing lines ") or "\n\n[Showing lines " in rendered
