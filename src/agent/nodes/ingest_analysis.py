"""
Node 1 — Ingest Analysis

Queries Splunk's _internal index to get ingest volume by sourcetype.
This is the first step in the pipeline: understand what data is being ingested.
It uses an LLM Agent equipped with Splunk MCP tools to dynamically fetch this data.
"""

import json
from datetime import datetime, timezone
from src.config import Config
from src.mcp.splunk_client import SplunkMCPClient
from src.ui.events import event_manager

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

async def ingest_analysis(state: dict) -> dict:
    """
    Agentic ingest volume metrics analysis.

    Reads: trigger_type, target_period_days, run_id
    Writes: ingest_by_source, total_daily_gb, current_step, events
    """
    run_id = state.get("run_id", "")
    days = state.get("target_period_days", Config.ANALYSIS_PERIOD_DAYS)

    # Emit start event
    await event_manager.emit(
        run_id,
        step="querying_ingest",
        title="Agentic Ingest Analysis",
        detail=f"Deploying Gemini agent to autonomously investigate _internal metrics for {days} days...",
        status="running",
    )

    try:
        # Create Splunk client and get LangChain tools
        client = SplunkMCPClient(
            host=Config.SPLUNK_HOST,
            port=Config.SPLUNK_PORT,
            token=Config.SPLUNK_TOKEN,
            username=Config.SPLUNK_USERNAME,
            password=Config.SPLUNK_PASSWORD,
        )
        tools = client.get_langchain_tools()

        # Probe MCP server to show tool availability
        mcp_status = await client.get_mcp_tool_names()
        transport_label = "Splunk MCP Server" if mcp_status["mcp_connected"] else "Splunk REST API"
        tool_names = [t["name"] for t in mcp_status["tools"]]
        await event_manager.emit(
            run_id,
            step="mcp_tools_ready",
            title=f"MCP Tools Ready: {transport_label}",
            detail=f"Agent equipped with {len(tool_names)} tool(s): {', '.join(tool_names)}. Gemini will autonomously decide which to call.",
            status="info",
            data={
                "mcp_connected": mcp_status["mcp_connected"],
                "transport": mcp_status["transport"],
                "tools": tool_names,
            },
        )

        llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            project=Config.GCP_PROJECT,
            location=Config.GCP_LOCATION,
            temperature=0.0,
        )

        system_msg = (
            "You are an autonomous Splunk Optimization Agent. Your job is to investigate Splunk log ingestion. You have tools to run Splunk SPL queries. "
            "You must return the highest volume sourcetypes formatted exactly as a JSON array of objects with keys: "
            "'sourcetype', 'daily_gb', and 'pct_of_total'. Do not return any markdown, text, or explanation, just the raw JSON array."
        )

        agent = create_react_agent(llm, tools=tools, prompt=system_msg)

        user_input = (
            f"Use your tools to find the log ingest volume per sourcetype over the last {days} days. "
            f"Please run this specific SPL: 'index=_internal source=*metrics.log group=per_sourcetype_thruput | stats sum(kb) as total_kb by series | eval daily_gb = round(total_kb / 1024 / 1024 / {days}, 2) | sort - daily_gb | head 50 | eventstats sum(daily_gb) as grand_total | eval pct_of_total = round(daily_gb / grand_total * 100, 1) | table series, daily_gb, pct_of_total | rename series as sourcetype' "
            f"Run the query with earliest_time='-{days}d', parse the results, and then format the result into the required JSON array."
        )

        # Emit event showing agent is invoking the MCP tool
        await event_manager.emit(
            run_id,
            step="mcp_tool_called",
            title="MCP Tool Invoked: splunk_run_query",
            detail=f"Agent calling splunk_run_query on _internal index (last {days} days)...",
            status="info",
            data={"tool": "splunk_run_query", "index": "_internal", "transport": mcp_status["transport"]},
        )

        result = await agent.ainvoke({"messages": [("user", user_input)]})
        raw_content = result["messages"][-1].content
        if isinstance(raw_content, list):
            output_str = " ".join(
                part.get("text", str(part)) if isinstance(part, dict) else str(part)
                for part in raw_content
            )
        else:
            output_str = str(raw_content)
        output_str = output_str.strip()
        
        # Clean markdown if present
        if output_str.startswith("```"):
            output_str = output_str.split("\n", 1)[1]
        if output_str.endswith("```"):
            output_str = output_str.rsplit("```", 1)[0]
        output_str = output_str.strip()

        # Parse results into structured data
        ingest_data = json.loads(output_str)

        # Standardize types just in case LLM gave string numbers
        for item in ingest_data:
            item["daily_gb"] = float(item.get("daily_gb", 0))
            item["pct_of_total"] = float(item.get("pct_of_total", 0))
            
        total_gb = sum(item["daily_gb"] for item in ingest_data)

        # Emit completion event
        await event_manager.emit(
            run_id,
            step="ingest_complete",
            title="Agentic Ingest Complete",
            detail=f"Agent used {transport_label} tools to find {len(ingest_data)} sourcetypes. Total: {round(total_gb, 2)} GB/day",
            status="complete",
            data={
                "sourcetype_count": len(ingest_data),
                "total_daily_gb": round(total_gb, 2),
                "top_sources": ingest_data[:5],
                "transport": mcp_status["transport"],
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
