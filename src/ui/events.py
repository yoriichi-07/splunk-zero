"""
Splunk Zero — SSE Event Manager

Manages event queues for real-time streaming to the UI.
Each agent run gets its own queue. Nodes push events,
the SSE endpoint yields them to the browser.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Optional


class EventManager:
    """
    Manages SSE event streams for agent runs.

    Usage:
        # In server.py — create once
        event_manager = EventManager()

        # In agent nodes — push events
        await event_manager.emit(run_id, "querying_ingest", "Analyzing Ingest Volume", ...)

        # In SSE endpoint — consume events
        async for event in event_manager.subscribe(run_id):
            yield event
    """

    def __init__(self):
        self._queues: dict[str, asyncio.Queue] = {}
        self._completed: dict[str, bool] = {}

    def create_run(self, run_id: str) -> None:
        """Create a new event queue for a run."""
        self._queues[run_id] = asyncio.Queue()
        self._completed[run_id] = False

    async def emit(
        self,
        run_id: str,
        step: str,
        title: str,
        detail: str = "",
        status: str = "running",
        data: Optional[dict] = None,
    ) -> dict:
        """
        Push an event to a run's queue.

        Args:
            run_id: The run identifier
            step: Machine-readable step name (e.g. "querying_ingest")
            title: Human-readable title (e.g. "Analyzing Ingest Volume")
            detail: Description of what's happening
            status: "running" | "complete" | "error" | "info"
            data: Optional structured data payload

        Returns:
            The event dict that was emitted
        """
        event = {
            "step": step,
            "title": title,
            "detail": detail,
            "status": status,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        queue = self._queues.get(run_id)
        if queue:
            await queue.put(event)

        return event

    async def complete(self, run_id: str) -> None:
        """Mark a run as complete and send terminal event."""
        await self.emit(
            run_id,
            step="done",
            title="Stream Complete",
            detail="All events have been sent.",
            status="complete",
        )
        self._completed[run_id] = True
        # Push sentinel to unblock any waiting subscribers
        queue = self._queues.get(run_id)
        if queue:
            await queue.put(None)

    async def error(self, run_id: str, error_message: str) -> None:
        """Send an error event and complete the stream."""
        await self.emit(
            run_id,
            step="error",
            title="Pipeline Error",
            detail=error_message,
            status="error",
        )
        self._completed[run_id] = True
        queue = self._queues.get(run_id)
        if queue:
            await queue.put(None)

    async def subscribe(self, run_id: str) -> AsyncGenerator[str, None]:
        """
        Async generator that yields SSE-formatted events for a run.

        Yields strings in SSE format:
            data: {"step": "...", "title": "...", ...}\n\n

        Terminates when the run is complete.
        """
        queue = self._queues.get(run_id)
        if not queue:
            yield f"data: {json.dumps({'step': 'error', 'title': 'Run Not Found', 'detail': f'No run with id {run_id}', 'status': 'error'})}\n\n"
            return

        while True:
            event = await queue.get()

            # None sentinel = stream complete
            if event is None:
                break

            yield f"data: {json.dumps(event)}\n\n"

    def is_complete(self, run_id: str) -> bool:
        """Check if a run has completed."""
        return self._completed.get(run_id, False)

    def cleanup(self, run_id: str) -> None:
        """Remove a run's queue to free memory."""
        self._queues.pop(run_id, None)
        self._completed.pop(run_id, None)


# Global singleton — imported by server.py and agent nodes
event_manager = EventManager()
