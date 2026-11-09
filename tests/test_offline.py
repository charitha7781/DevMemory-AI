"""
Offline logic test with a fake Hindsight + fake LLM (no keys, no network).
Checks the plumbing only - it is NOT evidence that real Hindsight memory works.
Run:  python tests/test_offline.py   (or: pytest tests/test_offline.py)
"""
import os
import sys
import tempfile
import threading
import time
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


def _reset_hindsight_state():
    hm._client = None
    hm._bank_ready = False
    hm._bank_error = None
    hm._shutdown = False


def test_executor_thread_consistency_and_serialization():
    _reset_hindsight_state()

    thread_ids = []
    counters = {"active": 0, "max_active": 0}
    state_lock = threading.Lock()

    class ThreadFake:
        def create_bank(self, **kw):
            pass

        def _record(self):
            with state_lock:
                counters["active"] += 1
                counters["max_active"] = max(counters["max_active"], counters["active"])
            time.sleep(0.02)
            thread_ids.append(threading.get_ident())
            with state_lock:
                counters["active"] -= 1

        def retain(self, bank_id, content, **kw):
            self._record()

        def recall(self, bank_id, query, **kw):
            self._record()
            return SimpleNamespace(results=[])

        def reflect(self, **kw):
            self._record()
            return SimpleNamespace(text="")

        def list_memories(self, **kw):
            self._record()
            return SimpleNamespace(items=[])

        def get_version(self):
            self._record()

        def close(self):
            self._record()

    hm._client = ThreadFake()
    hm._bank_ready = True

    def caller(i):
        hm.store_memory({"module": "incident", "problem": f"problem {i}", "outcome": "success"})
        hm.retrieve_memory(f"query {i}")
        hm.reflect_memory(f"reflection {i}")
        hm.list_memories(limit=5)
        hm.memory_health()

    threads = [threading.Thread(target=caller, args=(i,)) for i in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert thread_ids, "no Hindsight SDK calls were recorded"
    assert len(set(thread_ids)) == 1, f"SDK calls ran on multiple threads: {set(thread_ids)}"
    assert counters["max_active"] == 1, f"SDK calls overlapped (max concurrent = {counters['max_active']})"

    hm.close_hindsight()


def test_executor_timeout_is_reported():
    _reset_hindsight_state()

    class SlowFake:
        def create_bank(self, **kw):
            pass

        def retain(self, *args, **kw):
            time.sleep(0.2)

        def close(self):
            pass

    hm._client = SlowFake()
    hm._bank_ready = True
    original_timeout = hm.EXECUTOR_TIMEOUT
    hm.EXECUTOR_TIMEOUT = 0.01
    try:
        result = hm.store_memory(
            {"module": "incident", "problem": "slow operation", "outcome": "success"}
        )
    finally:
        hm.EXECUTOR_TIMEOUT = original_timeout
        hm.close_hindsight()

    assert result["ok"] is False
    assert "timed out" in (result["error"] or "").lower()


def test_bank_creation_failure_is_not_cached_as_ready():
    _reset_hindsight_state()

    class BankFailFake:
        def __init__(self):
            self.calls = 0

        def create_bank(self, **kw):
            self.calls += 1
            raise RuntimeError("permission denied")

        def recall(self, *args, **kw):
            return SimpleNamespace(results=[])

        def close(self):
            pass

    fake = BankFailFake()
    hm._client = fake
    hm._bank_ready = False

    first = hm.retrieve_memory("anything")
    assert first["ok"] is True
    assert hm._bank_ready is False
    assert hm._bank_error and "permission denied" in hm._bank_error.lower()
    assert fake.calls == 1

    hm.retrieve_memory("anything else")
    assert fake.calls == 2, "a failed bank creation should be retried, not cached"

    hm.close_hindsight()


def test_close_hindsight_resets_and_closes_on_worker():
    _reset_hindsight_state()

    class ClosableFake:
        def __init__(self):
            self.closed = False
            self.close_thread = None

        def create_bank(self, **kw):
            pass

        def close(self):
            self.closed = True
            self.close_thread = threading.get_ident()

    fake = ClosableFake()
    hm._client = fake
    hm._bank_ready = True
    hm._bank_error = "old error"

    worker_id = hm._hindsight_executor.submit(threading.get_ident).result(timeout=5)
    result = hm.close_hindsight()

    assert result["ok"] is True
    assert fake.closed is True
    assert fake.close_thread == worker_id
    assert hm._client is None
    assert hm._bank_ready is False
    assert hm._bank_error is None

    assert hm.close_hindsight()["ok"] is True


def test_shutdown_hindsight_stops_executor():
    from concurrent.futures import ThreadPoolExecutor

    _reset_hindsight_state()
    original_executor = hm._hindsight_executor
    hm._hindsight_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="hindsight-test")

    class ClosableFake:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    fake = ClosableFake()
    hm._client = fake
    hm._bank_ready = True

    try:
        result = hm.shutdown_hindsight()
        assert result["ok"] is True
        assert fake.closed is True
        assert hm._shutdown is True
        assert hm._client is None

        try:
            hm._hindsight_executor.submit(lambda: None)
            raised = False
        except RuntimeError:
            raised = True
        assert raised, "executor should reject work after shutdown"

        assert hm.shutdown_hindsight()["ok"] is True
    finally:
        hm._hindsight_executor = original_executor
        hm._shutdown = False
        hm._client = None
        hm._bank_ready = False
        hm._bank_error = None


if __name__ == "__main__":
    test_full_flow()
    test_unavailable_and_bad_input()
    test_other_modules_and_sanitize()
    test_executor_thread_consistency_and_serialization()
    test_executor_timeout_is_reported()
    test_bank_creation_failure_is_not_cached_as_ready()
    test_close_hindsight_resets_and_closes_on_worker()
    test_shutdown_hindsight_stops_executor()
    print("offline tests passed")
