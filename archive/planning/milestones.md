# Milestones

Hackathon deadline: June 15, 2026.

## Phase 1 - Foundation

Goal: prove every external system can be reached.

- [x] Local Splunk Enterprise running.
- [x] Splunk MCP Server installed.
- [x] Splunk REST API health check works.
- [x] `_internal` ingest metrics query works.
- [x] `_audit` search activity query works.
- [x] GitHub API can read repo files.
- [x] GitHub API can create/delete branches.
- [x] Gemini API call works.
- [x] `.env` configured.
- [x] Synthetic data loader created.
- [x] FastAPI health endpoint created.
- [x] Decision made: REST fallback is the reliable Splunk path for this demo.

Definition of done: connectivity is verified and no core dependency is unknown.

## Phase 2 - Agent Pipeline

Goal: run autonomously from trigger to GitHub PR.

- [x] LangGraph state schema.
- [x] Node 1: ingest analysis.
- [x] Node 2: search audit.
- [x] Node 3: waste detection.
- [x] Node 4: source tracing.
- [x] Node 5: code analysis.
- [x] Node 6: PR creation.
- [x] Node 7: report generation.
- [x] SSE event emission from nodes.
- [x] Error events for failed stages.
- [x] `POST /trigger` endpoint.
- [x] End-to-end run verified previously with real PR creation.

Definition of done: `POST /trigger` runs without manual intervention and creates real PRs when waste is detected.

## Phase 3 - UI Of Thinking

Goal: make the working agent understandable and impressive to a judge.

- [x] Single-page dashboard at `/`.
- [x] Real-time SSE event stream.
- [x] Trigger and reset controls.
- [x] Pipeline progress visualization.
- [x] Evidence metrics for sourcetypes, waste, savings, and PRs.
- [x] Waste table with sourcetype, ingest, searches, and savings.
- [x] PR link rendering.
- [x] Final report card.
- [x] Responsive layout.
- [x] Premium UI rebuild completed after the earlier generic version.
- [x] Deterministic demo-scale savings for synthetic sourcetypes.
- [x] Context docs repaired.

Definition of done: a non-technical judge can understand what the agent did, why it matters, and where the real PRs are.

## Phase 4 - Submission Package

Completed. Ready for submission.

- [x] Root README with setup and run instructions.
- [x] Open-source license.
- [x] Visual architecture diagram.
- [x] Demo video script and planning (video to be recorded).
- [x] Final code cleanup (Black formatting).
- [x] Edge-case tests.
- [ ] Submission form (To be completed by user).
