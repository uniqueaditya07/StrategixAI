from __future__ import annotations

import json
import os
from urllib.parse import urlencode, urlparse

from flask import Flask, g, jsonify, redirect, render_template_string, request

from analytics.firebase_service import firebase_client_config
from analytics.firebase_service import list_user_collection, save_user_report, save_user_simulation
from backend.firebase_auth import require_firebase_auth


AUTH_PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>StrategixAI Login</title>
  <style>
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #F8FAFC;
      background:
        radial-gradient(circle at 72% -18%, rgba(47, 123, 255, 0.14), transparent 32%),
        linear-gradient(135deg, #05070A 0%, #0B1220 100%);
    }
    .auth-shell {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px 16px;
    }
    .auth-card {
      width: min(100%, 520px);
      border: 1px solid rgba(255, 255, 255, 0.075);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.045);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
      padding: clamp(28px, 5vw, 48px);
    }
    .auth-kicker {
      margin-bottom: 14px;
      color: #2F7BFF;
      font-size: 0.76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }
    .auth-brand {
      font-size: clamp(42px, 8vw, 68px);
      line-height: 0.92;
      font-weight: 900;
    }
    .auth-copy {
      margin: 18px 0 28px;
      color: #B8C0CC;
      font-size: 1rem;
      line-height: 1.65;
    }
    .status {
      color: #8D96A5;
      font-size: 0.92rem;
      line-height: 1.6;
    }
    .debug {
      margin-top: 14px;
      color: #64748B;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
      font-size: 0.72rem;
      line-height: 1.5;
      overflow-wrap: anywhere;
      display: __DEBUG_DISPLAY__;
    }
    .error {
      color: #FCA5A5;
      margin-top: 14px;
      font-size: 0.86rem;
      line-height: 1.5;
      display: none;
    }
    .google-button {
      width: 100%;
      min-height: 46px;
      margin: 0 0 16px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 8px;
      background: #F8FAFC;
      color: #0F172A;
      cursor: pointer;
      font: inherit;
      font-size: 0.95rem;
      font-weight: 800;
      transition: transform 140ms ease, opacity 140ms ease, background 140ms ease;
    }
    .google-button:hover:not(:disabled) {
      background: #FFFFFF;
      transform: translateY(-1px);
    }
    .google-button:disabled {
      cursor: wait;
      opacity: 0.58;
    }
  </style>
