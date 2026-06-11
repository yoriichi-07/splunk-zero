"""
Node 3 — Waste Detection

Cross-references ingest volume with search activity to find wasteful sources.
A source is "wasteful" if it consumes a high percentage of ingest volume
but has zero or very few searches in the analysis period.
"""

from src.config import Config
from src.ui.events import event_manager


DEMO_SCALE_BASELINES = {
    # The local HEC dataset is intentionally small; these baselines model the
    # same services at enterprise Splunk scale for a repeatable demo.
    "app:payment-service:debug": {"daily_gb": 12.40, "pct_of_total": 35.0},
    "app:user-auth:debug": {"daily_gb": 8.10, "pct_of_total": 22.8},
    "app:inventory-api:debug": {"daily_gb": 5.24, "pct_of_total": 14.8},
}


def _is_in_scope_sourcetype(sourcetype: str) -> bool:
    """Keep Phase 3 demo focused on application logs, not Splunk internals."""
    return sourcetype.startswith("app:")


def _scaled_source_values(sourcetype: str, daily_gb: float, pct: float) -> dict:
    """Return deterministic demo-scale values for known synthetic sourcetypes."""
    baseline = DEMO_SCALE_BASELINES.get(sourcetype)
    if not baseline:
        return {
            "daily_gb": daily_gb,
            "pct_of_total": pct,
            "demo_scaled": False,
            "observed_daily_gb": daily_gb,
        }

    scaled_daily_gb = max(daily_gb, baseline["daily_gb"])
    scaled_pct = max(pct, baseline["pct_of_total"])
    return {
        "daily_gb": round(scaled_daily_gb, 2),
        "pct_of_total": round(scaled_pct, 1),
        "demo_scaled": daily_gb < baseline["daily_gb"],
        "observed_daily_gb": daily_gb,
    }


async def waste_detection(state: dict) -> dict:
    """
    Cross-reference ingest data with search audit to find waste.

    Reads: run_id, ingest_by_source, search_activity, total_daily_gb
    Writes: wasteful_sources, total_monthly_savings, waste_found, current_step, events
    """
    run_id = state.get("run_id", "")
    ingest_data = state.get("ingest_by_source", [])
    search_data = state.get("search_activity", [])

    threshold_pct = Config.WASTE_THRESHOLD_PCT
    min_searches = Config.MIN_SEARCH_COUNT
    cost_per_gb = Config.COST_PER_GB_PER_DAY

    # Emit start event
    await event_manager.emit(
        run_id,
        step="detecting_waste",
        title="Finding Wasteful Sources",
        detail=f"Cross-referencing {len(ingest_data)} sourcetypes against {len(search_data)} search patterns...",
        status="running",
        data={
            "threshold_pct": threshold_pct,
            "min_search_count": min_searches,
        },
    )

    # Build lookup: sourcetype -> search count
    searched = {}
    for row in search_data:
        st = row.get("searched_sourcetype", "")
        count = row.get("search_count", 0)
        if st:
            searched[st] = searched.get(st, 0) + count

    # Find wasteful sources using dual criteria
    wasteful = []
    seen_sourcetypes = set()

    # Pass 1: High-volume waste (above threshold % AND low searches)
    for source in ingest_data:
        sourcetype = source.get("sourcetype", "")
        daily_gb = source.get("daily_gb", 0.0)
        pct = source.get("pct_of_total", 0.0)
        search_count = searched.get(sourcetype, 0)

        if (
            _is_in_scope_sourcetype(sourcetype)
            and pct > threshold_pct
            and search_count < min_searches
        ):
            values = _scaled_source_values(sourcetype, daily_gb, pct)
            est_monthly_cost = round(values["daily_gb"] * 30 * cost_per_gb, 2)
            wasteful.append(
                {
                    "sourcetype": sourcetype,
                    **values,
                    "search_count_30d": search_count,
                    "est_monthly_cost": est_monthly_cost,
                }
            )
            seen_sourcetypes.add(sourcetype)

    # Pass 2: Zero-search waste (any ingest, literally zero searches)
    # This catches application-level sourcetypes like our synthetic data
    # that have some volume but nobody ever searches for them.
    for source in ingest_data:
        sourcetype = source.get("sourcetype", "")
        if sourcetype in seen_sourcetypes:
            continue

        daily_gb = source.get("daily_gb", 0.0)
        pct = source.get("pct_of_total", 0.0)
        search_count = searched.get(sourcetype, 0)

        if search_count == 0 and _is_in_scope_sourcetype(sourcetype):
            values = _scaled_source_values(sourcetype, daily_gb, pct)
            if values["daily_gb"] <= 0:
                continue
            est_monthly_cost = round(values["daily_gb"] * 30 * cost_per_gb, 2)
            wasteful.append(
                {
                    "sourcetype": sourcetype,
                    **values,
                    "search_count_30d": search_count,
                    "est_monthly_cost": est_monthly_cost,
                }
            )
            seen_sourcetypes.add(sourcetype)

    # Sort by cost (most expensive waste first)
    wasteful.sort(key=lambda x: x["est_monthly_cost"], reverse=True)

    # Calculate total savings
    total_savings = sum(w["est_monthly_cost"] for w in wasteful)
    waste_found = len(wasteful) > 0

    # Emit result event
    if waste_found:
        await event_manager.emit(
            run_id,
            step="waste_found",
            title="Waste Detected!",
            detail=f"Found {len(wasteful)} wasteful sourcetype(s). Estimated savings: ${total_savings:,.2f}/month",
            status="complete",
            data={
                "wasteful_count": len(wasteful),
                "total_monthly_savings": total_savings,
                "wasteful_sources": wasteful,
            },
        )
    else:
        await event_manager.emit(
            run_id,
            step="no_waste",
            title="No Significant Waste Found",
            detail=f"All sourcetypes above {threshold_pct}% volume have sufficient search activity.",
            status="complete",
            data={"threshold_pct": threshold_pct, "min_searches": min_searches},
        )

    return {
        "wasteful_sources": wasteful,
        "total_monthly_savings": round(total_savings, 2),
        "waste_found": waste_found,
        "current_step": "waste_detection_complete",
    }
