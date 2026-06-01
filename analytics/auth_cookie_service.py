"""Streamlit browser-cookie helpers for Supabase auth persistence."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from typing import Any

import streamlit as st

from analytics.auth_service import (
    AUTH_ACCESS_TOKEN_COOKIE,
    AUTH_REFRESH_TOKEN_COOKIE,
    AuthError,
    restore_user_from_oauth_code,
    restore_user_from_cookie_tokens,
    session_cookie_values,
)


COOKIE_PREFIX = "strategixai_auth_"
OAUTH_CODE_VERIFIER_COOKIE = "oauth_code_verifier"
AUTH_LOGOUT_PENDING_STATE_KEY = "auth_logout_pending"


def get_auth_cookie_manager(*, secrets: Mapping[str, Any] | None = None) -> MutableMapping[str, str]:
    """Create the encrypted Streamlit cookie manager used for Supabase tokens."""

    try:
        from streamlit_cookies_manager import EncryptedCookieManager
    except ImportError as exc:
        raise AuthError("Install streamlit-cookies-manager before using persistent login.") from exc

    return EncryptedCookieManager(
        prefix=COOKIE_PREFIX,
        password=_cookie_password(secrets=secrets or st.secrets),
    )


def ensure_cookie_manager_ready(cookies: Any) -> None:
    """Wait until the Streamlit cookie component has loaded browser cookies."""

    ready = getattr(cookies, "ready", None)
    if callable(ready) and not ready():
        st.stop()


def restore_auth_from_cookies(
    *,
    cookies: Mapping[str, str],
    session_state: MutableMapping[str, Any],
    client: Any | None = None,
) -> bool:
    """Restore Streamlit auth state from persisted Supabase token cookies."""

    if session_state.get(AUTH_LOGOUT_PENDING_STATE_KEY):
        clear_auth_cookies(cookies)
        session_state.pop(AUTH_LOGOUT_PENDING_STATE_KEY, None)
        return False

    if session_state.get("auth_user"):
        return True

    user = restore_user_from_cookie_tokens(
        access_token=cookies.get(AUTH_ACCESS_TOKEN_COOKIE),
        refresh_token=cookies.get(AUTH_REFRESH_TOKEN_COOKIE),
        client=client,
        session_state=session_state,
    )
    if user is not None:
        return True

    clear_auth_cookies(cookies)
    return False


def restore_auth_from_oauth_callback(
    *,
    auth_code: str | None,
    redirect_url: str,
    cookies: MutableMapping[str, str],
    session_state: MutableMapping[str, Any],
    client: Any | None = None,
) -> bool:
    """Exchange a Supabase OAuth callback code and persist the restored session."""

    if not auth_code:
        return False

    user = restore_user_from_oauth_code(
        auth_code=auth_code,
        code_verifier=cookies.get(OAUTH_CODE_VERIFIER_COOKIE),
        redirect_url=redirect_url,
        client=client,
        session_state=session_state,
    )
    clear_oauth_code_verifier(cookies)
    if user is None:
        clear_auth_cookies(cookies)
        return False

    persist_auth_cookies(cookies=cookies, session_state=session_state)
    return True


def persist_auth_cookies(
    *,
    cookies: MutableMapping[str, str],
    session_state: MutableMapping[str, Any],
) -> None:
    """Persist the active Supabase access and refresh tokens in browser cookies."""

    values = session_cookie_values(session_state)
    if values is None:
        return
    for key, value in values.items():
        cookies[key] = value
    _save_cookies(cookies)


def mark_logout_pending(session_state: MutableMapping[str, Any]) -> None:
    """Prevent stale browser cookies from restoring auth on the next rerun."""

    session_state[AUTH_LOGOUT_PENDING_STATE_KEY] = True


def clear_auth_cookies(cookies: MutableMapping[str, str] | Mapping[str, str]) -> None:
    """Clear persisted Supabase auth token cookies."""

    if not isinstance(cookies, MutableMapping):
        return
    for key in (AUTH_ACCESS_TOKEN_COOKIE, AUTH_REFRESH_TOKEN_COOKIE):
        try:
            del cookies[key]
        except KeyError:
            pass
    _save_cookies(cookies)


def clear_oauth_code_verifier(cookies: MutableMapping[str, str] | Mapping[str, str]) -> None:
    """Clear the short-lived PKCE code verifier used during OAuth callback exchange."""

    if not isinstance(cookies, MutableMapping):
        return
    try:
        del cookies[OAUTH_CODE_VERIFIER_COOKIE]
    except KeyError:
        pass
    _save_cookies(cookies)


def _save_cookies(cookies: Any) -> None:
    save = getattr(cookies, "save", None)
    if callable(save):
        save()


def _cookie_password(*, secrets: Mapping[str, Any]) -> str:
    config = secrets.get("auth_cookies", {})
    if isinstance(config, Mapping) and config.get("password"):
        return str(config["password"])

    supabase_config = secrets.get("supabase", {})
    if isinstance(supabase_config, Mapping) and supabase_config.get("anon_key"):
        return str(supabase_config["anon_key"])

    raise AuthError("Set auth_cookies.password in Streamlit secrets for persistent login cookies.")


__all__ = [
    "AUTH_ACCESS_TOKEN_COOKIE",
    "AUTH_REFRESH_TOKEN_COOKIE",
    "AUTH_LOGOUT_PENDING_STATE_KEY",
    "COOKIE_PREFIX",
    "OAUTH_CODE_VERIFIER_COOKIE",
    "clear_auth_cookies",
    "clear_oauth_code_verifier",
    "ensure_cookie_manager_ready",
    "get_auth_cookie_manager",
    "mark_logout_pending",
    "persist_auth_cookies",
    "restore_auth_from_cookies",
    "restore_auth_from_oauth_callback",
]
