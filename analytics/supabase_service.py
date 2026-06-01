"""Supabase Auth client helpers for StrategixAI Phase 8."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from datetime import datetime
from typing import Any

import streamlit as st

from models.user_schema import AuthSession, PublicUser


AUTH_SESSION_STATE_KEY = "auth_session"
AUTH_ACCESS_TOKEN_COOKIE = "sb_access_token"
AUTH_REFRESH_TOKEN_COOKIE = "sb_refresh_token"
OAUTH_CODE_QUERY_PARAM = "code"
OAUTH_ERROR_QUERY_PARAM = "error"


class AuthError(ValueError):
    """Friendly authentication or account validation error."""


def get_supabase_client(*, secrets: Mapping[str, Any] | None = None) -> Any:
    """Create a Supabase client from Streamlit secrets."""

    config = (secrets or st.secrets).get("supabase", {})
    url = config.get("url")
    anon_key = config.get("anon_key")
    if not url or not anon_key:
        raise AuthError("Supabase credentials are missing from Streamlit secrets.")

    try:
        from supabase import create_client
    except ImportError as exc:
        raise AuthError("Install the supabase package before using Supabase Auth.") from exc

    return create_client(url, anon_key)


def get_authenticated_supabase_client(
    *,
    session_state: Mapping[str, Any] | None = None,
) -> Any:
    """Create a Supabase client and attach the in-memory user session."""

    client = get_supabase_client()
    session = current_auth_session(session_state=session_state or st.session_state)
    if session is not None:
        client.auth.set_session(session.access_token, session.refresh_token)
    return client


def sign_up_user(
    *,
    name: str,
    email: str,
    password: str,
    client: Any | None = None,
) -> AuthSession:
    """Register a user with Supabase Auth using name as user metadata."""

    normalized_name = name.strip()
    if not normalized_name:
        raise AuthError("Name is required.")

    supabase = client or get_supabase_client()
    try:
        response = supabase.auth.sign_up(
            {
                "email": email.strip().lower(),
                "password": password,
                "options": {"data": {"name": normalized_name}},
            }
        )
    except Exception as exc:
        raise AuthError(_auth_error_message(exc, "Could not create account.")) from exc

    return _auth_session_from_response(response)


def sign_in_user(
    *,
    email: str,
    password: str,
    client: Any | None = None,
) -> AuthSession:
    """Authenticate a user with Supabase Auth."""

    supabase = client or get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": password}
        )
    except Exception as exc:
        raise AuthError(_auth_error_message(exc, "Invalid email or password.")) from exc

    return _auth_session_from_response(response)


def start_google_oauth_login(
    *,
    redirect_url: str,
    client: Any | None = None,
    code_verifier_store: MutableMapping[str, str] | None = None,
    code_verifier_key: str | None = None,
) -> str:
    """Start Google OAuth through Supabase Auth and return the provider URL."""

    supabase = client or get_supabase_client()
    try:
        response = supabase.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": redirect_url},
            }
        )
    except Exception as exc:
        raise AuthError(_auth_error_message(exc, "Could not start Google sign-in.")) from exc

    auth_url = _get_field(response, "url")
    if not auth_url:
        raise AuthError("Supabase did not return a Google authorization URL.")

    verifier = _oauth_code_verifier(supabase)
    if verifier and code_verifier_store is not None and code_verifier_key:
        code_verifier_store[code_verifier_key] = verifier

    return str(auth_url)


def sign_out_user(*, client: Any | None = None) -> None:
    """Sign out the current Supabase session when a client is available."""

    if client is None:
        try:
            client = get_supabase_client()
        except AuthError:
            return
    try:
        client.auth.sign_out()
    except Exception:
        return


def restore_auth_session(
    *,
    access_token: str,
    refresh_token: str,
    client: Any | None = None,
) -> AuthSession:
    """Restore a Supabase session from in-memory access and refresh tokens."""

    supabase = client or get_supabase_client()
    try:
        response = supabase.auth.set_session(access_token, refresh_token)
    except Exception as exc:
        raise AuthError(_auth_error_message(exc, "Could not restore auth session.")) from exc
    return _auth_session_from_response(response)


def exchange_oauth_code_for_session(
    *,
    auth_code: str,
    code_verifier: str | None,
    redirect_url: str,
    client: Any | None = None,
) -> AuthSession:
    """Exchange a Supabase OAuth callback code for a Supabase session."""

    if not auth_code:
        raise AuthError("Missing Supabase OAuth callback code.")

    supabase = client or get_supabase_client()
    params: dict[str, str] = {
        "auth_code": auth_code,
        "redirect_to": redirect_url,
    }
    if code_verifier:
        params["code_verifier"] = code_verifier

    try:
        response = supabase.auth.exchange_code_for_session(params)
    except Exception as exc:
        raise AuthError(_auth_error_message(exc, "Could not complete Google sign-in.")) from exc
    return _auth_session_from_response(response)


def restore_auth_session_from_oauth_code(
    *,
    auth_code: str | None,
    code_verifier: str | None,
    redirect_url: str,
    client: Any | None = None,
    session_state: MutableMapping[str, Any],
) -> AuthSession | None:
    """Restore and store a Supabase session from an OAuth callback code."""

    if not auth_code:
        return None

    try:
        session = exchange_oauth_code_for_session(
            auth_code=auth_code,
            code_verifier=code_verifier,
            redirect_url=redirect_url,
            client=client,
        )
    except AuthError:
        clear_auth_session_state(session_state=session_state)
        return None

    store_auth_session(session, session_state=session_state)
    return session


def restore_auth_session_from_tokens(
    *,
    access_token: str | None,
    refresh_token: str | None,
    client: Any | None = None,
    session_state: MutableMapping[str, Any],
) -> AuthSession | None:
    """Restore and store a Supabase session from persisted browser tokens."""

    if not access_token or not refresh_token:
        return None

    try:
        session = restore_auth_session(
            access_token=access_token,
            refresh_token=refresh_token,
            client=client,
        )
    except AuthError:
        clear_auth_session_state(session_state=session_state)
        return None

    store_auth_session(session, session_state=session_state)
    return session


def store_auth_session(
    session: AuthSession,
    *,
    session_state: MutableMapping[str, Any],
) -> None:
    """Store the active Supabase auth session in Streamlit session_state."""

    session_state[AUTH_SESSION_STATE_KEY] = session.model_dump(mode="json")
    session_state["auth_user"] = session.user.model_dump(mode="json")


def current_auth_session(
    *,
    session_state: Mapping[str, Any],
) -> AuthSession | None:
    """Return the in-memory Supabase auth session, if present and valid."""

    payload = session_state.get(AUTH_SESSION_STATE_KEY)
    if payload is None:
        return None
    return AuthSession.model_validate(payload)


def clear_auth_session_state(*, session_state: MutableMapping[str, Any]) -> None:
    """Clear local in-memory Supabase auth state."""

    session_state.pop(AUTH_SESSION_STATE_KEY, None)
    session_state.pop("auth_user", None)


def auth_cookie_values(session_state: Mapping[str, Any]) -> dict[str, str] | None:
    """Return browser-cookie token values for the current in-memory auth session."""

    session = current_auth_session(session_state=session_state)
    if session is None:
        return None
    return {
        AUTH_ACCESS_TOKEN_COOKIE: session.access_token,
        AUTH_REFRESH_TOKEN_COOKIE: session.refresh_token,
    }


def _auth_session_from_response(response: Any) -> AuthSession:
    """Convert a Supabase auth response object into the app session contract."""

    session = _get_field(response, "session")
    if session is None:
        raise AuthError("Supabase did not return an active session. Confirm email verification settings.")

    access_token = _get_field(session, "access_token")
    refresh_token = _get_field(session, "refresh_token")
    user = _get_field(session, "user") or _get_field(response, "user")
    if not access_token or not refresh_token or user is None:
        raise AuthError("Supabase returned an incomplete auth session.")

    return AuthSession(
        user=_public_user_from_supabase_user(user),
        access_token=str(access_token),
        refresh_token=str(refresh_token),
    )


def _public_user_from_supabase_user(user: Any) -> PublicUser:
    """Convert a Supabase user object into the session-safe user payload."""

    metadata = _get_field(user, "user_metadata") or {}
    if not isinstance(metadata, Mapping):
        metadata = {}
    email = str(_get_field(user, "email") or "").strip().lower()
    name = str(
        metadata.get("name")
        or metadata.get("full_name")
        or metadata.get("display_name")
        or (email.split("@", 1)[0] if email else "")
        or ""
    ).strip()
    created_at = _parse_datetime(_get_field(user, "created_at"))

    return PublicUser(
        user_id=str(_get_field(user, "id") or ""),
        name=name,
        email=email,
        created_at=created_at,
    )


def _get_field(source: Any, field_name: str) -> Any:
    """Read a field from either a Supabase object or a dict-like fake."""

    if isinstance(source, Mapping):
        return source.get(field_name)
    return getattr(source, field_name, None)


def _parse_datetime(value: Any) -> datetime | None:
    """Parse Supabase timestamp strings when present."""

    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def _auth_error_message(exc: Exception, fallback: str) -> str:
    """Extract a compact Supabase error message."""

    message = getattr(exc, "message", None) or str(exc)
    return message if message else fallback


def _oauth_code_verifier(supabase: Any) -> str | None:
    """Read the PKCE verifier generated by the Supabase SDK, when present."""

    auth = _get_field(supabase, "auth")
    storage_key = _get_field(auth, "_storage_key")
    storage = _get_field(auth, "_storage")
    get_item = _get_field(storage, "get_item")
    if not storage_key or not callable(get_item):
        return None
    verifier = get_item(f"{storage_key}-code-verifier")
    return str(verifier) if verifier else None
