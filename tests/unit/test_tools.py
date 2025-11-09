"""Unit tests for tools."""

import pytest

from koder.tools.filesystem.read import ListDirectoryTool, ReadFileTool
from koder.tools.registry import ToolRegistry, registry


class TestToolRegistry:
    """Tests for tool registry."""

    def test_register_tool(self):
        """Test tool registration."""
        test_registry = ToolRegistry()

        @test_registry.register("test")
        class TestTool:
            pass

        assert "TestTool" in test_registry._tools
        assert "test" in test_registry._categories
        assert "TestTool" in test_registry._categories["test"]

    def test_get_tools_by_category(self):
        """Test getting tools by category."""
        # Import to ensure tools are registered
        from koder.tools.filesystem import read, write  # noqa

        # Use global registry that has tools registered
        tools = registry.get_tools(categories=["filesystem"])
        assert len(tools) > 0

    def test_list_categories(self):
        """Test listing categories."""
        # Load tools by importing
        from koder.tools.filesystem import read, write  # noqa
        from koder.tools.git import status  # noqa
        from koder.tools.code import parser  # noqa

        # Use global registry
        categories = registry.list_categories()
        assert "filesystem" in categories
        assert "git" in categories
        assert "code" in categories


class TestReadFileTool:
    """Tests for ReadFileTool."""

    def test_read_existing_file(self, test_workspace):
        """Test reading an existing file."""
        tool = ReadFileTool(workspace_path=str(test_workspace))
        result = tool._run("test.py")

        assert "def hello():" in result
        assert "Error" not in result

    def test_read_nonexistent_file(self, test_workspace):
        """Test reading a nonexistent file."""
        tool = ReadFileTool(workspace_path=str(test_workspace))
        result = tool._run("nonexistent.py")

        assert "Error" in result
        assert "not found" in result.lower()


class TestListDirectoryTool:
    """Tests for ListDirectoryTool."""

    def test_list_directory(self, test_workspace):
        """Test listing directory contents."""
        tool = ListDirectoryTool(workspace_path=str(test_workspace))
        result = tool._run(".")

        assert "test.py" in result
        assert "README.md" in result

    def test_list_nonexistent_directory(self, test_workspace):
        """Test listing nonexistent directory."""
        tool = ListDirectoryTool(workspace_path=str(test_workspace))
        result = tool._run("nonexistent")

        assert "Error" in result
