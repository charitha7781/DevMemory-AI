"""
hindsight_memory.py  (Member 1)

ALL direct communication with Hindsight lives here. Uses the official Python client:
    pip install hindsight-client
    from hindsight_client import Hindsight
    client.retain(bank_id=..., content=...)
    client.recall(bank_id=..., query=...)      -> .results[i].text / .type
    client.reflect(bank_id=..., query=...)     -> .text

Every public function returns a dict and NEVER raises, so the Streamlit UI cannot crash
because of a memory problem.

Public API
    store_memory(data)                -> {"ok", "error", "document_id"}
    retrieve_memory(query, module)    -> {"ok", "status", "memories":[{text,type,status}], "error"}
    reflect_memory(query, context)    -> {"ok", "text", "error"}
    record_feedback(problem_id, outcome, developer_note, fix_applied) -> {"ok", "error", ...}
    list_memories(limit)              -> {"ok", "items":[str], "error"}   (for Memory Explorer)
    memory_health()                   -> {"ok", "error", "bank_id", "base_url"}
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout
import json
import os
import re
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

BANK_ID = os.getenv("HINDSIGHT_BANK_ID", "devmemory-ai")
BASE_URL = os.getenv("HINDSIGHT_BASE_URL", "http://localhost:8888")
API_KEY = os.getenv("HINDSIGHT_API_KEY") or None
TIMEOUT = float(os.getenv("HINDSIGHT_TIMEOUT", "90"))
MAX_RECALL = int(os.getenv("HINDSIGHT_MAX_RECALL", "6"))
EXECUTOR_TIMEOUT = TIMEOUT + 30

VALID_MODULES = {"incident", "code_review", "deployment"}
PENDING_FILE = Path(__file__).resolve().parent / ".pending_analyses.json"

_client = None
_bank_ready = False
_bank_error: str | None = None
_lock = threading.Lock()
_shutdown_lock = threading.Lock()
_shutdown = False

_hindsight_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="hindsight"
)


def _submit_and_wait(fn, *args, **kwargs):
    """Submit work to the Hindsight worker and wait with a bounded timeout."""
    future = _hindsight_executor.submit(fn, *args, **kwargs)
    try:
        return future.result(timeout=EXECUTOR_TIMEOUT)
    except FuturesTimeout as exc:
        future.cancel()
        raise MemoryUnavailable(
            f"Hindsight operation timed out after {EXECUTOR_TIMEOUT:.0f}s."
        ) from exc


def _call_hindsight(method_name: str, **kwargs):
    """Run Hindsight SDK operations on one dedicated worker thread."""
    client = _get_client()
    method = getattr(client, method_name)

    return _submit_and_wait(method, **kwargs)


def _close_client():
    """Close and reset the shared client on the executor worker thread."""
    global _client, _bank_ready, _bank_error

    client = _client
    _client = None
    _bank_ready = False
    _bank_error = None

    if client is None:
        return {"ok": True, "error": None}

    try:
        client.close()
        return {"ok": True, "error": None}
    except Exception as exc:
        return {"ok": False, "error": _friendly_error(exc)}


def close_hindsight():
    """Close the Hindsight client on its worker thread. Safe to call repeatedly."""
    if _shutdown:
        return {"ok": False, "error": "Hindsight executor has been shut down."}

    try:
        return _submit_and_wait(_close_client)
    except Exception as exc:
        return {"ok": False, "error": _friendly_error(exc)}


def shutdown_hindsight():
    """Close the client and stop the worker thread. Idempotent; not reusable afterwards."""
    global _shutdown

    with _shutdown_lock:
        if _shutdown:
            return {"ok": True, "error": None}

        result = close_hindsight()
        _hindsight_executor.shutdown(wait=True)
        _shutdown = True

    return result


class MemoryUnavailable(Exception):
    """Hindsight cannot be used (missing package / not reachable / bad credentials)."""


# --------------------------------------------------------------------------- #
# Client handling
# --------------------------------------------------------------------------- #
def _friendly_error(exc: Exception) -> str:
    if isinstance(exc, MemoryUnavailable):
        return str(exc)
    msg = str(exc) or exc.__class__.__name__
    low = msg.lower()
    if any(k in low for k in ("401", "403", "unauthorized", "forbidden", "invalid api key")):
        return "Hindsight rejected the credentials. Check HINDSIGHT_API_KEY in your .env file."
    if any(k in low for k in ("connection", "connect", "refused", "timed out", "timeout",
                              "name or service", "resolve", "unreachable")):
        return (f"Cannot reach Hindsight at {BASE_URL}. Check HINDSIGHT_BASE_URL and make sure "
                f"the Hindsight server/service is running.")
    return f"Hindsight error: {msg[:300]}"



def _init_client():
    """Create and initialise the Hindsight client on the executor worker thread."""
    global _client, _bank_ready, _bank_error

    if _client is None:
        try:
            from hindsight_client import Hindsight
        except ImportError as exc:
            raise MemoryUnavailable(
                "Package 'hindsight-client' is not installed. Run: pip install hindsight-client"
            ) from exc

        kwargs: dict[str, Any] = {
            "base_url": BASE_URL,
            "timeout": TIMEOUT
        }

        if API_KEY:
            kwargs["api_key"] = API_KEY

        _client = Hindsight(**kwargs)
        _bank_ready = False

    if _bank_ready:
        return _client

    try:
        _client.create_bank(
            bank_id=BANK_ID,
            name="DevMemory AI",
            mission=(
                "Engineering memory for incidents, code reviews and deployment failures. "
                "Always distinguish developer-verified fixes from unverified AI suggestions "
                "and from fixes that were tried and failed."
            ),
        )
        _bank_ready = True
        _bank_error = None

    except Exception as exc:
        # An existing bank is the common "failure"; anything else leaves the bank
        # unready so a later call can retry instead of caching a false success.
        message = str(exc).lower()
        if any(k in message for k in ("already exists", "already exist", "duplicate", "conflict", "409")):
            _bank_ready = True
            _bank_error = None
        else:
            _bank_ready = False
            _bank_error = _friendly_error(exc)

    return _client


def _get_client():
    """Return the shared client, built and initialised on the worker thread."""
    if _shutdown:
        raise MemoryUnavailable("Hindsight executor has been shut down.")

    return _submit_and_wait(_init_client)


# --------------------------------------------------------------------------- #
# Safety: never store secrets / personal data
# --------------------------------------------------------------------------- #
_REDACTIONS = [
    (re.compile(r"(?i)\b((?:api[_-]?key|secret|token|password|passwd|pwd|auth)\w*\s*[:=]\s*)([\"']?)[^\s\"',;]+\2"),
     r"\1[REDACTED]"),
    (re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._\-]{12,}"), "Bearer [REDACTED]"),
    (re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}"), "[REDACTED_KEY]"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{20,}"), "[REDACTED_KEY]"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"), "[REDACTED_KEY]"),
    (re.compile(r"\bAKIA[0-9A-Z]{12,}"), "[REDACTED_KEY]"),
    (re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"), "[REDACTED_EMAIL]"),
    (re.compile(r"(?i)(://[^:/\s]+:)[^@\s]+(@)"), r"\1[REDACTED]\2"),  # user:pass@host in URLs
]


def sanitize(text: str) -> str:
    """Remove obvious credentials / emails before text is sent to the LLM or stored."""
    for pattern, repl in _REDACTIONS:
        text = pattern.sub(repl, text)
    return text


# --------------------------------------------------------------------------- #
# Memory text format  (natural language so Hindsight's fact extraction keeps the status)
# --------------------------------------------------------------------------- #
def _norm_outcome(outcome: str) -> str:
    o = (outcome or "").strip().lower()
    if o in {"success", "succeeded", "worked", "confirmed", "verified", "fixed", "yes", "confirmed_success"}:
        return "success"
    if o in {"failure", "failed", "fail", "no", "unsuccessful", "did not work", "confirmed_failure"}:
        return "failure"
    if o in {"convention", "info"}:
        return o
    return "unverified"


def build_memory_text(data: dict) -> str:
    module = str(data.get("module", "")).strip().lower()
    outcome = _norm_outcome(str(data.get("outcome", "")))
    g = lambda k: sanitize(str(data.get(k) or "").strip())  # noqa: E731
    problem, cause, fix, notes = g("problem"), g("root_cause"), g("suggested_fix"), g("notes")

    if outcome == "success":
        parts = [f"DEVELOPER-VERIFIED SUCCESS ({module} module).",
                 f"Problem: {problem}."]
        if cause:
            parts.append(f"Root cause: {cause}.")
        parts.append(f"Fix that WORKED, confirmed by the developer: {fix or 'not specified'}.")
    elif outcome == "failure":
        parts = [f"DEVELOPER-REPORTED FAILURE ({module} module).",
                 f"Problem: {problem}.",
                 f"Attempted fix that DID NOT WORK: {fix or 'not specified'}.",
                 "This was an unsuccessful attempt and must NOT be recommended as a verified fix."]
        if cause:
            parts.append(f"Suspected cause at the time: {cause}.")
    elif outcome == "convention":
        parts = [f"PROJECT CONVENTION ({module} module): {problem}."]
    else:
        parts = [f"UNVERIFIED SUGGESTION ({module} module).",
                 f"Problem: {problem}.",
                 f"Suggested fix (NOT tested by a developer): {fix or 'not specified'}."]
    if notes:
        parts.append(f"Developer note: {notes}.")
    return " ".join(parts)


def classify_memory(text: str) -> str:
    """verified_success | failed_attempt | unverified | convention | other

    Hindsight extracts facts from what we retain and may paraphrase them, so our own markers are
    checked first and plain-language heuristics second. Check the real recalled text during testing.
    """
    t = text.lower()
    if "developer-verified success" in t:
        return "verified_success"
    if "developer-reported failure" in t:
        return "failed_attempt"
    if "project convention" in t:
        return "convention"
    if "unverified suggestion" in t:
        return "unverified"
    if ("did not work" in t or "failed attempt" in t or "unsuccessful attempt" in t
            or "did not fix" in t or "was unsuccessful" in t):
        return "failed_attempt"
    if "verified" in t and ("worked" in t or "resolved" in t or "confirmed" in t):
        return "verified_success"
    if "not tested" in t or "not been tested" in t or "unverified" in t:
        return "unverified"
    return "other"


# --------------------------------------------------------------------------- #
# retain / recall / reflect
# --------------------------------------------------------------------------- #

def store_memory(data: dict) -> dict:
    """
    Retain one structured record in the shared Hindsight bank.
    """
    try:
        module = str(data.get("module", "")).strip().lower()

        if module not in VALID_MODULES:
            return {
                "ok": False,
                "error": f"module must be one of {sorted(VALID_MODULES)}",
                "document_id": None,
            }

        if not str(data.get("problem", "")).strip():
            return {
                "ok": False,
                "error": "'problem' is required.",
                "document_id": None,
            }

        outcome = _norm_outcome(str(data.get("outcome", "")))
        content = build_memory_text(data)
        problem_id = str(data.get("problem_id") or uuid.uuid4().hex[:8])
        document_id = f"{problem_id}-{outcome}"

        _call_hindsight(
            "retain",
            bank_id=BANK_ID,
            content=content,
            context=f"devmemory {module} {outcome}",
            timestamp=datetime.now(),
            document_id=document_id,
            metadata={
                "module": module,
                "outcome": outcome,
                "verified_by_developer": str(
                    bool(data.get("verified_by_developer", False))
                ).lower(),
                "problem_id": problem_id,
            },
            retain_async=False,
        )

        return {
            "ok": True,
            "error": None,
            "document_id": document_id,
        }

    except Exception as exc:
        return {
            "ok": False,
            "error": _friendly_error(exc),
            "document_id": None,
        }



def retrieve_memory(query: str, module: str | None = None) -> dict:
    """Recall relevant memories. status is 'ok', 'empty' or 'unavailable'."""
    try:
        query = sanitize((query or "").strip())[:1000]
        if not query:
            return {"ok": True, "status": "empty", "memories": [], "error": None}
        if module:
            query = f"{module} module: {query}"

        response = _call_hindsight(
                            "recall",
                            bank_id=BANK_ID,
                            query=query,
                            max_tokens=2048,
                            budget="mid",
                        )

        memories: list[dict] = []
        seen: set[str] = set()
        for r in getattr(response, "results", None) or []:
            text = (getattr(r, "text", "") or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            memories.append({"text": text,
                             "type": str(getattr(r, "type", "") or ""),
                             "status": classify_memory(text)})
            if len(memories) >= MAX_RECALL:
                break
        return {"ok": True, "status": "ok" if memories else "empty", "memories": memories, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "status": "unavailable", "memories": [], "error": _friendly_error(exc)}


def reflect_memory(query: str, context: str | None = None) -> dict:
    """Ask Hindsight to reflect (higher-level insight) over stored memories."""
    try:
        kwargs: dict[str, Any] = {"bank_id": BANK_ID, "query": sanitize(query), "budget": "low"}
        if context:
            kwargs["context"] = sanitize(context)
        answer = _call_hindsight("reflect", **kwargs)
        return {"ok": True, "text": (getattr(answer, "text", "") or "").strip(), "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "text": "", "error": _friendly_error(exc)}


def list_memories(limit: int = 50) -> dict:
    """Best-effort listing for the Memory Explorer screen."""
    try:
        resp = _call_hindsight(
                    "list_memories",
                    bank_id=BANK_ID,
                    limit=limit,
                    offset=0,
                )
        raw = (getattr(resp, "items", None) or getattr(resp, "memories", None)
               or getattr(resp, "results", None) or (resp if isinstance(resp, list) else []))
        items = []
        for it in raw:
            text = it.get("text") if isinstance(it, dict) else getattr(it, "text", None)
            items.append(str(text if text else it))
        return {"ok": True, "items": items, "error": None}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "items": [], "error": _friendly_error(exc)}


def memory_health() -> dict:
    try:
        _call_hindsight("get_version")
        return {"ok": True, "error": None, "bank_id": BANK_ID, "base_url": BASE_URL,
                "bank_error": _bank_error}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": _friendly_error(exc), "bank_id": BANK_ID, "base_url": BASE_URL,
                "bank_error": _bank_error}


# --------------------------------------------------------------------------- #
# Pending analyses (AI suggestions that no developer has verified yet).
# They are NOT written to Hindsight until the developer gives feedback, so an untested
# AI suggestion can never be recalled later as if it were a proven fix.
# --------------------------------------------------------------------------- #
def new_problem_id(module: str) -> str:
    return f"{module[:3]}-{uuid.uuid4().hex[:8]}"


def _read_pending() -> dict:
    try:
        return json.loads(PENDING_FILE.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def save_pending(problem_id: str, record: dict) -> None:
    with _lock:
        data = _read_pending()
        data[problem_id] = {**record, "created_at": datetime.now().isoformat(timespec="seconds")}
        if len(data) > 200:  # keep the file small
            for k in list(data)[: len(data) - 200]:
                data.pop(k, None)
        try:
            PENDING_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass


def load_pending(problem_id: str) -> dict | None:
    return _read_pending().get(problem_id)


# --------------------------------------------------------------------------- #
# Developer feedback  -> verified success / unsuccessful attempt
# --------------------------------------------------------------------------- #
def record_feedback(problem_id: str, outcome: str, developer_note: str = "", fix_applied: str = "") -> dict:
    """
    outcome: "success" (fix worked) or "failure" (fix did not work).
    fix_applied: which fix the developer actually tried (defaults to the AI's top recommendations).
    """
    norm = _norm_outcome(outcome)
    if norm not in {"success", "failure"}:
        return {"ok": False, "error": "outcome must be 'success' or 'failure'."}

    pending = load_pending(problem_id)
    if not pending:
        return {"ok": False, "error": f"Unknown problem_id '{problem_id}'. Run an analysis first."}

    fix = fix_applied.strip() or "; ".join(pending.get("recommendations", [])[:3])
    result = store_memory({
        "module": pending["module"],
        "problem": pending.get("problem", ""),
        "root_cause": pending.get("root_cause", ""),
        "suggested_fix": fix,
        "outcome": norm,
        "verified_by_developer": True,
        "notes": developer_note,
        "problem_id": problem_id,
    })
    return {**result, "outcome": norm}
