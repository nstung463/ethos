from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from api.services.file_store import FileStore


@lru_cache(maxsize=1)
def get_file_store() -> FileStore:
    root = Path(os.getenv("ETHOS_MANAGED_FILES_DIR", Path.cwd() / "workspace" / "managed_files"))
    return FileStore(root=root)


def get_open_terminal_base_url() -> str:
    return os.getenv("OPEN_TERMINAL_URL", "http://localhost:8000").rstrip("/")


def get_open_terminal_api_key() -> str:
    return os.getenv("OPEN_TERMINAL_API_KEY", "")


def get_terminal_name() -> str:
    return os.getenv("ETHOS_TERMINAL_NAME", "Ethos Sandbox")
