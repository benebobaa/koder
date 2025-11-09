"""Custom exception classes."""


class KoderError(Exception):
    """Base exception for Koder."""

    pass


class ConfigurationError(KoderError):
    """Configuration-related errors."""

    pass


class ToolError(KoderError):
    """Tool execution errors."""

    pass


class AgentError(KoderError):
    """Agent execution errors."""

    pass


class LLMError(KoderError):
    """LLM-related errors."""

    pass


class ValidationError(KoderError):
    """Input validation errors."""

    pass
