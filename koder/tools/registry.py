"""Tool registry for managing agent tools."""

from typing import Optional

from langchain_core.tools import BaseTool

# Tool categorization constants for planning mode
READ_ONLY_CATEGORIES = {"code", "git.read"}
WRITE_CATEGORIES = {"filesystem.write", "git.write"}

# Tools that require user approval before execution
APPROVAL_REQUIRED_TOOLS = {
    "WriteFileTool",
    "AppendToFileTool",
    "DeleteFileTool",  # Future
    "GitCommitTool",  # Future
    "GitPushTool",  # Future
    "RunCommandTool",  # Future
}

# Tools that are read-only and safe to execute immediately
READ_ONLY_TOOLS = {
    "ReadFileTool",
    "ListDirectoryTool",
    "FindFilesTool",
    "ParsePythonTool",
    "GitStatusTool",
    "GitDiffTool",
    "GitLogTool",
}


class ToolRegistry:
    """Central registry for agent tools with category and permission support."""

    def __init__(self):
        """Initialize tool registry."""
        self._tools: dict[str, type[BaseTool]] = {}
        self._categories: dict[str, list[str]] = {}
        self._instances: dict[str, BaseTool] = {}
        self._tool_metadata: dict[str, dict] = {}  # Stores needs_approval, is_read_only, etc.

    def register(self, category: str = "general", needs_approval: bool = False, is_read_only: bool = False):
        """
        Decorator for registering tools with metadata.

        Args:
            category: Tool category for organization
            needs_approval: Whether tool requires user approval
            is_read_only: Whether tool only reads (no modifications)

        Returns:
            Decorator function

        Example:
            @registry.register("filesystem", needs_approval=True)
            class MyWriteTool(BaseTool):
                ...
        """

        def decorator(tool_class: type[BaseTool]):
            tool_name = tool_class.__name__

            # Register tool class
            self._tools[tool_name] = tool_class

            # Add to category
            if category not in self._categories:
                self._categories[category] = []
            self._categories[category].append(tool_name)

            # Store metadata
            self._tool_metadata[tool_name] = {
                "category": category,
                "needs_approval": needs_approval,
                "is_read_only": is_read_only,
            }

            return tool_class

        return decorator

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool instance by name.

        Args:
            name: Tool class name

        Returns:
            Tool instance or None if not found
        """
        if name in self._instances:
            return self._instances[name]

        if name in self._tools:
            # Create and cache instance
            instance = self._tools[name]()
            self._instances[name] = instance
            return instance

        return None

    def get_tools(
        self,
        categories: Optional[list[str]] = None,
        names: Optional[list[str]] = None,
    ) -> list[BaseTool]:
        """
        Get tool instances, optionally filtered by category or name.

        Args:
            categories: List of categories to include (None = all)
            names: Specific tool names to include (None = all)

        Returns:
            List of tool instances
        """
        if names:
            # Get specific tools by name
            tools = []
            for name in names:
                tool = self.get_tool(name)
                if tool:
                    tools.append(tool)
            return tools

        if categories:
            # Get tools by categories
            tool_names = []
            for category in categories:
                tool_names.extend(self._categories.get(category, []))
        else:
            # Get all tools
            tool_names = list(self._tools.keys())

        # Create instances
        return [self.get_tool(name) for name in tool_names if self.get_tool(name)]

    def list_categories(self) -> list[str]:
        """
        List all registered categories.

        Returns:
            List of category names
        """
        return list(self._categories.keys())

    def list_tools(self, category: Optional[str] = None) -> list[str]:
        """
        List registered tool names.

        Args:
            category: Optional category to filter by

        Returns:
            List of tool names
        """
        if category:
            return self._categories.get(category, [])
        return list(self._tools.keys())

    def is_read_only_tool(self, name: str) -> bool:
        """
        Check if a tool is read-only.

        Args:
            name: Tool name (class name)

        Returns:
            True if tool is read-only or in READ_ONLY_TOOLS constant
        """
        # Check metadata first
        if name in self._tool_metadata:
            if self._tool_metadata[name].get("is_read_only"):
                return True

        # Fallback to constant
        return name in READ_ONLY_TOOLS

    def needs_approval(self, name: str) -> bool:
        """
        Check if a tool requires user approval before execution.

        Args:
            name: Tool name (class name)

        Returns:
            True if tool needs approval
        """
        # Check metadata first
        if name in self._tool_metadata:
            if self._tool_metadata[name].get("needs_approval"):
                return True

        # Fallback to constant
        return name in APPROVAL_REQUIRED_TOOLS

    def get_read_only_tools(self) -> list[BaseTool]:
        """
        Get all read-only tools.

        Returns:
            List of read-only tool instances
        """
        read_only_names = [
            name for name in self._tools.keys()
            if self.is_read_only_tool(name)
        ]
        return [self.get_tool(name) for name in read_only_names if self.get_tool(name)]

    def get_write_tools(self) -> list[BaseTool]:
        """
        Get all write tools (not read-only).

        Returns:
            List of write tool instances
        """
        write_names = [
            name for name in self._tools.keys()
            if not self.is_read_only_tool(name)
        ]
        return [self.get_tool(name) for name in write_names if self.get_tool(name)]

    def get_approval_required_tools(self) -> list[BaseTool]:
        """
        Get all tools that require user approval.

        Returns:
            List of approval-required tool instances
        """
        approval_names = [
            name for name in self._tools.keys()
            if self.needs_approval(name)
        ]
        return [self.get_tool(name) for name in approval_names if self.get_tool(name)]

    def clear(self) -> None:
        """Clear all registered tools and instances."""
        self._tools.clear()
        self._categories.clear()
        self._instances.clear()
        self._tool_metadata.clear()


# Global registry instance
registry = ToolRegistry()
