"""Filesystem write tools."""

from pathlib import Path

from pydantic import Field

from koder.tools.base import KoderTool, WriteToolMixin
from koder.tools.registry import registry


@registry.register("filesystem", needs_approval=True, is_read_only=False)
class WriteFileTool(WriteToolMixin, KoderTool):
    """Write content to a file."""

    name: str = "write_file"
    description: str = (
        "Write content to a file. Creates the file if it doesn't exist. "
        "Input should be a JSON object with 'file_path' and 'content' keys."
    )

    create_dirs: bool = Field(
        default=True,
        description="Whether to create parent directories if they don't exist",
    )

    def _run(self, file_path: str, content: str) -> str:
        """
        Write content to file.

        Args:
            file_path: Path to file to write
            content: Content to write

        Returns:
            Success message or error
        """
        try:
            # Validate path is within workspace
            self.validate_write_path(file_path)

            path = Path(self.workspace_path) / file_path
            path = path.resolve()

            # Create parent directories if needed
            if self.create_dirs:
                path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            path.write_text(content, encoding="utf-8")

            return f"Successfully wrote {len(content)} characters to {file_path}"

        except Exception as e:
            return self._handle_error(e)


@registry.register("filesystem", needs_approval=True, is_read_only=False)
class AppendToFileTool(WriteToolMixin, KoderTool):
    """Append content to a file."""

    name: str = "append_to_file"
    description: str = (
        "Append content to an existing file. "
        "Input should be a JSON object with 'file_path' and 'content' keys."
    )

    def _run(self, file_path: str, content: str) -> str:
        """
        Append content to file.

        Args:
            file_path: Path to file
            content: Content to append

        Returns:
            Success message or error
        """
        try:
            # Validate path
            self.validate_write_path(file_path)

            path = Path(self.workspace_path) / file_path
            path = path.resolve()

            if not path.exists():
                return f"Error: File not found: {file_path}"

            # Append content
            with path.open("a", encoding="utf-8") as f:
                f.write(content)

            return f"Successfully appended {len(content)} characters to {file_path}"

        except Exception as e:
            return self._handle_error(e)
