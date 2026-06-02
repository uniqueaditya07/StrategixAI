"""Copilot API security and backend integration tests for Phase 9."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app
from backend.copilot_scope import BLOCKED_SCOPE_REPLY


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


def test_copilot_chat_blocks_out_of_scope_messages_without_gemini(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})

    def fail_if_called(_: str) -> dict[str, Any]:
        raise AssertionError("Gemini should not be called for blocked messages")

    monkeypatch.setattr("backend.copilot_routes.generate_response", fail_if_called)
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"workspace_id": "northstar-saas", "message": "What is the capital of France?"},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["reply"] == BLOCKED_SCOPE_REPLY
    assert payload["source"] == "scope_guard"
    assert payload["gemini_ok"] is False
    assert payload["workspace_id"] == "northstar-saas"
    assert payload["auth_scope"] == "user_workspace_verified"


def test_copilot_chat_returns_gemini_response_for_allowed_message(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})
    monkeypatch.setattr(
        "backend.copilot_routes.generate_response",
        lambda _: {
            "ok": True,
            "reply": "Revenue growth should be evaluated against CAC and runway.",
            "source": "gemini",
            "model": "test-gemini",
            "error": None,
        },
    )
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"workspace_id": "northstar-saas", "message": "Assess revenue growth risks."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["reply"] == "Revenue growth should be evaluated against CAC and runway."
    assert payload["source"] == "gemini"
    assert payload["gemini_ok"] is True
    assert payload["model"] == "test-gemini"
    assert payload["workspace_id"] == "northstar-saas"
    assert payload["auth_scope"] == "user_workspace_verified"


def test_copilot_chat_returns_fallback_when_gemini_unavailable(monkeypatch: Any) -> None:
    monkeypatch.setattr("backend.firebase_auth.verify_id_token", lambda _: {"uid": "user-a"})
    monkeypatch.setattr(
        "backend.copilot_routes.generate_response",
        lambda _: {
            "ok": False,
            "reply": "StrategixAI Copilot is temporarily unavailable.",
            "source": "gemini",
            "model": "test-gemini",
            "error": "gemini_unavailable",
        },
    )
    client = create_app().test_client()

    response = client.post(
        "/api/copilot/chat",
        headers={"Authorization": "Bearer valid-token"},
        json={"workspace_id": "northstar-saas", "message": "Recommend a strategy."},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["reply"] == "StrategixAI Copilot is temporarily unavailable."
    assert payload["source"] == "fallback"
    assert payload["gemini_ok"] is False
    assert payload["model"] == "test-gemini"
    assert payload["error"] == "gemini_unavailable"
    assert payload["workspace_id"] == "northstar-saas"
    assert payload["auth_scope"] == "user_workspace_verified"
