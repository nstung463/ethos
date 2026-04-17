from __future__ import annotations

from starlette.testclient import TestClient, WebSocketDisconnect

from src.app import create_app


def _auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/guest", json={})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_thread(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post("/v1/threads", headers=headers)
    assert response.status_code == 200
    return response.json()["id"]


def _assert_websocket_denied(client: TestClient, path: str, headers: dict[str, str] | None = None) -> None:
    try:
        kwargs = {"headers": headers} if headers is not None else {}
        with client.websocket_connect(path, **kwargs):
            raise AssertionError("Websocket connection should have been denied")
    except WebSocketDisconnect:
        return
    except Exception as exc:  # pragma: no cover - Starlette denial type varies by version
        status_code = getattr(exc, "status_code", None)
        if status_code in {401, 404, 429}:
            return
        raise


def test_terminal_http_requires_authentication() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/api/terminals/")

    assert response.status_code == 401


def test_terminal_http_rejects_other_users_thread() -> None:
    with TestClient(create_app()) as client:
        headers_a = _auth_headers(client)
        headers_b = _auth_headers(client)
        thread_id = _create_thread(client, headers_a)

        response = client.get(f"/api/terminals/{thread_id}/files/cwd", headers=headers_b)

    assert response.status_code == 404


def test_terminal_websocket_requires_authentication() -> None:
    with TestClient(create_app()) as client:
        headers = _auth_headers(client)
        thread_id = _create_thread(client, headers)

        _assert_websocket_denied(client, f"/api/terminals/{thread_id}/api/terminals/session-1")


def test_terminal_websocket_rejects_other_users_thread() -> None:
    with TestClient(create_app()) as client:
        headers_a = _auth_headers(client)
        headers_b = _auth_headers(client)
        thread_id = _create_thread(client, headers_a)

        _assert_websocket_denied(
            client,
            f"/api/terminals/{thread_id}/api/terminals/session-1",
            headers=headers_b,
        )