</head>
<body>
  <main class="auth-shell">
    <section class="auth-card">
      <div class="auth-kicker">Executive strategy intelligence</div>
      <div class="auth-brand">StrategixAI</div>
      <div class="auth-copy">Sign in with Google to continue.</div>
      <button class="google-button" id="googleButton" type="button" disabled>Continue with Google</button>
      <div class="status" id="status">Preparing Firebase Auth...</div>
      <div class="debug" id="debug"></div>
      <div class="error" id="error"></div>
    </section>
  </main>
  <script type="module">
    const firebaseConfig = __FIREBASE_CONFIG__;
    const returnTo = __RETURN_TO__;
    const AUTH_DEBUG = __AUTH_DEBUG__;
    const FIREBASE_APP_URL = "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";
    const FIREBASE_AUTH_URL = "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
    const statusEl = document.getElementById("status");
    const errorEl = document.getElementById("error");
    const debugEl = document.getElementById("debug");
    const googleButton = document.getElementById("googleButton");
    let firebaseAuth = null;
    let googleProvider = null;
    let signInWithPopupFn = null;
    let signInWithRedirectFn = null;
    let authReady = false;
    let terminalStateReached = false;
    const flow = {
      strategy: "signInWithPopup",
      currentUrl: window.location.href,
      returnTo,
      beforeSignIn: false,
      afterSignInCall: false,
      getRedirectResultCalled: false,
      getRedirectResultReturnedUser: false,
      authStateRestoredUser: false,
      tokenReady: false,
      error: ""
    };

    const logStage = (stage, details = {}) => {
      Object.assign(flow, details);
      const rows = {
        stage,
        strategy: flow.strategy,
        currentUrl: flow.currentUrl,
        beforeSignIn: flow.beforeSignIn,
        afterSignInCall: flow.afterSignInCall,
        getRedirectResultCalled: flow.getRedirectResultCalled,
        getRedirectResultReturnedUser: flow.getRedirectResultReturnedUser,
        authStateRestoredUser: flow.authStateRestoredUser,
        tokenReady: flow.tokenReady,
        hasAuthTokenQueryParam: new URL(window.location.href).searchParams.has("auth_token"),
        error: flow.error
      };
      debugEl.textContent = Object.entries(rows)
        .map(([key, value]) => `${key}: ${value}`)
        .join(" | ");
      console.debug("StrategixAI Firebase auth flow", rows);
    };

    const setStatus = (message, stage, details = {}) => {
      statusEl.textContent = message;
      logStage(stage, details);
    };

    const describeError = (error) => {
      if (!error) {
        return "Unknown JavaScript error.";
      }
      const parts = [];
      if (error.code) {
        parts.push(`code=${error.code}`);
      }
      if (error.name) {
        parts.push(`name=${error.name}`);
      }
      if (error.message) {
        parts.push(`message=${error.message}`);
      } else {
        parts.push(String(error));
      }
      if (error.stack) {
        parts.push(`stack=${error.stack}`);
      }
      return parts.join(" | ");
    };

    const importFailureHint = (url, error) => {
      const text = describeError(error);
      const failedFetch = /Failed to fetch|Importing a module script failed|dynamically imported module|Load failed|NetworkError/i.test(text);
      const blockerHint = failedFetch && navigator.onLine
        ? " The browser reports it is online, so this can be a Firebase CDN, DNS, firewall, browser extension, privacy setting, or adblock blocking gstatic.com."
        : "";
      return `Firebase CDN import failed for ${url}. ${text}.${blockerHint}`;
    };

    const fail = (message, userMessage = "We could not complete Google sign-in. Please try again.") => {
      terminalStateReached = true;
      googleButton.disabled = false;
      statusEl.textContent = "Sign-in could not continue.";
      errorEl.textContent = AUTH_DEBUG ? message : userMessage;
      errorEl.style.display = "block";
      logStage("failed", { error: message });
    };

    const storageGet = (key) => {
      try {
        return window.sessionStorage.getItem(key);
      } catch (error) {
        throw new Error(`sessionStorage.getItem(${key}) failed. ${describeError(error)} Browser storage may be blocked by a privacy setting, extension, incognito policy, or browser security policy.`);
      }
    };

    const storageSet = (key, value) => {
      try {
        window.sessionStorage.setItem(key, value);
      } catch (error) {
        throw new Error(`sessionStorage.setItem(${key}) failed. ${describeError(error)} Firebase redirect fallback requires browser storage to survive the Google redirect.`);
      }
    };

    const storageRemove = (key) => {
      try {
        window.sessionStorage.removeItem(key);
      } catch (error) {
        console.warn(`StrategixAI sessionStorage.removeItem(${key}) failed`, error);
      }
    };

    const finish = (token, debugReason) => {
      terminalStateReached = true;
      const url = new URL(returnTo);
      url.searchParams.set("auth_token", token);
      url.searchParams.set("auth_debug", debugReason || "firebase_user");
      url.searchParams.set("auth_stage", "before_streamlit_receives_auth_state");
      url.searchParams.set("auth_strategy", flow.strategy);
      url.searchParams.delete("signed_out");
      logStage("before_streamlit_receives_auth_state", { tokenReady: Boolean(token) });
      window.location.replace(url.toString());
    };

    const waitForCurrentUser = (auth, onAuthStateChanged, timeoutMs = 5000) => {
      if (auth.currentUser) {
        return Promise.resolve(auth.currentUser);
      }
      return new Promise((resolve) => {
        let unsubscribe = () => {};
        const timeoutId = window.setTimeout(() => {
          unsubscribe();
          resolve(auth.currentUser);
        }, timeoutMs);
        unsubscribe = onAuthStateChanged(auth, (user) => {
          if (!user) {
            return;
          }
          window.clearTimeout(timeoutId);
          unsubscribe();
          resolve(user);
        });
      });
    };

    const importFirebaseModule = async (label, url) => {
      setStatus(`Importing ${label}...`, `before_import_${label}`);
      try {
        const module = await import(url);
        setStatus(`Imported ${label}.`, `after_import_${label}`);
        return module;
      } catch (error) {
        console.error(`StrategixAI failed importing ${label}`, error);
        throw new Error(importFailureHint(url, error));
      }
    };

    const runStep = async (label, action) => {
      setStatus(`${label}...`, `before_${label}`);
      try {
        const result = await action();
        setStatus(`${label} complete.`, `after_${label}`);
        return result;
      } catch (error) {
        console.error(`StrategixAI ${label} failed`, error);
        throw new Error(`${label} failed. ${describeError(error)}`);
      }
    };

    window.addEventListener("error", (event) => {
      if (!terminalStateReached) {
        fail(`Unhandled JavaScript error: ${event.message || "Unknown error"} at ${event.filename || "unknown file"}:${event.lineno || "unknown line"}`);
      }
    });

    window.addEventListener("unhandledrejection", (event) => {
      if (!terminalStateReached) {
        fail(`Unhandled JavaScript promise rejection: ${describeError(event.reason)}`);
      }
    });

    window.setTimeout(() => {
      if (!terminalStateReached && !authReady) {
        fail("Firebase auth did not finish within 20 seconds. Last visible step is shown above; check whether gstatic.com or Google/Firebase auth endpoints are blocked by a browser extension, adblocker, privacy setting, firewall, or network policy.");
      }
    }, 20000);

    const signInWithPopup = async () => {
      if (!firebaseAuth || !googleProvider || !signInWithPopupFn) {
        fail("Firebase Auth is not ready yet. The popup sign-in function was not initialized.");
        return;
      }
      terminalStateReached = false;
      googleButton.disabled = true;
      errorEl.textContent = "";
      errorEl.style.display = "none";
      flow.strategy = "signInWithPopup";
      try {
        setStatus("signInWithPopup()...", "before_signInWithPopup", { beforeSignIn: true });
        const result = await signInWithPopupFn(firebaseAuth, googleProvider);
        logStage("after_signInWithPopup_call", { afterSignInCall: true, authStateRestoredUser: Boolean(firebaseAuth.currentUser) });
        if (!result?.user) {
          throw new Error("signInWithPopup() completed without result.user.");
        }
        setStatus("Getting Firebase ID token...", "before_popup_getIdToken");
        const token = await result.user.getIdToken();
        setStatus("Completing sign-in...", "popup_user", { tokenReady: Boolean(token) });
        finish(token, "popup_user");
      } catch (error) {
        console.error("StrategixAI signInWithPopup failed", error);
        const popupBlocked = error?.code === "auth/popup-blocked";
        if (popupBlocked && signInWithRedirectFn) {
          await fallbackToRedirect(error);
          return;
        }
        fail(`signInWithPopup() failed. ${describeError(error)}`);
      } finally {
        if (!terminalStateReached) {
          googleButton.disabled = false;
        }
      }
    };

    const fallbackToRedirect = async (popupError) => {
      flow.strategy = "signInWithRedirectFallback";
      setStatus(`Popup was blocked or closed; falling back to redirect. ${describeError(popupError)}`, "popup_blocked_redirect_fallback");
      storageSet("strategixai_return_to", returnTo);
      storageSet("strategixai_google_redirect_started", "1");
      setStatus("signInWithRedirect() fallback...", "before_signInWithRedirect", { beforeSignIn: true });
      const redirectPromise = signInWithRedirectFn(firebaseAuth, googleProvider);
      logStage("after_signInWithRedirect_call", { afterSignInCall: true });
      setStatus("Redirecting to Google...", "after_signInWithRedirect_call", { afterSignInCall: true });
      await redirectPromise;
    };

    const main = async () => {
      try {
        setStatus("Firebase helper JavaScript started.", "starting");
        const { initializeApp, getApps } = await importFirebaseModule("firebase-app.js", FIREBASE_APP_URL);
        const {
          getAuth,
          GoogleAuthProvider,
          getRedirectResult,
          onAuthStateChanged,
          signInWithPopup,
          signInWithRedirect,
          setPersistence,
          browserLocalPersistence,
          browserSessionPersistence,
          inMemoryPersistence
        } = await importFirebaseModule("firebase-auth.js", FIREBASE_AUTH_URL);

        const app = await runStep("initializeApp()", () => getApps().length ? getApps()[0] : initializeApp(firebaseConfig));
        const auth = await runStep("getAuth()", () => getAuth(app));
        firebaseAuth = auth;
        signInWithPopupFn = signInWithPopup;
        signInWithRedirectFn = signInWithRedirect;
        googleProvider = new GoogleAuthProvider();
        googleProvider.setCustomParameters({ prompt: "select_account" });

        setStatus("setPersistence()...", "before_setPersistence");
        try {
          await setPersistence(auth, browserLocalPersistence);
          setStatus("setPersistence() complete with browserLocalPersistence.", "after_setPersistence", { authStateRestoredUser: Boolean(auth.currentUser) });
        } catch (persistenceError) {
          console.warn("StrategixAI browserLocalPersistence failed; trying session persistence", persistenceError);
          setStatus(`browserLocalPersistence failed; trying browserSessionPersistence. ${describeError(persistenceError)}`, "setPersistence_local_failed");
          try {
            await setPersistence(auth, browserSessionPersistence);
            setStatus("setPersistence() complete with browserSessionPersistence.", "after_setPersistence", { authStateRestoredUser: Boolean(auth.currentUser) });
          } catch (sessionPersistenceError) {
            console.warn("StrategixAI browserSessionPersistence failed; using in-memory persistence", sessionPersistenceError);
            setStatus(`browserSessionPersistence failed; trying inMemoryPersistence. ${describeError(sessionPersistenceError)}`, "setPersistence_session_failed");
            await setPersistence(auth, inMemoryPersistence);
            setStatus("setPersistence() complete with inMemoryPersistence.", "after_setPersistence", { authStateRestoredUser: Boolean(auth.currentUser) });
          }
        }

        setStatus("getRedirectResult()...", "before_getRedirectResult", { getRedirectResultCalled: true });
        flow.getRedirectResultCalled = true;
        const result = await getRedirectResult(auth);
        setStatus("getRedirectResult() complete.", "after_getRedirectResult", {
          getRedirectResultReturnedUser: Boolean(result?.user),
          authStateRestoredUser: Boolean(auth.currentUser)
        });
        if (result?.user) {
          setStatus("Completing sign-in...", "redirect_result_user");
          storageRemove("strategixai_google_redirect_started");
          finish(await result.user.getIdToken(), "redirect_result_user");
          return;
        }

        setStatus("Restoring Firebase session...", "before_auth_state_restore");
        const restoredUser = await waitForCurrentUser(auth, onAuthStateChanged);
        logStage("after_auth_state_restore", { authStateRestoredUser: Boolean(restoredUser) });
        if (restoredUser) {
          setStatus("Completing restored sign-in...", "restored_current_user");
          storageRemove("strategixai_google_redirect_started");
          finish(await restoredUser.getIdToken(), "restored_current_user");
          return;
        }

        storageRemove("strategixai_google_redirect_started");
        authReady = true;
        googleButton.disabled = false;
        setStatus("Ready. Click Continue with Google.", "ready_for_popup_sign_in");
      } catch (error) {
        console.error("StrategixAI top-level Firebase sign-in failed", error);
        if (error?.code === "auth/unauthorized-domain") {
          fail(
            "Add localhost and 127.0.0.1 to Firebase Authentication > Settings > Authorized domains.",
            "Google sign-in is not available for this app origin. Please contact the app owner."
          );
        } else {
          fail(describeError(error) || "Firebase sign-in failed.");
        }
      }
    };

    googleButton.addEventListener("click", signInWithPopup);
    main();
  </script>
