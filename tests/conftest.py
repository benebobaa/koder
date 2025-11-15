"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from langgraph.checkpoint.sqlite import SqliteSaver

from koder.config.settings import Settings


@pytest.fixture(scope="session")
def test_settings():
    """Test settings with overrides."""
    return Settings(
        llm__provider="anthropic",
        llm__anthropic_api_key="test-key",
        llm__openai_api_key="test-key",
        llm__deepseek_api_key="test-key",
        storage__checkpoint_path=":memory:",
        storage__vector_store_path=":memory:",
        storage__cache_path=":memory:",
        observability__langsmith_tracing=False,
    )


@pytest.fixture
def mock_llm():
    """Mock LLM for testing."""
    llm = AsyncMock()
    llm.invoke = MagicMock(return_value=AIMessage(content="Test response from LLM"))
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="Test response from LLM"))
    llm.bind_tools = MagicMock(return_value=llm)
    return llm


@pytest.fixture
def memory_checkpointer():
    """In-memory checkpointer for tests."""
    return SqliteSaver.from_conn_string(":memory:")


@pytest.fixture
def test_workspace(tmp_path):
    """Create temporary workspace for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create some test files
    (workspace / "test.py").write_text("def hello():\n    print('Hello')\n")
    (workspace / "README.md").write_text("# Test Project\n")

    return workspace


@pytest.fixture
def sample_code():
    """Sample Python code for testing."""
    return """
def fibonacci(n):
    '''Calculate Fibonacci number.'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

class Calculator:
    '''Simple calculator class.'''

    def add(self, a, b):
        return a + b

    def subtract(self, a, b):
        return a - b
"""
