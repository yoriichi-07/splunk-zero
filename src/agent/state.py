"""
Splunk Zero — LangGraph State Schema

Defines the state that flows through all agent nodes.
Each node reads what it needs and writes its outputs.
The 'events' field uses Annotated[list, add] so each node
can append events without overwriting previous ones.
"""

from typing import TypedDict, Annotated, Optional
from operator import add


class SplunkZeroState(TypedDict, total=False):
    """
    State schema for the Splunk Zero agent pipeline.

    Fields are grouped by the stage that writes them.
    All fields use total=False (optional) because the state
    is built up incrementally as nodes execute.
    """

    # ── Trigger metadata ──────────────────────────────────
    trigger_type: str              # "webhook" | "cron" | "manual"
    target_period_days: int        # Analysis window (default: 30)
    run_id: str                    # Unique run identifier

    # ── Stage 1: Ingest Analysis ──────────────────────────
    ingest_by_source: list[dict]   # [{sourcetype, daily_gb, pct_of_total}]
    total_daily_gb: float          # Sum of all ingest

    # ── Stage 2: Search Audit ─────────────────────────────
    search_activity: list[dict]    # [{searched_sourcetype, search_count}]

    # ── Stage 3: Waste Detection ──────────────────────────
    wasteful_sources: list[dict]   # [{sourcetype, daily_gb, pct_of_total,
                                   #   search_count_30d, est_monthly_cost}]
    total_monthly_savings: float   # Sum of all waste costs
    waste_found: bool              # Routing flag for conditional edge

    # ── Stage 4: Source Tracing ───────────────────────────
    source_repos: list[dict]       # [{sourcetype, repo, config_file_path, confidence}]

    # ── Stage 5: Code Analysis ────────────────────────────
    proposed_changes: list[dict]   # [{repo, file, old_content, new_content,
                                   #   old_level, new_level, diff_summary}]

    # ── Stage 6: PR Creation ─────────────────────────────
    pull_requests: list[dict]      # [{repo, pr_url, pr_number, title, branch}]

    # ── Stage 7: Report ──────────────────────────────────
    report: dict                   # {summary, sources_analyzed, waste_found,
                                   #  prs_created, total_savings, timestamp}

    # ── Cross-cutting ────────────────────────────────────
    events: Annotated[list[dict], add]  # SSE events for UI (append-only)
    errors: list[dict]                  # [{step, error, timestamp}]
    current_step: str                   # Current node name for UI tracking
