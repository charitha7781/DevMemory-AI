"""
REAL end-to-end demo flow (real Hindsight + real LLM). Run from the project root:
    python tests/test_incident.py
Steps = the final demo: analyse -> developer confirms fix -> store -> similar incident -> memory used.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine import analyse_incident, store_feedback_result  # noqa: E402


def show(title, r):
    print(f"\n=== {title} ===")
    print("title:", r["title"], "| confidence:", r["confidence"])
    print("root cause:", r["root_cause"])
    for i, rec in enumerate(r["recommendations"], 1):
        print(f"  {i}. {rec}")
    print("memory_status:", r["memory_status"], "| memory_used:", r["memory_used"])
    print("memory_insight:", r["memory_insight"])
    print("verified solutions recalled:", r["previously_verified_solutions"])
    print("warnings:", r["warnings"], "| error:", r["error"])


def main() -> int:
    """Run the real integration demo explicitly; do not execute during pytest collection."""
    first = analyse_incident("ERROR: Database connection timeout\nConnection pool exhausted.\nUnable to connect to database.")
    show("1. FIRST INCIDENT", first)
    if first["error"]:
        return 1

    fb = store_feedback_result(first["problem_id"], "success",
                               "Raised pool size and fixed a connection leak; service recovered.")
    print("\n=== 2. DEVELOPER FEEDBACK STORED ===", fb)
    if not fb["ok"]:
        return 1

    second = analyse_incident("FATAL: could not obtain DB connection - pool exhausted after 30s wait")
    show("3. SIMILAR INCIDENT (should recall the verified fix)", second)
    return 0 if not second["error"] else 1


if __name__ == "__main__":
    sys.exit(main())
