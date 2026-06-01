"""Deployment-ready authentication facade for StrategixAI Phase 8."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from analytics.supabase_service import (
    AuthError,
    AUTH_ACCESS_TOKEN_COOKIE,
    AUTH_REFRESH_TOKEN_COOKIE,
    auth_cookie_values,
    clear_auth_session_state,
    current_auth_session,
    restore_auth_session_from_oauth_code,
    restore_auth_session_from_tokens,
    start_google_oauth_login as start_supabase_google_oauth_login,
    sign_in_user,
    sign_out_user,
    sign_up_user,
    store_auth_session,
)
from models.user_schema import AuthSession, PublicUser


AUTH_BACKEND = "supabase"


def register_user(
    *,
    name: str,
    email: str,
    password: str,
    client: Any | None = None,
    session_state: MutableMapping[str, Any] | None = None,
) -> PublicUser:
    """Register a user through Supabase Auth and store the session in memory."""

    session = sign_up_user(
        name=name,
        email=email,
        password=password,
        client=client,
    )
    if session_state is not None:
        store_auth_session(session, session_state=session_state)
    return session.user


def authenticate_user(
    *,
    email: str,
    password: str,
    client: Any | None = None,
    session_state: MutableMapping[str, Any] | None = None,
) -> PublicUser:
    """Authenticate a user through Supabase Auth and store the session in memory."""

    session = sign_in_user(email=email, password=password, client=client)
    if session_state is not None:
        store_auth_session(session, session_state=session_state)
    return session.user


def start_google_oauth_login(
    *,
    redirect_url: str,
    client: Any | None = None,
    code_verifier_store: MutableMapping[str, str] | None = None,
    code_verifier_key: str | None = None,
) -> str:
    """Start Google Sign-In through Supabase Auth and return the provider URL."""

    return start_supabase_google_oauth_login(
        redirect_url=redirect_url,
        client=client,
        code_verifier_store=code_verifier_store,
        code_verifier_key=code_verifier_key,
    )


def restore_user_from_oauth_code(
    *,
    auth_code: str | None,
    code_verifier: str | None,
    redirect_url: str,
    client: Any | None = None,
    session_state: MutableMapping[str, Any],
) -> PublicUser | None:
    """Restore a Supabase user from a Google OAuth callback code."""

    session = restore_auth_session_from_oauth_code(
        auth_code=auth_code,
        code_verifier=code_verifier,
        redirect_url=redirect_url,
        client=client,
        session_state=session_state,
    )
    return session.user if session is not None else None


def restore_user_from_cookie_tokens(
    *,
    access_token: str | None,
    refresh_token: str | None,
    client: Any | None = None,
    session_state: MutableMapping[str, Any],
) -> PublicUser | None:
    """Restore a Supabase user from browser cookie tokens."""

    session = restore_auth_session_from_tokens(
        access_token=access_token,
        refresh_token=refresh_token,
        client=client,
        session_state=session_state,
    )
    return session.user if session is not None else None


def get_authenticated_user(
    *,
    session_state: MutableMapping[str, Any],
) -> PublicUser | None:
    """Return the current authenticated user from Streamlit session state."""

    session = current_auth_session(session_state=session_state)
    return session.user if session is not None else None


def is_authenticated(*, session_state: MutableMapping[str, Any]) -> bool:
    """Return whether the protected app should be shown."""

    return get_authenticated_user(session_state=session_state) is not None


def logout_user(
    *,
    client: Any | None = None,
    session_state: MutableMapping[str, Any],
) -> None:
    """Sign out through Supabase and clear local in-memory auth state."""

    sign_out_user(client=client)
    clear_auth_session_state(session_state=session_state)


def session_cookie_values(session_state: MutableMapping[str, Any]) -> dict[str, str] | None:
    """Return cookie-safe token values for the current Supabase session."""

    return auth_cookie_values(session_state)


__all__ = [
    "AUTH_BACKEND",
    "AUTH_ACCESS_TOKEN_COOKIE",
    "AUTH_REFRESH_TOKEN_COOKIE",
    "AuthError",
    "AuthSession",
    "PublicUser",
    "authenticate_user",
    "get_authenticated_user",
    "is_authenticated",
    "logout_user",
    "register_user",
    "restore_user_from_oauth_code",
    "restore_user_from_cookie_tokens",
    "session_cookie_values",
    "start_google_oauth_login",
]
