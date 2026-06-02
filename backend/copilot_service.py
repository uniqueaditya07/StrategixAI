from __future__ import annotations

from typing import Any


DUMMY_COPILOT_REPLY = "This is a test Copilot response. Gemini is not connected yet."
COPILOT_PHASE = "phase_9_step_3"


def copilot_health_response() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "copilot",
        "status": "ready",
        "gemini_connected": False,
    }


def build_dummy_copilot_response(payload: dict[str, Any]) -> dict[str, Any]:
    workspace_id = payload.get("workspace_id") or ""
    return {
        "ok": True,
        "reply": DUMMY_COPILOT_REPLY,
        "source": "dummy_backend",
        "workspace_id": workspace_id,
        "phase": COPILOT_PHASE,
    }


def normalize_copilot_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {"workspace_id": "", "message": "", "context": {}}

    context = payload.get("context")
    return {
        "workspace_id": str(payload.get("workspace_id") or ""),
        "message": str(payload.get("message") or ""),
        "context": context if isinstance(context, dict) else {},
    }
