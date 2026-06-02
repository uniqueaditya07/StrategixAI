"""Gemini backend client tests for Phase 9 Step 5."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend import gemini_client


def test_gemini_client_reports_unavailable_without_api_key(monkeypatch: Any) -> None:
    gemini_client._load_gemini_api_key.cache_clear()
    gemini_client._client.cache_clear()
    monkeypatch.setattr("backend.gemini_client._secrets_path", lambda: Path("missing-secrets.toml"))

    assert gemini_client.is_gemini_available() is False


def test_gemini_client_initializes_with_api_key(monkeypatch: Any) -> None:
    class FakeClient:
        def __init__(self, **kwargs: Any) -> None:
            self.kwargs = kwargs

    gemini_client._client.cache_clear()
    monkeypatch.setattr("backend.gemini_client._load_gemini_api_key", lambda: "test-key")
    monkeypatch.setattr("backend.gemini_client.genai", SimpleNamespace(Client=FakeClient))
    monkeypatch.setattr(
        "backend.gemini_client.types",
        SimpleNamespace(HttpOptions=lambda **kwargs: kwargs),
    )

    assert gemini_client.is_gemini_available() is True


def test_generate_response_returns_safe_failure_when_unavailable(monkeypatch: Any) -> None:
    gemini_client._client.cache_clear()
    monkeypatch.setattr("backend.gemini_client._client", lambda: None)

    response = gemini_client.generate_response("Assess growth options.")

    assert response["ok"] is False
    assert response["reply"] == "StrategixAI Copilot is temporarily unavailable."
    assert response["error"] == "gemini_unavailable"
