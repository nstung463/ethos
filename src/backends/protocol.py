"""Backend protocol — abstract interface all sandbox backends must implement.

Mirrors the SandboxBackendProtocol in deepagents but implemented from scratch.
Backends only need to implement three primitives:
  - execute(command) → run a shell command, return output + exit_code
  - upload_files([(path, bytes)]) → write bytes to sandbox paths
  - download_files([path]) → read bytes from sandbox paths

All higher-level operations (ls, read, write, edit, glob, grep) are derived
from those three primitives in BaseSandbox.
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


# ── Protocol ───────────────────────────────────────────────────────────────────

@runtime_checkable
class SandboxProtocol(Protocol):
    """Minimal interface that all backends must implement."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this sandbox instance."""
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