</body>
</html>
"""


LOGOUT_PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Signing out | StrategixAI</title>
  <style>
    * { box-sizing: border-box; }
    html, body {
      margin: 0;
      min-height: 100%;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: #F8FAFC;
      background: linear-gradient(135deg, #05070A 0%, #0B1220 100%);
    }
    .auth-shell {
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 24px 16px;
    }
    .auth-card {
      width: min(100%, 480px);
      border: 1px solid rgba(255, 255, 255, 0.075);
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.045);
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
      padding: clamp(28px, 5vw, 44px);
    }
    .auth-kicker {
      margin-bottom: 14px;
      color: #2F7BFF;
      font-size: 0.76rem;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.12em;
    }
    .auth-brand {
      font-size: clamp(38px, 7vw, 58px);
      line-height: 0.96;
      font-weight: 900;
    }
    .status {
      margin-top: 18px;
      color: #B8C0CC;
      font-size: 0.95rem;
      line-height: 1.6;
    }
    .error {
      display: none;
      margin-top: 12px;
      color: #FCA5A5;
      font-size: 0.84rem;
      line-height: 1.5;
    }
  </style>
</head>
<body>
  <main class="auth-shell">
    <section class="auth-card">
      <div class="auth-kicker">Secure sign-out</div>
      <div class="auth-brand">StrategixAI</div>
      <div class="status" id="status">Signing you out...</div>
      <div class="error" id="error"></div>
    </section>
  </main>
  <script type="module">
    const firebaseConfig = __FIREBASE_CONFIG__;
    const returnTo = __RETURN_TO__;
    const statusEl = document.getElementById("status");
    const errorEl = document.getElementById("error");

    const finish = () => {
      const url = new URL(returnTo);
      url.searchParams.set("signed_out", "1");
      url.searchParams.delete("auth_token");
      window.location.replace(url.toString());
    };

    try {
      const { initializeApp, getApps } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js");
      const { getAuth, signOut } = await import("https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js");
      const app = getApps().length ? getApps()[0] : initializeApp(firebaseConfig);
      const auth = getAuth(app);
      await signOut(auth);
      statusEl.textContent = "Signed out. Returning to login...";
      finish();
    } catch (error) {
      console.error("StrategixAI Firebase sign-out failed", error);
      errorEl.textContent = "We could not fully clear the browser session. Returning to login...";
      errorEl.style.display = "block";
      window.setTimeout(finish, 900);
    }
  </script>
</body>
</html>
"""


