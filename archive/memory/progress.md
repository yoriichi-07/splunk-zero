# Project Progress

## Current Status

Phase 4 + MCP Enhancement + Native MCP HTTP Transport complete. 

The backend pipeline works end to end, the UI has been rebuilt into a premium operational dashboard, MCP connection is fully working and green using a custom HTTP POST transport wrapper, all submission package tasks are finished, and the project is ready for final demo recording and submission.

## Completed

- Context workflow created under `planning/` and `memory/`.
- Idea locked: Splunk Zero, "Zero noise. Zero waste. Zero unused data."
- Stack locked: Python, FastAPI, LangGraph, vanilla HTML/CSS/JS, SSE, PyGithub, Gemini.
- Local Splunk Enterprise verified through REST API.
- Splunk `_internal` ingest metrics verified.
- Splunk `_audit` search activity verified.
- Splunk MCP Server installed. MCP SDK (`get_mcp_tool_names()`, `mcp_list_tools()`) now explicitly probed and results surfaced to judges via UI and API.
- Custom HTTP POST transport wrapper implemented in `splunk_client.py` - resolves the 405 Method Not Allowed error, enabling true, native Splunk MCP server tool connectivity and turning the UI badge **green**.
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

## MCP Enhancement (Latest Session - 2026-06-10 & 2026-06-11)

**Goal:** Make MCP usage visible and provable to judges for the "Best Use of Splunk MCP Server" bonus track.

**Completed:**
- Deleted temp files `current_diff.patch` and `patch.txt`.
- Updated `.env.example` to reflect Vertex AI migration.
- Added `get_mcp_tool_names()` async method to `SplunkMCPClient`.
- Added `GET /mcp-tools` endpoint to `server.py` - live MCP discovery API for judges.
- Enhanced health check `/health` to include MCP probe results.
- Enhanced `ingest_analysis.py` and `search_audit.py` to emit `mcp_tools_ready` and `mcp_tool_called` SSE events.
- Added MCP status pill to the topbar in `index.html` (green=MCP SSE, amber=REST fallback).
- Implemented custom JSON-RPC HTTP POST transport in `splunk_client.py` to support Splunk's POST-only endpoint, resolving the `405` GET error and making the UI status pill green.
- Corrected Splunk MCP tool parameters (`search_query` -> `query`, `max_results` -> `row_limit`) and output parsing in `splunk_client.py`.
- Verified MCP connection successfully via `tests.test_mcp_connection`. All 27 unit tests pass (100% clean).

## Current Priority

Project is complete. The only remaining tasks are user-led: recording the demo video using the provided script, and completing the submission form.

## Known Technical Risks

| Risk | Status |
|---|---|
| MCP SSE on Windows throws TaskGroup/transport errors | **RESOLVED**: Bypassed SSE client and implemented custom HTTP POST transport wrapper to match Splunk's JSON-RPC protocol natively. Green connection verified. |
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

## Session Summary - 2026-06-11 (MCP Connection Fix)

Probed Splunk MCP server endpoint -> identified `405 Method Not Allowed` on GET requests -> determined that Splunk MCP is a JSON-RPC over HTTP POST endpoint -> implemented custom HTTP POST transport in `splunk_client.py` using `anyio` memory streams -> mapped tool arguments and output formats to REST schema -> verified that MCP connects and queries Splunk successfully -> verified live server `/mcp-tools` returns green status -> updated `walkthrough.md` and `task.md` -> ran unit tests.

## Session Summary - 2026-06-14 (Final Submission Polish)

Read every file in the project end-to-end. Identified 7 critical issues and 4 non-critical items:

**Critical fixes applied:**
1. Renamed `architecture.png` → `architecture_diagram.png` (submission name requirement)
2. Removed `.env.example` from `.gitignore` (judges need the template)
3. Fixed README config table: `GOOGLE_API_KEY` → `GCP_PROJECT`/`GCP_LOCATION`
4. Fixed README prerequisites: "Google AI Studio" → "Vertex AI via ADC"
5. Changed default `APP_PORT` from `8000` → `8888` in `config.py`
6. Added `mcp` and `anyio` to `requirements.txt`
7. Unified `LLM_MODEL` default to `gemini-2.5-flash`

**Non-critical fixes:**
8. Rewrote README with collapsible `<details>` sections
9. Added `.benchmarks/` and `scripts/scratch/` to `.gitignore`
10. Updated `planning/README.md` to reflect Phase 4 complete
11. Created `architecture_diagram.md` with Mermaid diagram

All submission requirements verified: license ✅, README ✅, architecture diagram ✅, .env.example ✅, setup instructions ✅, dependencies ✅.
Remaining user tasks: record demo video, push to GitHub, submit.

