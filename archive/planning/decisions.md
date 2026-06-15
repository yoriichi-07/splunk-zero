# Technical Decisions

These decisions are locked unless the user explicitly reopens them.

## 1. Product Idea: Splunk Zero

Splunk Zero is a log-cost optimization agent. It detects wasteful Splunk ingest, proves low usage with `_audit`, and opens GitHub PRs to reduce logging noise.

Why: it is more differentiated than another chatbot or incident summarizer, and the demo has a clear ROI number.

## 2. Primary Track

Platform and Developer Experience.

Why: the agent improves developer operations by turning observability cost evidence into code changes.

## 3. Bonus Target

Best Use of Splunk MCP Server.

Why: the core idea depends on Splunk operational metadata and agentic investigation. The local runtime uses REST fallback when MCP SSE is unstable, but the architecture and client remain MCP-aware.

## 4. Backend

Python, FastAPI, LangGraph.

Why: Python is the lowest-friction language for LangGraph, Splunk examples, PyGithub, and hackathon speed.

## 5. GitHub Integration

Use PyGithub rather than a GitHub MCP server.

Why: GitHub needs only a small set of reliable operations: read files, create branches, commit files, and open PRs.

## 6. Frontend

Use vanilla HTML/CSS/JS with Server-Sent Events.

Why: the UI is a single live dashboard. SSE is simpler than WebSockets for one-way streaming, and no build system is needed.

## 7. Splunk Environment

Use local Splunk Enterprise for development and demo.

Why: local Splunk gives access to internal indexes and avoids cloud permission uncertainty.

## 8. Authentication

Use admin-level Splunk credentials for the local demo.

Production note: use a scoped role with access to the required indexes.

## 9. LLM

Use Google Vertex AI (Gemini 2.5 Flash / 3.1 Flash Lite).

Why: repository mapping, config change generation, and PR text are lightweight reasoning tasks. Using Vertex AI allows us to securely authenticate via Application Default Credentials (ADC) rather than managing raw API keys.

## 10. Remediation Safety

The agent creates PRs, not direct production changes.

Why: this keeps humans in the approval loop while still proving the agent can act.
