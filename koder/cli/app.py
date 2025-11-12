"""Main CLI application."""

from typing import Optional

import typer
from rich.panel import Panel

from koder.cli.ui.console import console
from koder.config.loader import load_env_file
from koder.observability.logging import configure_logging

# Create main Typer app
app = typer.Typer(
    name="koder",
    help="Koder: AI-powered code assistant using LangGraph",
    add_completion=True,
    rich_markup_mode="rich",
)

# Register command modules
from koder.cli.commands import chat, task, embedding

app.add_typer(chat.app, name="chat", help="Interactive chat mode")
app.add_typer(task.app, name="task", help="Execute one-off tasks")
app.add_typer(embedding.app, name="embedding", help="Manage semantic code embeddings")


@app.callback()
def main(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose logging",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output",
    ),
    env_file: Optional[str] = typer.Option(
        None,
        "--env-file",
        "-e",
        help="Path to .env file",
    ),
):
    """
    Koder: AI-powered code assistant.

    A CLI tool powered by LangGraph for intelligent code assistance.
    """
    # Load environment variables
    load_env_file(env_file)

    # Configure logging
    log_level = "DEBUG" if verbose else "WARNING" if quiet else "INFO"
    configure_logging(level=log_level)


@app.command()
def version():
    """Show version information."""
    console.print(
        Panel(
            "[bold cyan]Koder[/bold cyan] v0.1.0\n"
            "AI-powered code assistant\n"
            "Built with LangGraph and LangChain",
            title="Version",
            border_style="cyan",
        )
    )


@app.command()
def info():
    """Show system information."""
    from koder.config.settings import get_settings

    settings = get_settings()

    # Get the correct model based on provider
    if settings.llm.provider == "anthropic":
        model = settings.llm.anthropic_model
    elif settings.llm.provider == "openai":
        model = settings.llm.openai_model
    elif settings.llm.provider == "deepseek":
        model = settings.llm.deepseek_model
    elif settings.llm.provider == "moonshot":
        model = settings.llm.moonshot_model
    else:
        model = "unknown"

    info_text = f"""
[bold]Configuration:[/bold]
  LLM Provider: {settings.llm.provider}
  Model: {model}
  Temperature: {settings.llm.temperature}
  Max Tokens: {settings.llm.max_tokens}

[bold]Storage:[/bold]
  Vector Store: {settings.storage.vector_store_path}
  Checkpoints: {settings.storage.checkpoint_path}
  Cache: {settings.storage.cache_path}

[bold]Observability:[/bold]
  LangSmith Tracing: {settings.observability.langsmith_tracing}
  Log Level: {settings.observability.log_level}
"""

    console.print(Panel(info_text, title="System Info", border_style="blue"))


if __name__ == "__main__":
    app()
