"""code_review_engine.py (Member 1) - Intelligent Code Review."""
from __future__ import annotations

import hindsight_memory as hm
import llm_service
from engine_utils import (COMMON_RULES, MAX_INPUT_CHARS, as_list, as_str, attach_memory,
                          memory_block, parse_indices)

SYSTEM = "You are DevMemory AI, a meticulous senior code reviewer who remembers recurring issues and project conventions."

SCHEMA = """{
  "summary": "2-3 sentence overall assessment",
  "findings": [
    {"severity": "high | medium | low", "category": "bug | logic | security | performance | style",
     "issue": "what is wrong and where (function / line hint)", "fix": "how to fix it"}
  ],
  "suggestions": ["general improvements"],
  "memory_insight": "how past memory (recurring issues/conventions) influenced the review, or 'No relevant past memory.'",
  "used_memory_numbers": [1]
}"""


def _result() -> dict:
    return {
        "problem_id": None, "summary": "", "findings": [], "findings_detailed": [], "suggestions": [],
        "recalled_memories": [], "memory_used": False, "memory_status": "empty", "memory_insight": "",
        "previously_verified_solutions": [], "previously_failed_attempts": [],
        "warnings": [], "error": None,
    }


def review_code(code: str, language: str = "python") -> dict:
    """Review source code. Never raises."""
    result = _result()
    if not (code or "").strip():
        result["error"] = "Please paste some code to review."
        return result

    language = (language or "python").strip()
    src = hm.sanitize(code.strip())[:MAX_INPUT_CHARS]

    mem = hm.retrieve_memory(f"{language} code review findings and conventions. {src[:400]}", module="code_review")
    memories = mem["memories"]
    result["memory_status"] = mem["status"]
    if mem["status"] == "unavailable":
        result["warnings"].append(f"{mem['error']} The review below does NOT use past memory.")
    elif mem["status"] == "empty":
        result["warnings"].append("No relevant past review memory was found.")

    prompt = f"""Review this {language} code for bugs, logic errors, security concerns and improvements.

{COMMON_RULES}
PAST MEMORIES (earlier review findings, recurring issues, project conventions):
{memory_block(memories)}

CODE ({language}):
<<<
{src}
>>>

Return ONLY a JSON object with exactly this shape:
{SCHEMA}"""
    try:
        data = llm_service.generate_json(prompt, system=SYSTEM)
    except llm_service.LLMError as exc:
        result["error"] = str(exc)
        result["recalled_memories"] = [m["text"] for m in memories]
        return result

    detailed = [f for f in (data.get("findings") or []) if isinstance(f, dict)]
    result["findings_detailed"] = detailed
    flat = [f"[{as_str(f.get('severity'), 'info').upper()}] {as_str(f.get('issue'))}"
            + (f" Fix: {as_str(f.get('fix'))}" if f.get("fix") else "") for f in detailed]
    result["findings"] = flat or as_list(data.get("findings"))
    result["summary"] = as_str(data.get("summary"), "Review complete.")
    result["suggestions"] = as_list(data.get("suggestions"))
    result["memory_insight"] = as_str(data.get("memory_insight"), "No relevant past memory.")
    attach_memory(result, memories, parse_indices(data.get("used_memory_numbers"), len(memories)))

    result["problem_id"] = hm.new_problem_id("code_review")
    hm.save_pending(result["problem_id"], {
        "module": "code_review",
        "problem": f"{language} code review: {result['summary']}",
        "root_cause": "; ".join(result["findings"][:3]),
        "recommendations": (result["findings"] + result["suggestions"])[:3],
    })
    return result


def store_convention(rule: str, note: str = "") -> dict:
    """Teach the shared memory a project coding convention (e.g. 'Always validate divisors')."""
    return hm.store_memory({"module": "code_review", "problem": rule, "outcome": "convention",
                            "verified_by_developer": True, "notes": note})
