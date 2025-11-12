"""LLM factory for multi-provider support."""

from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import ConfigurableField
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI

from koder.config.settings import LLMSettings
from koder.llm.providers.moonshot import create_moonshot_llm


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
        # If configurability is not needed, create only the requested provider
        if not configurable:
            if settings.provider == "anthropic":
                return ChatAnthropic(
                    model=settings.anthropic_model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    api_key=settings.anthropic_api_key,
                )
            elif settings.provider == "openai":
                return ChatOpenAI(
                    model=settings.openai_model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    api_key=settings.openai_api_key,
                )
            elif settings.provider == "deepseek":
                return ChatDeepSeek(
                    model=settings.deepseek_model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    api_key=settings.deepseek_api_key,
                )
            elif settings.provider == "moonshot":
                return create_moonshot_llm(
                    model=settings.moonshot_model,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens,
                    api_key=settings.moonshot_api_key,
                )
            else:
                raise ValueError(f"Unknown provider: {settings.provider}")

        # For configurable mode, create all providers
        anthropic_llm = ChatAnthropic(
            model=settings.anthropic_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.anthropic_api_key,
        )

        openai_llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.openai_api_key,
        )

        deepseek_llm = ChatDeepSeek(
            model=settings.deepseek_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.deepseek_api_key,
        )

        moonshot_llm = create_moonshot_llm(
            model=settings.moonshot_model,
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            api_key=settings.moonshot_api_key,
        )

        # Select base LLM based on configured provider
        if settings.provider == "anthropic":
            base_llm = anthropic_llm
        elif settings.provider == "openai":
            base_llm = openai_llm
        elif settings.provider == "deepseek":
            base_llm = deepseek_llm
        elif settings.provider == "moonshot":
            base_llm = moonshot_llm
        else:
            raise ValueError(f"Unknown provider: {settings.provider}")

        # Add configurability
        llm = base_llm.configurable_alternatives(
            ConfigurableField(id="llm_provider"),
            default_key=settings.provider,
            anthropic=anthropic_llm,
            openai=openai_llm,
            deepseek=deepseek_llm,
            moonshot=moonshot_llm,
        )
        return llm

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

    @staticmethod
    def create_moonshot_llm(
        model: str = "moonshot-v1-8k",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        api_key: Optional[str] = None,
    ) -> ChatOpenAI:
        """Create Moonshot LLM directly."""
        return create_moonshot_llm(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )


def get_llm_config(provider: str, thread_id: Optional[str] = None) -> dict:
    """
    Generate LLM runtime configuration.

    Args:
        provider: Provider name ('anthropic', 'openai', 'deepseek', or 'moonshot')
        thread_id: Optional thread ID for checkpointing

    Returns:
        Configuration dictionary
    """
    config = {"configurable": {"llm_provider": provider}}

    if thread_id:
        config["configurable"]["thread_id"] = thread_id

    return config
