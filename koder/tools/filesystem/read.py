"""Filesystem read tools."""

from pathlib import Path
from typing import Any

from pydantic import Field

from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


@registry.register("filesystem", needs_approval=False, is_read_only=True)
class ReadFileTool(ReadOnlyTool):
    """Read contents of a file."""

    name: str = "read_file"
    description: str = (
        "Read the contents of a file. "
        "Input should be a file path relative to the workspace. "
        "Returns the file contents as a string."
    )

    max_size_mb: int = Field(
        default=10,
        description="Maximum file size to read in MB",
    )

    def _run(self, file_path: str) -> str:
        """
        Read file contents.

        Args:
            file_path: Path to file to read

        Returns:
            File contents
        """
        try:
            path = Path(self.workspace_path) / file_path
            path = path.resolve()

            if not path.exists():
                return f"Error: File not found: {file_path}"

            if not path.is_file():
                return f"Error: Path is not a file: {file_path}"

            # Check file size
            file_size_mb = path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.max_size_mb:
                return (
                    f"Error: File too large ({file_size_mb:.2f} MB). "
                    f"Maximum: {self.max_size_mb} MB"
                )

            # Read file
            content = path.read_text(encoding="utf-8")
            return content

        except UnicodeDecodeError:
            return f"Error: File is not a text file or has invalid encoding: {file_path}"
        except Exception as e:
            return self._handle_error(e)


@registry.register("filesystem", needs_approval=False, is_read_only=True)
class ListDirectoryTool(ReadOnlyTool):
    """List contents of a directory."""

    name: str = "list_directory"
    description: str = (
        "List files and directories in a given path. "
        "Input should be a directory path relative to the workspace. "
        "Returns a formatted list of entries."
    )

    show_hidden: bool = Field(
        default=False,
        description="Whether to show hidden files/directories",
    )

    def _run(self, directory_path: str = ".") -> str:
        """
        List directory contents.

        Args:
            directory_path: Path to directory to list

        Returns:
            Formatted directory listing
        """
        try:
            path = Path(self.workspace_path) / directory_path
            path = path.resolve()

            if not path.exists():
                return f"Error: Directory not found: {directory_path}"

            if not path.is_dir():
                return f"Error: Path is not a directory: {directory_path}"

            # Get entries
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name))

            # Filter hidden files if needed
            if not self.show_hidden:
                entries = [e for e in entries if not e.name.startswith(".")]

            # Format output
            lines = [f"Contents of {directory_path}:", ""]

            for entry in entries:
                prefix = "[DIR] " if entry.is_dir() else "[FILE]"
                lines.append(f"{prefix} {entry.name}")

            if not entries:
                lines.append("(empty directory)")

            return "\n".join(lines)

        except Exception as e:
            return self._handle_error(e)


@registry.register("filesystem", needs_approval=False, is_read_only=True)
class FindFilesTool(ReadOnlyTool):
    """Find files matching a pattern."""

    name: str = "find_files"
    description: str = (
        "Find files matching a glob pattern. "
        "Input should be a glob pattern (e.g., '**/*.py' for all Python files). "
        "Returns a list of matching file paths."
    )

    max_results: int = Field(
        default=100,
        description="Maximum number of results to return",
    )

    def _run(self, pattern: str) -> str:
        """
        Find files matching pattern.

        Args:
            pattern: Glob pattern to match

        Returns:
            List of matching files
        """
        try:
            path = Path(self.workspace_path)

            # Find matching files
            matches = list(path.glob(pattern))

            # Filter to files only and limit results
            files = [m for m in matches if m.is_file()][: self.max_results]

            if not files:
                return f"No files found matching pattern: {pattern}"

            # Format output
            lines = [f"Found {len(files)} file(s) matching '{pattern}':", ""]

            for file in files:
                rel_path = file.relative_to(path)
                lines.append(f"  {rel_path}")

            if len(matches) > self.max_results:
                lines.append(f"\n(showing first {self.max_results} results)")

            return "\n".join(lines)

        except Exception as e:
            return self._handle_error(e)
