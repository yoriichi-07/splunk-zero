"""
Splunk Zero — Demo Reset Script

Resets the demo repository to a clean state:
1. Resets logging.conf to all DEBUG levels
2. Deletes all splunk-zero/* branches
3. Closes all open PRs

Usage:
    python -m scripts.reset_demo
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from github import Github


def reset_demo():
    """Reset the demo repo to a clean state."""
    token = os.getenv("GITHUB_TOKEN", "")
    repo_name = os.getenv("GITHUB_REPO", "")

    if not token or not repo_name:
        print("[FAIL] GITHUB_TOKEN and GITHUB_REPO must be set in .env")
        return False

    print("\n" + "=" * 50)
    print("  Splunk Zero -- Demo Reset")
    print("=" * 50)

    g = Github(token)
    repo = g.get_repo(repo_name)

    # 1. Reset logging.conf to all DEBUG
    print("\n  [1] Resetting logging.conf to all DEBUG levels...")
    new_content = """[loggers]
keys=root,paymentService,orderService,userService,notificationService

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=detailed,brief

[logger_root]
level=DEBUG
handlers=consoleHandler,fileHandler

[logger_paymentService]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=payment
propagate=0

[logger_orderService]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=order
propagate=0

[logger_userService]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=user
propagate=0

[logger_notificationService]
level=DEBUG
handlers=consoleHandler,fileHandler
qualname=notification
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=detailed
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=DEBUG
formatter=detailed
args=('/var/log/app/application.log', 'a', 10485760, 5)

[formatter_detailed]
format=%(asctime)s %(name)s %(levelname)s %(module)s %(funcName)s %(message)s
datefmt=%Y-%m-%d %H:%M:%S

[formatter_brief]
format=%(asctime)s %(levelname)s %(message)s
"""

    try:
        f = repo.get_contents("logging.conf")
        repo.update_file(
            path="logging.conf",
            message="Reset logging levels to DEBUG for demo",
            content=new_content,
            sha=f.sha,
            branch="main",
        )
        print("       [OK] logging.conf reset to all DEBUG")
    except Exception as e:
        print(f"       [WARN] Could not reset logging.conf: {e}")

    # 2. Delete splunk-zero/* branches
    print("\n  [2] Cleaning up old branches...")
    try:
        branches = list(repo.get_branches())
        for branch in branches:
            if branch.name.startswith("splunk-zero/"):
                try:
                    ref = repo.get_git_ref(f"heads/{branch.name}")
                    ref.delete()
                    print(f"       [OK] Deleted: {branch.name}")
                except Exception as e:
                    print(f"       [WARN] Could not delete {branch.name}: {e}")
    except Exception as e:
        print(f"       [WARN] Could not list branches: {e}")

    # 3. Close open PRs
    print("\n  [3] Closing open PRs...")
    try:
        for pr in repo.get_pulls(state="open"):
            pr.edit(state="closed")
            print(f"       [OK] Closed PR #{pr.number}: {pr.title}")
    except Exception as e:
        print(f"       [WARN] Could not close PRs: {e}")

    print("\n" + "=" * 50)
    print("  Demo reset complete!")
    print("=" * 50 + "\n")
    return True


if __name__ == "__main__":
    reset_demo()
