"""
ai_engine.py (Member 1) - the ONLY file Member 2's Streamlit code needs to import.

    from ai_engine import (analyse_incident, review_code, analyse_deployment,
                           store_feedback, store_memory, retrieve_memory,
                           reflect_on_memories, list_memories, health_check)

Every function returns plain dicts/bools and never raises.
"""
from __future__ import annotations

import hindsight_memory as hm
import llm_service
from code_review_engine import review_code, store_convention
from deployment_engine import analyse_deployment
from incident_engine import analyse_incident

store_memory = hm.store_memory
retrieve_memory = hm.retrieve_memory
list_memories = hm.list_memories


def store_feedback_result(problem_id: str, outcome: str, developer_note: str = "", fix_applied: str = "") -> dict:
    """Detailed version: {"ok": bool, "error": str|None, "outcome": "success"|"failure", ...}"""
    return hm.record_feedback(problem_id, outcome, developer_note, fix_applied)


def store_feedback(problem_id: str, outcome: str, developer_note: str = "", fix_applied: str = "") -> bool:
    """
    outcome = "success" -> stored as DEVELOPER-VERIFIED SUCCESS
    outcome = "failure" -> stored as unsuccessful attempt (never recommended as a verified fix)
    Returns True when the outcome was really retained in Hindsight.
    """
    return bool(hm.record_feedback(problem_id, outcome, developer_note, fix_applied).get("ok"))


def reflect_on_memories(query: str) -> dict:
    return hm.reflect_memory(query)


def health_check() -> dict:
    """Quick status for a sidebar badge: {"hindsight": {...}, "llm": {...}}"""
    return {"hindsight": hm.memory_health(), "llm": llm_service.ping()}


__all__ = ["analyse_incident", "review_code", "analyse_deployment", "store_feedback",
           "store_feedback_result", "store_memory", "retrieve_memory", "reflect_on_memories",
           "list_memories", "store_convention", "health_check"]
