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
    print("\n=== COPILOT PAYLOAD START ===")
    print("Content-Type:", request.content_type)
    print("Raw Body:", request.get_data(cache=True, as_text=True))
    payload = request.get_json(silent=True)
    print("Parsed Payload:", payload)
    print("Payload Type:", type(payload))
    if not isinstance(payload, dict):
        print("=== COPILOT HTTP 400 ===")
        print("Reason: Invalid request body")
        return jsonify({"error": "Invalid request body"}), 400

    normalized_payload = normalize_copilot_payload(payload)
    print("workspace_id:", normalized_payload.get("workspace_id"))
    if not normalized_payload["workspace_id"]:
        print("=== COPILOT HTTP 400 ===")
        print("Reason: workspace_id is required")
        return jsonify({"error": "workspace_id is required"}), 400

    try:
        validate_copilot_workspace_access(g.current_user["uid"], normalized_payload["workspace_id"])
    except CopilotWorkspaceAccessError:
        return jsonify({"error": "Forbidden"}), 403

    workspace_id = normalized_payload["workspace_id"]
    if not is_copilot_scope_allowed(normalized_payload["message"]):
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

    gemini_response = generate_response(normalized_payload["message"])
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
