"""Agent graph nodes — each node is one step in the Splunk Zero pipeline."""

from src.agent.nodes.ingest_analysis import ingest_analysis
from src.agent.nodes.search_audit import search_audit
from src.agent.nodes.waste_detection import waste_detection
from src.agent.nodes.source_tracing import source_tracing
from src.agent.nodes.code_analysis import code_analysis
from src.agent.nodes.pr_creation import pr_creation
from src.agent.nodes.report import report

__all__ = [
    "ingest_analysis",
    "search_audit",
    "waste_detection",
    "source_tracing",
    "code_analysis",
    "pr_creation",
    "report",
]
