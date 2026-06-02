# Architecture — Splunk Zero

## System Overview

```
┌──────────────┐     ┌────────────────────────────────────────────┐     ┌──────────────┐
│   Trigger    │     │          Splunk Zero System Agent          │     │   Outputs    │
│              │     │                                            │     │              │
│  Webhook /   │────▶│  FastAPI Server                            │────▶│  GitHub PR   │
│  Cron /      │     │    │                                       │     │  Cost Report │
│  Manual API  │     │    ▼                                       │     │  Slack/Email │
│              │     │  LangGraph Orchestrator                    │     │  Notification│
└──────────────┘     │    │                                       │     └──────────────┘
                     │    ├── Splunk MCP Client ──▶ Splunk Instance│
                     │    │     • _internal index (ingest volume) │
                     │    │     • _audit index (search activity)  │
                     │    │     • main index (source verification)│
                     │    │                                       │
                     │    ├── GitHub API Client ──▶ GitHub Repos  │
                     │    │     • Find logging config files       │
                     │    │     • Create branch + PR              │
                     │    │                                       │
                     │    └── LLM (analysis + PR description)     │
                     │                                            │
                     │  SSE Event Stream ────────▶ UI of Thinking │
                     └────────────────────────────────────────────┘
```

## LangGraph State Machine

The agent follows a linear pipeline with conditional exits. Each node emits events to the UI.

```
START
  │
  ▼
[1. INGEST_ANALYSIS]
  Query _internal index for ingest volume by source/sourcetype
  Output: ranked list of top N sources by daily GB
  │
  ▼
[2. SEARCH_AUDIT]
  Query _audit index for search activity per source
  Output: search frequency map — which sources are actually queried
  │
  ▼
[3. WASTE_DETECTION]
  Cross-reference: find sources with HIGH ingest + LOW/ZERO searches
  Apply threshold: >5% of total volume AND <2 searches in 30 days
  Output: list of "wasteful" sources with % volume and $ cost
  │
  ├── (No waste found) ──▶ [REPORT_CLEAN] ──▶ END
  │
  ▼
[4. SOURCE_TRACING]
  For each wasteful source, identify the likely microservice/app
  Use source metadata + LLM to map sourcetype → GitHub repo
  Output: repo + file path candidates for logging config
  │
  ├── (No repo found) ──▶ [REPORT_MANUAL] ──▶ END
  │
  ▼
[5. CODE_ANALYSIS]
  Read logging config files from GitHub (log4j.xml, logging.py, etc.)
  Identify current log level settings (DEBUG, INFO, WARN)
  LLM generates the config change (DEBUG → ERROR/WARN)
  Output: diff of proposed changes
  │
  ▼
[6. PR_CREATION]
  Create branch on GitHub
  Commit the logging config change
  Open PR with auto-generated description including:
    - Which source was wasteful
    - Current vs proposed log level
    - Estimated monthly cost savings
  Output: PR URL
  │
  ▼
[7. REPORT]
  Compile full report: all findings, actions taken, total savings
  Send notification (webhook response / email / Slack)
  │
  ▼
END
```

## State Schema

```python
from typing import TypedDict, Annotated, Optional
from operator import add

class SplunkZeroState(TypedDict):
    # Trigger info
    trigger_type: str              # "webhook" | "cron" | "manual"
    target_period_days: int        # e.g. 30

    # Stage 1: Ingest data
    ingest_by_source: list[dict]   # [{source, sourcetype, daily_gb, pct_total}]
    total_daily_gb: float

    # Stage 2: Audit data
    search_activity: list[dict]    # [{source, search_count_30d}]

    # Stage 3: Waste detection
    wasteful_sources: list[dict]   # [{source, daily_gb, pct, searches, est_monthly_cost}]
    total_monthly_savings: float

    # Stage 4: Source tracing
    source_repos: list[dict]       # [{source, repo, config_file_path, confidence}]

    # Stage 5: Code analysis
    proposed_changes: list[dict]   # [{repo, file, old_level, new_level, diff}]

    # Stage 6: PR creation
    pull_requests: list[dict]      # [{repo, pr_url, title}]

    # Stage 7: Report
    report: dict                   # Final summary

    # Meta
    events: Annotated[list, add]   # SSE events for UI
    errors: list[dict]             # Any errors encountered
    current_step: str              # For UI tracking
```

## Splunk MCP Queries (The SPL)

### Query 1 — Ingest Volume by Source (last 30 days)

```spl
index=_internal source=*metrics.log group=per_sourcetype_thruput
| stats sum(kb) as total_kb by series
| eval daily_gb = round(total_kb / 1024 / 1024 / 30, 2)
| sort - daily_gb
| head 50
| eventstats sum(daily_gb) as grand_total
| eval pct_of_total = round(daily_gb / grand_total * 100, 1)
| table series, daily_gb, pct_of_total
| rename series as sourcetype
```

