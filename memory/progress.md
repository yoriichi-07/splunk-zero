# Project Progress

## Current Status

Phase 4 + MCP Enhancement complete. 

The backend pipeline works end to end, the UI has been rebuilt into a premium operational dashboard, MCP visibility has been added throughout the stack, and all submission package tasks are finished. The project is ready for final demo recording and submission.

## Completed

- Context workflow created under `planning/` and `memory/`.
- Idea locked: Splunk Zero, "Zero noise. Zero waste. Zero unused data."
- Stack locked: Python, FastAPI, LangGraph, vanilla HTML/CSS/JS, SSE, PyGithub, Gemini.
- Local Splunk Enterprise verified through REST API.
- Splunk `_internal` ingest metrics verified.
- Splunk `_audit` search activity verified.
- Splunk MCP Server installed. MCP SDK (`get_mcp_tool_names()`, `mcp_list_tools()`) now explicitly probed and results surfaced to judges via UI and API.
- GitHub PAT verified for read/write operations.
- Demo repo configured: `yoriichi-07/splunk-zero-demo-app`.
- Gemini connection verified via Vertex AI ADC.
- FastAPI app built on port `8888`.
- SSE event manager built for per-run streams.
- LangGraph state schema and 7-node pipeline built.
- Synthetic data loader built for three app debug sourcetypes.
- Demo reset endpoint and script built.
- End-to-end pipeline verified: trigger -> detect waste -> create PRs -> report savings.

## Phase 3 Repair (Previous Session)

- Rebuilt the UI into a premium command-center dashboard.
- Fixed documentation drift and broken encoding in context files.
- Replaced hidden random waste inflation with deterministic demo scaling.
- Fixed the stale `pct` bug in the zero-search waste pass.
- Improved `_audit` sourcetype extraction for sourcetypes containing `:` or `-`.

## MCP Enhancement (Latest Session - 2026-06-10)

**Goal:** Make MCP usage visible and provable to judges for the "Best Use of Splunk MCP Server" bonus track.

**Completed:**
- Deleted temp files `current_diff.patch` and `patch.txt` (left by previous agent).
- Updated `.env.example` to reflect Vertex AI migration (removed `GOOGLE_API_KEY`, added `GCP_PROJECT`, `GCP_LOCATION`).
- Added `get_mcp_tool_names()` async method to `SplunkMCPClient` - probes Splunk MCP server and returns `{mcp_connected, transport, tools, tool_count, error}`.
- Added `GET /mcp-tools` endpoint to `server.py` - live MCP discovery API for judges.
- Enhanced health check `/health` to include MCP probe results.
- Enhanced `ingest_analysis.py` to emit `mcp_tools_ready` and `mcp_tool_called` SSE events before each tool call.
- Enhanced `search_audit.py` similarly - both nodes now show which transport is active.
- Added MCP status pill to the topbar in `index.html` (green=MCP SSE, amber=REST fallback).
- Added MCP badge CSS styles (`mcp-live`, `mcp-rest`) and tool list/tool call rendering to `style.css`.
- Updated `app.js` STEP_MAP to include new MCP event steps, enhanced health check to update MCP pill, added special `renderEventCard` branch for MCP tool events.
- All 27 unit tests still passing (100% clean).

## Current Priority

Project is complete. The only remaining tasks are user-led: recording the demo video using the provided script, and completing the submission form.

## Known Technical Risks

| Risk | Status |
|---|---|
| MCP SSE on Windows throws TaskGroup/transport errors | Now explicitly surfaced via UI pill and `/mcp-tools` endpoint. REST fallback documented for judges. |
| Synthetic demo data is small vs enterprise scale | Mitigated by deterministic demo-scale baselines |
| LLM may produce invalid JSON for code changes | Existing fence-stripping parser handles it |
| Demo repo must be clean before each run | Use `/reset-demo` button or `python -m scripts.reset_demo` |

## Environment

- Splunk: local Enterprise, REST API at `https://localhost:8089`.
- App: `http://localhost:8888`.
- GitHub user: `yoriichi-07`.
- Demo repo: `yoriichi-07/splunk-zero-demo-app`.
- Python: local venv under `venv/`.
- LLM: Google Vertex AI (Gemini 2.5 Flash) via ADC.

## Session Summary - 2026-06-10 (MCP Enhancement)

Full read of all project files -> identified temp files and MCP visibility gap -> deleted `current_diff.patch` + `patch.txt` -> fixed `.env.example` -> added `get_mcp_tool_names()` to client -> added `/mcp-tools` endpoint + health MCP probe -> added MCP events to `ingest_analysis` and `search_audit` -> added MCP status pill to UI + badge CSS -> handled MCP event rendering in JS -> ran 27 unit tests (all pass) -> created comprehensive walkthrough artifact -> updated context engineering files.
