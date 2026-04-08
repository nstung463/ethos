"""DaytonaSandbox — remote isolated container via Daytona SDK.

Mirrors langchain-daytona DaytonaSandbox but without deepagents dependency.
Wraps a `daytona.Sandbox` and implements execute() + upload/download.
All high-level file operations (ls, read, write, edit, glob, grep) are
inherited from BaseSandbox and run as Python scripts via execute().

Usage:
    from daytona import Daytona, CreateSandboxParams
    from src.backends.daytona import DaytonaSandbox

    sandbox = Daytona().create(CreateSandboxParams(language="python"))
    backend = DaytonaSandbox(sandbox=sandbox)

    agent = create_ethos_agent(backend=backend)
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import cast
from uuid import uuid4

from src.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from src.backends.sandbox import BaseSandbox

SyncPollingInterval = float | Callable[[float], float]


class DaytonaSandbox(BaseSandbox):
    """Daytona remote sandbox backend.

    Requires the `daytona` package: pip install daytona
    """

    def __init__(
        self,
        *,
        sandbox: object,  # daytona.Sandbox — typed as object to avoid hard import
        timeout: int = 30 * 60,
        sync_polling_interval: SyncPollingInterval = 0.25,
    ) -> None:
        """Wrap an existing Daytona sandbox.

        Args:
            sandbox: A `daytona.Sandbox` instance (already created).
            timeout: Default command timeout in seconds.
            sync_polling_interval: Seconds between polling calls (or a callable
                that receives elapsed seconds and returns the next delay).
        """
        self._sandbox = sandbox
        self._default_timeout = timeout

        if callable(sync_polling_interval):
            self._poll_interval: Callable[[float], float] = cast(
                "Callable[[float], float]", sync_polling_interval
            )
        else:
            interval = sync_polling_interval

            def _fixed(_elapsed: float) -> float:
                return interval

            self._poll_interval = _fixed

    @property
    def id(self) -> str:
        return str(self._sandbox.id)  # type: ignore[attr-defined]

    # ── Core primitives ────────────────────────────────────────────────────────

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the Daytona sandbox.

        Uses Daytona's session-based execution with log polling for sync support.
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        return self._execute_via_session(command, timeout=effective_timeout)

    def _execute_via_session(self, command: str, *, timeout: int) -> ExecuteResponse:
        try:
            from daytona import SessionExecuteRequest
        except ImportError as e:
            return ExecuteResponse(
                output="Error: daytona package not installed. Run: pip install daytona",
                exit_code=1,
            )

        session_id = str(uuid4())
        self._sandbox.process.create_session(session_id)  # type: ignore[attr-defined]

        try:
            started_at = time.monotonic()
            result = self._sandbox.process.execute_session_command(  # type: ignore[attr-defined]
                session_id,
                SessionExecuteRequest(command=command, run_async=True),
                timeout=timeout,
            )

            while True:
                if timeout != 0 and time.monotonic() - started_at >= timeout:
                    return ExecuteResponse(
                        output=f"Command timed out after {timeout}s",
                        exit_code=124,
                        truncated=False,
                    )

                cmd_result = self._sandbox.process.get_session_command(  # type: ignore[attr-defined]
                    session_id, result.cmd_id
                )
                if cmd_result.exit_code is not None:
                    break

                elapsed = time.monotonic() - started_at
                time.sleep(self._poll_interval(elapsed))

            logs = self._sandbox.process.get_session_command_logs(  # type: ignore[attr-defined]
                session_id, result.cmd_id
            )
        finally:
            try:
                self._sandbox.process.delete_session(session_id)  # type: ignore[attr-defined]
            except Exception:
                pass

        output = logs.stdout or ""
        if logs.stderr and logs.stderr.strip():
            output += f"\n<stderr>{logs.stderr.strip()}</stderr>"

        return ExecuteResponse(
            output=output,
            exit_code=cmd_result.exit_code,
            truncated=False,
        )

    def upload_files(self, files: list[tuple[str, bytes]]) -> list[FileUploadResponse]:
        """Upload files into the Daytona sandbox."""
        try:
            from daytona import FileUpload
        except ImportError:
            return [FileUploadResponse(path=p, error="daytona not installed") for p, _ in files]

        responses: list[FileUploadResponse] = []
        upload_requests = []

        for path, content in files:
            if not path.startswith("/"):
                responses.append(FileUploadResponse(path=path, error="invalid_path: must be absolute"))
                continue
            upload_requests.append((path, FileUpload(source=content, destination=path)))
            responses.append(FileUploadResponse(path=path))

        if upload_requests:
            self._sandbox.fs.upload_files([req for _, req in upload_requests])  # type: ignore[attr-defined]

        return responses

    def download_files(self, paths: list[str]) -> list[FileDownloadResponse]:
        """Download files from the Daytona sandbox."""
        try:
            from daytona import FileDownloadRequest
        except ImportError:
            return [FileDownloadResponse(path=p, error="daytona not installed") for p in paths]

        responses: list[FileDownloadResponse] = []
        valid_indices: list[int] = []
        download_requests: list[FileDownloadRequest] = []

        for i, path in enumerate(paths):
            if not path.startswith("/"):
                responses.append(FileDownloadResponse(path=path, error="invalid_path"))
            else:
                valid_indices.append(i)
                download_requests.append(FileDownloadRequest(source=path))
                responses.append(FileDownloadResponse(path=path))

        if download_requests:
            daytona_responses = self._sandbox.fs.download_files(download_requests)  # type: ignore[attr-defined]
            for idx, resp in zip(valid_indices, daytona_responses):
                if resp.result is None:
                    responses[idx] = FileDownloadResponse(
                        path=paths[idx], error="file_not_found"
                    )
                else:
                    responses[idx] = FileDownloadResponse(
                        path=paths[idx], content=resp.result
                    )

        return responses
