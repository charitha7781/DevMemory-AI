"""incident_engine.py (Member 1) - Incident Intelligence."""
from __future__ import annotations

import hindsight_memory as hm
import llm_service
from engine_utils import (COMMON_RULES, MAX_INPUT_CHARS, as_list, as_str, attach_memory,
                          extract_query, memory_block, parse_indices)

SYSTEM = "You are DevMemory AI, a careful senior site-reliability engineer who learns from past incidents."

SCHEMA = """{
  "title": "short incident title",
  "root_cause": "the LIKELY root cause, phrased as likely/possible",
  "confidence": "low | medium | high",
  "recommendations": ["ordered, concrete actions the developer should try"],
  "memory_insight": "how past memory changed your advice, or 'No relevant past memory.'",
  "used_memory_numbers": [1]
}"""


def _result() -> dict:
    return {
        "problem_id": None, "title": "", "root_cause": "", "confidence": "low",
        "recommendations": [], "recalled_memories": [], "memory_used": False,
        "memory_status": "empty", "memory_insight": "",
        "previously_verified_solutions": [], "previously_failed_attempts": [],
        "warnings": [], "error": None,
    }


def analyse_incident(log_text: str) -> dict:
    """Analyse an error log / stack trace using Hindsight memory + the LLM. Never raises."""
    result = _result()
    if not (log_text or "").strip():
        result["error"] = "Please paste an error log or stack trace."
        return result

    log = hm.sanitize(log_text.strip())[:MAX_INPUT_CHARS]

    # 1) Recall similar past incidents
    mem = hm.retrieve_memory(extract_query(log), module="incident")
    memories = mem["memories"]
    result["memory_status"] = mem["status"]
    if mem["status"] == "unavailable":
        result["warnings"].append(f"{mem['error']} The analysis below does NOT use past memory.")
    elif mem["status"] == "empty":
        result["warnings"].append("No relevant past memory was found; this is a fresh analysis.")

    # 2) Ask the LLM, with the recalled memories in the prompt
    prompt = f"""Analyse this production incident.

{COMMON_RULES}
PAST MEMORIES:
{memory_block(memories)}

INCIDENT LOG:
<<<
{log}
>>>

Return ONLY a JSON object with exactly this shape:
{SCHEMA}"""
    try:
        data = llm_service.generate_json(prompt, system=SYSTEM)
    except llm_service.LLMError as exc:
        result["error"] = str(exc)
        result["recalled_memories"] = [m["text"] for m in memories]
        return result

    result["title"] = as_str(data.get("title"), "Incident")
    result["root_cause"] = as_str(data.get("root_cause"), "Could not determine a likely cause.")
    result["confidence"] = as_str(data.get("confidence"), "low").lower()
    result["recommendations"] = as_list(data.get("recommendations"))
    result["memory_insight"] = as_str(data.get("memory_insight"), "No relevant past memory.")
    attach_memory(result, memories, parse_indices(data.get("used_memory_numbers"), len(memories)))

    # 3) Keep the (still UNVERIFIED) suggestion locally until the developer gives feedback
    result["problem_id"] = hm.new_problem_id("incident")
    hm.save_pending(result["problem_id"], {
        "module": "incident", "problem": result["title"] + ": " + log[:300].replace("\n", " "),
        "root_cause": result["root_cause"], "recommendations": result["recommendations"],
    })
    return result
