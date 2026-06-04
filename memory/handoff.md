# Conversation Handoff — Splunk Zero Hackathon Project

> **Purpose:** This file captures EVERYTHING from the initial conversation (da6ef238-694e-4705-8e0c-4bddd688bf6b) so a new agent can continue seamlessly. Read this FIRST before doing anything.

---

## 1. What Is This Project?

**Splunk Zero** ("Zero noise. Zero waste. Zero unused data.") is an autonomous AI agent being built for the **Splunk Agentic Ops Hackathon** (deadline: **June 15, 2026** — 11 days remain as of June 4).

**What it does:** A webhook triggers the agent. It queries Splunk's internal indexes to find log sources consuming high volume that nobody searches for, traces those sources to a GitHub repo, and creates a Pull Request to reduce the logging level — with dollar cost savings in the PR description.

**Tracks:** Primary = Platform & Developer Experience. Bonus = Best Use of Splunk MCP Server.

---

## 2. Project Location and Structure

**Root directory:** `d:\intel\splunk\splunk hack\splunk-zero\`

> **IMPORTANT:** The project was originally at `d:\intel\splunk\splunk hack\` but was moved by the user to `d:\intel\splunk\splunk hack\splunk-zero\`. All paths are relative to this root.

```
splunk-zero/
├── .env                    # Real credentials (gitignored)
├── .env.example            # Template for .env
├── .gitignore              # Ignores .env, __pycache__, etc.
├── requirements.txt        # Python dependencies
│
├── src/
│   ├── __init__.py
│   ├── config.py           # Central config loader from .env
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── splunk_client.py  # Splunk MCP + REST API client (dual-mode)
│   ├── github/
│   │   └── __init__.py     # Placeholder (Phase 2)
│   ├── agent/
│   │   ├── __init__.py
│   │   └── nodes/
│   │       └── __init__.py # Placeholder (Phase 2)
│   └── ui/
│       └── __init__.py     # Placeholder (Phase 3)
│
├── tests/
│   ├── __init__.py
│   ├── test_mcp_connection.py   # Splunk connectivity test (PASSING)
│   ├── test_github_connection.py # GitHub connectivity test (PASSING)
│   └── test_llm_connection.py   # LLM connection test (PASSING)
│
├── planning/               # Strategy documents
│   ├── README.md           # Master entry point
│   ├── architecture.md     # System design, state schema, SPL queries
│   ├── decisions.md        # 8 locked technical decisions
│   ├── milestones.md       # 4-phase plan with checkboxes
│   ├── demo-script.md      # 90-second demo flow (gitignored)
│   └── judging-alignment.md # Judging criteria mapping (gitignored)
│
├── memory/                 # Living state
│   ├── handoff.md          # THIS FILE — conversation continuation context
│   ├── progress.md         # Current status, blockers, next steps
│   └── stack.md            # Locked tech stack, env vars, dependencies
│
├── hackathon-context/      # Original hackathon materials (gitignored)
└── resources/              # Reference links (gitignored)
```

---

## 3. What Has Been Accomplished

### Phase 1 Progress: 7/10 items complete

| Item | Status | Details |
|---|---|---|
| Splunk Enterprise running | DONE | v10.4.0, Windows, localhost:8089, 500MB license (10GB upgrade pending) |
| MCP Server installed | DONE | Active, endpoints visible at `https://localhost:8089/services/mcp` |
| MCP SSE connection | BLOCKED | `sse_client` throws TaskGroup error. REST fallback works fine. |
| _internal index queries | DONE | Via REST API. Returns 10+ sourcetypes with ingest volumes. |
| _audit index queries | DONE | Via REST API. Returns user search activity. |
| GitHub read access | DONE | Can read repo files, found logging.conf. |
| GitHub write access | DONE | Can create/delete branches. |
| FastAPI server | NOT STARTED | Skeleton exists but no server code yet. |
| .env configured | DONE | All keys set: Splunk, GitHub, Gemini. |
| Synthetic demo data | NOT STARTED | Need realistic log sources for demo. |

### Connection Test Results (June 4, 2026)

**Splunk REST API — ALL PASSING:**
```
Server: Shree_, Version: 10.4.0, OS: Windows
Indexes: _internal (390K events, 35MB), _audit (41K events, 4MB), main (empty)
_internal query: kvstore 0.44 GB/day, splunkd 0.04 GB/day, + 8 more
_audit query: splunk-system-user 109 searches, yoriichi 1 search
```

**GitHub — ALL PASSING:**
```
User: yoriichi-07
Repo: yoriichi-07/splunk-zero-demo-app (main branch)
Files: README.md, logging.conf, src/
Write: Branch create/delete works
```

**MCP SSE — FAILING (non-blocking):**
```
Error: "unhandled errors in a TaskGroup (1 sub-exception)"
Fixed ssl_context issue (use httpx_client_factory instead)
Remaining issue is likely Splunk MCP Server's SSE implementation
```

---

## 4. Critical Technical Discoveries

These are hard-won lessons from debugging. Don't re-learn them:

1. **Splunk has TWO completely separate auth systems:**
   - **MCP Encrypted Token** (created in MCP Server app) → for MCP protocol only
   - **Basic auth (username/password)** → for REST API (`/services/*`)
   - Using the MCP token with REST API gives 401 Unauthorized

2. **Splunk REST search endpoint needs POST, not GET:**
   - `POST /services/search/jobs/export` with form-encoded data
   - GET returns 405 Method Not Allowed

