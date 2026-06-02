from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st

try:
    import firebase_admin
    from firebase_admin import auth, credentials, firestore
except ImportError:  # pragma: no cover - handled at runtime in the UI
    firebase_admin = None
    auth = None
    credentials = None
    firestore = None


FIREBASE_CLIENT_KEYS = (
    "apiKey",
    "authDomain",
    "projectId",
    "storageBucket",
    "messagingSenderId",
    "appId",
    "measurementId",
)

STRATEGIXAI_FIREBASE_PROJECT_ID = "strategixai-a2dae"
STRATEGIXAI_FIREBASE_AUTH_DOMAIN = "strategixai-a2dae.firebaseapp.com"
LOGGER = logging.getLogger(__name__)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _secret_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value

    firebase_secrets = st.secrets.get("firebase", {}) if hasattr(st, "secrets") else {}
    for key in keys:
        if key in firebase_secrets and firebase_secrets[key]:
            return str(firebase_secrets[key])
    return ""


def firebase_client_config() -> dict[str, str]:
    """Return browser-safe Firebase Web SDK config."""

    config = {
        "apiKey": _secret_value("FIREBASE_API_KEY", "apiKey"),
        "authDomain": _secret_value("FIREBASE_AUTH_DOMAIN", "authDomain"),
        "projectId": _secret_value("FIREBASE_PROJECT_ID", "projectId"),
        "storageBucket": _secret_value("FIREBASE_STORAGE_BUCKET", "storageBucket"),
        "messagingSenderId": _secret_value("FIREBASE_MESSAGING_SENDER_ID", "messagingSenderId"),
        "appId": _secret_value("FIREBASE_APP_ID", "appId"),
        "measurementId": _secret_value("FIREBASE_MEASUREMENT_ID", "measurementId"),
    }
    if config.get("projectId") == STRATEGIXAI_FIREBASE_PROJECT_ID:
        config["authDomain"] = STRATEGIXAI_FIREBASE_AUTH_DOMAIN
    return {key: value for key, value in config.items() if value}


def firebase_is_configured() -> bool:
    config = firebase_client_config()
    return all(config.get(key) for key in ("apiKey", "authDomain", "projectId", "appId"))


def _resolve_service_account_path(service_account_path: str) -> Path:
    raw_path = Path(service_account_path).expanduser()
    if raw_path.is_absolute():
        return raw_path.resolve()

    module_path = Path(__file__).resolve()
    project_root = module_path.parents[1]
    candidates = [
        Path.cwd() / raw_path,
        project_root / raw_path,
        module_path.parent / raw_path,
        *[parent / raw_path for parent in module_path.parents],
    ]

    seen: set[Path] = set()
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.exists():
            return resolved

    return (project_root / raw_path).resolve()


def _log_service_account_path_debug(
    service_account_path: str,
    resolved_path: Path,
    exists: bool,
    project_id: str = "",
) -> None:
    LOGGER.info(
        "Firebase service account path debug: service_account_path=%r resolved_path=%s exists=%s project_id=%r",
        service_account_path,
        resolved_path,
        exists,
        project_id,
    )


def _service_account_info() -> dict[str, Any]:
    raw_json = _secret_value("FIREBASE_SERVICE_ACCOUNT_JSON", "service_account_json")
    if raw_json:
        service_account = json.loads(raw_json)
        LOGGER.info(
            "Firebase service account loaded from JSON secret: project_id=%r",
            service_account.get("project_id", ""),
        )
        return service_account

    firebase_secrets = st.secrets.get("firebase", {}) if hasattr(st, "secrets") else {}
    if "service_account" in firebase_secrets:
        service_account = dict(firebase_secrets["service_account"])
        LOGGER.info(
            "Firebase service account loaded from nested secret: project_id=%r",
            service_account.get("project_id", ""),
        )
        return service_account

    service_account_path = _secret_value("FIREBASE_SERVICE_ACCOUNT_PATH", "service_account_path")
    if service_account_path:
        resolved_path = _resolve_service_account_path(service_account_path)
        exists = resolved_path.exists()
        if not exists:
            _log_service_account_path_debug(service_account_path, resolved_path, exists)
            raise FileNotFoundError(f"Firebase service account file not found at: {resolved_path}")

        with resolved_path.open("r", encoding="utf-8") as file:
            service_account = json.load(file)
        _log_service_account_path_debug(
            service_account_path,
            resolved_path,
            exists,
            str(service_account.get("project_id", "")),
        )
        return service_account

    raise RuntimeError(
        "Firebase service account is not configured. Set FIREBASE_SERVICE_ACCOUNT_JSON, "
        "[firebase].service_account, or [firebase].service_account_path."
    )


def initialize_firebase_admin() -> None:
    if firebase_admin is None or credentials is None:
        raise RuntimeError("firebase-admin is not installed. Run pip install -r requirements.txt.")
    if firebase_admin._apps:
        return

    service_account = _service_account_info()
    cred = credentials.Certificate(service_account)
    firebase_admin.initialize_app(cred)


def firestore_client() -> Any:
    initialize_firebase_admin()
    return firestore.client()


def verify_id_token(id_token: str) -> dict[str, Any]:
    initialize_firebase_admin()
    return auth.verify_id_token(id_token)


def get_user_profile(uid: str) -> dict[str, Any] | None:
    doc = firestore_client().collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def create_or_update_login_profile(decoded_token: dict[str, Any]) -> dict[str, Any]:
    db = firestore_client()
    uid = str(decoded_token["uid"])
    ref = db.collection("users").document(uid)
    existing_doc = ref.get()
    existing = existing_doc.to_dict() if existing_doc.exists else {}
    now = utc_now()
    profile = {
        "uid": uid,
        "name": existing.get("name") or decoded_token.get("name") or "",
        "email": decoded_token.get("email", ""),
        "photoURL": decoded_token.get("picture", ""),
        "role": existing.get("role", ""),
        "goal": existing.get("goal", ""),
        "organization": existing.get("organization", ""),
        "onboardingCompleted": bool(existing.get("onboardingCompleted", False)),
        "createdAt": existing.get("createdAt") or now,
        "updatedAt": now,
    }
    ref.set(profile, merge=True)
    return profile


def complete_onboarding(uid: str, profile_update: dict[str, Any]) -> dict[str, Any]:
    ref = firestore_client().collection("users").document(uid)
    payload = {
        **profile_update,
        "uid": uid,
        "onboardingCompleted": True,
        "updatedAt": utc_now(),
    }
    ref.set(payload, merge=True)
    return ref.get().to_dict()


def save_user_simulation(uid: str, payload: dict[str, Any]) -> str:
    ref = firestore_client().collection("users").document(uid).collection("simulations").document()
    ref.set({**payload, "createdAt": utc_now()})
    return ref.id


def save_user_report(uid: str, payload: dict[str, Any]) -> str:
    ref = firestore_client().collection("users").document(uid).collection("reports").document()
    ref.set({**payload, "createdAt": utc_now()})
    return ref.id


def delete_user_report(uid: str, report_id: str) -> None:
    firestore_client().collection("users").document(uid).collection("reports").document(report_id).delete()


def list_user_collection(uid: str, collection_name: str, limit: int = 20) -> list[dict[str, Any]]:
    docs = (
        firestore_client()
        .collection("users")
        .document(uid)
        .collection(collection_name)
        .order_by("createdAt", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    rows: list[dict[str, Any]] = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        rows.append(data)
    return rows
