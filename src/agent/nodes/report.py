"""
Node 7 — Report Generation

Compiles a final summary report of the agent's investigation.
This is the last node in the pipeline — it aggregates all findings
into a structured report and emits the final SSE event.
"""

from datetime import datetime, timezone
from src.ui.events import event_manager


async def report(state: dict) -> dict:
    """
    Compile the final investigation report.

    Reads: run_id, ingest_by_source, search_activity, wasteful_sources,
           total_monthly_savings, source_repos, proposed_changes, pull_requests,
           waste_found, errors
    Writes: report, current_step, events
    """
    run_id = state.get("run_id", "")
    ingest = state.get("ingest_by_source", [])
    searches = state.get("search_activity", [])
    wasteful = state.get("wasteful_sources", [])
    total_savings = state.get("total_monthly_savings", 0)
    source_repos = state.get("source_repos", [])
    changes = state.get("proposed_changes", [])
    prs = state.get("pull_requests", [])
    waste_found = state.get("waste_found", False)
    errors = state.get("errors", [])

    # Build the report
    report_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": _build_summary(waste_found, wasteful, prs, total_savings),
        "sources_analyzed": len(ingest),
        "search_patterns_found": len(searches),
        "waste_found": waste_found,
        "wasteful_sources_count": len(wasteful),
        "repos_traced": len(source_repos),
        "changes_proposed": len(changes),
        "prs_created": len(prs),
        "total_monthly_savings": total_savings,
        "total_annual_savings": round(total_savings * 12, 2),
        "pull_requests": [
            {
                "sourcetype": pr.get("sourcetype", ""),
                "url": pr.get("pr_url", ""),
                "title": pr.get("title", ""),
            }
            for pr in prs
        ],
        "wasteful_details": [
            {
                "sourcetype": w.get("sourcetype", ""),
                "daily_gb": w.get("daily_gb", 0),
                "monthly_cost": w.get("est_monthly_cost", 0),
                "searches_30d": w.get("search_count_30d", 0),
            }
            for w in wasteful
        ],
        "errors": errors,
        "status": "completed_with_errors" if errors else "completed",
    }

    # Emit the final report event
    if waste_found and prs:
        # Success — waste found and PRs created
        await event_manager.emit(
            run_id,
            step="complete",
            title="Investigation Complete",
            detail=report_data["summary"],
            status="complete",
            data={
                "total_monthly_savings": total_savings,
                "total_annual_savings": total_savings * 12,
                "prs_created": len(prs),
                "pr_urls": [pr.get("pr_url", "") for pr in prs],
                "sources_analyzed": len(ingest),
            },
        )
    elif waste_found and not prs:
        # Waste found but PR creation failed
        await event_manager.emit(
            run_id,
            step="complete",
            title="Investigation Complete (Partial)",
            detail=f"Found ${total_savings:,.2f}/month in waste but could not create PRs. Check errors.",
            status="complete",
            data=report_data,
        )
    else:
        # No waste found — clean report
        await event_manager.emit(
            run_id,
            step="complete",
            title="Investigation Complete - All Clean",
            detail=f"Analyzed {len(ingest)} sourcetypes. No significant waste detected.",
            status="complete",
            data={"sources_analyzed": len(ingest)},
        )

    return {
        "report": report_data,
        "current_step": "complete",
    }


def _build_summary(
    waste_found: bool,
    wasteful: list,
    prs: list,
    total_savings: float,
) -> str:
    """Build a human-readable summary string."""
    if not waste_found:
        return "No significant wasteful log sources detected. All sourcetypes above the threshold have sufficient search activity."

    if prs:
        pr_links = ", ".join([pr.get("pr_url", "?") for pr in prs])
        return (
            f"Found {len(wasteful)} wasteful sourcetype(s). "
            f"Created {len(prs)} PR(s) to reduce logging levels. "
            f"Estimated savings: ${total_savings:,.2f}/month (${total_savings * 12:,.2f}/year). "
            f"PRs: {pr_links}"
        )

    return (
        f"Found {len(wasteful)} wasteful sourcetype(s) "
        f"worth ${total_savings:,.2f}/month, "
        f"but could not create PRs automatically."
    )
