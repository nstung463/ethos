from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from starlette.testclient import TestClient

from src.ai.permissions import PermissionMode
from src.app import create_app
from src.backends.local import LocalBackend


@pytest.fixture()
def client() -> TestClient:
    with TestClient(create_app()) as c:
        yield c


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/guest", json={})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_permission_defaults_round_trip(client: TestClient, auth_headers: dict[str, str]) -> None:
    initial = client.get("/auth/me/permissions", headers=auth_headers)
    assert initial.status_code == 200
    assert initial.json() == {"mode": None, "working_directories": [], "rules": []}

    payload = {
        "mode": "accept_edits",
        "working_directories": ["src"],
        "rules": [
            {"subject": "edit", "behavior": "allow", "matcher": "docs/**"},
        ],
    }
    updated = client.put("/auth/me/permissions", json=payload, headers=auth_headers)

    assert updated.status_code == 200
    assert updated.json() == payload


def test_thread_permission_overlay_persists_for_thread(client: TestClient, auth_headers: dict[str, str]) -> None:
    thread = client.post("/v1/threads", headers=auth_headers)
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    payload = {
        "mode": "bypass_permissions",
        "working_directories": ["sandbox/project"],
        "rules": [
            {"subject": "bash", "behavior": "allow", "matcher": "git status*"},
        ],
    }
    updated = client.patch(f"/v1/threads/{thread_id}/permissions", json=payload, headers=auth_headers)

    assert updated.status_code == 200
    body = updated.json()
    assert body["overlay"] == payload
    assert body["effective"]["mode"] == "bypass_permissions"
    assert "sandbox/project" in body["effective"]["working_directories"]

    fetched = client.get(f"/v1/threads/{thread_id}/permissions", headers=auth_headers)
    assert fetched.status_code == 200
    assert fetched.json()["overlay"] == payload


def test_promote_thread_permissions_updates_user_defaults(client: TestClient, auth_headers: dict[str, str]) -> None:
    defaults = {
        "mode": "accept_edits",
        "working_directories": ["src"],
        "rules": [
            {"subject": "edit", "behavior": "allow", "matcher": "notes/**"},
        ],
    }
    response = client.put("/auth/me/permissions", json=defaults, headers=auth_headers)
    assert response.status_code == 200

    thread = client.post("/v1/threads", headers=auth_headers)
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    overlay = {
        "mode": "dont_ask",
        "working_directories": ["sandbox/project"],
        "rules": [
            {"subject": "read", "behavior": "deny", "matcher": "secret/**"},
        ],
    }
    updated = client.patch(f"/v1/threads/{thread_id}/permissions", json=overlay, headers=auth_headers)
    assert updated.status_code == 200

    promoted = client.post(f"/v1/threads/{thread_id}/permissions/promote", headers=auth_headers)

    assert promoted.status_code == 200
    assert promoted.json()["mode"] == "dont_ask"
    assert set(promoted.json()["working_directories"]) == {"src", "sandbox/project"}
    assert promoted.json()["rules"] == [
        {"subject": "edit", "behavior": "allow", "matcher": "notes/**"},
        {"subject": "read", "behavior": "deny", "matcher": "secret/**"},
    ]


