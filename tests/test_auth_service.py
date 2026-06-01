"""Supabase authentication service tests for StrategixAI Phase 8."""

from __future__ import annotations

import sys
from types import SimpleNamespace
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from analytics.auth_service import (
    AUTH_ACCESS_TOKEN_COOKIE,
    AUTH_REFRESH_TOKEN_COOKIE,
    AuthError,
    authenticate_user,
    get_authenticated_user,
    is_authenticated,
    logout_user,
    register_user,
    restore_user_from_oauth_code,
    start_google_oauth_login,
)
from analytics.auth_cookie_service import (
    AUTH_LOGOUT_PENDING_STATE_KEY,
    COOKIE_PREFIX,
    OAUTH_CODE_VERIFIER_COOKIE,
    clear_auth_cookies,
    mark_logout_pending,
    persist_auth_cookies,
    restore_auth_from_cookies,
    restore_auth_from_oauth_callback,
)


class FakeSupabaseAuth:
    """Minimal fake for Supabase auth calls."""

    def __init__(
        self,
        *,
        fail_login: bool = False,
        fail_restore: bool = False,
        fail_oauth_exchange: bool = False,
    ) -> None:
        self.fail_login = fail_login
        self.fail_restore = fail_restore
        self.fail_oauth_exchange = fail_oauth_exchange
        self.sign_up_payload: dict | None = None
        self.sign_in_payload: dict | None = None
        self.oauth_payload: dict | None = None
        self.set_session_payload: tuple[str, str] | None = None
        self.exchange_code_payload: dict | None = None
        self.sign_out_called = False
        self._storage_key = "strategixai-auth"
        self._storage = FakeOAuthStorage()

    def sign_up(self, payload: dict) -> SimpleNamespace:
        self.sign_up_payload = payload
        return _auth_response(
            user_id="11111111-1111-1111-1111-111111111111",
            email=payload["email"],
            name=payload["options"]["data"]["name"],
        )

    def sign_in_with_password(self, payload: dict) -> SimpleNamespace:
        self.sign_in_payload = payload
        if self.fail_login:
            raise ValueError("Invalid login credentials")
        return _auth_response(
            user_id="22222222-2222-2222-2222-222222222222",
            email=payload["email"],
            name="",
        )

    def sign_out(self) -> None:
        self.sign_out_called = True

    def sign_in_with_oauth(self, payload: dict) -> SimpleNamespace:
        self.oauth_payload = payload
        self._storage.set_item("strategixai-auth-code-verifier", "pkce-verifier")
        return SimpleNamespace(
            provider=payload["provider"],
            url="https://example.supabase.co/auth/v1/authorize?provider=google",
        )

    def exchange_code_for_session(self, payload: dict) -> SimpleNamespace:
        self.exchange_code_payload = payload
        if self.fail_oauth_exchange or payload.get("auth_code") == "invalid-code":
            raise ValueError("Invalid OAuth callback")
        return _auth_response(
            user_id="44444444-4444-4444-4444-444444444444",
            email="google.user@example.com",
            name="Google User",
            access_token="oauth-access-token",
            refresh_token="oauth-refresh-token",
        )

    def set_session(self, access_token: str, refresh_token: str) -> SimpleNamespace:
        self.set_session_payload = (access_token, refresh_token)
        if self.fail_restore or access_token == "invalid-token":
            raise ValueError("Invalid refresh token")
        return _auth_response(
            user_id="33333333-3333-3333-3333-333333333333",
            email="restored@example.com",
            name="Restored User",
            access_token=access_token,
            refresh_token=refresh_token,
        )


class FakeSupabaseClient:
    """Minimal fake Supabase client with auth namespace."""

    def __init__(
        self,
        *,
        fail_login: bool = False,
        fail_restore: bool = False,
        fail_oauth_exchange: bool = False,
    ) -> None:
        self.auth = FakeSupabaseAuth(
            fail_login=fail_login,
            fail_restore=fail_restore,
            fail_oauth_exchange=fail_oauth_exchange,
        )


class FakeOAuthStorage:
    """In-memory Supabase PKCE storage fake."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def set_item(self, key: str, value: str) -> None:
        self.values[key] = value

    def get_item(self, key: str) -> str | None:
        return self.values.get(key)

    def remove_item(self, key: str) -> None:
        self.values.pop(key, None)


class FakeCookies(dict):
    """Mutable cookie fake that records saves."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.save_count = 0

    def save(self) -> None:
        self.save_count += 1


