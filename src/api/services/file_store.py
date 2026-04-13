from __future__ import annotations

import json
import mimetypes
import shutil
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any


class FileStore:
    """Small local file registry for OpenWebUI-compatible managed files."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files_dir = self.root / "files"
        self.index_path = self.root / "index.json"
        self._lock = Lock()
        self.files_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text("{}", encoding="utf-8")

    def _read_index(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_index(self, index: dict[str, dict[str, Any]]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def list_files(self) -> list[dict[str, Any]]:
        with self._lock:
            index = self._read_index()
        items = list(index.values())
        items.sort(key=lambda item: item.get("updated_at", 0), reverse=True)
        return items

    def get_file(self, file_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read_index().get(file_id)

    def save_upload(self, *, filename: str, content_type: str | None, source_path: Path) -> dict[str, Any]:
        file_id = str(uuid.uuid4())
        stored_name = f"{file_id}_{filename}"
        destination = self.files_dir / stored_name
        shutil.copy2(source_path, destination)
        return self._register_file(
            file_id=file_id,
            filename=filename,
            stored_path=destination,
            content_type=content_type,
        )

    def import_bytes(
        self,
        *,
        filename: str,
        content: bytes,
        content_type: str | None = None,
    ) -> dict[str, Any]:
        file_id = str(uuid.uuid4())
        stored_name = f"{file_id}_{filename}"
        destination = self.files_dir / stored_name
        destination.write_bytes(content)
        return self._register_file(
            file_id=file_id,
            filename=filename,
            stored_path=destination,
            content_type=content_type,
        )

    def _register_file(
        self,
        *,
        file_id: str,
        filename: str,
        stored_path: Path,
        content_type: str | None,
    ) -> dict[str, Any]:
        now = int(time.time())
        resolved_type = content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
        record = {
            "id": file_id,
            "filename": filename,
            "path": str(stored_path),
            "meta": {
                "name": filename,
                "content_type": resolved_type,
                "size": stored_path.stat().st_size,
            },
            "data": {},
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            index = self._read_index()
            index[file_id] = record
            self._write_index(index)
        return record

    def update_content(self, file_id: str, content: str) -> dict[str, Any] | None:
        with self._lock:
            index = self._read_index()
            record = index.get(file_id)
            if not record:
                return None
            path = Path(record["path"])
            path.write_text(content, encoding="utf-8")
            record["meta"]["size"] = path.stat().st_size
            record["updated_at"] = int(time.time())
            index[file_id] = record
            self._write_index(index)
            return record

    def delete_file(self, file_id: str) -> bool:
        with self._lock:
            index = self._read_index()
            record = index.pop(file_id, None)
            if not record:
                return False
            self._write_index(index)
        try:
            Path(record["path"]).unlink(missing_ok=True)
        except Exception:
            pass
        return True
