"""Configuration loader utilities."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_env_file(env_file: str | None = None) -> bool:
    """
    Load environment variables from .env file.

    Args:
        env_file: Path to .env file. If None, searches for .env in current directory.

    Returns:
        True if .env file was loaded, False otherwise.
    """
    if env_file is None:
        # Search for .env file in current directory and parent directories
        current_dir = Path.cwd()
        for parent in [current_dir] + list(current_dir.parents):
            env_path = parent / ".env"
            if env_path.exists():
                env_file = str(env_path)
                break

    if env_file and Path(env_file).exists():
        load_dotenv(env_file, override=True)
        return True

    return False


def ensure_data_directories(base_path: str = "./data") -> None:
    """
    Ensure data directories exist.

    Args:
        base_path: Base path for data storage.
    """
    data_path = Path(base_path)
    (data_path / "vector_store").mkdir(parents=True, exist_ok=True)
    (data_path / "checkpoints").mkdir(parents=True, exist_ok=True)
    (data_path / "cache").mkdir(parents=True, exist_ok=True)


def validate_api_keys(provider: str = "anthropic") -> None:
    """
    Validate that required API keys are set.

    Args:
        provider: LLM provider to validate keys for.

    Raises:
        ValueError: If required API keys are missing.
    """
    if provider == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise ValueError(
                "ANTHROPIC_API_KEY not set. Please set it in .env file or environment."
            )
    elif provider == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError(
                "OPENAI_API_KEY not set. Please set it in .env file or environment."
            )
    else:
        raise ValueError(f"Unknown provider: {provider}")