### Query 2 — Search Audit (what users actually search)

```spl
index=_audit action=search info=completed
| rex field=search "index\s*=\s*(?<searched_index>\w+)"
| rex field=search "sourcetype\s*=\s*(?<searched_sourcetype>\w+)"
| stats count as search_count by searched_sourcetype
| sort - search_count
```

### Query 3 — Cross-Reference (find the waste)

These two queries are run separately and cross-referenced in Python, not SPL. The logic:

```python
def detect_waste(ingest_data, audit_data, threshold_pct=5, min_searches=2):
    """Find sources that cost a lot but nobody uses."""
    searched = {row['searched_sourcetype']: row['search_count']
                for row in audit_data}

    wasteful = []
    for source in ingest_data:
        searches = searched.get(source['sourcetype'], 0)
        if source['pct_of_total'] > threshold_pct and searches < min_searches:
            wasteful.append({
                'sourcetype': source['sourcetype'],
                'daily_gb': source['daily_gb'],
                'pct_of_total': source['pct_of_total'],
                'search_count_30d': searches,
                'est_monthly_cost': round(source['daily_gb'] * 30 * 15, 2)  # $15/GB/day is typical
            })
    return wasteful
```

### Query 4 — Source Metadata (trace to origin)

```spl
index=_internal source=*metrics.log group=per_source_thruput
| where series!=""
| stats sum(kb) as total_kb by series
| sort - total_kb
| head 20
| rename series as source_path
```

## GitHub Integration

**NOT using a second MCP server.** Using `PyGithub` library directly — simpler, more reliable, fewer moving parts.

### Operations needed:
1. **Search repos** — Find repos by sourcetype/app name
2. **Read files** — Look for logging config files:
   - `log4j2.xml`, `logback.xml` (Java)
   - `logging.conf`, `logging.py` (Python)
   - `appsettings.json` (C#/.NET)
   - `.env`, `config.yaml` (generic)
3. **Create branch** — `dietitian/reduce-{sourcetype}-logging`
4. **Commit change** — Modified config file with reduced log level
5. **Open PR** — With auto-generated description + cost savings

## UI of Thinking — Event Stream

The agent emits Server-Sent Events (SSE) as it works. The UI renders them as cards.

### Event Schema:
```json
{
  "step": "querying_splunk",
  "title": "Analyzing Ingest Volume",
  "detail": "Running SPL query against _internal index...",
  "status": "running",
  "data": {},
  "timestamp": "2026-06-10T14:30:00Z"
}
```

### Event Sequence:
| Step | Title | What UI Shows |
|---|---|---|
| `triggered` | Agent Activated | Trigger type + timestamp |
| `querying_ingest` | Analyzing Ingest Volume | SPL query + "Scanning 50 sourcetypes..." |
| `querying_audit` | Checking Search Activity | SPL query + "Analyzing 30 days of searches..." |
| `detecting_waste` | Finding Wasteful Sources | Progress bar + count |
| `waste_found` | 🎯 Waste Detected | Card per wasteful source with GB + $cost |
| `tracing_source` | Tracing to Source Code | "Searching GitHub for {sourcetype}..." |
| `analyzing_code` | Reading Logging Config | File path + current log level |
| `creating_pr` | Writing Pull Request | Branch name + diff preview |
| `pr_created` | ✅ PR Created | Clickable PR link + savings amount |
| `complete` | Investigation Complete | Total savings + summary |

## Cost Calculation Formula

```
Monthly Cost = daily_gb × 30 × cost_per_gb_per_day

Where cost_per_gb_per_day varies by Splunk tier:
- Splunk Cloud: ~$15/GB/day (enterprise pricing)
- Splunk Enterprise: ~$5-10/GB/day (license cost amortized)

Default: $15/GB/day (makes the savings look more dramatic for demo)
```

## Project File Structure (what we'll build)

```
splunk hack/
├── src/
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── graph.py           # LangGraph workflow definition
│   │   ├── state.py           # State schema
│   │   └── nodes/
│   │       ├── ingest_analysis.py
│   │       ├── search_audit.py
│   │       ├── waste_detection.py
│   │       ├── source_tracing.py
│   │       ├── code_analysis.py
│   │       ├── pr_creation.py
│   │       └── report.py
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── splunk_client.py   # Splunk MCP wrapper
│   ├── github/
│   │   ├── __init__.py
│   │   └── client.py          # GitHub API wrapper
│   ├── ui/
│   │   ├── static/
│   │   │   ├── index.html
│   │   │   ├── styles.css
│   │   │   └── app.js
│   │   └── events.py          # SSE event manager
│   └── server.py              # FastAPI entry point
├── tests/
│   ├── test_mcp_connection.py
│   ├── test_waste_detection.py
│   └── test_github_client.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md                  # Submission README
```
