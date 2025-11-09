"""Chat command for interactive sessions."""

import uuid
from typing import Optional

import typer
from langchain_core.messages import HumanMessage

from koder.agent.checkpoints import get_checkpoint_config, get_checkpointer
from koder.agent.graph import create_agent
from koder.agent.state import create_initial_state
from koder.cli.ui.console import console, print_error, print_info, print_success
from koder.cli.ui.formatters import format_message
from koder.cli.ui.prompts import create_session, get_user_input
from koder.config.settings import get_settings
from koder.llm.factory import LLMFactory
from koder.observability.logging import get_logger
from koder.observability.tracing import configure_tracing
from koder.tools.code.parser import ParsePythonTool
from koder.tools.filesystem.read import FindFilesTool, ListDirectoryTool, ReadFileTool
from koder.tools.filesystem.write import AppendToFileTool, WriteFileTool
from koder.tools.git.status import GitDiffTool, GitLogTool, GitStatusTool

app = typer.Typer()
logger = get_logger(__name__)


@app.command()
def start(
    thread_id: Optional[str] = typer.Option(
        None,
        "--thread",
        "-t",
        help="Thread ID for session (creates new if not provided)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider (anthropic or openai)",
    ),
    workspace: str = typer.Option(
        ".",
        "--workspace",
        "-w",
        help="Workspace directory",
    ),
    mode: str = typer.Option(
        "auto",
        "--mode",
        "-m",
        help="Execution mode: auto (analyze complexity), quick (direct execution), plan (always plan)",
    ),
):
    """Start an interactive chat session with intelligent planning."""
    settings = get_settings()

    # Override provider if specified
    if provider:
        settings.llm.provider = provider

    # Configure tracing
    if settings.observability.langsmith_tracing:
        configure_tracing(
            api_key=settings.observability.langsmith_api_key,
            project=settings.observability.langsmith_project,
        )

    # Create thread ID if not provided
    if not thread_id:
        thread_id = f"chat-{uuid.uuid4().hex[:8]}"

    print_info(f"Starting chat session (thread: {thread_id})")
    print_info(f"Provider: {settings.llm.provider}")
    print_info(f"Mode: {mode}")
    print_info(f"Workspace: {workspace}")
    print_info("Type 'exit' or 'quit' to end the session\n")

    # Create LLM
    llm = LLMFactory.create_llm(settings.llm, configurable=True)

    # Create tools
    tools = [
        ReadFileTool(workspace_path=workspace),
        ListDirectoryTool(workspace_path=workspace),
        FindFilesTool(workspace_path=workspace),
        WriteFileTool(workspace_path=workspace),
        AppendToFileTool(workspace_path=workspace),
        ParsePythonTool(workspace_path=workspace),
        GitStatusTool(workspace_path=workspace),
        GitDiffTool(workspace_path=workspace),
        GitLogTool(workspace_path=workspace),
    ]

    # Create agent with checkpointing and planning support
    agent = create_agent(llm, tools, settings.storage.checkpoint_path, mode=mode)

    # Create prompt session
    session = create_session()

    # Chat loop
    try:
        while True:
            # Get user input
            user_input = get_user_input(session, "You: ")

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye"]:
                print_success("Goodbye!")
                break

            # Create message
            message = HumanMessage(content=user_input)

            # Run agent
            try:
                config = get_checkpoint_config(thread_id)

                # Stream agent execution
                console.print()
                for event in agent.stream(
                    {"messages": [message]},
                    config=config,
                ):
                    # Handle different event types
                    for node, output in event.items():
                        if "messages" in output:
                            for msg in output["messages"]:
                                format_message(msg)

                console.print()

            except Exception as e:
                print_error(f"Error: {str(e)}")
                logger.error("chat_error", error=str(e), exc_info=True)

    except KeyboardInterrupt:
        print_info("\nSession interrupted")
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        logger.error("chat_fatal", error=str(e), exc_info=True)


@app.command()
def list_threads():
    """List all chat threads."""
    from koder.agent.checkpoints import ThreadManager
    from koder.config.settings import get_settings

    settings = get_settings()

    # Get thread manager
    thread_mgr = ThreadManager(
        settings.storage.checkpoint_path.replace(".db", "_threads.db")
    )

    threads = thread_mgr.list_threads()

    if not threads:
        print_info("No chat threads found")
        return

    console.print(f"\n[bold]Chat Threads ({len(threads)}):[/bold]\n")

    for thread in threads:
        console.print(f"  [cyan]{thread['thread_id']}[/cyan]")
        if thread["title"]:
            console.print(f"    Title: {thread['title']}")
        console.print(f"    Created: {thread['created_at']}")
        console.print(f"    Updated: {thread['updated_at']}")
        console.print()


if __name__ == "__main__":
    app()
