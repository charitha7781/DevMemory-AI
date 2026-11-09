"""
Offline logic test with a fake Hindsight + fake LLM (no keys, no network).
Checks the plumbing only - it is NOT evidence that real Hindsight memory works.
Run:  python tests/test_offline.py   (or: pytest tests/test_offline.py)
"""
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hindsight_memory as hm  # noqa: E402
import llm_service  # noqa: E402


class FakeHindsight:
    def __init__(self):
        self.docs = {}

    def create_bank(self, **kw): pass
    def get_version(self): return SimpleNamespace(api_version="fake")

    def retain(self, bank_id, content, **kw):
        self.docs[kw.get("document_id", str(len(self.docs)))] = content

    def recall(self, bank_id, query, **kw):
        words = {w for w in query.lower().split() if len(w) > 4}
        hits = [c for c in self.docs.values() if words & set(c.lower().replace(".", " ").split())]
        return SimpleNamespace(results=[SimpleNamespace(text=c, type="world") for c in hits])

    def reflect(self, bank_id, query, **kw): return SimpleNamespace(text="fake insight")
    def list_memories(self, **kw): return SimpleNamespace(items=[SimpleNamespace(text=c) for c in self.docs.values()])


def setup():
    hm._client = FakeHindsight()
    hm._bank_ready = True
    hm.PENDING_FILE = Path(tempfile.mkdtemp()) / "pending.json"
    seen_prompts = []

    def fake_json(prompt, system=None):
        seen_prompts.append(prompt)
        used = [1] if "DEVELOPER-VERIFIED SUCCESS" in prompt else []
        return {"title": "Database Connection Failure", "root_cause": "Likely pool exhaustion",
                "confidence": "medium", "recommendations": ["Check pool size", "Check leaks"],
                "memory_insight": "uses past fix" if used else "No relevant past memory.",
                "used_memory_numbers": used,
                "failed_stage": "dependency installation", "possible_cause": "version conflict",
                "summary": "ok", "findings": [{"severity": "high", "issue": "division by zero", "fix": "check b"}],
                "suggestions": ["add tests"]}
    llm_service.generate_json = fake_json
    return seen_prompts


def test_full_flow():
    prompts = setup()
    import ai_engine as ai

    first = ai.analyse_incident("ERROR: Database connection timeout\nConnection pool exhausted.")
    assert first["error"] is None and first["problem_id"]
    assert first["memory_status"] == "empty" and first["memory_used"] is False
    assert not hm._client.docs, "untested AI suggestion must NOT be stored in Hindsight"

    assert ai.store_feedback(first["problem_id"], "success", "pool resized") is True
    assert len(hm._client.docs) == 1
    assert "DEVELOPER-VERIFIED SUCCESS" in list(hm._client.docs.values())[0]

    second = ai.analyse_incident("FATAL: database pool exhausted, connection timeout")
    assert second["memory_used"] is True
    assert second["previously_verified_solutions"], "verified fix should be surfaced"
    assert "VERIFIED SUCCESS" in prompts[-1]

    third = ai.analyse_incident("ERROR: Database connection timeout again, pool exhausted")
    ai.store_feedback(third["problem_id"], "failure", "restart did not help", fix_applied="Restart service")
    fail_text = [d for d in hm._client.docs.values() if "FAILURE" in d][0]
    assert hm.classify_memory(fail_text) == "failed_attempt"


def test_unavailable_and_bad_input():
    setup()
    import ai_engine as ai
    assert ai.analyse_incident("  ")["error"]
    assert ai.store_feedback("nope", "success") is False
    assert ai.store_feedback("nope", "maybe") is False

    def boom(*a, **k): raise ConnectionError("connection refused")
    hm._client.recall = boom
    r = ai.analyse_incident("ERROR timeout")
    assert r["memory_status"] == "unavailable" and r["warnings"] and r["error"] is None
    assert "does NOT use past memory" in r["warnings"][0]


def test_other_modules_and_sanitize():
    setup()
    import ai_engine as ai
    assert ai.analyse_deployment("Build failed. dependency conflict")["failed_stage"]
    rv = ai.review_code("def divide(a,b):\n return a/b", "python")
    assert rv["findings"] and rv["findings"][0].startswith("[HIGH]")
    assert ai.store_convention("Always validate divisors")["ok"]
    s = hm.sanitize("password=hunter2 api_key: sk-abcdefghijklmnopqrstuv mail me@x.com")
    assert "hunter2" not in s and "sk-abc" not in s and "me@x.com" not in s


if __name__ == "__main__":
    test_full_flow(); test_unavailable_and_bad_input(); test_other_modules_and_sanitize()
    print("offline tests passed")
