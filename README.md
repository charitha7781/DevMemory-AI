# DevMemory AI

DevMemory AI is an AI-assisted engineering knowledge system for analysing production incidents, reviewing source code, and diagnosing deployment/CI-CD failures. It uses Groq for analysis and Hindsight as long-term engineering memory.

## Core capabilities

- **Incident intelligence:** analyses error logs and stack traces, estimates likely causes, and recommends troubleshooting steps.
- **Intelligent code review:** identifies potential bugs, logic errors, security concerns, performance issues, and coding improvements.
- **Deployment intelligence:** identifies likely failed pipeline stages and recommends ordered troubleshooting steps.
- **Long-term engineering memory:** recalls relevant prior incidents, code-review conventions, and deployment failures.
- **Developer feedback loop:** stores a proposed fix as verified success or failed attempt only after a developer reports the outcome.
- **Credential sanitisation:** removes common API keys, tokens, passwords, and email addresses before text is sent to the model or memory service.

## Architecture

```text
Developer / Streamlit UI (Member 2)
                 |
                 v
             ai_engine.py
                 |
       +---------+----------+
       |         |          |
       v         v          v
 incident_   code_review_ deployment_
 engine.py   engine.py    engine.py
       |         |          |
       +---------+----------+
                 |
        +--------+--------+
        |                 |
        v                 v
   llm_service.py   hindsight_memory.py
        |                 |
        v                 v
  Groq                Hindsight
```

`ai_engine.py` is the integration interface intended for the Streamlit layer. Shared helpers are in `engine_utils.py`.

## Requirements

- Python 3.10 or newer (the code uses modern type annotations)
- Groq API key
- A reachable Hindsight server/service and, if required by the deployment, a Hindsight API key

## Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS / Linux
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Create a local environment file:

   ```bash
   cp .env.example .env
   ```

   On Windows, copy `.env.example` to `.env` manually if `cp` is unavailable.

4. Set the values in `.env`:

   ```dotenv
   HINDSIGHT_BASE_URL=http://localhost:8888
   HINDSIGHT_API_KEY=
   HINDSIGHT_BANK_ID=devmemory-ai
   LLM_API_KEY=your_groq_api_key
   LLM_MODEL=openai/gpt-oss-120b
   ```

   Keep `.env` private. Never commit real credentials. The Hindsight service must be running and reachable at `HINDSIGHT_BASE_URL` before real memory operations can succeed.

## Run the application integration

The Member 1 package exposes the engine functions; the Streamlit UI is supplied by the integrating application (Member 2). From this project directory, the UI can import:

```python
from ai_engine import (
    analyse_incident,
    review_code,
    analyse_deployment,
    store_feedback,
    store_feedback_result,
    retrieve_memory,
    reflect_on_memories,
    list_memories,
    store_convention,
    health_check,
)
```

Each analysis function returns a dictionary. Check `result["error"]` and display any entries in `result["warnings"]`. Memory availability is reported as `ok`, `empty`, or `unavailable`.

## Test and demo

Run the offline test suite (no API keys or network access required):

```bash
python tests/test_offline.py
# or
pytest -q
```

Run the real Hindsight retain/recall/reflect check after configuring a live Hindsight service:

```bash
python tests/test_memory.py
```

Run the real incident + developer-feedback demonstration after configuring both Groq and Hindsight:

```bash
python tests/test_incident.py
```

The real integration scripts are intentionally separate from the offline pytest suite. They require external services and credentials.

## Important design safeguards

- AI-generated recommendations are **not** stored as proven fixes immediately.
- A developer must explicitly report success or failure before the feedback is retained in Hindsight.
- Verified successes and failed attempts are labelled separately so a failed workaround is not presented as a proven solution.
- Causes are framed as possible/likely; recommendations are not represented as actions already performed.
- If Hindsight is unavailable, analysis can continue without memory and the result includes a warning.

## Project files

| File | Purpose |
|---|---|
| `ai_engine.py` | Unified public interface for the UI |
| `hindsight_memory.py` | Hindsight client, memory storage/retrieval, feedback, sanitisation |
| `llm_service.py` | Groq integration and JSON response parsing |
| `incident_engine.py` | Incident log analysis |
| `code_review_engine.py` | AI-assisted source-code review |
| `deployment_engine.py` | Deployment and CI/CD log analysis |
| `engine_utils.py` | Shared parsing and memory helpers |
| `tests/` | Offline tests and real-service integration demos |
| `sample-data/` | Example incident, deployment, and code-review inputs |
| `HANDOFF_TO_MEMBER2.md` | Integration contract for the Streamlit UI |

## Current package scope

This repository is the Member 1 AI/memory backend. It does not include the Member 2 Streamlit frontend unless that frontend is merged separately.
