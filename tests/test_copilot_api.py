"""Copilot API security tests for Phase 9 Step 4."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app


def test_copilot_health_remains_public() -> None:
    client = create_app().test_client()

    response = client.get("/api/copilot/health")

    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_copilot_chat_rejects_missing_token() -> None:
    client = create_app().test_client()

    response = client.post("/api/copilot/chat", json={"workspace_id": "northstar-saas"})

    assert response.status_code == 401


def test_copilot_chat_rejects_invalid_token(monkeypatch: Any) -> None:
    def reject_token(_: str) -> dict[str, Any]:
        raise ValueError("Invalid token")

    monkeypatch.setattr("backend.firebase_auth.verify_id_token", reject_token)
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer bad-token"},
        json={"workspace_id": "northstar-saas"},
    )

    assert response.status_code == 401


def test_copilot_chat_rejects_missing_workspace_id(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"message": "Hello"},
    )

    assert response.status_code == 400


def test_copilot_chat_rejects_invalid_workspace_id(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"workspace_id": "missing-workspace"},
    )

    assert response.status_code == 403


def test_copilot_chat_returns_step_4_dummy_response(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"workspace_id": "northstar-saas", "message": "Hello"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload == {
        "ok": True,
        "reply": "This is a test Copilot response. Gemini is not connected yet.",
        "source": "dummy_backend",
        "workspace_id": "northstar-saas",
        "phase": "phase_9_step_4",
        "auth_scope": "user_workspace_verified",
    }
