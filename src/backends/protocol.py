"""Backend protocol — abstract interface all sandbox backends must implement.

Mirrors the SandboxBackendProtocol in deepagents but implemented from scratch.
Backends only need to implement three primitives:
  - execute(command) → run a shell command, return output + exit_code
  - upload_files([(path, bytes)]) → write bytes to sandbox paths
  - download_files([path]) → read bytes from sandbox paths

Some backends derive higher-level filesystem operations (ls, read, write, edit,
glob, grep) from those three primitives via a command-backed base class, while
others implement them natively.
"""

from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ── Response types ─────────────────────────────────────────────────────────────

@dataclass
class ExecuteResponse:
    """Result of a shell command execution."""

    output: str
    """Combined stdout (+ stderr if redirected) from the command."""

    exit_code: int
    """Process exit code. 0 = success."""

    truncated: bool = False
    """True if the output was truncated due to size limits."""


@dataclass
class FileDownloadResponse:
    """Result of a single file download."""

    path: str
    content: bytes | None = None
    error: str | None = None  # 'file_not_found' | 'permission_denied' | ...


@dataclass
class FileUploadResponse:
    """Result of a single file upload."""

    path: str
    error: str | None = None


@dataclass
class ReadResult:
    """Result of a file read operation."""

    content: str | None = None
    error: str | None = None


@dataclass
class WriteResult:
    """Result of a file write operation."""

    path: str | None = None
    error: str | None = None


@dataclass
class EditResult:
    """Result of a file edit (string replacement) operation."""

    path: str | None = None
    occurrences: int = 0
    error: str | None = None


@dataclass
class LsEntry:
    path: str
    is_dir: bool


@dataclass
class LsResult:
    entries: list[LsEntry] = field(default_factory=list)
    error: str | None = None


@dataclass
class PathInfo:
    path: str
    exists: bool
    is_file: bool
    is_dir: bool
    size: int | None = None


# ── Protocol ───────────────────────────────────────────────────────────────────

@runtime_checkable
class SandboxProtocol(Protocol):
    """Minimal interface that all backends must implement."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this sandbox instance."""
        ...

    @property
    @abstractmethod
    def supported_shells(self) -> set[str]:
        """Shell tool names supported by this backend."""
        ...

    @abstractmethod
    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Run a shell command inside the sandbox."""
        ...

    @abstractmethod
    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Write files into the sandbox. Paths must be absolute."""
        ...

    @abstractmethod
    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Read files from the sandbox. Paths must be absolute."""
        ...


@runtime_checkable
class FilesystemBackendProtocol(SandboxProtocol, Protocol):
    """Low-level filesystem primitives used by higher-level filesystem tools."""

    @abstractmethod
    def read_bytes(self, path: str) -> FileDownloadResponse:
        """Read raw bytes from a backend-relative path."""
        ...

    @abstractmethod
    def write_bytes(self, path: str, content: bytes) -> FileUploadResponse:
        """Write raw bytes to a backend-relative path."""
        ...

    @abstractmethod
    def stat_path(self, path: str) -> PathInfo:
        """Return basic metadata for a backend-relative path."""
        ...

    @abstractmethod
    def list_dir(self, path: str) -> LsResult:
        """List one directory level for a backend-relative path."""
        ...

    @abstractmethod
    def walk(self, path: str) -> list[LsEntry]:
        """Recursively walk a backend-relative path and return entries."""
        ...