def test_chat_completion_uses_effective_thread_permission_context(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    thread = client.post("/v1/threads", headers=auth_headers)
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    user_defaults = client.put(
        "/auth/me/permissions",
        json={"mode": "accept_edits", "working_directories": ["src"], "rules": []},
        headers=auth_headers,
    )
    assert user_defaults.status_code == 200

    overlay = client.patch(
        f"/v1/threads/{thread_id}/permissions",
        json={
            "mode": "dont_ask",
            "working_directories": ["thread-only"],
            "rules": [{"subject": "bash", "behavior": "allow", "matcher": "git status*"}],
        },
        headers=auth_headers,
    )
    assert overlay.status_code == 200

    class _FakeAgent:
        async def ainvoke(self, payload: dict, config: dict | None = None) -> dict:
            return {"messages": [AIMessage(content="ok")]}

    captured: dict[str, object] = {}
    client.app.state.daytona_manager = type(
        "Manager",
        (),
        {
            "get_backend": lambda self, _thread_id: LocalBackend(str(tmp_path / "workspace")),
            "shutdown": lambda self: None,
        },
    )()

    def _fake_create_ethos_agent(*, model=None, backend=None, permission_context=None, root_dir=None, checkpointer=None):
        captured["model"] = model
        captured["backend"] = backend
        captured["permission_context"] = permission_context
        captured["root_dir"] = root_dir
        return _FakeAgent()

    with (
        patch("src.app.modules.chat.router.build_chat_model", return_value=object()),
        patch("src.app.modules.chat.router.create_ethos_agent", side_effect=_fake_create_ethos_agent),
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "ethos",
                "thread_id": thread_id,
                "messages": [{"role": "user", "content": "show status"}],
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    permission_context = captured["permission_context"]
    assert permission_context is not None
    assert permission_context.mode is PermissionMode.DONT_ASK
    assert {str(path) for path in permission_context.working_directories} >= {
        str((tmp_path / "workspace").resolve()),
        str((tmp_path / "workspace" / "src").resolve()),
        str((tmp_path / "workspace" / "thread-only").resolve()),
    }
    assert [rule.matcher for rule in permission_context.rules] == ["git status*"]


def test_agent_uses_checkpointer_from_app_state(client, auth_headers):
    """Two requests must receive the same non-None MemorySaver instance from app.state."""
    from unittest.mock import patch

    seen: list[int] = []

    def _capturing_create(**kwargs):
        checkpointer = kwargs.get("checkpointer")
        seen.append(id(checkpointer))

        class _FakeAgent:
            async def astream_events(self, input_data, config=None, version=None):
                return
                yield

            async def aget_state(self, config):
                class _Snap:
                    tasks = []
                return _Snap()

            async def ainvoke(self, payload, config=None):
                from langchain_core.messages import AIMessage
                return {"messages": [AIMessage(content="ok")]}

        return _FakeAgent()

    with patch("src.app.modules.chat.router.create_ethos_agent", side_effect=_capturing_create):
        client.post(
            "/v1/chat/completions",
            json={"model": "ethos", "messages": [{"role": "user", "content": "hi"}]},
            headers=auth_headers,
        )
        client.post(
            "/v1/chat/completions",
            json={"model": "ethos", "messages": [{"role": "user", "content": "hi again"}]},
            headers=auth_headers,
        )

    assert len(seen) == 2
    # Each call must have received a non-None checkpointer
    assert seen[0] != id(None), "checkpointer must not be None — it should come from app.state"
    assert seen[1] != id(None), "checkpointer must not be None — it should come from app.state"
    assert seen[0] == seen[1], "Both requests must use the same MemorySaver instance from app.state"


def test_chat_completion_allows_one_shot_permission_override_from_metadata(
    client: TestClient,
    auth_headers: dict[str, str],
    tmp_path: Path,
) -> None:
    thread = client.post("/v1/threads", headers=auth_headers)
    assert thread.status_code == 200
    thread_id = thread.json()["id"]

    class _FakeAgent:
        async def ainvoke(self, payload: dict, config: dict | None = None) -> dict:
            return {"messages": [AIMessage(content="ok")]}

    captured: dict[str, object] = {}
    client.app.state.daytona_manager = type(
        "Manager",
        (),
        {
            "get_backend": lambda self, _thread_id: LocalBackend(str(tmp_path / "workspace")),
            "shutdown": lambda self: None,
        },
    )()

    def _fake_create_ethos_agent(*, model=None, backend=None, permission_context=None, root_dir=None, checkpointer=None):
        captured["permission_context"] = permission_context
        return _FakeAgent()

    with (
        patch("src.app.modules.chat.router.build_chat_model", return_value=object()),
        patch("src.app.modules.chat.router.create_ethos_agent", side_effect=_fake_create_ethos_agent),
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "ethos",
                "thread_id": thread_id,
                "messages": [{"role": "user", "content": "write hello.py"}],
                "metadata": {
                    "permission_override": {"mode": "bypass_permissions"},
                },
            },
            headers=auth_headers,
        )

    assert response.status_code == 200
    permission_context = captured["permission_context"]
    assert permission_context is not None
    assert permission_context.mode is PermissionMode.BYPASS_PERMISSIONS
