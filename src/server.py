"""
Splunk Zero — FastAPI Server

The main entry point for the application.
Provides:
    GET  /health           — System health check
    POST /trigger          — Start an agent pipeline run
    GET  /events/{run_id}  — SSE stream of agent events
    GET  /                 — Serves the UI (Phase 3)
"""

import uuid
import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from sse_starlette.sse import EventSourceResponse
from pathlib import Path

from src.config import Config
from src.ui.events import event_manager
from src.agent.graph import splunk_zero_graph
from src.mcp.splunk_client import SplunkMCPClient


# ── App Setup ─────────────────────────────────────────────
app = FastAPI(
    title="Splunk Zero",
    description="Zero noise. Zero waste. Zero unused data.",
    version="1.0.0",
)

# CORS — allow the UI to connect from any origin during dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for UI (Phase 3)
static_dir = Path(__file__).parent / "ui" / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Health Check ──────────────────────────────────────────
@app.get("/health")
async def health_check():
    """
    System health check.
    Validates config and optionally tests Splunk connectivity.
    """
    missing = Config.validate()

    # Quick Splunk connectivity test
    splunk_status = "unknown"
    splunk_info = {}
    try:
        client = SplunkMCPClient(
            host=Config.SPLUNK_HOST,
            port=Config.SPLUNK_PORT,
            token=Config.SPLUNK_TOKEN,
            username=Config.SPLUNK_USERNAME,
            password=Config.SPLUNK_PASSWORD,
        )
        health = await client.rest_health_check()
        splunk_status = "healthy"
        splunk_info = health
    except Exception as e:
        splunk_status = f"error: {str(e)}"

    return JSONResponse(
        {
            "status": "healthy" if not missing else "degraded",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "config": {
                "missing_keys": missing,
                "splunk_host": f"{Config.SPLUNK_HOST}:{Config.SPLUNK_PORT}",
                "github_repo": Config.GITHUB_REPO,
                "llm_model": Config.LLM_MODEL,
            },
            "splunk": {
                "status": splunk_status,
                **splunk_info,
            },
        }
    )


# ── Trigger Agent Run ────────────────────────────────────
@app.post("/trigger")
async def trigger_run(background_tasks: BackgroundTasks):
    """
    Start a new agent pipeline run.

    Returns immediately with a run_id.
    The pipeline runs in the background.
    Subscribe to /events/{run_id} for real-time updates.
    """
    run_id = str(uuid.uuid4())[:8]

    # Create event queue for this run
    event_manager.create_run(run_id)

    # Start the pipeline in background
    background_tasks.add_task(_run_pipeline, run_id)

    return JSONResponse(
        {
            "status": "started",
            "run_id": run_id,
            "events_url": f"/events/{run_id}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


async def _run_pipeline(run_id: str):
    """Execute the full agent pipeline."""
    try:
        # Emit trigger event
        await event_manager.emit(
            run_id,
            step="triggered",
            title="Agent Activated",
            detail="Splunk Zero agent is starting investigation...",
            status="running",
        )

        # Build initial state
        initial_state = {
            "run_id": run_id,
            "trigger_type": "manual",
            "target_period_days": Config.ANALYSIS_PERIOD_DAYS,
            "events": [],
            "errors": [],
            "current_step": "starting",
        }

        # Run the LangGraph pipeline
        result = await splunk_zero_graph.ainvoke(initial_state)

        # Signal stream completion
        await event_manager.complete(run_id)

    except Exception as e:
        await event_manager.error(run_id, f"Pipeline failed: {str(e)}")


# ── Demo Reset ───────────────────────────────────────────
@app.post("/reset-demo")
async def reset_demo():
    """Reset the demo repository to a clean state."""
    try:
        from scripts.reset_demo import reset_demo as do_reset

        success = do_reset()
        return JSONResponse(
            {
                "status": "success" if success else "failed",
                "message": (
                    "Demo repo reset to clean state" if success else "Reset failed"
                ),
            }
        )
    except Exception as e:
        return JSONResponse(
            {
                "status": "error",
                "message": str(e),
            },
            status_code=500,
        )


# ── SSE Event Stream ─────────────────────────────────────
@app.get("/events/{run_id}")
async def event_stream(run_id: str):
    """
    Server-Sent Events stream for a pipeline run.
    Connect via EventSource in the browser to receive real-time updates.
    """
    return EventSourceResponse(event_manager.subscribe(run_id))


# ── UI Landing Page ──────────────────────────────────────
@app.get("/")
async def root():
    """Serve the UI landing page."""
    html_file = static_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text(encoding="utf-8"))

    # Fallback if UI hasn't been built yet
    return HTMLResponse(
        """
    <!DOCTYPE html>
    <html>
    <head><title>Splunk Zero</title></head>
    <body style="background:#0a0a0a;color:#fff;font-family:sans-serif;
                 display:flex;align-items:center;justify-content:center;
                 height:100vh;margin:0;">
        <div style="text-align:center;">
            <h1>Splunk Zero</h1>
            <p>Zero noise. Zero waste. Zero unused data.</p>
            <p style="color:#666;">UI coming in Phase 3. Use the API:</p>
            <code style="color:#0f0;">POST /trigger</code> |
            <code style="color:#0f0;">GET /events/{run_id}</code> |
            <code style="color:#0f0;">GET /health</code>
        </div>
    </body>
    </html>
    """
    )


# ── Run directly ─────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    print("\\n" + "=" * 50)
    print("  Splunk Zero -- Starting Server")
    print("=" * 50)
    Config.print_status()
    uvicorn.run(
        "src.server:app",
        host="0.0.0.0",
        port=Config.APP_PORT,
        reload=True,
    )
