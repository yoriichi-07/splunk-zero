"""
Node 4 — Source Tracing

Maps wasteful sourcetypes to GitHub repositories and logging config files.
Uses a configurable mapping for demo reliability, with LLM fallback for
unknown sourcetypes.

For the hackathon demo, we use a SOURCE_REPO_MAP that maps our synthetic
sourcetypes to the demo repo. In production, this would be entirely LLM-driven.
"""

import json
from src.config import Config
from src.ui.events import event_manager
from src.github.client import GitHubClient

# LLM import
from langchain_google_genai import ChatGoogleGenerativeAI


# ── Demo mapping ──────────────────────────────────────────
# Maps known sourcetypes to repos + config paths for reliable demo.
# This is the "cheat sheet" that makes the demo work every time.
# In production, this would be empty and the LLM would do all mapping.
SOURCE_REPO_MAP = {
    "app:payment-service:debug": {
        "repo": None,  # Will be filled from Config.GITHUB_REPO
        "config_file": "logging.conf",
        "confidence": 0.95,
    },
    "app:user-auth:debug": {
        "repo": None,
        "config_file": "logging.conf",
        "confidence": 0.90,
    },
    "app:inventory-api:debug": {
        "repo": None,
        "config_file": "logging.conf",
        "confidence": 0.85,
    },
}


async def source_tracing(state: dict) -> dict:
    """
    Map wasteful sourcetypes to GitHub repos and logging config files.

    Reads: run_id, wasteful_sources
    Writes: source_repos, current_step, events
    """
    run_id = state.get("run_id", "")
    wasteful = state.get("wasteful_sources", [])
    demo_repo = Config.GITHUB_REPO

    # Emit start event
    await event_manager.emit(
        run_id,
        step="tracing_source",
        title="Tracing to Source Code",
        detail=f"Mapping {len(wasteful)} wasteful sourcetype(s) to GitHub repositories...",
        status="running",
    )

    source_repos = []
    github_client = GitHubClient(Config.GITHUB_TOKEN)

    for source in wasteful:
        sourcetype = source.get("sourcetype", "")

        # Check demo mapping first
        mapping = SOURCE_REPO_MAP.get(sourcetype)
        if mapping:
            repo = mapping["repo"] or demo_repo
            config_file = mapping["config_file"]
            confidence = mapping["confidence"]

            # Verify the file actually exists
            try:
                configs = github_client.search_logging_configs(repo)
                config_file_found = any(c["name"] == config_file for c in configs)
                if not config_file_found and configs:
                    config_file = configs[0]["path"]
                    confidence = confidence * 0.8
            except Exception:
                pass

            source_repos.append(
                {
                    "sourcetype": sourcetype,
                    "repo": repo,
                    "config_file_path": config_file,
                    "confidence": confidence,
                    "method": "configured_mapping",
                }
            )

            await event_manager.emit(
                run_id,
                step="source_traced",
                title=f"Source Found: {sourcetype}",
                detail=f"Mapped to {repo} -> {config_file} (confidence: {confidence:.0%})",
                status="info",
                data={
                    "sourcetype": sourcetype,
                    "repo": repo,
                    "config_file": config_file,
                },
            )

        else:
            # LLM fallback — ask Gemini to reason about the mapping
            try:
                result = await _llm_trace_source(sourcetype, demo_repo)
                source_repos.append(result)

                await event_manager.emit(
                    run_id,
                    step="source_traced",
                    title=f"Source Found: {sourcetype}",
                    detail=f"LLM mapped to {result['repo']} -> {result['config_file_path']}",
                    status="info",
                    data=result,
                )

            except Exception as e:
                # Can't trace this source — log it and continue
                await event_manager.emit(
                    run_id,
                    step="source_trace_failed",
                    title=f"Could Not Trace: {sourcetype}",
                    detail=f"Failed to map sourcetype to a repository: {str(e)}",
                    status="error",
                )

    # Emit completion
    traced_count = len(source_repos)
    await event_manager.emit(
        run_id,
        step="tracing_complete",
        title="Source Tracing Complete",
        detail=f"Successfully traced {traced_count}/{len(wasteful)} sourcetype(s) to repos.",
        status="complete",
        data={"traced_count": traced_count, "total_wasteful": len(wasteful)},
    )

    return {
        "source_repos": source_repos,
        "current_step": "source_tracing_complete",
    }


async def _llm_trace_source(sourcetype: str, default_repo: str) -> dict:
    """Use LLM to reason about which repo a sourcetype might belong to."""

    llm = ChatGoogleGenerativeAI(
        model=Config.LLM_MODEL,
        project=Config.GCP_PROJECT,
        location=Config.GCP_LOCATION,
        temperature=0.0,
    )

    prompt = f"""You are analyzing a Splunk sourcetype to determine which GitHub repository it likely belongs to.

Sourcetype: {sourcetype}
Available repo to check: {default_repo}

Based on the sourcetype name, what application or service would produce these logs?
What logging configuration file would you expect to find?

Respond with valid JSON only (no markdown):
{{
    "sourcetype": "{sourcetype}",
    "repo": "{default_repo}",
    "config_file_path": "logging.conf",
    "confidence": 0.7,
    "reasoning": "Brief explanation"
}}
"""

    response = await llm.ainvoke(prompt)

    # Handle response.content being either str or list (Gemini SDK variation)
    raw_content = response.content
    if isinstance(raw_content, list):
        # Extract text from list of content parts
        content = " ".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw_content
        )
    else:
        content = str(raw_content)
    content = content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    result = json.loads(content)
    result["method"] = "llm_reasoning"
    return result
