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

    # Core settings
    enabled: bool = Field(
        default=True,
        description="Enable/disable embedding system entirely"
    )
    mode: Literal["off", "lexical", "primary", "reranker"] = Field(
        default="reranker",
        description=(
            "Retrieval mode: "
            "'off' = no retrieval, "
            "'lexical' = keyword search only (free), "
            "'primary' = embeddings only (current behavior), "
            "'reranker' = lexical first-pass then embedding re-rank (recommended)"
        )
    )

    # API settings
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")
    model: str = "models/text-embedding-004"
    dimension: int = Field(
        default=768,
        description="Embedding dimensions (768 or 512 for cost savings, 3072 max)"
    )

    # Cost controls
    max_monthly_cost_usd: float = Field(
        default=50.0,
        description="Maximum monthly budget for embedding API calls in USD"
    )
    max_daily_api_calls: int = Field(
        default=1000,
        description="Maximum API calls per day to prevent runaway costs"
    )

    # Caching
    cache_ttl_hours: int = Field(
        default=24,
        description="How long to cache embedding results (hours)"
    )
    cache_enabled: bool = Field(
        default=True,
        description="Enable persistent caching of embeddings"
    )

    # File watching
    watch_files: bool = Field(
        default=True,
        description="Auto-enable file watching to keep index fresh"
    )
    watch_debounce_seconds: int = Field(
        default=2,
        description="Debounce delay for file change detection"
    )

    # Retrieval settings
    lexical_top_k: int = Field(
        default=20,
        description="Number of lexical results for re-ranking mode"
    )
    final_top_k: int = Field(
        default=5,
        description="Final number of results to return"
    )

    # A/B testing
    ab_test_enabled: bool = Field(
        default=False,
        description="Enable A/B testing to compare retrieval modes"
    )
    ab_test_ratio: float = Field(
        default=0.5,
        description="Ratio of tasks using embeddings (0.0-1.0) in A/B test"
    )

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


class WebSearchSettings(BaseSettings):
    """Web search configuration."""

    backend: Literal["duckduckgo", "tavily", "brave"] = Field(
        default="duckduckgo", description="Web search backend to use"
    )
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")
    brave_api_key: str = Field(default="", alias="BRAVE_API_KEY")
    max_results: int = Field(
        default=5, description="Maximum number of search results to return"
    )
    safe_search: bool = Field(default=True, description="Enable safe search filtering")

    model_config = SettingsConfigDict(
        env_prefix="WEB_SEARCH_",
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
    web_search: WebSearchSettings = Field(default_factory=WebSearchSettings)

    # Agent settings
    max_iterations: int = 10
    timeout_seconds: int = 300
    recursion_limit: int = Field(
        default=100, description="Maximum recursion depth for LangGraph execution"
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
