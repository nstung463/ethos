"""HTTP routes for authentication.

Register this router in `src/app/router.py` when auth implementation starts.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from src.app.core.settings import get_settings
from src.app.dependencies import get_auth_repository, get_current_user
from src.app.modules.auth.repository import AuthRepository, AuthUser
from src.app.modules.auth.schemas import (
    GuestSessionRequest,
    PermissionProfilePayload,
    SessionResponse,
    SessionUserResponse,
)
from src.app.modules.auth.service import AuthService
from src.app.services.permissions import PermissionContextService
from src.app.services.rate_limiter import RateLimitRule
from src.app.dependencies import enforce_rate_limit
from src.app.dependencies import get_thread_store
from src.app.services.thread_store import ThreadStore

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(repo: AuthRepository = Depends(get_auth_repository)) -> AuthService:
    return AuthService(repo)


def get_permission_service(
    repo: AuthRepository = Depends(get_auth_repository),
    thread_store: ThreadStore = Depends(get_thread_store),
) -> PermissionContextService:
    return PermissionContextService(repo, thread_store)


@router.post("/guest", response_model=SessionResponse)
async def create_guest_session(
    http_request: Request,
    payload: GuestSessionRequest,
    service: AuthService = Depends(get_auth_service),
):
    settings = get_settings()
    enforce_rate_limit(
        request=http_request,
        rule=RateLimitRule(
            scope="auth_guest_session",
            limit=settings.auth_guest_session_limit,
            window_seconds=settings.auth_guest_session_window_seconds,
        ),
    )
    user, session = service.create_guest_session(display_name=payload.display_name)
    return SessionResponse(
        access_token=session.token,
        user=SessionUserResponse(id=user.id, display_name=user.display_name),
    )


@router.get("/me", response_model=SessionUserResponse)
async def get_me(user: AuthUser = Depends(get_current_user)):
    return SessionUserResponse(id=user.id, display_name=user.display_name)


@router.get("/me/permissions", response_model=PermissionProfilePayload)
async def get_my_permissions(
    user: AuthUser = Depends(get_current_user),
    service: PermissionContextService = Depends(get_permission_service),
):
    return service.get_user_defaults(user_id=user.id)


@router.put("/me/permissions", response_model=PermissionProfilePayload)
async def update_my_permissions(
    payload: PermissionProfilePayload,
    user: AuthUser = Depends(get_current_user),
    service: PermissionContextService = Depends(get_permission_service),
):
    return service.update_user_defaults(user_id=user.id, profile=payload.model_dump())
