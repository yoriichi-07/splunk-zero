# Handoff Document — Splunk Zero

## Last Updated: 2026-06-05 (Phase 3 Complete)

## Quick Start
```bash
cd "d:\intel\splunk\splunk hack\splunk-zero"
python -m scripts.reset_demo    # Reset demo repo before each demo
python -m src.server             # Start server at http://localhost:8888
```

## What Is This?
**Splunk Zero** is an AI agent that autonomously detects wasteful logging in Splunk, traces it to source code in GitHub, and creates Pull Requests to fix it — saving organizations real money.

**Tagline:** "Zero noise. Zero waste. Zero unused data."

## Architecture
```
User clicks "Start Investigation" in UI
    → POST /trigger → run_id returned
    → Background: LangGraph pipeline runs 7 nodes
    → Each node emits SSE events via EventManager
    → Browser receives events via EventSource API
    → UI renders event cards in real-time
    → Pipeline creates real PRs on GitHub
```

## 7-Node LangGraph Pipeline
1. **ingest_analysis** — Query `_internal` for sourcetype volumes
2. **search_audit** — Query `_audit` for search activity 
3. **waste_detection** — Cross-reference: high-volume + zero searches = waste
4. **source_tracing** — Map sourcetype → GitHub repo (LLM fallback)
5. **code_analysis** — Read config, LLM proposes log level reduction
6. **pr_creation** — Create branch, commit change, open PR
7. **report** — Compile final summary with savings calculation

## Key Files
| File | Purpose |
|---|---|
| `src/server.py` | FastAPI server — /health, /trigger, /events, /reset-demo |
| `src/ui/events.py` | SSE EventManager — async queue per run |
| `src/ui/static/index.html` | Dashboard UI |
| `src/ui/static/style.css` | CSS design system (dark glassmorphism) |
| `src/ui/static/app.js` | JS — SSE streaming, event rendering, animations |
| `src/agent/graph.py` | LangGraph workflow definition |
| `src/agent/state.py` | State schema (SplunkZeroState TypedDict) |
| `src/agent/nodes/*.py` | All 7 pipeline nodes |
| `src/mcp/splunk_client.py` | Splunk REST API client |
| `src/github/client.py` | GitHub API client |
| `src/config.py` | Configuration from .env |
| `scripts/reset_demo.py` | Reset demo repo before each run |

## What Phase 3 Built
- Dark glassmorphism dashboard with ambient orb background animations
- Real-time SSE event streaming via EventSource API
- 7-step pipeline progress indicator with animated status dots
- 4 stat cards (sourcetypes, waste found, monthly savings, PRs created)
- Countup animation for savings stat ($0 → $11,583 over 1.2s)
- Event cards with color-coded status borders (blue=running, green=complete, red=error, purple=info)
- Savings highlight badges ($X,XXX/month with annual projection)
- Final report card with summary grid and clickable PR buttons
- Reset Demo button in header for quick repo cleanup
- Demo reset script (scripts/reset_demo.py)

## Demo Flow
1. Open http://localhost:8888
2. Click "Start Investigation"
3. Watch events stream in real-time (~60 seconds total)
4. Stats populate: 32 sourcetypes → 4 waste → $11K savings → 3 PRs
5. Final report shows clickable links to real GitHub PRs
6. Click "Reset Demo" to clean up for next run

## Known Issues / Gotchas
- **MCP SSE doesn't work on Windows** — TaskGroup bug. Uses REST API fallback.
- **Waste detection only flags `app:*` sourcetypes** — Avoids false positives on Splunk internal `node:sidecar:*` etc.
- **LLM (Gemini) sometimes returns content as list** — Code handles `.join()` for parts.
- **Demo repo must be reset between runs** — Use /reset-demo or `python -m scripts.reset_demo`.
- **Port 8888** — Splunk Web uses 8000, our app uses 8888.

## What's Next (Phase 4 — Polish)
1. Record demo video
2. Write project README
3. Final submission packaging
