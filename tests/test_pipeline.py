"""
Splunk Zero — End-to-End Pipeline Test

Triggers the agent and streams SSE events to verify the full pipeline.

Usage:
    python -m tests.test_pipeline
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
import pytest

BASE_URL = "http://localhost:8888"

def _is_server_running():
    try:
        r = httpx.get(f"{BASE_URL}/health", timeout=1)
        return r.status_code == 200
    except Exception:
        return False


def test_health():
    """Test the health endpoint."""
    print("\n" + "=" * 60)
    print("  Splunk Zero -- Pipeline Test")
    print("=" * 60)

    if not _is_server_running():
        pytest.skip("FastAPI server is not running on localhost:8888")

    print("\n[1] Testing /health...")
    r = httpx.get(f"{BASE_URL}/health", timeout=10)
    data = r.json()
    print(f"    Status: {data['status']}")
    print(f"    Splunk: {data['splunk']['status']}")
    if data["splunk"].get("server_name"):
        print(
            f"    Server: {data['splunk']['server_name']} v{data['splunk'].get('version', '?')}"
        )
    assert data["status"] == "healthy"


def test_trigger_and_stream():
    """Trigger a run and stream events."""
    if not _is_server_running():
        pytest.skip("FastAPI server is not running on localhost:8888")

    print("\n[2] Triggering pipeline run...")
    r = httpx.post(f"{BASE_URL}/trigger", timeout=10)
    data = r.json()
    run_id = data["run_id"]
    print(f"    Run ID: {run_id}")
    print(f"    Events URL: {data['events_url']}")

    print("\n[3] Streaming events...\n")

    event_count = 0
    try:
        with httpx.stream(
            "GET", f"{BASE_URL}/events/{run_id}", timeout=120
        ) as response:
            for line in response.iter_lines():
                line = line.strip()

                # SSE format: "data: {json}" or empty lines
                if not line:
                    continue

                if line.startswith("data:"):
                    json_str = line[5:].strip()
                    if not json_str:
                        continue

                    try:
                        event = json.loads(json_str)
                        event_count += 1
                        step = event.get("step", "?")
                        status = event.get("status", "?")
                        title = event.get("title", "?")
                        detail = event.get("detail", "")

                        # Format status indicator
                        if status == "running":
                            indicator = "[..]"
                        elif status == "complete":
                            indicator = "[OK]"
                        elif status == "error":
                            indicator = "[!!]"
                        elif status == "info":
                            indicator = "[--]"
                        else:
                            indicator = "[??]"

                        print(f"    {indicator} {title}")
                        if detail:
                            print(f"         {detail[:100]}")

                        # Print data highlights
                        event_data = event.get("data", {})
                        if "total_monthly_savings" in event_data:
                            savings = event_data["total_monthly_savings"]
                            print(f"         >> SAVINGS: ${savings:,.2f}/month")
                        if "pr_url" in event_data:
                            print(f"         >> PR: {event_data['pr_url']}")

                        # Stop on completion
                        if step == "done":
                            print("\n    Stream complete.")
                            break

                    except json.JSONDecodeError:
                        pass  # Skip malformed lines

    except httpx.ReadTimeout:
        print("\n    [WARN] Stream timed out after 120s")
    except Exception as e:
        print(f"\n    [FAIL] Stream error: {e}")

    print(f"\n    Total events received: {event_count}")
    assert event_count > 0


def main():
    try:
        test_health()
        test_trigger_and_stream()
        print("\n[OK] Pipeline test run complete! All checks passed.")
    except AssertionError as e:
        print(f"\n[FAIL] Health check or assertion failed: {e}")
    except Exception as e:
        print(f"\n[FAIL] Pipeline test failed: {e}")

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()


def test_route_after_waste_detection():
    from src.agent.graph import _route_after_waste_detection

    state_no_waste = {"waste_found": False}
    assert _route_after_waste_detection(state_no_waste) == "report"

    state_waste = {"waste_found": True}
    assert _route_after_waste_detection(state_waste) == "source_tracing"
