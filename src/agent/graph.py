"""
Splunk Zero — LangGraph Workflow

Wires the 7 agent nodes into a state graph with conditional routing.
The graph follows a linear pipeline with one conditional edge:
after waste_detection, if no waste is found, skip straight to report.

Pipeline:
    START -> ingest_analysis -> search_audit -> waste_detection
        -> [waste found?]
            -> YES: source_tracing -> code_analysis -> pr_creation -> report -> END
            -> NO:  report -> END
"""

from langgraph.graph import StateGraph, END

from src.agent.state import SplunkZeroState
from src.agent.nodes.ingest_analysis import ingest_analysis
from src.agent.nodes.search_audit import search_audit
from src.agent.nodes.waste_detection import waste_detection
from src.agent.nodes.source_tracing import source_tracing
from src.agent.nodes.code_analysis import code_analysis
from src.agent.nodes.pr_creation import pr_creation
from src.agent.nodes.report import report


def _route_after_waste_detection(state: dict) -> str:
    """
    Conditional edge after waste detection.
    If waste is found, continue to source_tracing.
    If no waste, skip to report.
    """
    if state.get("waste_found", False):
        return "source_tracing"
    return "report"


def build_graph():
    """
    Build and compile the Splunk Zero agent graph.

    Returns a compiled LangGraph that can be invoked with:
        result = await graph.ainvoke(initial_state)
    """
    # Create the state graph
    graph = StateGraph(SplunkZeroState)

    # Add all nodes
    graph.add_node("ingest_analysis", ingest_analysis)
    graph.add_node("search_audit", search_audit)
    graph.add_node("waste_detection", waste_detection)
    graph.add_node("source_tracing", source_tracing)
    graph.add_node("code_analysis", code_analysis)
    graph.add_node("pr_creation", pr_creation)
    graph.add_node("report", report)

    # Set entry point
    graph.set_entry_point("ingest_analysis")

    # Add edges (linear pipeline)
    graph.add_edge("ingest_analysis", "search_audit")
    graph.add_edge("search_audit", "waste_detection")

    # Conditional edge after waste detection
    graph.add_conditional_edges(
        "waste_detection",
        _route_after_waste_detection,
        {
            "source_tracing": "source_tracing",
            "report": "report",
        },
    )

    # Continue the action pipeline
    graph.add_edge("source_tracing", "code_analysis")
    graph.add_edge("code_analysis", "pr_creation")
    graph.add_edge("pr_creation", "report")

    # Report is the terminal node
    graph.add_edge("report", END)

    # Compile and return
    return graph.compile()


# Pre-compiled graph — import and use directly
splunk_zero_graph = build_graph()
