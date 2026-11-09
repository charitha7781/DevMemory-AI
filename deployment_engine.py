"""deployment_engine.py (Member 1) - Deployment / CI-CD Intelligence."""
from __future__ import annotations

import hindsight_memory as hm
import llm_service
from engine_utils import (COMMON_RULES, MAX_INPUT_CHARS, as_list, as_str, attach_memory,
                          extract_query, memory_block, parse_indices)

SYSTEM = "You are DevMemory AI, a careful DevOps engineer who learns from past pipeline failures."

SCHEMA = """{
  "failed_stage": "e.g. dependency installation | build | test | docker build | deploy | health check",
  "possible_cause": "the POSSIBLE cause, phrased as possible/likely",
  "confidence": "low | medium | high",
  "recommendations": ["ordered troubleshooting steps"],
  "memory_insight": "how past failures/outcomes influenced your advice, or 'No relevant past memory.'",
  "used_memory_numbers": [1]
}"""

# Used only if the LLM is unavailable, so the screen still shows something useful.
_STAGES = [
    ("dependency installation", ("dependency", "pip install", "npm install", "package version", "requirements", "resolution")),
    ("test", ("test failed", "tests failed", "assertionerror", "pytest", "jest")),
    ("docker build", ("docker", "dockerfile", "image build")),
    ("build", ("build failed", "compilation", "compile error", "syntaxerror")),
    ("deployment", ("deploy", "rollout", "kubectl", "helm")),
    ("health check", ("health check", "readiness", "liveness", "502", "503")),
]


def _guess_stage(log: str) -> str:
    low = log.lower()
    for stage, words in _STAGES:
        if any(w in low for w in words):
            return stage
    return "unknown"


def _result() -> dict:
    return {
        "problem_id": None, "failed_stage": "", "possible_cause": "", "confidence": "low",
        "recommendations": [], "recalled_memories": [], "memory_used": False,
        "memory_status": "empty", "memory_insight": "",
        "previously_verified_solutions": [], "previously_failed_attempts": [],
        "warnings": [], "error": None,
    }


def analyse_deployment(log_text: str) -> dict:
    """Analyse deployment / CI-CD logs. Never raises."""
    result = _result()
    if not (log_text or "").strip():
        result["error"] = "Please paste deployment or pipeline logs."
        return result

    log = hm.sanitize(log_text.strip())[:MAX_INPUT_CHARS]

    mem = hm.retrieve_memory(extract_query(log), module="deployment")
    memories = mem["memories"]
    result["memory_status"] = mem["status"]
    if mem["status"] == "unavailable":
        result["warnings"].append(f"{mem['error']} The analysis below does NOT use past memory.")
    elif mem["status"] == "empty":
        result["warnings"].append("No relevant past deployment memory was found.")

    prompt = f"""Analyse this deployment / CI-CD failure. Identify the failed stage and the possible cause.

{COMMON_RULES}
PAST MEMORIES:
{memory_block(memories)}

DEPLOYMENT LOG:
<<<
{log}
>>>

Return ONLY a JSON object with exactly this shape:
{SCHEMA}"""
    try:
        data = llm_service.generate_json(prompt, system=SYSTEM)
    except llm_service.LLMError as exc:
        # graceful fallback: heuristic stage + clear message, no invented cause
        result["error"] = str(exc)
        result["failed_stage"] = _guess_stage(log)
        result["possible_cause"] = "AI analysis unavailable; stage estimated from keywords in the log."
        result["recalled_memories"] = [m["text"] for m in memories]
        return result

    result["failed_stage"] = as_str(data.get("failed_stage"), _guess_stage(log))
    result["possible_cause"] = as_str(data.get("possible_cause"), "Could not determine a likely cause.")
    result["confidence"] = as_str(data.get("confidence"), "low").lower()
    result["recommendations"] = as_list(data.get("recommendations"))
    result["memory_insight"] = as_str(data.get("memory_insight"), "No relevant past memory.")
    attach_memory(result, memories, parse_indices(data.get("used_memory_numbers"), len(memories)))

    result["problem_id"] = hm.new_problem_id("deployment")
    hm.save_pending(result["problem_id"], {
        "module": "deployment",
        "problem": f"Deployment failed at {result['failed_stage']}: {log[:250]}".replace("\n", " "),
        "root_cause": result["possible_cause"], "recommendations": result["recommendations"],
    })
    return result