3. **MCP Python SDK v1.13.1 `sse_client` API:**
   - Does NOT accept `ssl_context` parameter
   - Use `httpx_client_factory` parameter instead for SSL bypass
   - Signature: `(url, headers, timeout, sse_read_timeout, httpx_client_factory, auth)`

4. **Windows console encoding (cp1252) breaks on emoji:**
   - Never use emoji (checkmarks, warning signs) in print statements
   - Use ASCII markers: `[OK]`, `[FAIL]`, `[WARN]`
   - Do NOT use `io.TextIOWrapper` to fix it — crashes on PowerShell

5. **GITHUB_REPO format:** Must be `owner/repo` (e.g., `yoriichi-07/splunk-zero-demo-app`), not the full URL

6. **LLM Integration:**
   - Working with `gemini-3.1-flash-lite` (or other Gemini models) via Google AI Studio.
   - The `.env` has `GOOGLE_API_KEY` set, and we use `langchain-google-genai`.

---

## 5. User Preferences and Constraints

- **"I value planning more than anything"** — Always plan before building
- **"Don't overcomplicate for simple stuff"** — Keep it practical, hackathon-focused
- **"Take the prompt with a pinch of salt"** — The original Claude prompt was overly complex; we trimmed 20 files to 8
- **"Don't expect to build in one go"** — Phase-based, incremental delivery
- **Splunk license:** 500MB currently, 10GB coming. Keep demo data small.
- **LLM credits:** Limited. Use the cheapest model that works (like `gemini-3.1-flash-lite`).
- **GitHub user:** `yoriichi-07`
- **Splunk server name:** `Shree_`

---

## 6. What Needs to Be Done Next

### Immediate (Phase 1 completion — Day 2-3)
1. **Debug MCP SSE** or formally decide to use REST-only (for judging, MCP would be better)
2. **Build FastAPI server** (`src/server.py`) with `/health` and `/trigger` endpoints
3. **Create synthetic data loader** script to inject demo data into Splunk `main` index
4. **Verify LLM integration** — test Gemini via `langchain-google-genai` (DONE: verified with `tests/test_llm_connection.py`).

### Phase 2 (Days 4-7) — The Core Pipeline
5. Define LangGraph state schema (`SplunkZeroState` in `architecture.md`)
6. Build agent nodes: ingest analysis, search audit, waste detection, source tracing, code analysis, PR creation, report generation
7. Wire up SSE event emission from each node
8. End-to-end test: trigger → PR created

### Phase 3 (Days 8-10) — UI of Thinking
9. Build the frontend (HTML/CSS/JS) with dark glassmorphism theme
10. SSE event consumption → animated card display
11. Polish and demo rehearsal

### Phase 4 (Days 11-13) — Submission
12. Architecture diagram, README, demo video
13. Edge case testing, code cleanup
14. Devpost submission

---

## 7. Key Files to Read First

When starting a new conversation, read these in order:

1. **This file** (you're reading it)
2. `memory/progress.md` — Current status and blockers
3. `planning/architecture.md` — System design and LangGraph schema
4. `planning/decisions.md` — 8 locked technical decisions
5. `planning/milestones.md` — Phase-by-phase checklist
6. `src/config.py` — Configuration system
7. `src/mcp/splunk_client.py` — The Splunk client (dual MCP+REST)

---

## 8. .env Structure (DO NOT commit)

```env
# Splunk
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_TOKEN=<MCP Encrypted Token — long base64 string>
SPLUNK_MCP_URL=https://localhost:8089/services/mcp
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=<Splunk admin password>

# GitHub
GITHUB_TOKEN=ghp_<...>
GITHUB_REPO=yoriichi-07/splunk-zero-demo-app
GITHUB_BRANCH_PREFIX=splunk-zero

# LLM
GOOGLE_API_KEY=<Gemini API key>
LLM_MODEL=gemini-3.1-flash-lite

# App
APP_PORT=8000
COST_PER_GB_PER_DAY=15
WASTE_THRESHOLD_PCT=5
MIN_SEARCH_COUNT=2
ANALYSIS_PERIOD_DAYS=30
```

---

## 9. Conversation History

- **Conversation ID:** `da6ef238-694e-4705-8e0c-4bddd688bf6b`
- **Logs:** `C:\Users\shree\.gemini\antigravity-ide\brain\da6ef238-694e-4705-8e0c-4bddd688bf6b\.system_generated\logs\transcript.jsonl`
- **Started:** 2026-06-02
- **Last active:** 2026-06-04

### Timeline of work:
1. **June 2 (session 1):** Received master prompt from Claude agent. Built context engineering system (planning/ + memory/). Selected FinOps Dietitian idea. Locked 8 technical decisions. Created architecture, milestones, demo script, judging alignment.
2. **June 2 (session 2):** Renamed to "Splunk Zero". Switched LLM from OpenAI/Anthropic to Gemini Flash. Updated all planning docs. Scaffolded code structure. Created .env, requirements.txt, config.py, splunk_client.py, test scripts.
3. **June 3:** User installed Splunk MCP Server, created tokens. First test runs. Fixed: ModuleNotFoundError (PyGithub), GITHUB_REPO format, Unicode encoding on Windows. Discovered MCP vs REST auth separation.
4. **June 4:** Fixed REST API POST vs GET (405 error). Fixed MCP SSE ssl_context issue. REST API now fully working — _internal and _audit queries return real data. GitHub fully working. MCP SSE still has TaskGroup error (non-blocking).
