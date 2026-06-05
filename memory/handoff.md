# Conversation Handoff — Splunk Zero Hackathon Project

> **Purpose:** This file captures EVERYTHING from the project so a new agent can continue seamlessly. Read this FIRST before doing anything.

---

## 1. What Is This Project?

**Splunk Zero** ("Zero noise. Zero waste. Zero unused data.") is an autonomous AI agent being built for the **Splunk Agentic Ops Hackathon** (deadline: **June 15, 2026** — 10 days remain as of June 5).

**What it does:** A webhook triggers the agent. It queries Splunk's internal indexes to find log sources consuming high volume that nobody searches for, traces those sources to a GitHub repo, and creates a Pull Request to reduce the logging level — with dollar cost savings in the PR description.

**Tracks:** Primary = Platform & Developer Experience. Bonus = Best Use of Splunk MCP Server.

---

## 2. Project Location and Structure

**Root directory:** `d:\intel\splunk\splunk hack\splunk-zero\`

```
splunk-zero/
├── .env                    # Real credentials (gitignored)
├── .env.example            # Template for .env
├── .gitignore
├── requirements.txt
│
├── src/
│   ├── __init__.py
│   ├── config.py           # Central config (HEC, REST, GitHub, LLM, app settings)
│   ├── server.py           # FastAPI server (/health, /trigger, /events/{run_id}, /)
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── splunk_client.py  # Splunk MCP + REST API client (dual-mode, REST used)
│   ├── github/
│   │   ├── __init__.py
│   │   └── client.py        # GitHub API wrapper (search, read, branch, commit, PR)
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── state.py          # SplunkZeroState TypedDict (LangGraph schema)
│   │   ├── graph.py          # LangGraph workflow (7 nodes, conditional edge)
│   │   └── nodes/
│   │       ├── __init__.py
│   │       ├── ingest_analysis.py   # Node 1: Query _internal for volume
│   │       ├── search_audit.py      # Node 2: Query _audit for search activity
│   │       ├── waste_detection.py   # Node 3: Cross-reference → find waste
│   │       ├── source_tracing.py    # Node 4: Map sourcetype → repo (LLM)
│   │       ├── code_analysis.py     # Node 5: Read config, propose changes (LLM)
│   │       ├── pr_creation.py       # Node 6: Create branch, commit, open PR
│   │       └── report.py           # Node 7: Compile final report
│   └── ui/
│       ├── __init__.py
│       ├── events.py         # SSE EventManager (async queue-based)
│       └── static/
│           └── index.html    # Placeholder UI (Phase 3)
│
├── scripts/
│   ├── __init__.py
│   ├── synthetic_data.py     # HEC data loader (3 sourcetypes, 1900 events)
│   ├── quick_test.py         # Quick trigger/health check
│   └── debug_sse.py          # SSE stream debug tool
│
├── tests/
│   ├── __init__.py
│   ├── test_mcp_connection.py
│   ├── test_github_connection.py
│   ├── test_llm_connection.py
│   └── test_pipeline.py      # Full E2E pipeline test
│
├── planning/
│   ├── architecture.md
│   ├── decisions.md
│   ├── milestones.md
│   ├── demo-script.md
│   └── judging-alignment.md
│
├── memory/
│   ├── handoff.md            # THIS FILE
│   ├── progress.md           # Current status
│   └── stack.md              # Tech stack details
│
└── hackathon-context/        # Original hackathon materials
```

---

## 3. Current Status: Phase 2 COMPLETE ✓

### What Works End-to-End:

1. **POST /trigger** → starts agent pipeline in background, returns `run_id`
2. **GET /events/{run_id}** → SSE stream of real-time events
3. **Pipeline flow:**
   - Node 1: Queries Splunk _internal → finds 32 sourcetypes
   - Node 2: Queries Splunk _audit → finds search activity
   - Node 3: Cross-references → detects 10 wasteful sourcetypes ($26,522/month)
   - Node 4: Maps sourcetypes to GitHub repos (configured + LLM fallback)
   - Node 5: Reads logging.conf, LLM proposes DEBUG→ERROR change
   - Node 6: Creates branch, commits modified config, opens PR
   - Node 7: Compiles final report

### Verified Results (June 5, 2026):

- **10 wasteful sourcetypes detected** (3 synthetic + 7 Splunk internal with ":" format)
- **$26,522.38/month estimated savings**
- **2 real GitHub PRs created:**
  - PR #1: `[Splunk Zero] Reduce app:user-auth:debug logging: DEBUG -> ERROR`
  - PR #2: `[Splunk Zero] Reduce app:payment-service:debug logging: DEBUG -> ERROR`
- **2 branches created** on yoriichi-07/splunk-zero-demo-app

### Server Details:
- **App URL:** http://localhost:8888 (NOT 8000 — Splunk Web uses 8000)
- **Start command:** `python -m src.server`
- **Health check:** GET /health returns Splunk status + config validation

---

## 4. Critical Technical Discoveries

These are hard-won lessons. Don't re-learn them:

1. **Splunk has TWO separate auth systems:** MCP Encrypted Token (MCP only) vs Basic auth (REST API)
2. **Splunk REST search needs POST**, not GET (returns 405 on GET)
3. **MCP SSE is broken** — `sse_client` throws TaskGroup error. REST fallback works perfectly.
4. **Windows console (cp1252) breaks on emoji** — Use ASCII markers: `[OK]`, `[FAIL]`, `[WARN]`
5. **GITHUB_REPO format:** Must be `owner/repo`, not full URL
6. **Splunk Web uses port 8000** — Our app runs on port 8888
7. **Gemini `response.content` can be a list** — Must check `isinstance(content, list)` before `.strip()`
8. **LangGraph `Annotated[list, add]`** — enables append-only event accumulation across nodes
9. **Waste detection needs dual-pass:** (1) high-volume + low-search, (2) any-volume + zero-search for app sourcetypes
10. **sse-starlette format:** `data: ` prefix on each line, with `\r\n\r\n` separators

---

## 5. What's Next: Phase 3 — UI of Thinking

### Design:
- Dark glassmorphism dashboard
- Real-time pipeline visualization (SSE card animations)
- Savings dashboard with metrics
- Demo-ready polish

### Technical:
- Build `src/ui/static/` (HTML/CSS/JS)
- Connect to `/events/{run_id}` via EventSource API
- Animate cards for each pipeline step
- Show PR links and savings numbers

### Phase 4 — Submission:
- Architecture diagram, README, demo video
- Edge case testing, code cleanup
- Devpost submission

---

## 6. .env Structure

```env
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_TOKEN=<MCP Encrypted Token>
SPLUNK_MCP_URL=https://localhost:8089/services/mcp
SPLUNK_USERNAME=<admin username>
SPLUNK_PASSWORD=<admin password>
SPLUNK_HEC_TOKEN=<HEC token for synthetic data>
SPLUNK_HEC_PORT=8088

GITHUB_TOKEN=ghp_<...>
GITHUB_REPO=yoriichi-07/splunk-zero-demo-app
GITHUB_BRANCH_PREFIX=splunk-zero

GOOGLE_API_KEY=<Gemini API key>
LLM_MODEL=gemini-3.1-flash-lite

APP_PORT=8888
COST_PER_GB_PER_DAY=15
WASTE_THRESHOLD_PCT=5
MIN_SEARCH_COUNT=2
ANALYSIS_PERIOD_DAYS=30
```

---

## 7. Conversation History

| Conversation | Dates | Summary |
|---|---|---|
| `da6ef238-694e-4705-8e0c-4bddd688bf6b` | June 2-4 | Phase 1: Context engineering, scaffolding, Splunk/GitHub/LLM verification |
| `49945469-a2be-4235-a4f1-dec5f31478ec` | June 5 | Phase 2: Built entire pipeline, all 7 nodes, FastAPI server, synthetic data, E2E verified with real PRs |

### Key Files to Read First:
1. **This file** (you're reading it)
2. `memory/progress.md` — Current status and blockers
3. `src/agent/graph.py` — The pipeline architecture
4. `src/server.py` — The API server
5. `planning/architecture.md` — System design
