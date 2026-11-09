"""
REAL Hindsight test (no mocks). Run from the project root:
    python tests/test_memory.py
Proves retain -> recall -> reflect against your actual Hindsight. Keep the output as demo evidence.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hindsight_memory as hm  # noqa: E402


def main() -> int:
    print("Hindsight health:", hm.memory_health())

    marker = f"TEST-{int(time.time())}"
    print("\n[1] RETAIN a clearly labelled test incident")
    r = hm.store_memory({
        "module": "incident",
        "problem": f"{marker} Database connection pool exhausted, requests timing out",
        "root_cause": "Pool size too small for traffic and connections not released",
        "suggested_fix": "Increase pool size and close connections in a finally block",
        "outcome": "success", "verified_by_developer": True,
        "notes": "Service recovered after the change",
    })
    print(r)
    if not r["ok"]:
        return 1

    print("\n[2] RECALL with a similar description")
    time.sleep(2)
    rec = hm.retrieve_memory("database connection timeout pool exhausted", module="incident")
    print("status:", rec["status"], "| error:", rec["error"])
    for m in rec["memories"]:
        print(f"  - ({m['status']}) {m['text'][:200]}")
    if rec["status"] != "ok":
        print("FAIL: nothing recalled")
        return 1

    print("\n[3] REFLECT")
    print(hm.reflect_memory("What have we learned about database connection problems?"))
    print("\nPASS: retain + recall work against real Hindsight")
    return 0


if __name__ == "__main__":
    sys.exit(main())
