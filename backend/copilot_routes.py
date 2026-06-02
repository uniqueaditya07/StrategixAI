from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from backend.copilot_security import (
    CopilotWorkspaceAccessError,
    validate_copilot_workspace_access,
)
from backend.copilot_service import (
    build_dummy_copilot_response,
    copilot_health_response,
    normalize_copilot_payload,
)
from backend.firebase_auth import require_firebase_auth


copilot_bp = Blueprint("copilot", __name__, url_prefix="/api/copilot")


@copilot_bp.get("/health")
def copilot_health():
    return jsonify(copilot_health_response())


@copilot_bp.post("/chat")
@require_firebase_auth
def copilot_chat():
    # TODO Phase 9 Step 5: connect Gemini only after user/workspace isolation is confirmed.
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

    return jsonify(build_dummy_copilot_response(payload))
