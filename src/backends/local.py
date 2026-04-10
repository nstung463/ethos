"""LocalSandbox — runs commands via subprocess on the local machine.

Used when no remote sandbox is configured. The workspace root acts as
the sandbox boundary; commands run in a subprocess with cwd=root.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from uuid import uuid4

from src.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from src.backends.sandbox import BaseSandbox


class LocalSandbox(BaseSandbox):
    """Local process sandbox. Commands run via subprocess, files via pathlib."""

    def __init__(self, root_dir: str = "./workspace", timeout: int = 120) -> None:
        self._root = Path(root_dir).resolve()
        self._root.mkdir(parents=True, exist_ok=True)
        self._default_timeout = timeout
        self._id = str(uuid4())

    @property
    def id(self) -> str:
        return self._id

    @property
    def supported_shells(self) -> set[str]:
        return {"powershell"} if os.name == "nt" else {"bash"}

    @property
    def root(self) -> Path:
        return self._root

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Run a shell command in the workspace root via subprocess."""
        effective_timeout = timeout if timeout is not None else self._default_timeout
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self._root),
                timeout=effective_timeout,
            )
            output = result.stdout
            if result.stderr.strip():
                output += f"\n<stderr>{result.stderr.strip()}</stderr>"
            return ExecuteResponse(
                output=output,
                exit_code=result.returncode,
                truncated=False,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                output=f"Command timed out after {effective_timeout}s",
                exit_code=124,
                truncated=False,
            )
        except Exception as e:
            return ExecuteResponse(output=str(e), exit_code=1, truncated=False)

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        responses = []
        for path, content in files:
            try:
                p = Path(path)
                if not p.is_absolute():
                    p = self._root / path
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(content)
                responses.append(FileUploadResponse(path=path))
            except Exception as e:
                responses.append(FileUploadResponse(path=path, error=str(e)))
        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        responses = []
        for path in paths:
            try:
                p = Path(path)
                if not p.is_absolute():
                    p = self._root / path
                if not p.exists():
                    responses.append(FileDownloadResponse(path=path, error="file_not_found"))
                else:
                    responses.append(FileDownloadResponse(path=path, content=p.read_bytes()))
            except Exception as e:
                responses.append(FileDownloadResponse(path=path, error=str(e)))
        return responses
