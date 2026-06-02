from __future__ import annotations

from flask import Blueprint, jsonify, request

from backend.copilot_service import (
    build_dummy_copilot_response,
    copilot_health_response,
    normalize_copilot_payload,
)


copilot_bp = Blueprint("copilot", __name__, url_prefix="/api/copilot")


@copilot_bp.get("/health")
def copilot_health():
    return jsonify(copilot_health_response())


@copilot_bp.post("/chat")
def copilot_chat():
    # TODO Phase 9 Step 4: enforce authenticated user id from verified Firebase token.
    # TODO Phase 9 Step 4: validate that the active workspace belongs to that user.
    # TODO Phase 9 Step 5: connect Gemini only after user/workspace isolation is confirmed.
    payload = normalize_copilot_payload(request.get_json(silent=True) or {})
    return jsonify(build_dummy_copilot_response(payload))
