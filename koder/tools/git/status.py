"""Git status tools."""

from git import Repo
from git.exc import InvalidGitRepositoryError

from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


@registry.register("git", needs_approval=False, is_read_only=True)
class GitStatusTool(ReadOnlyTool):
    """Get git repository status."""

    name: str = "git_status"
    description: str = (
        "Get the current git status of the repository. "
        "Shows modified, staged, and untracked files. "
        "No input required."
    )

    def _run(self) -> str:
        """
        Get git status.

        Returns:
            Formatted git status output
        """
        try:
            repo = Repo(self.workspace_path, search_parent_directories=True)

            if repo.bare:
                return "Error: Repository is bare"

            # Get status information
            lines = ["Git Status:", ""]

            # Current branch
            try:
                branch = repo.active_branch.name
                lines.append(f"Branch: {branch}")
            except TypeError:
                lines.append("Branch: (detached HEAD)")

            # Modified files
            modified = [item.a_path for item in repo.index.diff(None)]
            if modified:
                lines.append(f"\nModified files ({len(modified)}):")
                for file in modified:
                    lines.append(f"  M {file}")

            # Staged files
            staged = [item.a_path for item in repo.index.diff("HEAD")]
            if staged:
                lines.append(f"\nStaged files ({len(staged)}):")
                for file in staged:
                    lines.append(f"  A {file}")

            # Untracked files
            untracked = repo.untracked_files
            if untracked:
                lines.append(f"\nUntracked files ({len(untracked)}):")
                for file in untracked:
                    lines.append(f"  ? {file}")

            # Clean status
            if not modified and not staged and not untracked:
                lines.append("\nWorking tree clean")

            return "\n".join(lines)

        except InvalidGitRepositoryError:
            return "Error: Not a git repository"
        except Exception as e:
            return self._handle_error(e)


@registry.register("git", needs_approval=False, is_read_only=True)
class GitDiffTool(ReadOnlyTool):
    """Get git diff."""

    name: str = "git_diff"
    description: str = (
        "Show git diff for changes in the repository. "
        "Input should be an optional file path. If not provided, shows all changes."
    )

    def _run(self, file_path: str = "") -> str:
        """
        Get git diff.

        Args:
            file_path: Optional specific file to diff

        Returns:
            Diff output
        """
        try:
            repo = Repo(self.workspace_path, search_parent_directories=True)

            if file_path:
                # Diff specific file
                diff = repo.git.diff(file_path)
                if not diff:
                    return f"No changes in {file_path}"
            else:
                # Diff all changes
                diff = repo.git.diff()
                if not diff:
                    return "No changes to show"

            return diff

        except InvalidGitRepositoryError:
            return "Error: Not a git repository"
        except Exception as e:
            return self._handle_error(e)


@registry.register("git", needs_approval=False, is_read_only=True)
class GitLogTool(ReadOnlyTool):
    """Get git commit history."""

    name: str = "git_log"
    description: str = (
        "Show recent git commit history. "
        "Input should be the number of commits to show (default: 10)."
    )

    def _run(self, count: int = 10) -> str:
        """
        Get git log.

        Args:
            count: Number of commits to show

        Returns:
            Formatted commit history
        """
        try:
            repo = Repo(self.workspace_path, search_parent_directories=True)

            commits = list(repo.iter_commits(max_count=count))

            if not commits:
                return "No commits found"

            lines = [f"Recent commits (showing {len(commits)}):", ""]

            for commit in commits:
                lines.append(f"Commit: {commit.hexsha[:8]}")
                lines.append(f"Author: {commit.author.name} <{commit.author.email}>")
                lines.append(f"Date: {commit.committed_datetime}")
                lines.append(f"Message: {commit.message.strip()}")
                lines.append("")

            return "\n".join(lines)

        except InvalidGitRepositoryError:
            return "Error: Not a git repository"
        except Exception as e:
            return self._handle_error(e)