def _auth_response(
    *,
    user_id: str,
    email: str,
    name: str,
    access_token: str = "access-token",
    refresh_token: str = "refresh-token",
) -> SimpleNamespace:
    user = SimpleNamespace(
        id=user_id,
        email=email,
        user_metadata={"name": name},
        created_at="2026-06-01T00:00:00Z",
    )
    session = SimpleNamespace(
        user=user,
        access_token=access_token,
        refresh_token=refresh_token,
    )
    return SimpleNamespace(user=user, session=session)


def test_auth_ui_guard_rejects_unauthenticated_state() -> None:
    """Protected app flow should not be shown without a Supabase session."""

    session_state: dict = {}

    assert get_authenticated_user(session_state=session_state) is None
    assert is_authenticated(session_state=session_state) is False


def test_supabase_sign_up_wrapper_receives_email_password_name() -> None:
    """Registration should delegate credentials and name metadata to Supabase Auth."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    user = register_user(
        name="Ava Strategy",
        email="AVA@Example.COM",
        password="securepass123",
        client=client,
        session_state=session_state,
    )

    assert client.auth.sign_up_payload == {
        "email": "ava@example.com",
        "password": "securepass123",
        "options": {"data": {"name": "Ava Strategy"}},
    }
    assert user.user_id == "11111111-1111-1111-1111-111111111111"
    assert user.name == "Ava Strategy"
    assert session_state["auth_session"]["access_token"] == "access-token"


def test_supabase_login_wrapper_handles_success() -> None:
    """Login should store the Supabase session when credentials are accepted."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    user = authenticate_user(
        email="AVA@Example.COM",
        password="securepass123",
        client=client,
        session_state=session_state,
    )

    assert client.auth.sign_in_payload == {
        "email": "ava@example.com",
        "password": "securepass123",
    }
    assert user.email == "ava@example.com"
    assert is_authenticated(session_state=session_state) is True


def test_supabase_login_wrapper_handles_failure() -> None:
    """Login failures should return a friendly AuthError."""

    client = FakeSupabaseClient(fail_login=True)
    try:
        authenticate_user(
            email="ava@example.com",
            password="wrongpass123",
            client=client,
            session_state={},
        )
    except AuthError:
        return
    raise AssertionError("Invalid Supabase login should be rejected")


def test_google_oauth_wrapper_uses_supabase_provider() -> None:
    """Google sign-in should be started through Supabase Auth."""

    client = FakeSupabaseClient()
    verifier_store: dict[str, str] = {}

    auth_url = start_google_oauth_login(
        redirect_url="http://localhost:8501",
        client=client,
        code_verifier_store=verifier_store,
        code_verifier_key=OAUTH_CODE_VERIFIER_COOKIE,
    )

    assert auth_url.startswith("https://example.supabase.co/auth/v1/authorize")
    assert client.auth.oauth_payload["provider"] == "google"
    assert verifier_store[OAUTH_CODE_VERIFIER_COOKIE] == "pkce-verifier"


def test_google_oauth_wrapper_passes_redirect_to() -> None:
    """Supabase OAuth should receive the Streamlit redirect URL."""

    client = FakeSupabaseClient()

    start_google_oauth_login(
        redirect_url="http://localhost:8501",
        client=client,
    )

    assert client.auth.oauth_payload["options"]["redirect_to"] == "http://localhost:8501"


def test_auth_screen_source_exposes_google_and_email_auth_controls() -> None:
    """The Streamlit auth screen should expose Google plus email login/register controls."""

    app_source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

    assert "Continue with Google" in app_source
    assert "or continue with email" in app_source
    assert 'st.tabs(["Login", "Register"])' in app_source
    assert "login_email" in app_source
    assert "login_password" in app_source
    assert "register_email" in app_source
    assert "register_password" in app_source


def test_email_auth_screen_uses_supabase_auth_wrappers() -> None:
    """Email forms should use Supabase-backed login and registration wrappers."""

    app_source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")

    assert "authenticate_user(" in app_source
    assert "register_user(" in app_source
    assert "persist_auth_cookies(cookies=cookies, session_state=st.session_state)" in app_source
    assert "json" not in app_source[app_source.find("def render_auth_screen") : app_source.find("def selected_control_values")]


