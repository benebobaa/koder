"""Kimi Moonshot provider configuration."""

import os
from typing import Optional

from langchain_openai import ChatOpenAI

# Available Moonshot models
MOONSHOT_V1_8K = "moonshot-v1-8k"
MOONSHOT_V1_32K = "moonshot-v1-32k"
MOONSHOT_V1_128K = "moonshot-v1-128k"

# K2 Models
KIMI_K2_0711_PREVIEW = "kimi-k2-0711-preview"
KIMI_K2_0905_PREVIEW = "kimi-k2-0905-preview"
KIMI_K2_TURBO_PREVIEW = "kimi-k2-turbo-preview"
KIMI_K2_THINKING = "kimi-k2-thinking"
KIMI_K2_THINKING_TURBO = "kimi-k2-thinking-turbo"

# Model capabilities
MODEL_CONTEXT_WINDOWS = {
    # V1 Models
    MOONSHOT_V1_8K: 8_192,
    MOONSHOT_V1_32K: 32_768,
    MOONSHOT_V1_128K: 131_072,

    # K2 Models
    KIMI_K2_0711_PREVIEW: 131_072,      # Context length 128k
    KIMI_K2_0905_PREVIEW: 262_144,      # Context length 256k
    KIMI_K2_TURBO_PREVIEW: 262_144,     # Context length 256k, high-speed
    KIMI_K2_THINKING: 262_144,          # Context length 256k, reasoning model
    KIMI_K2_THINKING_TURBO: 262_144,    # Context length 256k, thinking + high-speed
}

MODEL_MAX_OUTPUT_TOKENS = {
    # V1 Models
    MOONSHOT_V1_8K: 8_192,
    MOONSHOT_V1_32K: 32_768,
    MOONSHOT_V1_128K: 65_536,

    # K2 Models
    KIMI_K2_0711_PREVIEW: 65_536,
    KIMI_K2_0905_PREVIEW: 65_536,
    KIMI_K2_TURBO_PREVIEW: 65_536,
    KIMI_K2_THINKING: 65_536,
    KIMI_K2_THINKING_TURBO: 65_536,
}


def create_moonshot_llm(
    model: str = MOONSHOT_V1_8K,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> ChatOpenAI:
    """
    Create a Kimi Moonshot LLM instance using OpenAI-compatible API.

    Args:
        model: Moonshot model to use
        temperature: Temperature for sampling
        max_tokens: Maximum tokens to generate
        api_key: Moonshot API key

    Returns:
        Configured ChatOpenAI instance with Moonshot API
    """
    # Use provided API key or fall back to environment variable
    if api_key is None:
        api_key = os.getenv("MOONSHOT_API_KEY")

    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
        base_url="https://api.moonshot.ai/v1",
    )


def get_model_info(model: str) -> dict:
    """Get information about a Moonshot model."""
    return {
        "model": model,
        "context_window": MODEL_CONTEXT_WINDOWS.get(model, 8_192),
        "max_output_tokens": MODEL_MAX_OUTPUT_TOKENS.get(model, 8_192),
    }