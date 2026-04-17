"""Persistence layer for auth data."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any


@dataclass(frozen=True)
class AuthUser:
    id: str
    display_name: str
    created_at: int


@dataclass(frozen=True)
class AuthSession:
    token: str
    user_id: str
    created_at: int


class AuthRepository:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.index_path = self.root / "auth.json"
        self._lock = Lock()
        self.root.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self.index_path.write_text(json.dumps({"users": {}, "sessions": {}}, indent=2), encoding="utf-8")

    def _read_index(self) -> dict[str, dict[str, Any]]:
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
        users = data.get("users") if isinstance(data.get("users"), dict) else {}
        sessions = data.get("sessions") if isinstance(data.get("sessions"), dict) else {}
        return {"users": users, "sessions": sessions}

    def _write_index(self, index: dict[str, dict[str, Any]]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2), encoding="utf-8")

    def create_guest_session(self, *, display_name: str | None = None) -> tuple[AuthUser, AuthSession]:
        now = int(time.time())
        user = AuthUser(
            id=f"user_{uuid.uuid4().hex}",
            display_name=(display_name or "Guest").strip() or "Guest",
            created_at=now,
        )
        session = AuthSession(
            token=secrets.token_urlsafe(32),
            user_id=user.id,
            created_at=now,
        )
        with self._lock:
            index = self._read_index()
            index["users"][user.id] = {
                "id": user.id,
                "display_name": user.display_name,
                "created_at": user.created_at,
                "permission_defaults": {
                    "mode": None,
                    "working_directories": [],
                    "rules": [],
                },
            }
            index["sessions"][session.token] = {
                "token": session.token,
                "user_id": session.user_id,
                "created_at": session.created_at,
            }
            self._write_index(index)
        return user, session

    def get_session(self, token: str) -> AuthSession | None:
        with self._lock:
            raw = self._read_index()["sessions"].get(token)
        if not raw:
            return None
        return AuthSession(
            token=str(raw["token"]),
            user_id=str(raw["user_id"]),
            created_at=int(raw["created_at"]),
        )

    def get_user(self, user_id: str) -> AuthUser | None:
        with self._lock:
            raw = self._read_index()["users"].get(user_id)
        if not raw:
            return None
        return AuthUser(
            id=str(raw["id"]),
            display_name=str(raw["display_name"]),
            created_at=int(raw["created_at"]),
        )

    def get_permission_defaults(self, user_id: str) -> dict[str, Any]:
        with self._lock:
            raw = self._read_index()["users"].get(user_id)
        if not raw:
            return {"mode": None, "working_directories": [], "rules": []}
        defaults = raw.get("permission_defaults")
        if not isinstance(defaults, dict):
            return {"mode": None, "working_directories": [], "rules": []}
        mode = defaults.get("mode")
        working_directories = defaults.get("working_directories")
        rules = defaults.get("rules")
        return {
            "mode": mode if isinstance(mode, str) else None,
            "working_directories": [item for item in (working_directories or []) if isinstance(item, str)],
            "rules": [item for item in (rules or []) if isinstance(item, dict)],
        }

    def update_permission_defaults(self, *, user_id: str, defaults: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            index = self._read_index()
            raw = index["users"].get(user_id)
            if not raw:
                return None
            raw["permission_defaults"] = defaults
            index["users"][user_id] = raw
            self._write_index(index)
        return defaults
