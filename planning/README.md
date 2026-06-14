# Splunk Zero Context Guide

Splunk Zero is an autonomous agent for the Splunk Agentic Ops Hackathon. It analyzes Splunk ingest, finds costly log sources that nobody searches, traces those sources to GitHub, and opens pull requests that reduce noisy logging.

## Current Boundary

Work is complete through Phase 4 + MCP Enhancement:

- Phase 1: connectivity and environment verified.
- Phase 2: backend agent pipeline working end to end.
- Phase 3: UI of Thinking built and repaired.
- Phase 4: submission package complete.
- MCP Enhancement: native HTTP POST transport, green status verified.

## Session Workflow

At the start of a new session, read these files in order:

1. `memory/handoff.md` - fastest operational summary.
2. `memory/progress.md` - current status, known risks, next work.
3. `memory/stack.md` - locked technology and environment.
4. `planning/milestones.md` - phase boundaries.
5. `planning/architecture.md` - system design and data flow.
6. `planning/decisions.md` - locked technical decisions.
7. `planning/judging-alignment.md` - why this should score well.
8. `planning/demo-script.md` - demo narrative and judge Q&A.

At the end of a session, update `memory/progress.md` and `memory/handoff.md`.

## Project Promise

The demo must communicate one idea instantly:

> Splunk Zero is not a chatbot. It is a worker that turns Splunk evidence into a real GitHub PR with a clear dollar impact.

## Key Files

| Area | Files |
|---|---|
| Server | `src/server.py` |
| Event streaming | `src/ui/events.py` |
| Frontend | `src/ui/static/index.html`, `src/ui/static/style.css`, `src/ui/static/app.js` |
| Agent graph | `src/agent/graph.py`, `src/agent/state.py`, `src/agent/nodes/*.py` |
| Splunk access | `src/mcp/splunk_client.py` |
| GitHub access | `src/github/client.py` |
| Demo data/reset | `scripts/synthetic_data.py`, `scripts/reset_demo.py` |
| Manual verification | `tests/test_pipeline.py`, `tests/test_mcp_connection.py`, `tests/test_github_connection.py`, `tests/test_llm_connection.py` |

## Run Commands

```powershell
python -m scripts.reset_demo
python -m src.server
```

Open `http://localhost:8888`.
