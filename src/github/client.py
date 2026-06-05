"""
Splunk Zero — GitHub API Client

Wraps PyGithub for the specific operations Splunk Zero needs:
- Search for logging config files in a repo
- Read file contents
- Create branches
- Commit file changes
- Open Pull Requests

All methods return structured dicts for clean integration with agent nodes.
"""

from github import Github, GithubException
from typing import Optional


# Known logging config file names to search for
LOGGING_CONFIG_FILES = [
    "logging.conf",
    "logging.ini",
    "logging.py",
    "logging.yaml",
    "logging.yml",
    "logging.json",
    "log4j.xml",
    "log4j.properties",
    "log4j2.xml",
    "log4j2.yaml",
    "logback.xml",
    "logback-spring.xml",
    "appsettings.json",
    "appsettings.Development.json",
    "config.yaml",
    "config.yml",
]


class GitHubClient:
    """
    GitHub operations for Splunk Zero.

    Handles repo access, file reading, branch creation,
    commits, and PR creation.
    """

    def __init__(self, token: str):
        self._github = Github(token)
        self._user = None

    @property
    def user(self):
        if self._user is None:
            self._user = self._github.get_user()
        return self._user

    def search_logging_configs(self, repo_name: str) -> list[dict]:
        """
        Search a repo for logging configuration files.

        Args:
            repo_name: "owner/repo" format

        Returns:
            List of dicts: [{name, path, size, download_url}]
        """
        try:
            repo = self._github.get_repo(repo_name)
            found = []

            # Search root directory
            try:
                root_contents = repo.get_contents("")
                for item in root_contents:
                    if item.name.lower() in [f.lower() for f in LOGGING_CONFIG_FILES]:
                        found.append({
                            "name": item.name,
                            "path": item.path,
                            "size": item.size,
                            "sha": item.sha,
                        })
            except GithubException:
                pass

            # Search common subdirectories
            config_dirs = ["src", "config", "conf", "resources", "src/main/resources"]
            for dir_path in config_dirs:
                try:
                    dir_contents = repo.get_contents(dir_path)
                    if not isinstance(dir_contents, list):
                        dir_contents = [dir_contents]
                    for item in dir_contents:
                        if item.name.lower() in [f.lower() for f in LOGGING_CONFIG_FILES]:
                            found.append({
                                "name": item.name,
                                "path": item.path,
                                "size": item.size,
                                "sha": item.sha,
                            })
                except GithubException:
                    # Directory doesn't exist — skip
                    continue

            return found

        except GithubException as e:
            raise RuntimeError(f"Failed to search repo {repo_name}: {e}")

    def read_file(self, repo_name: str, file_path: str) -> dict:
        """
        Read a file's content from a repo.

        Args:
            repo_name: "owner/repo" format
            file_path: Path within the repo

        Returns:
            {content, sha, path, size, encoding}
        """
        try:
            repo = self._github.get_repo(repo_name)
            content = repo.get_contents(file_path)
            return {
                "content": content.decoded_content.decode("utf-8"),
                "sha": content.sha,
                "path": content.path,
                "size": content.size,
                "encoding": content.encoding,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to read {file_path} from {repo_name}: {e}")

    def create_branch(
        self, repo_name: str, branch_name: str, from_branch: Optional[str] = None
    ) -> dict:
        """
        Create a new branch in a repo.

        Args:
            repo_name: "owner/repo" format
            branch_name: Name for the new branch
            from_branch: Base branch (default: repo's default branch)

        Returns:
            {branch_name, sha, ref}
        """
        try:
            repo = self._github.get_repo(repo_name)
            base = from_branch or repo.default_branch
            base_branch = repo.get_branch(base)
            sha = base_branch.commit.sha

            ref = repo.create_git_ref(
                ref=f"refs/heads/{branch_name}",
                sha=sha,
            )
            return {
                "branch_name": branch_name,
                "sha": sha,
                "ref": ref.ref,
            }
        except GithubException as e:
            if e.status == 422:
                # Branch already exists — get its info
                try:
                    existing = repo.get_branch(branch_name)
                    return {
                        "branch_name": branch_name,
                        "sha": existing.commit.sha,
                        "ref": f"refs/heads/{branch_name}",
                        "already_existed": True,
                    }
                except GithubException:
                    pass
            raise RuntimeError(f"Failed to create branch {branch_name}: {e}")

    def commit_file(
        self,
        repo_name: str,
        branch: str,
        file_path: str,
        new_content: str,
        commit_message: str,
        file_sha: Optional[str] = None,
    ) -> dict:
        """
        Commit a file change to a branch.

        Args:
            repo_name: "owner/repo" format
            branch: Branch to commit to
            file_path: Path of the file to update
            new_content: New file content
            commit_message: Commit message
            file_sha: SHA of the existing file (for updates).
                       If None, will be fetched automatically.

        Returns:
            {commit_sha, commit_url, file_path}
        """
        try:
            repo = self._github.get_repo(repo_name)

            # Get current file SHA if not provided
            if file_sha is None:
                try:
                    current = repo.get_contents(file_path, ref=branch)
                    file_sha = current.sha
                except GithubException:
                    # File doesn't exist — create it
                    file_sha = None

            if file_sha:
                # Update existing file
                result = repo.update_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    sha=file_sha,
                    branch=branch,
                )
            else:
                # Create new file
                result = repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    branch=branch,
                )

            return {
                "commit_sha": result["commit"].sha,
                "commit_url": result["commit"].html_url,
                "file_path": file_path,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to commit {file_path}: {e}")

    def create_pull_request(
        self,
        repo_name: str,
        branch: str,
        title: str,
        body: str,
        base_branch: Optional[str] = None,
    ) -> dict:
        """
        Create a Pull Request.

        Args:
            repo_name: "owner/repo" format
            branch: Head branch (the one with changes)
            title: PR title
            body: PR description (markdown)
            base_branch: Target branch (default: repo's default branch)

        Returns:
            {pr_url, pr_number, title, state}
        """
        try:
            repo = self._github.get_repo(repo_name)
            base = base_branch or repo.default_branch

            pr = repo.create_pull(
                title=title,
                body=body,
                head=branch,
                base=base,
            )
            return {
                "pr_url": pr.html_url,
                "pr_number": pr.number,
                "title": pr.title,
                "state": pr.state,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to create PR: {e}")

    def get_repo_info(self, repo_name: str) -> dict:
        """Get basic repo info for validation."""
        try:
            repo = self._github.get_repo(repo_name)
            return {
                "full_name": repo.full_name,
                "default_branch": repo.default_branch,
                "description": repo.description,
                "html_url": repo.html_url,
            }
        except GithubException as e:
            raise RuntimeError(f"Failed to access repo {repo_name}: {e}")
