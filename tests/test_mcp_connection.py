"""
Splunk Connection Test -- Phase 1 Verification

Tests both MCP protocol (SSE) and REST API fallback.

Usage:
    python -m tests.test_mcp_connection
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from src.mcp.splunk_client import SplunkMCPClient
import pytest

@pytest.mark.asyncio
async def test_connection():
    """Test Splunk connectivity via MCP and REST API."""
    print("\n" + "=" * 60)
    print("  Splunk Zero -- Connection Test")
    print("=" * 60)

    # 1. Check config
    print("\n[1/6] Checking configuration...")
    Config.print_status()

    if __name__ != "__main__":
        if not Config.SPLUNK_TOKEN or not Config.SPLUNK_USERNAME or Config.SPLUNK_USERNAME == "your_username_here":
            pytest.skip("Splunk credentials are not configured")

    if not Config.SPLUNK_TOKEN:
        print("[FAIL] SPLUNK_TOKEN not set. Cannot proceed.")
        assert False, "SPLUNK_TOKEN not set"

    client = SplunkMCPClient(
        host=Config.SPLUNK_HOST,
        port=Config.SPLUNK_PORT,
        token=Config.SPLUNK_TOKEN,
        username=Config.SPLUNK_USERNAME,
        password=Config.SPLUNK_PASSWORD,
    )

    # 2. REST API health check (most reliable -- test this first)
    print("[2/6] Testing Splunk REST API connectivity...")
    success = False
    try:
        result = await client.rest_health_check()
        print("  [OK] Splunk REST API is reachable")
        print(f"       Server: {result.get('server_name', 'unknown')}")
        print(f"       Version: {result.get('version', 'unknown')}")
        print(f"       OS: {result.get('os', 'unknown')}")
        success = True
    except Exception as e:
        print(f"  [FAIL] REST API failed: {e}")
        print(
            f"         Is Splunk running on https://{Config.SPLUNK_HOST}:{Config.SPLUNK_PORT}?"
        )
        if __name__ != "__main__":
            pytest.skip("Splunk REST API is not reachable")
        success = False

    if not success:
        assert False, "REST API connection failed"

    # 3. MCP protocol connection
    print("\n[3/6] Testing MCP Server (SSE protocol)...")
    mcp_works = False
    try:
        tools = await client.mcp_list_tools()
        mcp_works = True
        print(f"  [OK] MCP Server connected! Found {len(tools)} tools:")
        for tool in tools[:10]:
            name = tool.name if hasattr(tool, "name") else str(tool)
            desc = ""
            if hasattr(tool, "description") and tool.description:
                desc = tool.description[:60]
            print(f"       - {name}: {desc}")
        if len(tools) > 10:
            print(f"       ... and {len(tools) - 10} more")
    except Exception as e:
        print(f"  [WARN] MCP protocol failed: {e}")
        print("         Will use REST API fallback (still fully functional)")

    # 4. List indexes
    print("\n[4/6] Listing available indexes...")
    try:
        result = await client.rest_get_indexes()
        indexes = result.get("indexes", [])
        print(f"  [OK] Found {len(indexes)} indexes:")
        key_indexes = ["_internal", "_audit", "main"]
        for idx in indexes:
            name = idx["name"]
            marker = " <-- NEEDED" if name in key_indexes else ""
            events = idx.get("totalEventCount", "?")
            size = idx.get("currentDBSizeMB", "?")
            try:
                event_count = int(str(events).replace("N/A", "0") or "0")
            except (ValueError, TypeError):
                event_count = 0
            if name in key_indexes or event_count > 0:
                print(f"       - {name}: {events} events, {size} MB{marker}")
    except Exception as e:
        print(f"  [FAIL] Failed to list indexes: {e}")

    # 5. Test _internal query
    print("\n[5/6] Querying _internal index (ingest metrics)...")
    try:
        spl = (
            "index=_internal source=*metrics.log group=per_sourcetype_thruput "
            "| stats sum(kb) as total_kb by series "
            "| eval daily_gb = round(total_kb / 1024 / 1024, 4) "
            "| sort - daily_gb | head 10"
        )
        result = await client.run_query(spl, earliest_time="-1d")

        rows = _extract_rows(result)

        if rows:
            print(f"  [OK] _internal query returned {len(rows)} sourcetypes:")
            for row in rows[:5]:
                if isinstance(row, dict):
                    name = row.get("series", row.get("sourcetype", "?"))
                    gb = row.get("daily_gb", "?")
                    print(f"       - {name}: {gb} GB/day")
                else:
                    print(f"       - {_truncate(_to_str(row))}")
        else:
            print(
                "  [WARN] Query returned empty results (might be normal for fresh install)"
            )
    except Exception as e:
        print(f"  [FAIL] _internal query failed: {e}")

    # 6. Test _audit query
    print("\n[6/6] Querying _audit index (search activity)...")
    try:
        spl = (
            "index=_audit action=search info=completed "
            "| stats count by user | head 10"
        )
        result = await client.run_query(spl, earliest_time="-7d")

        rows = _extract_rows(result)

        if rows:
            print(f"  [OK] _audit query returned {len(rows)} results:")
            for row in rows[:5]:
                if isinstance(row, dict):
                    user = row.get("user", "?")
                    count = row.get("count", "?")
                    print(f"       - {user}: {count} searches")
                else:
                    print(f"       - {_truncate(_to_str(row))}")
        else:
            print("  [WARN] No search activity recorded yet (normal for fresh install)")
    except Exception as e:
        print(f"  [FAIL] _audit query failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print("  Splunk REST API:  [OK] Working")
    print(
        f"  MCP Protocol:     {'[OK] Working' if mcp_works else '[WARN] Failed (using REST fallback)'}"
    )
    print("  _internal access: See test 5 above")
    print("  _audit access:    See test 6 above")

    if not mcp_works:
        print(
            "\n  NOTE: MCP failed but REST API works -- we can still build everything."
        )
        print("        REST API gives us full Splunk access for all queries.")

    print("=" * 60 + "\n")
    assert success is True


def _extract_rows(result):
    """Extract row data from various response formats."""
    if isinstance(result, dict) and "results" in result:
        return result["results"]
    if hasattr(result, "content"):
        content = result.content
        if isinstance(content, list):
            return content
        if content:
            return [content]
    if result:
        return [result]
    return []


def _to_str(obj) -> str:
    """Safely convert any object to string."""
    if hasattr(obj, "text"):
        return obj.text
    return str(obj)


def _truncate(text: str, max_len: int = 150) -> str:
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text


if __name__ == "__main__":
    asyncio.run(test_connection())
