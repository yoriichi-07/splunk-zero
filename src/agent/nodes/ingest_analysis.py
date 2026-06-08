"""
Node 1 — Ingest Analysis

Queries Splunk's _internal index to get ingest volume by sourcetype.
This is the first step in the pipeline: understand what data is being ingested.
"""

from datetime import datetime, timezone
from src.config import Config
from src.mcp.splunk_client import SplunkMCPClient
from src.ui.events import event_manager


async def ingest_analysis(state: dict) -> dict:
    """
    Query _internal index for ingest volume metrics.

    Reads: trigger_type, target_period_days, run_id
    Writes: ingest_by_source, total_daily_gb, current_step, events
    """
    run_id = state.get("run_id", "")
    days = state.get("target_period_days", Config.ANALYSIS_PERIOD_DAYS)

    # Emit start event
    await event_manager.emit(
        run_id,
        step="querying_ingest",
        title="Analyzing Ingest Volume",
        detail=f"Querying Splunk _internal index for {days}-day ingest metrics...",
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

        # Run the ingest volume query
        result = await client.query_ingest_volume(days=days)
        rows = result.get("results", [])

        # Parse results into structured data
        ingest_data = []
        total_gb = 0.0

        for row in rows:
            daily_gb = float(row.get("daily_gb", 0))
            pct = float(row.get("pct_of_total", 0))
            sourcetype = row.get("sourcetype", row.get("series", "unknown"))

            ingest_data.append(
                {
                    "sourcetype": sourcetype,
                    "daily_gb": daily_gb,
                    "pct_of_total": pct,
                }
            )
            total_gb += daily_gb

        # Emit completion event
        await event_manager.emit(
            run_id,
            step="ingest_complete",
            title="Ingest Analysis Complete",
            detail=f"Found {len(ingest_data)} sourcetypes. Total: {round(total_gb, 2)} GB/day",
            status="complete",
            data={
                "sourcetype_count": len(ingest_data),
                "total_daily_gb": round(total_gb, 2),
                "top_sources": ingest_data[:5],
            },
        )

        return {
            "ingest_by_source": ingest_data,
            "total_daily_gb": round(total_gb, 4),
            "current_step": "ingest_analysis_complete",
        }

    except Exception as e:
        error_msg = f"Ingest analysis failed: {str(e)}"
        await event_manager.emit(
            run_id,
            step="ingest_error",
            title="Ingest Analysis Failed",
            detail=error_msg,
            status="error",
        )
        return {
            "ingest_by_source": [],
            "total_daily_gb": 0.0,
            "current_step": "ingest_analysis_error",
            "errors": [
                {
                    "step": "ingest_analysis",
                    "error": error_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
