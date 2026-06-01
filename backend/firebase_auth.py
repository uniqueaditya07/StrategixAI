from __future__ import annotations

from functools import wraps
from typing import Any, Callable

from flask import g, jsonify, request

from analytics.firebase_service import verify_id_token


def current_user_from_authorization_header(header_value: str | None) -> dict[str, Any]:
    if not header_value or not header_value.startswith("Bearer "):
        raise ValueError("Missing Firebase bearer token")

    decoded = verify_id_token(header_value.removeprefix("Bearer ").strip())
    return {
        "uid": decoded["uid"],
        "email": decoded.get("email", ""),
        "name": decoded.get("name", ""),
        "photoURL": decoded.get("picture", ""),
        "claims": decoded,
    }


def require_firebase_auth(route: Callable[..., Any]) -> Callable[..., Any]:
    """Flask decorator that verifies Firebase Auth ID tokens."""

    @wraps(route)
    def wrapped(*args: Any, **kwargs: Any) -> Any:
        try:
            g.current_user = current_user_from_authorization_header(
                request.headers.get("Authorization")
            )
        except Exception:
            return jsonify({"error": "Unauthorized"}), 401
        return route(*args, **kwargs)

    return wrapped
