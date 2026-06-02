# Splunk Zero — Zero Noise. Zero Waste. Zero Unused Data.

## What This Project Is

**Splunk Zero** is an **autonomous AI agent** that analyzes a company's Splunk data ingestion, identifies expensive log sources that nobody actually searches, traces them to their source code on GitHub, and **creates a Pull Request to reduce the logging level** — calculating the exact dollar savings. Built for the **Splunk Agentic Ops Hackathon** (deadline: June 15, 2026).

## The Winning Strategy

| Dimension | Our Approach |
|---|---|
| **Primary Track** | Platform & Developer Experience |
| **Bonus Prize** | Best Use of Splunk MCP Server |
| **Differentiator** | Worker, not a chatbot — zero human input from trigger to PR |
| **Demo Centerpiece** | "UI of Thinking" — live step-by-step agent visualization |
| **The Double-Dip** | Uses MCP for deep multi-index analysis (`_internal` + `_audit`) to win both track AND bonus prize |

## Why This Wins

1. **Unique idea** — Nobody else will build a cost optimizer. Every other team will build chatbots or alert summarizers.
2. **Clear ROI** — The output is a dollar amount. Judges can immediately grasp the impact.
3. **Closes the action loop** — Agent doesn't just analyze, it writes actual code changes via GitHub PR.
4. **Deep MCP usage** — Queries internal Splunk indexes that most developers don't even know exist.
5. **Zero human input** — Webhook fires → agent investigates → PR created → human notified. That's it.

## How It Works (The Demo in 3 Sentences)

A webhook triggers the Splunk Zero agent. It uses the Splunk MCP Server to query `_internal` (what's being ingested) and `_audit` (what users actually search for), finds log sources consuming massive volume that nobody ever queries, then traces those sources to a GitHub repo and creates a PR changing the log level from DEBUG to ERROR — complete with a cost savings calculation showing "$4,200/month saved."

## Project Navigation

| File | Purpose |
|---|---|
| [architecture.md](file:///d:/intel/splunk/splunk%20hack/planning/architecture.md) | System design, LangGraph states, data flow |
| [milestones.md](file:///d:/intel/splunk/splunk%20hack/planning/milestones.md) | 4 phases with clear deliverables |
| [decisions.md](file:///d:/intel/splunk/splunk%20hack/planning/decisions.md) | Locked technical decisions |
| [demo-script.md](file:///d:/intel/splunk/splunk%20hack/planning/demo-script.md) | 90-second demo flow |
| [judging-alignment.md](file:///d:/intel/splunk/splunk%20hack/planning/judging-alignment.md) | Every judging criterion mapped to our features |
| [progress.md](file:///d:/intel/splunk/splunk%20hack/memory/progress.md) | Current state, blockers, next steps |
| [stack.md](file:///d:/intel/splunk/splunk%20hack/memory/stack.md) | Locked tech stack and environment |

## Session Protocol (Keep It Simple)

**Starting a session:** Read this file → check [progress.md](file:///d:/intel/splunk/splunk%20hack/memory/progress.md) → pick up where we left off.

**Ending a session:** Update [progress.md](file:///d:/intel/splunk/splunk%20hack/memory/progress.md) with what was done.

That's it. No ceremony.
