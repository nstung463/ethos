from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any


class ThreadStore:
    """Small JSON-backed store for user-owned chat threads."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.index_path = self.root / "threads.json"
        self._lock = Lock()
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text("{}", encoding="utf-8")

    def _read_index(self) -> dict[str, dict[str, Any]]:
        try:
            return json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_index(self, index: dict[str, dict[str, Any]]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def create_thread(self, *, user_id: str) -> dict[str, Any]:
        now = int(time.time())
        record = {
            "id": f"thread_{uuid.uuid4().hex}",
            "user_id": user_id,
            "created_at": now,
            "updated_at": now,
            "permission_overlay": {
                "mode": None,
                "working_directories": [],
                "rules": [],
            },
        }
        with self._lock:
            index = self._read_index()
            index[record["id"]] = record
            self._write_index(index)
        return record

    def list_threads(self, *, user_id: str) -> list[dict[str, Any]]:
        with self._lock:
            index = self._read_index()
        items = [item for item in index.values() if item.get("user_id") == user_id]
        items.sort(key=lambda item: item.get("updated_at", 0), reverse=True)
        return items

    def get_thread(self, thread_id: str) -> dict[str, Any] | None:
        with self._lock:
            return self._read_index().get(thread_id)

    def get_owned_thread(self, *, thread_id: str, user_id: str) -> dict[str, Any] | None:
        thread = self.get_thread(thread_id)
        if not thread or thread.get("user_id") != user_id:
            return None
        return thread

    def touch_thread(self, *, thread_id: str, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            index = self._read_index()
            record = index.get(thread_id)
            if not record or record.get("user_id") != user_id:
                return None
            record["updated_at"] = int(time.time())
            index[thread_id] = record
            self._write_index(index)
            return record

    def get_permission_overlay(self, *, thread_id: str, user_id: str) -> dict[str, Any] | None:
        with self._lock:
            index = self._read_index()
            record = index.get(thread_id)
            if not record or record.get("user_id") != user_id:
                return None
            overlay = record.get("permission_overlay")
            if not isinstance(overlay, dict):
                return {"mode": None, "working_directories": [], "rules": []}
            return {
                "mode": overlay.get("mode") if isinstance(overlay.get("mode"), str) else None,
                "working_directories": [item for item in (overlay.get("working_directories") or []) if isinstance(item, str)],
                "rules": [item for item in (overlay.get("rules") or []) if isinstance(item, dict)],
            }

    def update_permission_overlay(
        self,
        *,
        thread_id: str,
        user_id: str,
        overlay: dict[str, Any],
    ) -> dict[str, Any] | None:
        with self._lock:
            index = self._read_index()
            record = index.get(thread_id)
            if not record or record.get("user_id") != user_id:
                return None
            record["permission_overlay"] = overlay
            record["updated_at"] = int(time.time())
            index[thread_id] = record
            self._write_index(index)
        return overlay
