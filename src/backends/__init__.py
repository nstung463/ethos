"""Ethos sandbox backends.

Backends abstract where code executes and where files live.

- LocalSandbox  — subprocess + pathlib on the local machine (default)
- DaytonaSandbox — remote isolated container via Daytona SDK
"""

from src.backends.local import LocalSandbox
from src.backends.protocol import (
    EditResult,
    ExecuteResponse,
    FileDownloadResponse,
    FileUploadResponse,
    SandboxProtocol,
)

__all__ = [
    "LocalSandbox",
    "SandboxProtocol",
    "ExecuteResponse",
    "FileDownloadResponse",
    "FileUploadResponse",
    "EditResult",
]
