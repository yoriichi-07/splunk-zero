"""
Node 2 — Search Audit

Queries Splunk's _audit index to find what sourcetypes users actually search for.
This tells us which data is being used vs. which is just sitting there unused.
It uses an LLM Agent equipped with Splunk MCP tools to dynamically fetch this data.
"""

import json
from datetime import datetime, timezone
from src.config import Config
from src.mcp.splunk_client import SplunkMCPClient
from src.ui.events import event_manager

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent


async def search_audit(state: dict) -> dict:
    """
    Agentic search activity analysis.

    Reads: run_id, target_period_days
    Writes: search_activity, current_step, events
    """
    run_id = state.get("run_id", "")
    days = state.get("target_period_days", Config.ANALYSIS_PERIOD_DAYS)

    # Emit start event
    await event_manager.emit(
        run_id,
        step="querying_audit",
        title="Agentic Search Audit",
        detail=f"Deploying Gemini agent to autonomously investigate _audit history for {days} days...",
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

        # Show MCP transport in use for this node too
        mcp_status = await client.get_mcp_tool_names()
        transport_label = "Splunk MCP Server" if mcp_status["mcp_connected"] else "Splunk REST API"

        # Emit event showing agent is invoking the MCP tool for audit
        await event_manager.emit(
            run_id,
            step="mcp_tool_called",
            title="MCP Tool Invoked: splunk_run_query",
            detail=f"Agent calling splunk_run_query on _audit index (last {days} days)...",
            status="info",
            data={"tool": "splunk_run_query", "index": "_audit", "transport": mcp_status["transport"]},
        )

        llm = ChatGoogleGenerativeAI(
            model=Config.LLM_MODEL,
            project=Config.GCP_PROJECT,
            location=Config.GCP_LOCATION,
            temperature=0.0,
        )

        system_msg = (
            "You are an autonomous Splunk Optimization Agent. Your job is to investigate Splunk search activity. You have tools to run Splunk SPL queries. "
            "You must return the searched sourcetypes formatted exactly as a JSON array of objects with keys: "
            "'searched_sourcetype' and 'search_count'. Do not return any markdown, text, or explanation, just the raw JSON array."
        )

        agent = create_react_agent(llm, tools=tools, prompt=system_msg)

        user_input = (
            f"Use your tools to find how many times each sourcetype was searched over the last {days} days. "
            f"Please run this specific SPL: 'index=_audit action=search info=completed | rex field=search \"sourcetype\\\\s*=\\\\s*\\\\\"?(?<searched_sourcetype>[^\\\\s\\\\\"|]+)\" | stats count as search_count by searched_sourcetype | sort - search_count' "
            f"Run the query with earliest_time='-{days}d', parse the results, and then format the result into the required JSON array."
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

        # Parse results
        raw_search_data = json.loads(output_str)
        search_data = []
        total_searches = 0

        for row in raw_search_data:
            sourcetype = row.get("searched_sourcetype", "")
            count = int(row.get("search_count", 0))

            if sourcetype:  # Skip empty sourcetype entries
                search_data.append(
                    {
                        "searched_sourcetype": sourcetype,
                        "search_count": count,
                    }
                )
                total_searches += count

        # Emit completion event
        await event_manager.emit(
            run_id,
            step="audit_complete",
            title="Agentic Audit Complete",
            detail=f"Agent used {transport_label} tools to find {len(search_data)} sourcetypes searched. Total: {total_searches} searches.",
            status="complete",
            data={
                "sourcetypes_searched": len(search_data),
                "total_searches": total_searches,
                "top_searched": search_data[:5],
                "transport": mcp_status["transport"],
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
            "errors": [
                {
                    "step": "search_audit",
                    "error": error_msg,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ],
        }
