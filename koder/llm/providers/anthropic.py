"""Anthropic Claude provider configuration."""

from typing import Optional

from langchain_anthropic import ChatAnthropic

# Available Claude models
CLAUDE_OPUS = "claude-opus-4-20250514"
CLAUDE_SONNET = "claude-sonnet-4-5-20250929"
CLAUDE_HAIKU = "claude-haiku-4-20250917"

# Model capabilities
MODEL_CONTEXT_WINDOWS = {
    CLAUDE_OPUS: 200_000,
    CLAUDE_SONNET: 200_000,
    CLAUDE_HAIKU: 200_000,
}

MODEL_MAX_OUTPUT_TOKENS = {
    CLAUDE_OPUS: 16_384,
    CLAUDE_SONNET: 16_384,
    CLAUDE_HAIKU: 8_192,
}


def create_claude_llm(
    model: str = CLAUDE_SONNET,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> ChatAnthropic:
    """
    Create a Claude LLM instance.

    Args:
        model: Claude model to use
        temperature: Temperature for sampling
        max_tokens: Maximum tokens to generate
        api_key: Anthropic API key

    Returns:
        Configured ChatAnthropic instance
    """
    return ChatAnthropic(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )


def get_model_info(model: str) -> dict:
    """Get information about a Claude model."""
    return {
        "model": model,
        "context_window": MODEL_CONTEXT_WINDOWS.get(model, 200_000),
        "max_output_tokens": MODEL_MAX_OUTPUT_TOKENS.get(model, 4_096),
    }
