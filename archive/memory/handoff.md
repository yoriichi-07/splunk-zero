# Handoff - Splunk Zero

## Read This First

Splunk Zero is an autonomous cost-optimization agent for Splunk. It queries Splunk ingest and search metadata, identifies unused high-noise app logs, maps them to GitHub logging configs, and opens PRs that reduce DEBUG logging.

Current scope is complete through Phase 4 + MCP Enhancement. The project is fully built and ready for submission.

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
   - ingest analysis (Gemini + MCP tools → `_internal`)
   - search audit (Gemini + MCP tools → `_audit`)
   - waste detection (pure Python, no LLM)
   - source tracing (Gemini maps sourcetype → GitHub repo)
   - code analysis (Gemini reads config, proposes change)
   - PR creation (GitHub branch + commit + PR)
   - report (final SSE summary)
4. Each node emits SSE events through `src/ui/events.py`.
5. Browser renders the live "UI of Thinking".
6. GitHub PR links and savings appear in the final report.

## Key Files

| File | Purpose |
|---|---|
| `src/server.py` | FastAPI app: /health, /mcp-tools (NEW), /trigger, /events, /reset-demo, static UI |
| `src/ui/events.py` | Per-run SSE queue manager |
| `src/ui/static/index.html` | Dashboard (MCP status pill added) |
| `src/ui/static/style.css` | Design system (MCP badge styles added) |
| `src/ui/static/app.js` | SSE handling, MCP event rendering (NEW), stats |
| `src/agent/graph.py` | LangGraph workflow |
| `src/agent/state.py` | Agent state schema |
| `src/agent/nodes/*.py` | Pipeline node implementations |
| `src/mcp/splunk_client.py` | Splunk MCP/REST client + `get_mcp_tool_names()` (NEW) |
| `src/github/client.py` | GitHub API wrapper |
| `scripts/synthetic_data.py` | Loads demo sourcetypes into Splunk HEC |
| `scripts/reset_demo.py` | Resets GitHub repo for another demo run |

## MCP Enhancement (Latest Session)

The MCP integration has been significantly improved to make it visible to judges:

1. **`GET /mcp-tools` endpoint** — probes Splunk MCP server live, returns all available tools with connectivity status.

2. **`get_mcp_tool_names()` method** on `SplunkMCPClient` — async helper that returns `{mcp_connected, transport, tools, tool_count}`.

3. **MCP events in pipeline** — both `ingest_analysis` and `search_audit` now emit:
   - `mcp_tools_ready` — shows which transport (MCP SSE or REST fallback) and tool list
   - `mcp_tool_called` — shows each tool invocation with index name

4. **UI MCP status pill** — topbar now has a second pill showing MCP connectivity status (green=SSE, amber=REST fallback).

5. **UI MCP event rendering** — `mcp_tools_ready` and `mcp_tool_called` events render with special MCP badge styling.

## Important Gotchas

- Splunk Web may use port `8000`; this app uses `8888`.
- MCP SSE connection may fail on Windows (TaskGroup/transport issue). The app handles this gracefully with REST fallback. Judges can see which mode is active in the topbar MCP status pill.
- `.env` contains real secrets and must stay ignored.
- The project uses Vertex AI (ADC) — ensure `GCP_PROJECT` and `GCP_LOCATION` are set (not `GOOGLE_API_KEY`).
- `.env.example` has been updated to reflect Vertex AI migration.
- The demo repo should be reset before every run.
- Known synthetic sourcetypes:
  - `app:payment-service:debug`
  - `app:user-auth:debug`
  - `app:inventory-api:debug`
- Temp files `current_diff.patch` and `patch.txt` have been deleted (were left by previous agent).

## Unit Test Status

```
pytest tests/test_waste_detection.py -v
→ 27 passed in 6.78s ✅
```

## Final Polish Session (Latest)

11 fixes applied in final submission prep:

1. **Renamed** `architecture.png` → `architecture_diagram.png` (submission required exact name)
2. **Unignored** `.env.example` from `.gitignore` (judges need the template)
3. **Fixed README** — removed wrong `GOOGLE_API_KEY`, added correct `GCP_PROJECT`/`GCP_LOCATION`
4. **Fixed README prerequisites** — was "Google AI Studio" → now "Vertex AI via ADC"
5. **Fixed `config.py`** — default `APP_PORT` changed from `8000` → `8888`
6. **Added `mcp` and `anyio`** to `requirements.txt` (were imported but not listed)
7. **Unified `LLM_MODEL`** default to `gemini-2.5-flash` across all files
8. **README rewrite** with `<details>` collapsible sections (premium/professional)
9. **Added `.benchmarks/` and `scripts/scratch/`** to `.gitignore`
10. **Updated `planning/README.md`** to reflect Phase 4 complete
11. **Created `architecture_diagram.md`** with comprehensive Mermaid flowchart

## Next Steps (Post 2026-06-15 Final Session)

- **git push origin main** — 1 commit ahead of origin (`fix: SHA mismatch retry logic`)
- **Ensure GitHub repo is Public**
- **Reset demo repo before recording**: `python -m scripts.reset_demo`
- **Record demo video** (< 3 min) — follow Beat 0–6 script in planning/demo-script.md
- **Upload to YouTube/Vimeo** (public/unlisted)
- **Fill out hackathon submission form**
- **Celebrate!** 🎉

## Live Demo Verified (2026-06-15)

Last run results verified with chrome devtools:
- MCP: Connected (10 tools, SSE transport, GREEN)
- Splunk: 10.4.0 healthy
- Sourcetypes: 33 found
- Waste: 3 sourcetypes, $11,583/month ($138,996/year)
- PR creation: Fails only when demo not reset (expected). Reset fixes it.

