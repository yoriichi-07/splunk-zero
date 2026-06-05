"""
Splunk MCP Client — Connects to Splunk MCP Server via SSE transport.

The Splunk MCP Server exposes an SSE-based MCP endpoint (not plain REST).
We use the official Python MCP SDK to communicate properly.

Fallback: If MCP fails, we can use the Splunk REST API directly.
"""

import ssl
import json
import httpx
from typing import Optional
from contextlib import asynccontextmanager
from functools import partial

# Try MCP SDK first, fallback to REST
try:
    from mcp.client.sse import sse_client
    from mcp import ClientSession
    HAS_MCP_SDK = True
except ImportError:
    HAS_MCP_SDK = False
    print("[WARN] MCP SDK not installed. Using Splunk REST API fallback.")
    print("       Install with: pip install mcp")


class SplunkMCPClient:
    """
    Client for Splunk MCP Server.
    
    Primary: Uses MCP protocol over SSE (the proper way).
    Fallback: Uses Splunk REST API directly if MCP SDK unavailable.
    
    Note: MCP uses its own encrypted token for auth.
          REST API uses basic auth (username/password) - completely separate.
    """

    def __init__(
        self,
        host: str,
        port: int,
        token: str,
        username: str = "admin",
        password: str = "",
        verify_ssl: bool = False,
    ):
        self.host = host
        self.port = port
        self.base_url = f"https://{host}:{port}"
        self.mcp_url = f"{self.base_url}/services/mcp"
        self.token = token
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl

        # MCP protocol uses Bearer token
        self.mcp_headers = {
            "Authorization": f"Bearer {token}",
        }

        # REST API uses basic auth (separate from MCP token)
        self.rest_auth = (username, password) if password else None

    # ========================================================
    # MCP Protocol Methods (Primary — via SSE transport)
    # ========================================================

    @asynccontextmanager
    async def _mcp_session(self):
        """Create an MCP client session via SSE transport."""
        if not HAS_MCP_SDK:
            raise RuntimeError("MCP SDK not installed. pip install mcp")

        # Custom httpx client factory that skips SSL verification (local dev)
        def _no_verify_client_factory(**kwargs):
            return httpx.AsyncClient(verify=False, **kwargs)

        async with sse_client(
            url=self.mcp_url,
            headers=self.mcp_headers,
            httpx_client_factory=_no_verify_client_factory,
        ) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                yield session

    async def mcp_list_tools(self) -> list:
        """List all available MCP tools via proper MCP protocol."""
        async with self._mcp_session() as session:
            result = await session.list_tools()
            return result.tools

    async def mcp_call_tool(self, tool_name: str, arguments: dict = None) -> dict:
        """Call an MCP tool by name with arguments."""
        async with self._mcp_session() as session:
            result = await session.call_tool(tool_name, arguments or {})
            return result

    async def mcp_health_check(self) -> dict:
        """Check MCP server health via tool call."""
        return await self.mcp_call_tool("health_check")

    async def mcp_run_query(
        self,
        spl_query: str,
        earliest_time: str = "-30d",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> dict:
        """Execute an SPL query via MCP Server."""
        return await self.mcp_call_tool("splunk_run_query", {
            "search_query": spl_query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "max_results": max_results,
        })

    async def mcp_get_indexes(self) -> dict:
        """List all accessible indexes via MCP."""
        return await self.mcp_call_tool("splunk_get_indexes")

    # ========================================================
    # Splunk REST API Methods (Fallback)
    # ========================================================

    async def rest_search(
        self,
        spl_query: str,
        earliest_time: str = "-30d",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> dict:
        """Execute SPL query via Splunk REST API (fallback)."""
        url = f"{self.base_url}/services/search/jobs/export"
        data = {
            "search": f"search {spl_query}" if not spl_query.strip().startswith("|") else spl_query,
            "earliest_time": earliest_time,
            "latest_time": latest_time,
            "output_mode": "json",
            "count": max_results,
        }
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.post(
                url,
                data=data,
                auth=self.rest_auth,
                timeout=120,
            )
            response.raise_for_status()

            # Parse NDJSON response (one JSON object per line)
            results = []
            for line in response.text.strip().split("\n"):
                if line.strip():
                    try:
                        obj = json.loads(line)
                        if "result" in obj:
                            results.append(obj["result"])
                    except json.JSONDecodeError:
                        continue
            return {"results": results}

    async def rest_get_indexes(self) -> dict:
        """List indexes via Splunk REST API (fallback)."""
        url = f"{self.base_url}/services/data/indexes"
        params = {"output_mode": "json", "count": 0}
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.get(
                url,
                params=params,
                auth=self.rest_auth,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            entries = data.get("entry", [])
            return {
                "indexes": [
                    {
                        "name": e["name"],
                        "totalEventCount": e.get("content", {}).get("totalEventCount", "N/A"),
                        "currentDBSizeMB": e.get("content", {}).get("currentDBSizeMB", "N/A"),
                    }
                    for e in entries
                ]
            }

    async def rest_health_check(self) -> dict:
        """Check Splunk REST API connectivity (fallback)."""
        url = f"{self.base_url}/services/server/info"
        params = {"output_mode": "json"}
        async with httpx.AsyncClient(verify=self.verify_ssl) as client:
            response = await client.get(
                url,
                params=params,
                auth=self.rest_auth,
                timeout=15,
            )
            response.raise_for_status()
            data = response.json()
            entry = data.get("entry", [{}])[0]
            content = entry.get("content", {})
            return {
                "status": "healthy",
                "server_name": content.get("serverName", "unknown"),
                "version": content.get("version", "unknown"),
                "os": content.get("os_name", "unknown"),
            }

    # ========================================================
    # Unified Methods (try MCP first, fallback to REST)
    # ========================================================

    async def health_check(self) -> dict:
        """Health check — tries MCP first, falls back to REST API."""
        if HAS_MCP_SDK:
            try:
                return await self.mcp_health_check()
            except Exception as mcp_err:
                print(f"  [WARN] MCP health check failed: {mcp_err}")
                print(f"  Falling back to REST API...")

        return await self.rest_health_check()

    async def list_tools(self) -> list:
        """List available tools — MCP only (no REST equivalent)."""
        if not HAS_MCP_SDK:
            return [{"name": "REST_API_FALLBACK", "description": "Using Splunk REST API directly"}]
        return await self.mcp_list_tools()

    async def run_query(
        self,
        spl_query: str,
        earliest_time: str = "-30d",
        latest_time: str = "now",
        max_results: int = 100,
    ) -> dict:
        """Run SPL query — tries MCP first, falls back to REST."""
        if HAS_MCP_SDK:
            try:
                return await self.mcp_run_query(spl_query, earliest_time, latest_time, max_results)
            except Exception as mcp_err:
                print(f"  [WARN] MCP query failed: {mcp_err}")
                print(f"  Falling back to REST API...")

        return await self.rest_search(spl_query, earliest_time, latest_time, max_results)

    async def get_indexes(self) -> dict:
        """Get indexes — tries MCP first, falls back to REST."""
        if HAS_MCP_SDK:
            try:
                return await self.mcp_get_indexes()
            except Exception as mcp_err:
                print(f"  [WARN] MCP get_indexes failed: {mcp_err}")
                print(f"  Falling back to REST API...")

        return await self.rest_get_indexes()

    # ========================================================
    # Splunk Zero Specific Queries
    # ========================================================

    async def query_ingest_volume(self, days: int = 30) -> dict:
        """Query ingest volume by sourcetype from _internal metrics."""
        spl = (
            f'index=_internal source=*metrics.log group=per_sourcetype_thruput '
            f'| stats sum(kb) as total_kb by series '
            f'| eval daily_gb = round(total_kb / 1024 / 1024 / {days}, 2) '
            f'| sort - daily_gb '
            f'| head 50 '
            f'| eventstats sum(daily_gb) as grand_total '
            f'| eval pct_of_total = round(daily_gb / grand_total * 100, 1) '
            f'| table series, daily_gb, pct_of_total '
            f'| rename series as sourcetype'
        )
        return await self.run_query(spl, earliest_time=f"-{days}d")

    async def query_search_audit(self, days: int = 30) -> dict:
        """Query search audit to find what users actually search for."""
        spl = (
            f'index=_audit action=search info=completed '
            f'| rex field=search "sourcetype\\s*=\\s*(?<searched_sourcetype>\\w+)" '
            f'| stats count as search_count by searched_sourcetype '
            f'| sort - search_count'
        )
        return await self.run_query(spl, earliest_time=f"-{days}d")
