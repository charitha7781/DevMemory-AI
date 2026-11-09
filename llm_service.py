"""
llm_service.py  (Member 1)

Single LLM provider: Google Gemini (package: google-genai).
To switch provider later, only generate_response() has to change.

Env vars: LLM_API_KEY (required), LLM_MODEL (default gemini-2.5-flash)
"""
from __future__ import annotations

import json
import os
import re
import time

from dotenv import load_dotenv

load_dotenv()


class LLMError(Exception):
    """Raised with a user-friendly message (never a raw traceback)."""


def _api_key() -> str | None:
    return os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def generate_response(prompt: str, system: str | None = None, json_mode: bool = False) -> str:
    key = _api_key()
    if not key:
        raise LLMError("LLM_API_KEY is not set. Add it to your local .env file.")
    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")

    try:
        from google import genai
        from google.genai import types
    except ImportError as exc:
        raise LLMError("Package 'google-genai' is not installed. Run: pip install google-genai") from exc

    cfg: dict = {"temperature": 0.2}
    if system:
        cfg["system_instruction"] = system
    if json_mode:
        cfg["response_mime_type"] = "application/json"

    for attempt in range(3):
        try:
            client = genai.Client(api_key=key)
            resp = client.models.generate_content(
                model=model, contents=prompt, config=types.GenerateContentConfig(**cfg))
            text = (resp.text or "").strip()
            if not text:
                raise LLMError("The model returned an empty response. Please try again.")
            return text
        except LLMError:
            raise
        except Exception as exc:  # noqa: BLE001
            low = str(exc).lower()
            if any(k in low for k in ("429", "resource_exhausted", "quota", "rate limit", "rate-limit",
                                      "503", "unavailable", "overloaded")):
                if attempt < 2:
                    time.sleep(2 * (attempt + 1))
                    continue
                raise LLMError("The LLM is rate-limited or overloaded right now. Wait a moment and retry.") from exc
            if any(k in low for k in ("api key", "api_key_invalid", "401", "403", "permission")):
                raise LLMError("The LLM rejected the API key. Check LLM_API_KEY in your .env file.") from exc
            if ("404" in low or "not found" in low) and "model" in low:
                raise LLMError(f"Model '{model}' was not found. Set LLM_MODEL in .env to a model "
                               f"your key can use.") from exc
            raise LLMError(f"LLM request failed: {str(exc)[:300]}") from exc
    raise LLMError("The LLM did not respond. Please try again.")


def _parse_json(text: str) -> dict:
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I)
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        s, e = t.find("{"), t.rfind("}")
        if s == -1 or e <= s:
            raise LLMError("The model's answer was not valid JSON. Please try again.")
        try:
            data = json.loads(t[s:e + 1])
        except json.JSONDecodeError as exc:
            raise LLMError("The model's answer was not valid JSON. Please try again.") from exc
    if not isinstance(data, dict):
        raise LLMError("The model's answer had an unexpected format. Please try again.")
    return data


def generate_json(prompt: str, system: str | None = None) -> dict:
    """Ask the model for a JSON object and return it parsed (one automatic retry on bad JSON)."""
    try:
        return _parse_json(generate_response(prompt, system=system, json_mode=True))
    except LLMError as exc:
        if "valid JSON" not in str(exc):
            raise
        return _parse_json(generate_response(prompt + "\n\nReturn ONLY a valid JSON object.",
                                             system=system, json_mode=True))


def ping() -> dict:
    try:
        generate_response("Reply with the single word: ok")
        return {"ok": True, "error": None, "model": os.getenv("LLM_MODEL", "gemini-2.5-flash")}
    except LLMError as exc:
        return {"ok": False, "error": str(exc), "model": os.getenv("LLM_MODEL", "gemini-2.5-flash")}
