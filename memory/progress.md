# Project Progress

## Current Status: Phase 1 In Progress (7/10 items done)

## Current Priority
Fix MCP SSE connection, build FastAPI server, load synthetic demo data.

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
- [x] Splunk Enterprise running locally (500MB trial, 10GB upgrade pending)
- [x] Splunk MCP Server app installed (active, endpoints visible)
- [x] MCP Encrypted Token created
- [x] Splunk REST API verified working (health check, indexes, queries)
- [x] _internal index accessible — returns ingest metrics (10 sourcetypes)
- [x] _audit index accessible — returns search activity (3 users)
- [x] GitHub PAT created (repo scope, classic token)
- [x] GitHub API verified — read files, create/delete branches
- [x] Test repo created: yoriichi-07/splunk-zero-demo-app
- [x] Test repo has logging.conf with DEBUG-level services
- [x] .env file configured with all keys
- [x] Project structure scaffolded (src/, tests/, config)
- [x] Python venv created + dependencies installed
- [x] Gemini API verified (Google AI Studio, gemini-3.1-flash-lite works)

## In Progress
- [/] Phase 1: Foundation — 7/10 items complete
  - [ ] MCP SSE protocol connection (TaskGroup error, REST fallback works)
  - [ ] FastAPI server with health endpoint
  - [ ] Synthetic demo data loaded into Splunk

## Next Up (Priority Order)
1. **AI:** Debug MCP SSE connection (or commit to REST-only approach)
2. **AI:** Build FastAPI server with basic health endpoint
3. **AI:** Create synthetic data loading script
4. **AI:** Begin Phase 2 — LangGraph state schema and agent nodes

## Blockers
- MCP SSE protocol throws TaskGroup error (non-blocking — REST API works)
- Splunk license is 500MB (10GB upgrade pending — not blocking dev)

## Known Technical Risks

| Risk | Severity | Status |
|---|---|---|
| `_internal` / `_audit` index not accessible | High | **RESOLVED** — both accessible via REST API |
| MCP Server connection issues | Medium | **ACTIVE** — SSE fails, REST fallback works |
| Synthetic demo data not convincing | Medium | Not started yet |
| LLM hallucinating repo/file mapping | Low | Not tested yet |

## Key Technical Discoveries
1. **MCP Encrypted Token =/= REST API auth** — Two completely separate auth systems in Splunk
2. **Splunk REST search/jobs/export needs POST**, not GET (returns 405 on GET)
3. **MCP SSE `sse_client` uses `httpx_client_factory`**, not `ssl_context` (in mcp v1.13.1)
4. **Windows console (cp1252) can't handle emoji** — Use ASCII markers [OK]/[FAIL]/[WARN]
5. **GITHUB_REPO must be `owner/repo` format**, not full URL
6. **LLM Connection verified** — Gemini 3.1 Flash Lite works via Google AI Studio API key

## Environment Details
- **Splunk:** v10.4.0, Windows, server name "Shree_", localhost:8089
- **Python:** 3.13.5, system install (not using venv for running)
- **GitHub user:** yoriichi-07
- **LLM:** Google AI Studio gemini-3.1-flash-lite (confirmed working via test_llm_connection.py)
- **MCP SDK:** v1.13.1 (installed globally)

## Last Session
- **Date:** 2026-06-04
- **Summary:** Fixed REST API auth (basic auth vs MCP token), fixed POST vs GET for search, fixed MCP ssl_context issue. REST API now fully working — queries to _internal and _audit return real data. GitHub fully working. MCP SSE still has TaskGroup error.
