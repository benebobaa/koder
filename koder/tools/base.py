"""Base tool classes and utilities."""

from abc import ABC
from typing import Any, Optional

from langchain_core.tools import BaseTool as LangChainBaseTool
from pydantic import Field


class KoderTool(LangChainBaseTool, ABC):
    """
    Base class for Koder tools.

    Extends LangChain's BaseTool with common functionality for Koder tools.
    """

    workspace_path: str = Field(
        default=".",
        description="Path to the workspace directory",
    )

    def _handle_error(self, error: Exception) -> str:
        """
        Handle tool execution errors.

        Args:
            error: The exception that occurred

        Returns:
            Error message string
        """
        error_message = f"Error in {self.name}: {str(error)}"
        return error_message

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """
        Default async implementation that calls sync version.

        Override this method if the tool has a true async implementation.
        """
        return self._run(*args, **kwargs)


class ReadOnlyTool(KoderTool, ABC):
    """Base class for read-only tools that don't modify state."""

    pass


class WriteToolMixin:
    """Mixin for tools that modify filesystem or state."""

    def validate_write_path(self, path: str, workspace: Optional[str] = None) -> bool:
        """
        Validate that a path is within the workspace.

        Args:
            path: Path to validate
            workspace: Workspace path (uses self.workspace_path if not provided)

        Returns:
            True if path is valid

        Raises:
            ValueError: If path is outside workspace
        """
        from pathlib import Path

        workspace_path = Path(workspace or self.workspace_path).resolve()
        target_path = Path(path).resolve()

        # Check if target is within workspace
        try:
            target_path.relative_to(workspace_path)
            return True
        except ValueError:
            raise ValueError(
                f"Path {path} is outside workspace {workspace_path}. "
                "Write operations are restricted to workspace."
            )
