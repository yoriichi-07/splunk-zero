"""
Node 5 — Code Analysis

Reads logging configuration files from GitHub and uses the LLM to
propose changes that reduce logging levels (e.g., DEBUG -> ERROR/WARN).
Generates the modified config file content and a human-readable diff summary.
"""

import json
from datetime import datetime, timezone
from src.config import Config
from src.github.client import GitHubClient
from src.ui.events import event_manager

from langchain_google_genai import ChatGoogleGenerativeAI


async def code_analysis(state: dict) -> dict:
    """
    Read logging configs from GitHub and generate proposed changes.

    Reads: run_id, source_repos, wasteful_sources
    Writes: proposed_changes, current_step, events
    """
    run_id = state.get("run_id", "")
    source_repos = state.get("source_repos", [])
    wasteful = state.get("wasteful_sources", [])

    # Build wasteful lookup for cost data
    waste_lookup = {w["sourcetype"]: w for w in wasteful}

    # Emit start event
    await event_manager.emit(
        run_id,
        step="analyzing_code",
        title="Analyzing Logging Configurations",
        detail=f"Reading {len(source_repos)} config file(s) from GitHub...",
        status="running",
    )

    github_client = GitHubClient(Config.GITHUB_TOKEN)
    proposed_changes = []

    for source in source_repos:
        sourcetype = source.get("sourcetype", "")
        repo = source.get("repo", "")
        config_path = source.get("config_file_path", "")
        waste_info = waste_lookup.get(sourcetype, {})

        try:
            # Read current config file
            file_data = github_client.read_file(repo, config_path)
            old_content = file_data["content"]
            file_sha = file_data["sha"]

            await event_manager.emit(
                run_id,
                step="reading_config",
                title=f"Reading: {config_path}",
                detail=f"Found {len(old_content.splitlines())} lines in {repo}/{config_path}",
                status="info",
                data={"repo": repo, "file": config_path, "lines": len(old_content.splitlines())},
            )

            # Use LLM to analyze and propose changes
            change = await _analyze_and_propose(
                sourcetype=sourcetype,
                config_path=config_path,
                config_content=old_content,
                waste_info=waste_info,
            )

            if change:
                proposed_changes.append({
                    "sourcetype": sourcetype,
                    "repo": repo,
                    "file": config_path,
                    "file_sha": file_sha,
                    "old_content": old_content,
                    "new_content": change["new_content"],
                    "old_level": change["old_level"],
                    "new_level": change["new_level"],
                    "diff_summary": change["diff_summary"],
                })

                await event_manager.emit(
                    run_id,
                    step="change_proposed",
                    title=f"Change Proposed: {config_path}",
                    detail=f"{change['old_level']} -> {change['new_level']}",
                    status="complete",
                    data={
                        "old_level": change["old_level"],
                        "new_level": change["new_level"],
                        "diff_summary": change["diff_summary"],
                    },
                )

        except Exception as e:
            await event_manager.emit(
                run_id,
                step="analysis_error",
                title=f"Failed to Analyze: {config_path}",
                detail=str(e),
                status="error",
            )

    # Emit completion
    await event_manager.emit(
        run_id,
        step="analysis_complete",
        title="Code Analysis Complete",
        detail=f"Proposed {len(proposed_changes)} change(s) across {len(source_repos)} file(s).",
        status="complete",
        data={"changes_proposed": len(proposed_changes)},
    )

    return {
        "proposed_changes": proposed_changes,
        "current_step": "code_analysis_complete",
    }


async def _analyze_and_propose(
    sourcetype: str,
    config_path: str,
    config_content: str,
    waste_info: dict,
) -> dict:
    """
    Use LLM to analyze a logging config and propose level reduction.

    Returns:
        {new_content, old_level, new_level, diff_summary}
    """
    llm = ChatGoogleGenerativeAI(
        model=Config.LLM_MODEL,
        google_api_key=Config.GOOGLE_API_KEY,
        temperature=0.0,
    )

    daily_gb = waste_info.get("daily_gb", 0)
    monthly_cost = waste_info.get("est_monthly_cost", 0)

    prompt = f"""You are a logging optimization expert. Analyze this logging configuration file and propose changes to reduce the log level for the wasteful sourcetype.

**Context:**
- Sourcetype: {sourcetype}
- Current daily ingest: {daily_gb} GB/day
- Estimated monthly cost: ${monthly_cost}
- Nobody has searched these logs in 30 days
- Config file: {config_path}

**Current config content:**
```
{config_content}
```

**Task:**
1. Identify the current log level (e.g., DEBUG, INFO, TRACE)
2. Propose changing it to ERROR or WARN (whichever is more appropriate)
3. Generate the complete modified config file content
4. Provide a human-readable diff summary

**Respond with valid JSON only (no markdown fences):**
{{
    "old_level": "DEBUG",
    "new_level": "ERROR",
    "new_content": "... the entire modified config file content ...",
    "diff_summary": "Changed root logger level from DEBUG to ERROR in logging.conf"
}}

IMPORTANT: The "new_content" must be the COMPLETE file content with changes applied. Do NOT include markdown code fences in the JSON values.
"""

    response = await llm.ainvoke(prompt)

    # Handle response.content being either str or list (Gemini SDK variation)
    raw_content = response.content
    if isinstance(raw_content, list):
        content = " ".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw_content
        )
    else:
        content = str(raw_content)
    content = content.strip()

    # Strip markdown code fences if present
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:])
    if content.endswith("```"):
        content = content.rsplit("```", 1)[0]
    content = content.strip()

    result = json.loads(content)
    return result
