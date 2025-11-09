"""DeepSeek provider configuration."""

from typing import Optional

from langchain_deepseek import ChatDeepSeek

# Available DeepSeek models
DEEPSEEK_CHAT = "deepseek-chat"  # V3 - supports tool calling
DEEPSEEK_REASONER = "deepseek-reasoner"  # R1 - reasoning model (no tool support)

# Model capabilities
MODEL_CONTEXT_WINDOWS = {
    DEEPSEEK_CHAT: 64_000,
    DEEPSEEK_REASONER: 64_000,
}

MODEL_MAX_OUTPUT_TOKENS = {
    DEEPSEEK_CHAT: 8_192,
    DEEPSEEK_REASONER: 8_192,
}


def create_deepseek_llm(
    model: str = DEEPSEEK_CHAT,
    temperature: float = 0.7,
    max_tokens: int = 4096,
    api_key: Optional[str] = None,
) -> ChatDeepSeek:
    """
    Create a DeepSeek LLM instance.

    Args:
        model: DeepSeek model to use
        temperature: Temperature for sampling
        max_tokens: Maximum tokens to generate
        api_key: DeepSeek API key

    Returns:
        Configured ChatDeepSeek instance
    """
    return ChatDeepSeek(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )


def get_model_info(model: str) -> dict:
    """Get information about a DeepSeek model."""
    return {
        "model": model,
        "context_window": MODEL_CONTEXT_WINDOWS.get(model, 64_000),
        "max_output_tokens": MODEL_MAX_OUTPUT_TOKENS.get(model, 8_192),
    }
