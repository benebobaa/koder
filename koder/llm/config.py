"""LLM configuration utilities."""

from typing import Literal

from koder.llm.providers import anthropic, deepseek, moonshot, openai

ProviderType = Literal["anthropic", "openai", "deepseek", "moonshot"]


def get_default_model(provider: ProviderType) -> str:
    """Get default model for a provider."""
    if provider == "anthropic":
        return anthropic.CLAUDE_SONNET
    elif provider == "openai":
        return openai.GPT_4_TURBO
    elif provider == "deepseek":
        return deepseek.DEEPSEEK_CHAT
    elif provider == "moonshot":
        return moonshot.MOONSHOT_V1_8K
    else:
        raise ValueError(f"Unknown provider: {provider}")


def get_model_info(provider: ProviderType, model: str | None = None) -> dict:
    """Get model information."""
    if model is None:
        model = get_default_model(provider)

    if provider == "anthropic":
        return anthropic.get_model_info(model)
    elif provider == "openai":
        return openai.get_model_info(model)
    elif provider == "deepseek":
        return deepseek.get_model_info(model)
    elif provider == "moonshot":
        return moonshot.get_model_info(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


def validate_model(provider: ProviderType, model: str) -> bool:
    """Validate that a model exists for a provider."""
    if provider == "anthropic":
        return model in anthropic.MODEL_CONTEXT_WINDOWS
    elif provider == "openai":
        return model in openai.MODEL_CONTEXT_WINDOWS
    elif provider == "deepseek":
        return model in deepseek.MODEL_CONTEXT_WINDOWS
    elif provider == "moonshot":
        return model in moonshot.MODEL_CONTEXT_WINDOWS
    else:
        return False
