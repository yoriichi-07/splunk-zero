"""
GitHub API Connection Test -- Phase 1 Verification

Usage:
    python -m tests.test_github_connection
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import Config
from github import Github, GithubException


def test_github_connection():
    """Test GitHub API connectivity and permissions."""
    print("\n" + "=" * 60)
    print("  Splunk Zero -- GitHub Connection Test")
    print("=" * 60)

    # 1. Check config
    print("\n[1/4] Checking configuration...")
    if not Config.GITHUB_TOKEN:
        print("  [FAIL] GITHUB_TOKEN not set in .env")
        return False
    if not Config.GITHUB_REPO:
        print("  [FAIL] GITHUB_REPO not set in .env")
        return False
    print(f"  [OK] Token: set")
    print(f"  [OK] Repo:  {Config.GITHUB_REPO}")

    # 2. Authenticate
    print("\n[2/4] Authenticating with GitHub...")
    try:
        g = Github(Config.GITHUB_TOKEN)
        user = g.get_user()
        print(f"  [OK] Authenticated as: {user.login}")
    except GithubException as e:
        print(f"  [FAIL] Authentication failed: {e}")
        return False

    # 3. Access repo
    repo_name = Config.GITHUB_REPO
    # Strip URL prefix if accidentally included
    if "github.com/" in repo_name:
        repo_name = repo_name.split("github.com/")[-1].rstrip("/")
        print(f"  [NOTE] Stripped URL prefix. Using: {repo_name}")

    print(f"\n[3/4] Accessing repo: {repo_name}...")
    try:
        repo = g.get_repo(repo_name)
        print(f"  [OK] Repo found: {repo.full_name}")
        print(f"       Description: {repo.description or 'none'}")
        print(f"       Default branch: {repo.default_branch}")

        # List files in root
        contents = repo.get_contents("")
        file_names = [c.name for c in contents]
        print(f"       Root files: {', '.join(file_names)}")

        # Look for logging config files
        logging_patterns = [
            "logging.conf", "logging.ini", "log4j.xml", "log4j2.xml",
            "logback.xml", "logging.yaml", "logging.json",
            "appsettings.json",
        ]
        found_configs = [f for f in file_names if f.lower() in logging_patterns]

        if found_configs:
            print(f"  [OK] Logging configs found: {', '.join(found_configs)}")

            for config_name in found_configs:
                content = repo.get_contents(config_name)
                text = content.decoded_content.decode("utf-8")
                lines = text.split("\n")
                print(f"\n       --- {config_name} (first 10 lines) ---")
                for line in lines[:10]:
                    print(f"       {line}")
                if len(lines) > 10:
                    print(f"       ... ({len(lines) - 10} more lines)")
        else:
            print(f"  [WARN] No logging configs in repo root.")

    except GithubException as e:
        print(f"  [FAIL] Cannot access repo: {e}")
        print(f"         GITHUB_REPO should be: owner/repo (e.g. yoriichi-07/splunk-zero-demo-app)")
        print(f"         NOT the full URL.")
        return False

    # 4. Test write access
    print(f"\n[4/4] Testing write access (create test branch)...")
    test_branch_name = "splunk-zero/connection-test"
    try:
        default_branch = repo.get_branch(repo.default_branch)
        sha = default_branch.commit.sha

        ref = repo.create_git_ref(
            ref=f"refs/heads/{test_branch_name}",
            sha=sha,
        )
        print(f"  [OK] Branch created: {test_branch_name}")
        ref.delete()
        print(f"  [OK] Branch deleted (cleanup)")

    except GithubException as e:
        if e.status == 422:
            try:
                ref = repo.get_git_ref(f"heads/{test_branch_name}")
                ref.delete()
                print(f"  [OK] Write access confirmed (cleaned up old test branch)")
            except Exception:
                print(f"  [WARN] Branch already exists: {e}")
        else:
            print(f"  [FAIL] Write access failed: {e}")
            print(f"         Make sure your PAT has 'repo' scope")
            return False

    print("\n" + "=" * 60)
    print("  [OK] GitHub connection test complete! All checks passed.")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    test_github_connection()