def test_logout_clears_session_state() -> None:
    """Logout should sign out and remove local in-memory auth/session payloads."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    authenticate_user(
        email="ava@example.com",
        password="securepass123",
        client=client,
        session_state=session_state,
    )

    logout_user(client=client, session_state=session_state)

    assert client.auth.sign_out_called is True
    assert "auth_session" not in session_state
    assert "auth_user" not in session_state


def test_auth_cookie_keys_match_supabase_session_tokens() -> None:
    """Auth cookie helpers should use the exact token keys managed by Supabase auth."""

    assert AUTH_ACCESS_TOKEN_COOKIE == "sb_access_token"
    assert AUTH_REFRESH_TOKEN_COOKIE == "sb_refresh_token"
    assert COOKIE_PREFIX == "strategixai_auth_"


def test_refresh_restores_auth_from_cookie_tokens() -> None:
    """Refresh should restore session_state from Supabase token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies(
        {
            AUTH_ACCESS_TOKEN_COOKIE: "cookie-access-token",
            AUTH_REFRESH_TOKEN_COOKIE: "cookie-refresh-token",
        }
    )

    restored = restore_auth_from_cookies(
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is True
    assert client.auth.set_session_payload == ("cookie-access-token", "cookie-refresh-token")
    assert session_state["auth_user"]["email"] == "restored@example.com"
    assert session_state["auth_session"]["access_token"] == "cookie-access-token"


def test_oauth_callback_restores_auth_session_state() -> None:
    """OAuth callback code exchange should store auth_user and auth_session."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    user = restore_user_from_oauth_code(
        auth_code="oauth-code",
        code_verifier="pkce-verifier",
        redirect_url="http://localhost:8501",
        client=client,
        session_state=session_state,
    )

    assert user is not None
    assert user.user_id == "44444444-4444-4444-4444-444444444444"
    assert user.email == "google.user@example.com"
    assert session_state["auth_user"]["name"] == "Google User"
    assert session_state["auth_session"]["access_token"] == "oauth-access-token"
    assert client.auth.exchange_code_payload == {
        "auth_code": "oauth-code",
        "redirect_to": "http://localhost:8501",
        "code_verifier": "pkce-verifier",
    }


def test_cookie_persistence_after_oauth_callback() -> None:
    """Successful OAuth callback should persist Supabase token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies({OAUTH_CODE_VERIFIER_COOKIE: "pkce-verifier"})

    restored = restore_auth_from_oauth_callback(
        auth_code="oauth-code",
        redirect_url="http://localhost:8501",
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is True
    assert cookies[AUTH_ACCESS_TOKEN_COOKIE] == "oauth-access-token"
    assert cookies[AUTH_REFRESH_TOKEN_COOKIE] == "oauth-refresh-token"
    assert OAUTH_CODE_VERIFIER_COOKIE not in cookies


def test_cookie_persistence_after_email_login() -> None:
    """Successful email login should persist Supabase token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies()

    authenticate_user(
        email="ava@example.com",
        password="securepass123",
        client=client,
        session_state=session_state,
    )
    persist_auth_cookies(cookies=cookies, session_state=session_state)

    assert cookies[AUTH_ACCESS_TOKEN_COOKIE] == "access-token"
    assert cookies[AUTH_REFRESH_TOKEN_COOKIE] == "refresh-token"
    assert cookies.save_count == 1


def test_cookie_persistence_after_email_registration() -> None:
    """Successful email registration should persist Supabase token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies()

    register_user(
        name="Ava Strategy",
        email="ava@example.com",
        password="securepass123",
        client=client,
        session_state=session_state,
    )
    persist_auth_cookies(cookies=cookies, session_state=session_state)

    assert cookies[AUTH_ACCESS_TOKEN_COOKIE] == "access-token"
    assert cookies[AUTH_REFRESH_TOKEN_COOKIE] == "refresh-token"
    assert cookies.save_count == 1


def test_logout_clears_cookie_tokens_and_session_state() -> None:
    """Logout should clear Supabase session state and persisted token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies(
        {
            AUTH_ACCESS_TOKEN_COOKIE: "access-token",
            AUTH_REFRESH_TOKEN_COOKIE: "refresh-token",
        }
    )
    authenticate_user(
        email="ava@example.com",
        password="securepass123",
        client=client,
        session_state=session_state,
    )

    logout_user(client=client, session_state=session_state)
    clear_auth_cookies(cookies)

    assert client.auth.sign_out_called is True
    assert "auth_session" not in session_state
    assert "auth_user" not in session_state
    assert AUTH_ACCESS_TOKEN_COOKIE not in cookies
    assert AUTH_REFRESH_TOKEN_COOKIE not in cookies
    assert cookies.save_count == 1


def test_pending_logout_prevents_immediate_cookie_restore() -> None:
    """A logout rerun should not restore auth from stale token cookies."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies(
        {
            AUTH_ACCESS_TOKEN_COOKIE: "stale-access-token",
            AUTH_REFRESH_TOKEN_COOKIE: "stale-refresh-token",
        }
    )
    mark_logout_pending(session_state)

    restored = restore_auth_from_cookies(
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is False
    assert client.auth.set_session_payload is None
    assert "auth_session" not in session_state
    assert "auth_user" not in session_state
    assert AUTH_LOGOUT_PENDING_STATE_KEY not in session_state
    assert AUTH_ACCESS_TOKEN_COOKIE not in cookies
    assert AUTH_REFRESH_TOKEN_COOKIE not in cookies
    assert cookies.save_count == 1


def test_refresh_after_logout_remains_logged_out() -> None:
    """After logout clears cookies, refresh should remain unauthenticated."""

    client = FakeSupabaseClient()
    session_state: dict = {}
    cookies = FakeCookies(
        {
            AUTH_ACCESS_TOKEN_COOKIE: "access-token",
            AUTH_REFRESH_TOKEN_COOKIE: "refresh-token",
        }
    )
    authenticate_user(
        email="ava@example.com",
        password="securepass123",
        client=client,
        session_state=session_state,
    )

    mark_logout_pending(session_state)
    logout_user(client=client, session_state=session_state)
    clear_auth_cookies(cookies)
    restored = restore_auth_from_cookies(
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is False
    assert client.auth.sign_out_called is True
    assert is_authenticated(session_state=session_state) is False
    assert AUTH_LOGOUT_PENDING_STATE_KEY not in session_state
    assert AUTH_ACCESS_TOKEN_COOKIE not in cookies
    assert AUTH_REFRESH_TOKEN_COOKIE not in cookies


def test_invalid_cookie_token_does_not_authenticate() -> None:
    """Invalid persisted tokens should be ignored and cleared."""

    client = FakeSupabaseClient(fail_restore=True)
    session_state: dict = {}
    cookies = FakeCookies(
        {
            AUTH_ACCESS_TOKEN_COOKIE: "invalid-token",
            AUTH_REFRESH_TOKEN_COOKIE: "refresh-token",
        }
    )

    restored = restore_auth_from_cookies(
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is False
    assert is_authenticated(session_state=session_state) is False
    assert AUTH_ACCESS_TOKEN_COOKIE not in cookies
    assert AUTH_REFRESH_TOKEN_COOKIE not in cookies
    assert cookies.save_count == 1


def test_invalid_oauth_callback_does_not_authenticate() -> None:
    """Invalid OAuth callback code should not create an authenticated session."""

    client = FakeSupabaseClient(fail_oauth_exchange=True)
    session_state: dict = {}
    cookies = FakeCookies({OAUTH_CODE_VERIFIER_COOKIE: "pkce-verifier"})

    restored = restore_auth_from_oauth_callback(
        auth_code="invalid-code",
        redirect_url="http://localhost:8501",
        cookies=cookies,
        session_state=session_state,
        client=client,
    )

    assert restored is False
    assert is_authenticated(session_state=session_state) is False
    assert AUTH_ACCESS_TOKEN_COOKIE not in cookies
    assert AUTH_REFRESH_TOKEN_COOKIE not in cookies
    assert OAUTH_CODE_VERIFIER_COOKIE not in cookies


def main() -> None:
    """Run auth tests without requiring pytest."""

    test_auth_ui_guard_rejects_unauthenticated_state()
    test_supabase_sign_up_wrapper_receives_email_password_name()
    test_supabase_login_wrapper_handles_success()
    test_supabase_login_wrapper_handles_failure()
    test_google_oauth_wrapper_uses_supabase_provider()
    test_google_oauth_wrapper_passes_redirect_to()
    test_auth_screen_source_exposes_google_and_email_auth_controls()
    test_email_auth_screen_uses_supabase_auth_wrappers()
    test_logout_clears_session_state()
    test_auth_cookie_keys_match_supabase_session_tokens()
    test_refresh_restores_auth_from_cookie_tokens()
    test_oauth_callback_restores_auth_session_state()
    test_cookie_persistence_after_oauth_callback()
    test_cookie_persistence_after_email_login()
    test_cookie_persistence_after_email_registration()
    test_logout_clears_cookie_tokens_and_session_state()
    test_pending_logout_prevents_immediate_cookie_restore()
    test_refresh_after_logout_remains_logged_out()
    test_invalid_cookie_token_does_not_authenticate()
    test_invalid_oauth_callback_does_not_authenticate()
    print("Supabase authentication service tests passed")


if __name__ == "__main__":
    main()
