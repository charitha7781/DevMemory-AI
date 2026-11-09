# Member 1 -> Member 2 handoff

Import everything from one place:

```python
from ai_engine import (analyse_incident, review_code, analyse_deployment,
                       store_feedback, store_feedback_result, retrieve_memory,
                       reflect_on_memories, list_memories, store_convention, health_check)
```
All functions return plain dicts / bools and **never raise**. Always check `result["error"]` and `result["warnings"]`.

## Functions
| Call | Returns |
|---|---|
| `analyse_incident(log_text)` | `problem_id, title, root_cause, confidence, recommendations[], recalled_memories[], memory_used, memory_status, memory_insight, previously_verified_solutions[], previously_failed_attempts[], warnings[], error` |
| `review_code(code, language)` | `problem_id, summary, findings[], findings_detailed[], suggestions[], recalled_memories[], memory_used, memory_status, memory_insight, warnings[], error` |
| `analyse_deployment(log_text)` | `problem_id, failed_stage, possible_cause, confidence, recommendations[], recalled_memories[], memory_used, memory_status, memory_insight, ..., warnings[], error` |
| `store_feedback(problem_id, "success"\|"failure", developer_note="", fix_applied="")` | `True` only if really retained in Hindsight |
| `store_feedback_result(...)` | same but `{"ok", "error", "outcome"}` so you can show the error |
| `retrieve_memory(query, module=None)` | `{"ok","status","memories":[{text,type,status}],"error"}` |
| `reflect_on_memories(query)` | `{"ok","text","error"}` |
| `list_memories(limit=50)` | `{"ok","items":[str],"error"}` for Memory Explorer |
| `health_check()` | `{"hindsight":{ok,error,...},"llm":{ok,error,model}}` (makes one tiny LLM call) |

`memory_status`: `"ok"` (found), `"empty"` (nothing relevant), `"unavailable"` (Hindsight down - show the warning).
`previously_verified_solutions` is only filled when a developer-confirmed fix was really recalled from Hindsight and used.

## Streamlit example
```python
import streamlit as st
from ai_engine import analyse_incident, store_feedback_result

log = st.text_area("Paste error log")
if st.button("Analyse") and log:
    with st.spinner("Recalling memory and analysing..."):
        st.session_state["inc"] = analyse_incident(log)

r = st.session_state.get("inc")
if r:
    if r["error"]: st.error(r["error"])
    else:
        for w in r["warnings"]: st.warning(w)
        st.subheader(r["title"]); st.write("Possible root cause:", r["root_cause"])
        for rec in r["recommendations"]: st.markdown(f"- {rec}")
        if r["previously_verified_solutions"]:
            st.success("Previously verified solution (from Hindsight):\n\n" + "\n\n".join(r["previously_verified_solutions"]))
        c1, c2 = st.columns(2)
        note = st.text_input("Developer note (optional)")
        if c1.button("Fix worked"):  st.write(store_feedback_result(r["problem_id"], "success", note))
        if c2.button("Fix failed"):  st.write(store_feedback_result(r["problem_id"], "failure", note))
```

## Setup
Env var names (values stay in your local `.env`): `HINDSIGHT_BASE_URL`, `HINDSIGHT_API_KEY`, `HINDSIGHT_BANK_ID`, `LLM_API_KEY`, `LLM_MODEL`.
Dependencies: `streamlit python-dotenv hindsight-client google-genai pytest`.
Sample input that works: `sample-data/incident_logs.txt`.
Known limitations: retain takes a few seconds (Hindsight extracts facts); untested AI suggestions are intentionally NOT stored until feedback is given.
