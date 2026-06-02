# Milestones

13 days remaining (June 2 → June 15, 2026). Four phases, no fluff.

---

## Phase 1: Foundation — Verify Everything Connects (Days 1-3)

**Goal:** Prove that the core tools work. No application logic yet — just connectivity.

- [x] Splunk Enterprise running locally (500MB license, upgrade to 10GB pending)
- [ ] MCP Server app installed on Splunk instance
- [ ] MCP client connects and can call `list_indexes`
- [ ] SPL query to `_internal` returns ingest metrics
- [ ] SPL query to `_audit` returns search activity data
- [ ] GitHub API can read a test repo's files
- [ ] GitHub API can create a branch + PR on test repo
- [ ] FastAPI server starts and serves a basic health endpoint
- [ ] `.env` file created with all required keys
- [ ] Synthetic demo data loaded into Splunk (realistic log sources)

**Definition of Done:** Run a script that queries Splunk MCP for ingest data, cross-references audit data, and prints "wasteful sources" to terminal. Separately, create a test PR on GitHub.

**Owner:** Human (Splunk/Docker setup) + AI (code scaffolding)

---

## Phase 2: Core Agent Pipeline (Days 4-7)

**Goal:** The LangGraph agent runs end-to-end with real data.

- [ ] LangGraph state schema defined
- [ ] Node 1: Ingest analysis (real MCP query)
- [ ] Node 2: Search audit (real MCP query)
- [ ] Node 3: Waste detection (cross-reference logic)
- [ ] Node 4: Source tracing (LLM + metadata → repo mapping)
- [ ] Node 5: Code analysis (read GitHub logging configs)
- [ ] Node 6: PR creation (branch + commit + PR)
- [ ] Node 7: Report generation
- [ ] SSE event emission from each node
- [ ] Error handling at each node (graceful failures)
- [ ] Webhook trigger endpoint (`POST /trigger`)
- [ ] Full pipeline test: trigger → PR created

**Definition of Done:** Send a POST to `/trigger`, agent runs autonomously, a real GitHub PR appears with cost savings in the description.

**Owner:** AI (all code)

---

## Phase 3: UI of Thinking + Polish (Days 8-10)

**Goal:** The demo looks stunning and works flawlessly.

- [ ] HTML/CSS/JS "UI of Thinking" page
- [ ] Dark theme with glassmorphism cards
- [ ] Step-by-step cards appear as SSE events arrive
- [ ] Each card shows: title, detail text, status icon, timing
- [ ] Waste detection card shows $ savings prominently
- [ ] PR card shows clickable link
- [ ] Summary card with total savings
- [ ] Smooth animations (card entry, status transitions)
- [ ] Responsive layout (looks good on demo screen)
- [ ] Loading states and error states handled
- [ ] "Trigger" button on UI for easy demo start

**Definition of Done:** A non-technical person watching the UI can understand what the agent did and be impressed by the result.

**Owner:** AI (UI code) + Human (visual feedback)

---

## Phase 4: Submission Package (Days 11-13)

**Goal:** Everything needed for hackathon submission is ready.

- [ ] Architecture diagram (visual, not ASCII)
- [ ] README.md with setup instructions
- [ ] Demo video recorded (< 3 minutes)
- [ ] Code cleaned up, comments added
- [ ] `.env.example` complete
- [ ] Open source license file
- [ ] Edge cases tested (no waste found, repo not found, MCP timeout)
- [ ] Demo rehearsed at least 2x
- [ ] Devpost submission form filled out
- [ ] Video uploaded to YouTube

**Definition of Done:** Click "Submit" on Devpost with confidence.

**Owner:** Human (recording, submission) + AI (docs, edge cases)
