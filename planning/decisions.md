# Technical Decisions

All decisions are **locked** unless explicitly unlocked with clear reasoning.

---

### Decision 1: Chosen Idea — Splunk Zero
- **What:** Build **Splunk Zero** ("Zero noise. Zero waste. Zero unused data.") — an autonomous agent that optimizes log ingestion costs by finding wasteful sources and creating PRs to reduce log levels.
- **Why:** Most unique idea in the pool. Every other team will build chatbots, alert summarizers, or incident responders. Cost optimization with a dollar output gives judges a tangible ROI story. The action loop (read Splunk → write GitHub PR) is a clear differentiator. The name is premium and memorable.
- **Alternatives rejected:** Blast Radius agent — more crowded space (security incident response), harder to demo without realistic attack data, and harder to prove the agent did something useful.
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 2: Orchestration Framework — LangGraph (Python)
- **What:** Use LangGraph for the agent workflow orchestration.
- **Why:** LangGraph provides stateful, graph-based workflows with built-in checkpointing. It has first-class MCP client support via `langchain-mcp-adapters`. The state machine maps perfectly to our 7-step pipeline. Python is the natural choice because LangGraph's Python SDK is the most mature and all Splunk SDK examples are in Python.
- **Alternatives rejected:** AutoGen (too opinionated for multi-agent, we only need one agent), CrewAI (too high-level, less control), Custom (no time to build plumbing).
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 3: Language — Python
- **What:** Python as the primary language for all backend code.
- **Why:** LangGraph's best support is Python. Splunk SDK is Python-native. PyGithub is battle-tested. FastAPI is fast to build. The hackathon time constraint means we go with whatever has the least friction.
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 4: Splunk MCP Auth — Admin Token
- **What:** Use an admin-level Splunk authentication token for MCP access.
- **Why:** We MUST access `_internal` and `_audit` indexes. Default roles don't have read permissions for these internal indexes. An admin token (or a custom role with `index=_internal` + `index=_audit` permissions) is required. For hackathon speed, admin token is simplest.
- **Risk:** In production, you'd create a scoped role. For demo purposes, admin is fine.
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 5: GitHub Integration — PyGithub (REST API), Not a Second MCP
- **What:** Use the `PyGithub` library for all GitHub operations instead of a GitHub MCP server.
- **Why:** Adding a second MCP server introduces configuration complexity, potential auth issues, and another failure point — all for 4 operations (search, read, commit, PR). PyGithub wraps the GitHub REST API cleanly and is a single `pip install`. During the demo, we can still say "the agent bridges Splunk MCP data with GitHub actions" without needing the GitHub side to be MCP.
- **Alternatives rejected:** GitHub MCP server (over-engineering), raw `requests` to GitHub API (PyGithub is cleaner).
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 6: UI of Thinking — Vanilla HTML/CSS/JS + SSE
- **What:** Build the demo UI as a single HTML page with vanilla CSS and JavaScript, connected via Server-Sent Events (SSE) from FastAPI.
- **Why:** No framework overhead. SSE is simpler than WebSockets for one-directional event streaming. The UI only needs to render step cards — it doesn't need React/Next.js state management. A beautiful single page with animations is more impressive than a janky React app built in a rush. Faster to iterate on design.
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 7: Splunk Instance — Local Docker (Splunk Enterprise)
- **What:** Run Splunk Enterprise locally via Docker for development and demo.
- **Why:** Splunk Cloud trial may restrict access to `_internal` and `_audit` indexes. Local Docker gives us full admin control. Free developer license supports up to 500MB/day which is more than enough for demo data. We can pre-load synthetic data that tells a compelling story.
- **Fallback:** If we get Splunk Cloud access with admin permissions, we can switch — the MCP connection config is the only change.
- **Date:** 2026-06-02
- **Locked:** YES

---

### Decision 8: LLM Provider — Google Gemini Flash
- **What:** Use Gemini 2.0 Flash (or 2.5 Flash) via the Google Generative AI API.
- **Why:** Available API credits, cost-effective, and more than capable for our use case. The LLM's job is simple: map sourcetype → repo, suggest config changes, write PR descriptions. These are not frontier reasoning tasks. Gemini Flash handles them with room to spare. Using `langchain-google-genai` for LangGraph integration.
- **Date:** 2026-06-02
- **Locked:** YES
