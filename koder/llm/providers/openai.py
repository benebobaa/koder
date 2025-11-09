"""OpenAI GPT provider configuration."""

from typing import Optional

from langchain_openai import ChatOpenAI

# Available OpenAI models
GPT_4_TURBO = "gpt-4-turbo-preview"
GPT_4 = "gpt-4"
GPT_4O = "gpt-4o"
GPT_35_TURBO = "gpt-3.5-turbo"

# Model capabilities
MODEL_CONTEXT_WINDOWS = {
    GPT_4_TURBO: 128_000,
    GPT_4: 8_192,
    GPT_4O: 128_000,
    GPT_35_TURBO: 16_385,
}

MODEL_MAX_OUTPUT_TOKENS = {
    GPT_4_TURBO: 4_096,
    GPT_4: 4_096,
    GPT_4O: 4_096,
    GPT_35_TURBO: 4_096,
}


def create_openai_llm(
    model: str = GPT_4_TURBO,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> ChatOpenAI:
    """
    Create an OpenAI LLM instance.

    Args:
        model: OpenAI model to use
        temperature: Temperature for sampling
        max_tokens: Maximum tokens to generate
        api_key: OpenAI API key

    Returns:
        Configured ChatOpenAI instance
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )


def get_model_info(model: str) -> dict:
    """Get information about an OpenAI model."""
    return {
        "model": model,
        "context_window": MODEL_CONTEXT_WINDOWS.get(model, 8_192),
        "max_output_tokens": MODEL_MAX_OUTPUT_TOKENS.get(model, 4_096),
    }
