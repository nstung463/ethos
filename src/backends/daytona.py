"""Daytona sandbox backend for Ethos.

Provides:
- `DaytonaSandbox`: execute/upload/download primitives for BaseSandbox.
- `create_daytona_sandbox(...)`: context manager to create/reuse Daytona
  sandbox and yield a ready-to-use backend for `create_ethos_agent(...)`.
"""

from __future__ import annotations

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from src.backends.protocol import (
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
)
from src.backends.sandbox import BaseSandbox
from src.logger import get_logger

logger = get_logger(__name__)


class DaytonaSandbox(BaseSandbox):
    """Daytona remote sandbox backend.

    Requires the `daytona` package: pip install daytona
    """

    def __init__(
        self,
        *,
        sandbox: object,  # daytona.Sandbox — typed as object to avoid hard import
        timeout: int = 30 * 60,
    ) -> None:
        """Wrap an existing Daytona sandbox.

        Args:
            sandbox: A `daytona.Sandbox` instance (already created).
            timeout: Default command timeout in seconds.
        """
        self._sandbox = sandbox
        self._default_timeout = timeout

    @property
    def id(self) -> str:
        return str(self._sandbox.id)  # type: ignore[attr-defined]

    # ── Core primitives ────────────────────────────────────────────────────────

    def execute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        """Execute a shell command inside the Daytona sandbox.

        Uses Daytona process exec API for synchronous command execution.
        """
        effective_timeout = timeout if timeout is not None else self._default_timeout
        logger.debug("Executing command in Daytona sandbox (sandbox_id=%s)", self.id)
        try:
            result = self._sandbox.process.exec(command, timeout=effective_timeout)  # type: ignore[attr-defined]
        except Exception as e:
            logger.exception("Daytona exec failed (sandbox_id=%s)", self.id)
            return ExecuteResponse(output=f"Daytona exec failed: {e}", exit_code=1, truncated=False)

        return ExecuteResponse(output=result.result or "", exit_code=result.exit_code, truncated=False)

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


def _run_setup_script(backend: DaytonaSandbox, setup_script_path: str) -> None:
    if not os.path.exists(setup_script_path):
        logger.warning("Setup script not found: %s", setup_script_path)
        return
    with open(setup_script_path, encoding="utf-8") as f:
        script = f.read()
    logger.info("Running Daytona setup script: %s", setup_script_path)
    backend.execute(script)


@contextmanager
def create_daytona_sandbox(
    *,
    conversation_id: str,
    setup_script_path: str | None = None,
    output_dir: Path | None = None,
) -> Generator[DaytonaSandbox, None, None]:
    """Create/reuse a Daytona sandbox and yield DaytonaSandbox backend."""
    from daytona import CreateSandboxBaseParams, Daytona, DaytonaConfig
    from daytona.common.errors import DaytonaError

    api_key = os.environ.get("DAYTONA_API_KEY")
    if not api_key:
        raise ValueError("DAYTONA_API_KEY environment variable not set")

    logger.info("Creating or reusing Daytona sandbox (conversation_id=%s)", conversation_id)
    daytona = Daytona(DaytonaConfig(api_key=api_key))
    sandbox_name = conversation_id

    is_new = False
    try:
        sandbox = daytona.create(
            params=CreateSandboxBaseParams(name=sandbox_name, auto_delete_interval=5)
        )
        is_new = True
        logger.info("Created new Daytona sandbox: %s", sandbox_name)
    except DaytonaError as e:
        if "already exists" in str(e):
            sandbox = daytona.get(sandbox_id_or_name=sandbox_name)
            logger.info("Reusing existing Daytona sandbox: %s", sandbox_name)
        else:
            raise

    for _ in range(90):
        try:
            ready = sandbox.process.exec("echo ready", timeout=5)
            if ready.exit_code == 0:
                break
        except Exception:
            pass
        time.sleep(2)
    else:
        if is_new:
            sandbox.delete()
        raise RuntimeError("Daytona sandbox failed to start within 180 seconds")

    backend = DaytonaSandbox(sandbox=sandbox)
    logger.info("Daytona sandbox ready (sandbox_id=%s)", backend.id)
    if is_new:
        if setup_script_path is None:
            project_root = Path(__file__).resolve().parents[3]
            default_setup = project_root / "scripts" / "setup_daytona_sandbox.sh"
            if default_setup.exists():
                setup_script_path = str(default_setup)
        if setup_script_path:
            _run_setup_script(backend, setup_script_path)

    try:
        yield backend
    finally:
        if output_dir:
            logger.info("Collecting output files to local dir: %s", output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            list_result = backend.execute(
                "cd /tmp/OUTPUT_DIR && find . -type f 2>/dev/null | head -100"
            )
            if list_result.exit_code == 0 and list_result.output.strip():
                rel_paths = [p.strip() for p in list_result.output.splitlines() if p.strip()]
                abs_paths = [f"/tmp/OUTPUT_DIR/{p.lstrip('./')}" for p in rel_paths]
                for resp in backend.download_files(abs_paths):
                    if resp.content is not None:
                        (output_dir / Path(resp.path).name).write_bytes(resp.content)
                        logger.debug("Downloaded output file: %s", resp.path)
        logger.info("Deleting Daytona sandbox: %s", sandbox_name)
        sandbox.delete()
