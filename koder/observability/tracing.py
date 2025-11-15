"""LangSmith tracing configuration."""

import os

from langsmith import Client


def configure_tracing(
    api_key: str | None = None,
    project: str = "koder",
    enabled: bool = True,
) -> Client | None:
    """
    Configure LangSmith tracing.

    Args:
        api_key: LangSmith API key (uses env var if not provided)
        project: Project name for traces
        enabled: Whether to enable tracing

    Returns:
        LangSmith client if enabled, None otherwise
    """
    if not enabled:
        os.environ["LANGSMITH_TRACING"] = "false"
        return None

    # Set environment variables for LangChain
    if api_key:
        os.environ["LANGSMITH_API_KEY"] = api_key
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = project

    # Create and return client
    try:
        client = Client()
        return client
    except Exception:
        # Tracing configuration failed, disable it
        os.environ["LANGSMITH_TRACING"] = "false"
        return None


def disable_tracing() -> None:
    """Disable LangSmith tracing."""
    os.environ["LANGSMITH_TRACING"] = "false"


def enable_tracing(project: str = "koder") -> None:
    """
    Enable LangSmith tracing.

    Args:
        project: Project name for traces
    """
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_PROJECT"] = project