def _safe_return_to(value: str | None) -> str:
    fallback = "http://127.0.0.1:8502"
    if not value:
        return fallback
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"}:
        return fallback
    if parsed.hostname not in {"localhost", "127.0.0.1"}:
        return fallback
    return value


def _auth_debug_enabled() -> bool:
    configured = os.getenv("STRATEGIXAI_AUTH_DEBUG", "")
    if not configured:
        configured = str(
            getattr(__import__("streamlit"), "secrets", {}).get("firebase", {}).get("auth_debug", "")
        )
    return configured.strip().lower() in {"1", "true", "yes", "on", "debug"}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/auth/start")
    def auth_start():
        return_to = _safe_return_to(request.args.get("return_to"))
        return render_template_string(
            AUTH_PAGE_TEMPLATE,
        ).replace("__FIREBASE_CONFIG__", json.dumps(firebase_client_config())).replace(
            "__RETURN_TO__",
            json.dumps(return_to),
        ).replace(
            "__DEBUG_DISPLAY__",
            "block" if _auth_debug_enabled() else "none",
        ).replace(
            "__AUTH_DEBUG__",
            "true" if _auth_debug_enabled() else "false",
        )

    @app.get("/auth/logout")
    def auth_logout():
        return_to = _safe_return_to(request.args.get("return_to"))
        return render_template_string(
            LOGOUT_PAGE_TEMPLATE,
        ).replace("__FIREBASE_CONFIG__", json.dumps(firebase_client_config())).replace(
            "__RETURN_TO__",
            json.dumps(return_to),
        )

    @app.get("/api/me")
    @require_firebase_auth
    def me():
        return jsonify(g.current_user)

    @app.get("/api/simulations")
    @require_firebase_auth
    def simulations():
        return jsonify(list_user_collection(g.current_user["uid"], "simulations"))

    @app.post("/api/simulations")
    @require_firebase_auth
    def create_simulation():
        simulation_id = save_user_simulation(g.current_user["uid"], request.get_json(silent=True) or {})
        return jsonify({"id": simulation_id}), 201

    @app.get("/api/reports")
    @require_firebase_auth
    def reports():
        return jsonify(list_user_collection(g.current_user["uid"], "reports"))

    @app.post("/api/reports")
    @require_firebase_auth
    def create_report():
        report_id = save_user_report(g.current_user["uid"], request.get_json(silent=True) or {})
        return jsonify({"id": report_id}), 201

    return app


app = create_app()
