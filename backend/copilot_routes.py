from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from backend.copilot_security import (
    CopilotWorkspaceAccessError,
    validate_copilot_workspace_access,
)
from backend.copilot_scope import BLOCKED_SCOPE_REPLY, is_copilot_scope_allowed
from backend.copilot_service import (
    COPILOT_PHASE,
    copilot_health_response,
    normalize_copilot_payload,
)
from backend.firebase_auth import require_firebase_auth
from backend.gemini_client import generate_response


copilot_bp = Blueprint("copilot", __name__, url_prefix="/api/copilot")


@copilot_bp.get("/health")
def copilot_health():
    return jsonify(copilot_health_response())


@copilot_bp.post("/chat")
@require_firebase_auth
def copilot_chat():
    raw_payload = request.get_json(silent=True)
    if not isinstance(raw_payload, dict):
        return jsonify({"error": "Invalid request body"}), 400

    payload = normalize_copilot_payload(raw_payload)
    if not payload["workspace_id"]:
        return jsonify({"error": "workspace_id is required"}), 400

    try:
        validate_copilot_workspace_access(g.current_user["uid"], payload["workspace_id"])
    except CopilotWorkspaceAccessError:
        return jsonify({"error": "Forbidden"}), 403

    workspace_id = payload["workspace_id"]
    if not is_copilot_scope_allowed(payload["message"]):
        return jsonify(
            {
                "ok": True,
                "reply": BLOCKED_SCOPE_REPLY,
                "source": "scope_guard",
                "workspace_id": workspace_id,
                "phase": COPILOT_PHASE,
                "auth_scope": "user_workspace_verified",
                "gemini_ok": False,
            }
        )

    gemini_response = generate_response(payload["message"])
    if gemini_response.get("ok") is True:
        return jsonify(
            {
                "ok": True,
                "reply": gemini_response.get("reply") or "",
                "source": "gemini",
                "workspace_id": workspace_id,
                "phase": COPILOT_PHASE,
                "auth_scope": "user_workspace_verified",
                "gemini_ok": True,
                "model": gemini_response.get("model"),
            }
        )

    return jsonify(
        {
            "ok": True,
            "reply": gemini_response.get("reply") or "StrategixAI Copilot is temporarily unavailable.",
            "source": "fallback",
            "workspace_id": workspace_id,
            "phase": COPILOT_PHASE,
            "auth_scope": "user_workspace_verified",
            "gemini_ok": False,
            "model": gemini_response.get("model"),
            "error": gemini_response.get("error"),
        }
    )
