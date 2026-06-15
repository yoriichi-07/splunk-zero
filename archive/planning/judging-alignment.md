# Judging Alignment

## Technological Implementation

How Splunk Zero scores:

- LangGraph state machine with seven clear nodes.
- FastAPI endpoints for health, trigger, SSE, and reset.
- Splunk data access through MCP-aware client code with reliable REST fallback.
- Cross-index reasoning over `_internal` and `_audit`.
- GitHub API integration that creates real branches, commits, and PRs.
- SSE stream makes agent progress observable in real time.

Evidence to show:

- Working pipeline from UI trigger to GitHub PR.
- Code separation across agent nodes, Splunk client, GitHub client, and UI layer.
- Health checks and reset workflow.

## Design

How Splunk Zero scores:

- The UI is not a chat window; it is a mission-control view of autonomous work.
- Judges can see evidence, progress, actions, and final impact without reading logs.
- Cost savings and PR links are prominent.
- The interface is restrained and operational instead of generic decorative AI styling.

Evidence to show:

- Live event stream.
- Pipeline rail.
- Final report with monthly/annual savings and PR links.

## Potential Impact

How Splunk Zero scores:

- Every Splunk-heavy organization has log waste.
- The agent reports impact in dollars, not vague quality metrics.
- It closes the loop by creating a reviewable PR instead of only producing advice.
- The workflow can run on a schedule after the demo.

Evidence to show:

- Specific monthly and annual savings.
- Pull request body containing Splunk evidence.

## Quality Of Idea

How Splunk Zero scores:

- It targets Splunk FinOps and developer productivity, a less crowded angle than alert summarization.
- It uses Splunk to optimize Splunk itself.
- It is a worker, not a chatbot.
- It proves waste with search history rather than guessing.

Evidence to show:

- `_internal` for ingest volume.
- `_audit` for actual search usage.
- Automated GitHub remediation.

## Bonus: Best Use Of Splunk MCP Server

The project is designed around Splunk MCP concepts and Splunk internal data. The local implementation currently uses REST fallback for reliability, but the MCP-aware client remains in the architecture and can call MCP tools where the server transport is stable.

Best demo framing:

- "The agent uses Splunk's operational metadata as its evidence source."
- "It combines ingest data with search audit data to make a decision."
- "The UI exposes each investigation step instead of hiding the agent."

## Not Targeted

Splunk Hosted Models is not the primary prize target. Gemini is used for repository mapping, config reasoning, and PR text.
