"""
Node 2 — Search Audit

Queries Splunk's _audit index to find what sourcetypes users actually search for.
This tells us which data is being used vs. which is just sitting there unused.
"""

from datetime import datetime, timezone
from src.config import Config
from src.mcp.splunk_client import SplunkMCPClient
from src.ui.events import event_manager


async def search_audit(state: dict) -> dict:
    """
    Query _audit index for search activity by sourcetype.

    Reads: run_id, target_period_days
    Writes: search_activity, current_step, events
    """
    run_id = state.get("run_id", "")
    days = state.get("target_period_days", Config.ANALYSIS_PERIOD_DAYS)

    # Emit start event
    await event_manager.emit(
        run_id,
        step="querying_audit",
        title="Checking Search Activity",
        detail=f"Querying Splunk _audit index for {days}-day search history...",
        status="running",
    )

    try:
        # Create Splunk client
        client = SplunkMCPClient(
            host=Config.SPLUNK_HOST,
            port=Config.SPLUNK_PORT,
            token=Config.SPLUNK_TOKEN,
            username=Config.SPLUNK_USERNAME,
            password=Config.SPLUNK_PASSWORD,
        )

        # Run the search audit query
        result = await client.query_search_audit(days=days)
        rows = result.get("results", [])

        # Parse results
        search_data = []
        total_searches = 0

        for row in rows:
            sourcetype = row.get("searched_sourcetype", "")
            count = int(row.get("search_count", 0))

            if sourcetype:  # Skip empty sourcetype entries
                search_data.append({
                    "searched_sourcetype": sourcetype,
                    "search_count": count,
                })
                total_searches += count

        # Emit completion event
        await event_manager.emit(
            run_id,
            step="audit_complete",
            title="Search Audit Complete",
            detail=f"Found {len(search_data)} sourcetypes searched. Total: {total_searches} searches in {days} days.",
            status="complete",
            data={
                "sourcetypes_searched": len(search_data),
                "total_searches": total_searches,
                "top_searched": search_data[:5],
            },
        )

        return {
            "search_activity": search_data,
            "current_step": "search_audit_complete",
        }

    except Exception as e:
        error_msg = f"Search audit failed: {str(e)}"
        await event_manager.emit(
            run_id,
            step="audit_error",
            title="Search Audit Failed",
            detail=error_msg,
            status="error",
        )
        return {
            "search_activity": [],
            "current_step": "search_audit_error",
            "errors": [{"step": "search_audit", "error": error_msg,
                        "timestamp": datetime.now(timezone.utc).isoformat()}],
        }
