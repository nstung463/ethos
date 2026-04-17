"""Business logic for authentication."""

from __future__ import annotations

from src.app.modules.auth.repository import AuthRepository, AuthSession, AuthUser


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self._repo = repo

    def create_guest_session(self, *, display_name: str | None = None) -> tuple[AuthUser, AuthSession]:
        return self._repo.create_guest_session(display_name=display_name)
