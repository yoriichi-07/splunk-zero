# Demo Video Script

Target length: **under 3 minutes**.

---

## Pre-Recording Setup

1. Splunk Enterprise running with synthetic app debug sourcetypes loaded.
2. FastAPI server running: `python -m src.server`.
3. Dashboard open at `http://localhost:8888` in a clean browser window.
4. Demo repo (`yoriichi-07/splunk-zero-demo-app`) open in a second browser tab.
5. Demo reset completed: `python -m scripts.reset_demo`.
6. Screen recorder configured (OBS or similar), capturing the browser window.

---

## Recording Flow

### Beat 1 — The Hook (0:00 – 0:15)

**Narration:**

> "Every Splunk-heavy company pays for logs nobody reads. Debug-level application data piles up in indexes, consuming license and storage, while teams only search a fraction of it."
>
> "Splunk Zero finds that waste, proves it with Splunk's own data, and opens a pull request to fix it — all autonomously."

**On screen:** Show the dashboard in its idle state. Hold for 2–3 seconds so judges absorb the UI.

---

### Beat 2 — The Trigger (0:15 – 0:25)

**Narration:**

> "This is not a chatbot. The agent runs the entire investigation by itself — from evidence to action."

**Action:** Click **Start Investigation**. The pipeline rail and event ledger appear.

---

### Beat 3 — Evidence Gathering (0:25 – 1:00)

**Narration (as events stream):**

> "First, the agent queries Splunk's `_internal` index to see what data is being ingested and how much it costs."
>
> "Then it checks the `_audit` index to see what teams actually search."

**On screen:** Watch the pipeline steps light up. Point out the metric cards updating (sourcetypes count, etc.).

**When waste appears:**

> "Here's the proof. These three application debug sourcetypes are consuming budget — but they have zero search activity in 30 days."

**On screen:** The waste table appears with sourcetypes, GB/day, and savings.

---

### Beat 4 — Autonomous Action (1:00 – 1:45)

**Narration (as tracing, code analysis, and PR events appear):**

> "Now the agent maps each wasteful sourcetype to a source code repository. It reads the logging configuration, proposes a safer log level — DEBUG to ERROR — and writes the pull request."

**On screen:** Pipeline steps 4, 5, 6 complete. PR links appear in the event ledger.

**Action:** Click a PR link — switch to the GitHub tab.

> "The pull request includes the evidence: which sourcetype, how much data, how many searches, and the estimated savings. An engineer can review and merge."

**On screen:** Show the PR body with the evidence table and diff.

---

### Beat 5 — The Result (1:45 – 2:15)

**Action:** Switch back to the dashboard.

> "Investigation complete. The report shows monthly and annual savings, and direct links to every pull request the agent created."

**On screen:** Final report card visible in the event stream. Metric cards show total savings and PR count.

---

### Beat 6 — Close (2:15 – 2:30)

**Narration:**

> "Splunk Zero turns operational data into action. It uses Splunk's own metadata as evidence, AI for reasoning, and GitHub for remediation."
>
> "Zero noise. Zero waste. Zero unused data."

**On screen:** Hold on the completed dashboard for 2–3 seconds.

---

## Judge Q&A Preparation

If the video format allows follow-up or if presenting live:

| Question | Answer |
|----------|--------|
| **How do you know a log source is unused?** | Splunk `_audit` records completed searches. If a sourcetype has ingest volume but zero search activity across 30 days, that's strong evidence of waste. |
| **What if DEBUG logs are needed?** | The agent creates a PR, not a direct production change. Engineers review the evidence before merging. |
| **Is the savings number configurable?** | Yes. `COST_PER_GB_PER_DAY` is configurable in `.env`. The demo uses $15/GB/day, which reflects enterprise Splunk pricing. |
| **Why GitHub PRs instead of just a report?** | The PR closes the loop. The agent doesn't just explain the problem — it creates a reviewable, mergeable fix. |
| **What happens if no waste is found?** | The agent reports a clean environment. The pipeline short-circuits from waste detection straight to report. |
| **How does it use Splunk MCP?** | The architecture is MCP-aware. The client code can call MCP tools where the transport is stable. On local Windows, REST fallback ensures reliability while maintaining the same data access. |

---

## Post-Recording Checklist

- [ ] Video is under 3 minutes
- [ ] Audio is clear (no background noise)
- [ ] Dashboard UI is legible at 720p+ resolution
- [ ] GitHub PR tab is shown with evidence
- [ ] No secrets or passwords visible on screen
- [ ] Upload to YouTube or Vimeo (public or unlisted)
- [ ] Copy video URL for submission form
