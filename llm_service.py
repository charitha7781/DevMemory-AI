
from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


class LLMError(Exception):
    pass


def _api_key():
    return os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY")


def generate_response(prompt, system=None, json_mode=False):
    key = _api_key()

    if not key:
        raise LLMError("Missing Groq API key. Check LLM_API_KEY in .env.")

    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    try:
        client = Groq(api_key=key)

        messages = []

        if system:
            messages.append({
                "role": "system",
                "content": system
            })

        messages.append({
            "role": "user",
            "content": prompt
        })

        kwargs = {
            "model": model,
            "messages": messages,
            "temperature": 0.2,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = client.chat.completions.create(**kwargs)

        result = response.choices[0].message.content

        if not result:
            raise LLMError("The LLM returned an empty response.")

        return result.strip()

    except LLMError:
        raise

    except Exception as exc:
        message = str(exc).lower()

        if any(word in message for word in ("401", "403", "invalid api key", "authentication")):
            raise LLMError("Groq rejected the API key. Check LLM_API_KEY in .env.") from exc

        if any(word in message for word in ("429", "rate limit", "quota")):
            raise LLMError("Groq rate limit reached. Wait briefly and retry.") from exc

        if "model" in message and ("not found" in message or "decommissioned" in message):
            raise LLMError(f"Groq model '{model}' is unavailable. Check LLM_MODEL.") from exc

        raise LLMError(f"Groq request failed: {str(exc)[:300]}") from exc


def _parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)

        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        raise LLMError("The LLM did not return valid JSON.")


def generate_json(prompt, system=None):
    return _parse_json(
        generate_response(prompt, system=system, json_mode=True)
    )


def ping():
    try:
        generate_response("Reply with the single word: ok")
        return {"ok": True, "error": None}
    except LLMError as exc:
        return {"ok": False, "error": str(exc)}
