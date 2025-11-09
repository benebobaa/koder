"""LLM factory for multi-provider support."""

from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import ConfigurableField
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from koder.config.settings import LLMSettings


class LLMFactory:
    """Factory for creating LLM instances with runtime provider switching."""

    @staticmethod
    def create_llm(
        settings: LLMSettings,
        configurable: bool = True,
    ) -> BaseChatModel:
        """
        Create LLM with optional runtime provider switching.

        Args:
            settings: LLM configuration settings
            configurable: Whether to enable runtime provider switching

        Returns:
            Configured LLM instance
        """
        # Create Anthropic LLM
        anthropic_llm = ChatAnthropic(
            model=settings.anthropic_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.anthropic_api_key,
        )

        # Create OpenAI LLM
        openai_llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )

        # Create DeepSeek LLM
        deepseek_llm = ChatDeepSeek(
            model=settings.deepseek_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.deepseek_api_key,
        )

        # Select default based on configured provider
        if settings.provider == "anthropic":
            base_llm = anthropic_llm
        elif settings.provider == "deepseek":
            base_llm = deepseek_llm
        else:
            base_llm = openai_llm

        # Add configurability if requested
        if configurable:
            llm = base_llm.configurable_alternatives(
                ConfigurableField(id="llm_provider"),
                default_key=settings.provider,
                anthropic=anthropic_llm,
                openai=openai_llm,
                deepseek=deepseek_llm,
            )
            return llm

        return base_llm

    @staticmethod
    def create_anthropic_llm(
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
    ) -> ChatAnthropic:
        """Create Anthropic LLM directly."""
        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    @staticmethod
    def create_openai_llm(
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
    ) -> ChatOpenAI:
        """Create OpenAI LLM directly."""
        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    @staticmethod
    def create_deepseek_llm(
        model: str = "deepseek-chat",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
    ) -> ChatDeepSeek:
        """Create DeepSeek LLM directly."""
        return ChatDeepSeek(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )


def get_llm_config(provider: str, thread_id: Optional[str] = None) -> dict:
    """
    Generate LLM runtime configuration.

    Args:
        provider: Provider name ('anthropic', 'openai', or 'deepseek')
        thread_id: Optional thread ID for checkpointing

    Returns:
        Configuration dictionary
    """
    config = {"configurable": {"llm_provider": provider}}

    if thread_id:
        config["configurable"]["thread_id"] = thread_id

    return config
