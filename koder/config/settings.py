"""Configuration settings for Koder using Pydantic Settings."""

from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMSettings(BaseSettings):
    """LLM provider configuration."""

    provider: Literal["anthropic", "openai", "deepseek"] = "anthropic"
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    deepseek_api_key: str = Field(default="", alias="DEEPSEEK_API_KEY")
    anthropic_model: str = "claude-sonnet-4-5-20250929"
    openai_model: str = "gpt-4-turbo-preview"
    deepseek_model: str = "deepseek-chat"
    temperature: float = 0.7
    max_tokens: int = 4096

    model_config = SettingsConfigDict(
        env_prefix="LLM_",
        case_sensitive=False,
    )


class EmbeddingsSettings(BaseSettings):
    """Embeddings configuration."""

    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    model: str = "models/text-embedding-004"
    dimension: int = 768

    model_config = SettingsConfigDict(
        env_prefix="EMBEDDINGS_",
        case_sensitive=False,
    )


class ObservabilitySettings(BaseSettings):
    """Observability and monitoring configuration."""

    langsmith_tracing: bool = True
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = "koder"
    log_level: str = "INFO"
    json_logs: bool = False

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
    )


class StorageSettings(BaseSettings):
    """Storage paths and configuration."""

    vector_store_path: str = "./data/vector_store"
    checkpoint_path: str = "./data/checkpoints/checkpoints.db"
    cache_path: str = "./data/cache"

    model_config = SettingsConfigDict(
        case_sensitive=False,
    )


class MCPSettings(BaseSettings):
    """MCP (Model Context Protocol) configuration."""

    server_url: Optional[str] = None
    enabled: bool = False

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        case_sensitive=False,
    )


class Settings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Nested settings
    llm: LLMSettings = Field(default_factory=LLMSettings)
    embeddings: EmbeddingsSettings = Field(default_factory=EmbeddingsSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)
    storage: StorageSettings = Field(default_factory=StorageSettings)
    mcp: MCPSettings = Field(default_factory=MCPSettings)

    # Agent settings
    max_iterations: int = 10
    timeout_seconds: int = 300
    recursion_limit: int = Field(
        default=100,
        description="Maximum recursion depth for LangGraph execution"
    )


# Singleton settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Force reload settings from environment."""
    global _settings
    _settings = Settings()
    return _settings
