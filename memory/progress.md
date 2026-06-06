# Project Progress

## Current Status: Phase 3 Complete ✓

## Current Priority
Polish the demo, prepare for submission.

---

## Completed
- [x] Context engineering system created (planning/ + memory/)
- [x] Idea selected: **Splunk Zero** ("Zero noise. Zero waste. Zero unused data.")
- [x] Tech stack locked (Python + LangGraph + Gemini Flash via Google AI Studio)
- [x] Architecture designed (LangGraph state machine + SPL queries)
- [x] All 8 technical decisions made and documented
- [x] Milestones defined (4 phases, 13 days)
- [x] Demo script written
- [x] Judging alignment mapped
- [x] Splunk Enterprise running locally (10GB license active)
- [x] Splunk MCP Server app installed (active, endpoints visible)
- [x] MCP Encrypted Token created
- [x] Splunk REST API verified working (health check, indexes, queries)
- [x] _internal index accessible — returns ingest metrics (29+ sourcetypes)
- [x] _audit index accessible — returns search activity
- [x] GitHub PAT created (repo scope, classic token)
- [x] GitHub API verified — read files, create/delete branches
- [x] Test repo created: yoriichi-07/splunk-zero-demo-app
- [x] Test repo has logging.conf with DEBUG-level services
- [x] .env file configured with all keys (including HEC token)
- [x] Project structure scaffolded (src/, tests/, config)
- [x] Python venv created + dependencies installed
- [x] Gemini API verified (Google AI Studio, gemini-3.1-flash-lite works)
- [x] **MCP SSE decision: committed to REST-only** (SSE has TaskGroup bug, REST works perfectly)
- [x] **FastAPI server built** (src/server.py) — /health, /trigger, /events/{run_id}, /reset-demo
- [x] **Port conflict resolved** — Splunk Web uses 8000, app uses 8888
- [x] **SSE EventManager built** (src/ui/events.py) — async queue-based event streaming
- [x] **LangGraph state schema** (src/agent/state.py) — SplunkZeroState TypedDict
- [x] **GitHub API client** (src/github/client.py) — search, read, branch, commit, PR
- [x] **All 7 agent nodes built:**
  - Node 1: ingest_analysis — queries _internal for volume by sourcetype
  - Node 2: search_audit — queries _audit for search activity
  - Node 3: waste_detection — cross-references to find waste (dual-pass: high-volume + zero-search)
  - Node 4: source_tracing — maps sourcetype to repo (configurable + LLM fallback)
  - Node 5: code_analysis — reads config, LLM proposes log level change
  - Node 6: pr_creation — creates branch, commits, opens PR with cost savings
  - Node 7: report — compiles final summary with structured data
- [x] **LangGraph workflow** (src/agent/graph.py) — all nodes wired, conditional edge after waste_detection
- [x] **Synthetic data loaded** — 1,900 events across 3 custom sourcetypes via HEC
- [x] **Pipeline runs successfully** — 5+ test runs, creates real GitHub PRs
- [x] **E2E Verified:** trigger → waste detected → 3 PRs created → $11,583/mo savings
- [x] **Phase 3 — UI of Thinking:**
  - Dark glassmorphism dashboard (HTML/CSS/JS)
  - Real-time SSE event streaming via EventSource API
  - 7-step pipeline progress indicator with animated status dots
  - 4 stat cards with countup animation (sourcetypes, waste, savings, PRs)
  - Event cards with status-based styling (running/complete/error/info)
  - Savings highlight badges and waste tables
  - Final report card with PR links and summary grid
  - Reset Demo button for quick repo cleanup between runs
  - Demo reset script (scripts/reset_demo.py)

## In Progress
- [/] Final polish and demo preparation

## Next Up (Priority Order)
1. **Video demo** — Record the full pipeline demo from trigger to PR creation
2. **README** — Write the project README for submission
3. **Submission** — Package and submit

## Blockers
- None currently

## Known Technical Risks

| Risk | Severity | Status |
|---|---|---|
| `_internal` / `_audit` index not accessible | High | **RESOLVED** — both accessible via REST API |
| MCP Server connection issues | Medium | **RESOLVED** — committed to REST-only |
| Synthetic demo data not convincing | Medium | **RESOLVED** — 1,900 events loaded, 3 sourcetypes |
| LLM hallucinating repo/file mapping | Low | Mitigated with configurable SOURCE_REPO_MAP |
| Port conflict with Splunk Web | Low | **RESOLVED** — moved to port 8888 |
| Waste filter too broad | Medium | **RESOLVED** — tightened to `app:*` prefix only |

## Key Technical Discoveries
1. **MCP Encrypted Token =/= REST API auth** — Two completely separate auth systems in Splunk
2. **Splunk REST search/jobs/export needs POST**, not GET (returns 405 on GET)
3. **MCP SSE `sse_client` uses `httpx_client_factory`**, not `ssl_context` (in mcp v1.13.1)
4. **Windows console (cp1252) can't handle emoji** — Use ASCII markers [OK]/[FAIL]/[WARN]
5. **GITHUB_REPO must be `owner/repo` format**, not full URL
6. **LLM Connection verified** — Gemini 3.1 Flash Lite works via Google AI Studio API key
7. **Splunk Web uses port 8000** — Must use different port for our FastAPI app
8. **LangGraph `Annotated[list, add]`** — enables append-only event accumulation across nodes
9. **Waste filter must be `app:*` prefix** — `node:sidecar:*` and other Splunk internal sourcetypes have `:` too

## Environment Details
- **Splunk:** v10.4.0, Windows, server name "Shree_", localhost:8089, 10GB license
- **Python:** 3.13.5, system install
- **GitHub user:** yoriichi-07
- **LLM:** Google AI Studio gemini-3.1-flash-lite (confirmed working)
- **MCP SDK:** v1.13.1 (installed but SSE unused)
- **App Port:** 8888 (to avoid Splunk Web on 8000)

## Last Session
- **Date:** 2026-06-05
- **Summary:** Built Phase 3 UI — dark glassmorphism dashboard with real-time SSE event streaming, pipeline progress indicators, stat cards with countup animation, event cards with status colors, final report grid with PR links. Added demo reset button and script. Tightened waste detection filter to `app:*` prefix. Verified 3 clean demo runs creating real GitHub PRs. Phase 3 complete.
