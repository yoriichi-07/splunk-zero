"""
Node 6 — PR Creation

Creates a GitHub Pull Request with the proposed logging changes.
This is the ACTION step — the agent writes real code changes.

For each proposed change:
1. Creates a branch
2. Commits the modified config file
3. Opens a PR with an auto-generated description including cost savings
"""

from src.config import Config
from src.github.client import GitHubClient
from src.ui.events import event_manager


async def pr_creation(state: dict) -> dict:
    """
    Create GitHub PRs for proposed logging changes.

    Reads: run_id, proposed_changes, wasteful_sources, total_monthly_savings
    Writes: pull_requests, current_step, events
    """
    run_id = state.get("run_id", "")
    proposed_changes = state.get("proposed_changes", [])
    wasteful = state.get("wasteful_sources", [])
    total_savings = state.get("total_monthly_savings", 0)

    # Build waste lookup
    waste_lookup = {w["sourcetype"]: w for w in wasteful}

    # Emit start event
    await event_manager.emit(
        run_id,
        step="creating_pr",
        title="Creating Pull Request(s)",
        detail=f"Writing {len(proposed_changes)} change(s) to GitHub...",
        status="running",
    )

    github_client = GitHubClient(Config.GITHUB_TOKEN)
    pull_requests = []

    for change in proposed_changes:
        sourcetype = change.get("sourcetype", "")
        repo = change.get("repo", "")
        file_path = change.get("file", "")
        new_content = change.get("new_content", "")
        old_level = change.get("old_level", "DEBUG")
        new_level = change.get("new_level", "ERROR")
        file_sha = change.get("file_sha", "")
        diff_summary = change.get("diff_summary", "")
        waste_info = waste_lookup.get(sourcetype, {})

        # Sanitize sourcetype for branch name
        safe_sourcetype = sourcetype.replace(":", "-").replace(" ", "-").lower()
        branch_name = f"{Config.GITHUB_BRANCH_PREFIX}/reduce-{safe_sourcetype}-logging"

        try:
            # Step 1: Create branch
            await event_manager.emit(
                run_id,
                step="creating_branch",
                title="Creating Branch",
                detail=f"Branch: {branch_name}",
                status="info",
            )

            github_client.create_branch(repo, branch_name)

            # Step 2: Commit the change
            commit_msg = (
                f"chore: reduce {sourcetype} logging from {old_level} to {new_level}\n\n"
                f"Splunk Zero automated optimization:\n"
                f"- Sourcetype: {sourcetype}\n"
                f"- Daily ingest: {waste_info.get('daily_gb', '?')} GB/day\n"
                f"- Search activity (30d): {waste_info.get('search_count_30d', 0)} searches\n"
                f"- Estimated savings: ${waste_info.get('est_monthly_cost', 0):,.2f}/month\n"
            )

            commit_result = github_client.commit_file(
                repo_name=repo,
                branch=branch_name,
                file_path=file_path,
                new_content=new_content,
                commit_message=commit_msg,
                file_sha=file_sha,
            )

            # Step 3: Create PR
            pr_title = (
                f"[Splunk Zero] Reduce {sourcetype} logging: {old_level} -> {new_level}"
            )
            pr_body = _generate_pr_body(
                sourcetype=sourcetype,
                file_path=file_path,
                old_level=old_level,
                new_level=new_level,
                diff_summary=diff_summary,
                waste_info=waste_info,
                total_savings=total_savings,
            )

            pr_result = github_client.create_pull_request(
                repo_name=repo,
                branch=branch_name,
                title=pr_title,
                body=pr_body,
            )

            pull_requests.append(
                {
                    "sourcetype": sourcetype,
                    "repo": repo,
                    "pr_url": pr_result["pr_url"],
                    "pr_number": pr_result["pr_number"],
                    "title": pr_result["title"],
                    "branch": branch_name,
                    "commit_sha": commit_result["commit_sha"],
                }
            )

            # Emit PR created event
            await event_manager.emit(
                run_id,
                step="pr_created",
                title="PR Created!",
                detail=f"${waste_info.get('est_monthly_cost', 0):,.2f}/month savings",
                status="complete",
                data={
                    "pr_url": pr_result["pr_url"],
                    "pr_number": pr_result["pr_number"],
                    "title": pr_result["title"],
                    "sourcetype": sourcetype,
                    "savings": waste_info.get("est_monthly_cost", 0),
                },
            )

        except Exception as e:
            error_msg = f"Failed to create PR for {sourcetype}: {str(e)}"
            await event_manager.emit(
                run_id,
                step="pr_error",
                title=f"PR Failed: {sourcetype}",
                detail=error_msg,
                status="error",
            )

    # Emit completion
    await event_manager.emit(
        run_id,
        step="prs_complete",
        title="Pull Requests Complete",
        detail=f"Created {len(pull_requests)}/{len(proposed_changes)} PR(s).",
        status="complete",
        data={
            "prs_created": len(pull_requests),
            "total_proposed": len(proposed_changes),
        },
    )

    return {
        "pull_requests": pull_requests,
        "current_step": "pr_creation_complete",
    }


def _generate_pr_body(
    sourcetype: str,
    file_path: str,
    old_level: str,
    new_level: str,
    diff_summary: str,
    waste_info: dict,
    total_savings: float,
) -> str:
    """Generate a compelling PR description with cost savings."""

    daily_gb = waste_info.get("daily_gb", 0)
    pct = waste_info.get("pct_of_total", 0)
    searches = waste_info.get("search_count_30d", 0)
    monthly_cost = waste_info.get("est_monthly_cost", 0)

    return f"""## Splunk Zero - Automated Log Optimization

> **This PR was created automatically by [Splunk Zero](https://github.com/yoriichi-07/splunk-zero) - an AI agent that identifies and reduces wasteful logging.**

---

### What was found

| Metric | Value |
|--------|-------|
| **Sourcetype** | `{sourcetype}` |
| **Daily Ingest Volume** | {daily_gb} GB/day |
| **% of Total Ingest** | {pct}% |
| **Searches in Last 30 Days** | {searches} |
| **Estimated Monthly Cost** | **${monthly_cost:,.2f}** |

### The Problem

The sourcetype `{sourcetype}` accounts for **{pct}%** of total Splunk ingest volume ({daily_gb} GB/day), but has had **{searches} search(es)** in the last 30 days. This data is being ingested and stored at significant cost without providing operational value.

### The Fix

Changed logging level from `{old_level}` to `{new_level}` in `{file_path}`.

{diff_summary}

### Impact

- **Monthly savings:** ${monthly_cost:,.2f}
- **Annual savings:** ${monthly_cost * 12:,.2f}
- **Reduced noise:** Fewer low-priority log entries in Splunk indexes

### How This Was Detected

1. Splunk Zero queried the `_internal` index for ingest volume by sourcetype
2. Cross-referenced with the `_audit` index for actual search activity
3. Identified sourcetypes with high volume but zero/low search usage
4. Traced the sourcetype to this repository's logging configuration
5. Generated this PR to reduce the log level

---

*Splunk Zero: Zero noise. Zero waste. Zero unused data.*
"""
