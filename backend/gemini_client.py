from __future__ import annotations

import logging
import tomllib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from functools import lru_cache
from pathlib import Path
from typing import Any, TYPE_CHECKING

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None  # type: ignore[assignment]
    types = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from google.genai.client import Client as GeminiClient


logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-3.5-flash"
REQUEST_TIMEOUT_SECONDS = 20
REQUEST_TIMEOUT_MS = REQUEST_TIMEOUT_SECONDS * 1000
UNAVAILABLE_MESSAGE = "StrategixAI Copilot is temporarily unavailable."

EXECUTIVE_SYSTEM_PROMPT = """
You are StrategixAI Executive Strategy Copilot.

Operate like a senior strategy consultant and executive advisor. Your tone is
professional, concise, data-driven, business-focused, and suitable for MBA,
consulting, founder, and boardroom audiences.

Help with strategy, growth, profitability, revenue, risks, customer growth,
scenario tradeoffs, and boardroom communication. Avoid generic chatbot phrasing.
When data is not provided, state assumptions clearly and give practical
executive guidance rather than fabricating facts.
""".strip()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _secrets_path() -> Path:
    return _project_root() / ".streamlit" / "secrets.toml"


@lru_cache(maxsize=1)
def _load_gemini_api_key() -> str | None:
    path = _secrets_path()
    if not path.exists():
        logger.warning("Gemini secrets file is missing.")
        return None

    try:
        with path.open("rb") as secrets_file:
            secrets = tomllib.load(secrets_file)
    except Exception:
        logger.exception("Gemini secrets file could not be read.")
        return None

    gemini_config = secrets.get("gemini")
    if not isinstance(gemini_config, dict):
        logger.warning("Gemini secrets section is missing.")
        return None

    api_key = gemini_config.get("api_key")
    if not isinstance(api_key, str) or not api_key.strip():
        logger.warning("Gemini API key is missing.")
        return None

    return api_key.strip()


@lru_cache(maxsize=1)
def _client() -> "GeminiClient | None":
    api_key = _load_gemini_api_key()
    if not api_key:
        return None
    if genai is None or types is None:
        logger.warning("google-genai package is not available.")
        return None

    try:
        return genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
    except Exception:
        logger.exception("Gemini client initialization failed.")
        return None


def is_gemini_available() -> bool:
    """Return whether Gemini is configured and the SDK client can initialize."""

    return _client() is not None


def generate_response(prompt: str) -> dict[str, Any]:
    """Generate a Copilot response with a stable backend-safe response shape."""

    clean_prompt = prompt.strip() if isinstance(prompt, str) else ""
    if not clean_prompt:
        return {
            "ok": False,
            "reply": UNAVAILABLE_MESSAGE,
            "source": "gemini",
            "model": MODEL_NAME,
            "error": "empty_prompt",
        }

    client = _client()
    if client is None:
        return {
            "ok": False,
            "reply": UNAVAILABLE_MESSAGE,
            "source": "gemini",
            "model": MODEL_NAME,
            "error": "gemini_unavailable",
        }

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_generate_content, client, clean_prompt)
            response_text = future.result(timeout=REQUEST_TIMEOUT_SECONDS)
    except FutureTimeoutError:
        logger.warning("Gemini response timed out.")
        return {
            "ok": False,
            "reply": UNAVAILABLE_MESSAGE,
            "source": "gemini",
            "model": MODEL_NAME,
            "error": "gemini_timeout",
        }
    except Exception:
        logger.exception("Gemini response generation failed.")
        return {
            "ok": False,
            "reply": UNAVAILABLE_MESSAGE,
            "source": "gemini",
            "model": MODEL_NAME,
            "error": "gemini_generation_failed",
        }

    if not response_text:
        logger.warning("Gemini returned an empty response.")
        return {
            "ok": False,
            "reply": UNAVAILABLE_MESSAGE,
            "source": "gemini",
            "model": MODEL_NAME,
            "error": "empty_response",
        }

    return {
        "ok": True,
        "reply": response_text,
        "source": "gemini",
        "model": MODEL_NAME,
        "error": None,
    }


def _generate_content(client: "GeminiClient", prompt: str) -> str:
    if types is None:
        raise RuntimeError("google-genai types are unavailable.")

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            systemInstruction=EXECUTIVE_SYSTEM_PROMPT,
            temperature=0.35,
            maxOutputTokens=900,
        ),
    )
    text = getattr(response, "text", None)
    return text.strip() if isinstance(text, str) else ""
