# Handoff - Splunk Zero

## Read This First

Splunk Zero is an autonomous cost-optimization agent for Splunk. It queries Splunk ingest and search metadata, identifies unused high-noise app logs, maps them to GitHub logging configs, and opens PRs that reduce DEBUG logging.

Current scope is complete through Phase 4. The project is fully built and ready for submission.

## Quick Start

```powershell
cd "D:\intel\splunk\splunk hack\splunk-zero"
python -m scripts.reset_demo
python -m src.server
```

Then open `http://localhost:8888`.

## Architecture In One Pass

1. User starts a run in the UI.
2. `POST /trigger` creates a run id and event queue.
3. LangGraph executes seven nodes:
   - ingest analysis
   - search audit
   - waste detection
   - source tracing
   - code analysis
   - PR creation
   - report
4. Each node emits SSE events through `src/ui/events.py`.
5. Browser renders the live "UI of Thinking".
6. GitHub PR links and savings appear in the final report.

## Key Files

| File | Purpose |
|---|---|
| `src/server.py` | FastAPI app, health, trigger, SSE, reset, static UI |
| `src/ui/events.py` | Per-run SSE queue manager |
| `src/ui/static/index.html` | Phase 3 dashboard markup |
| `src/ui/static/style.css` | Phase 3 dashboard design system |
| `src/ui/static/app.js` | SSE handling, event rendering, stats, reset |
| `src/agent/graph.py` | LangGraph workflow |
| `src/agent/state.py` | Agent state schema |
| `src/agent/nodes/*.py` | Pipeline node implementations |
| `src/mcp/splunk_client.py` | Splunk MCP/REST client |
| `src/github/client.py` | GitHub API wrapper |
| `scripts/synthetic_data.py` | Loads demo sourcetypes into Splunk HEC |
| `scripts/reset_demo.py` | Resets GitHub repo for another demo run |

## Phase 3 State

The earlier Phase 3 UI was functional but generic. It has now been rebuilt as a premium operational dashboard with:

- restrained dark command-center styling
- evidence-first metrics
- clear run controls
- seven-step pipeline rail
- live event ledger
- deterministic savings presentation
- final report with PR links
- responsive layout

## Important Gotchas

- Splunk Web may use port `8000`; this app uses `8888`.
- MCP SSE exists in code but REST fallback is the reliable path on this machine.
- `.env` contains real secrets and must stay ignored.
- `.env.example`, `planning/`, `memory/`, `resources/`, and `hackathon-context/` should remain trackable.
- The demo repo should be reset before every run.
- Known synthetic sourcetypes:
  - `app:payment-service:debug`
  - `app:user-auth:debug`
  - `app:inventory-api:debug`

## Next Work If User Continues

The development phases are complete. The remaining work is user-led:

- Record the demo video using `planning/demo-script.md`
- Fill out the hackathon submission form
- Celebrate!
