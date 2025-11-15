"""Task command for one-off executions."""

import uuid

import typer
from langchain_core.messages import HumanMessage

from koder.agent.checkpoints import get_checkpoint_config
from koder.agent.graph import create_agent
from koder.agent.state import create_initial_state
from koder.cli.ui.console import print_error, print_info, print_success
from koder.cli.ui.formatters import format_message
from koder.config.settings import get_settings
from koder.llm.factory import LLMFactory
from koder.observability.logging import get_logger
from koder.tools.code.parser import ParsePythonTool
from koder.tools.context import ContextRetrievalTool
from koder.tools.execution import BashTool, PythonTool
from koder.tools.filesystem.read import FindFilesTool, ListDirectoryTool, ReadFileTool
from koder.tools.filesystem.write import WriteFileTool
from koder.tools.git.status import GitDiffTool, GitStatusTool
from koder.tools.web import WebSearchTool

app = typer.Typer()
logger = get_logger(__name__)


@app.command()
def run(
    task: str = typer.Argument(..., help="Task description"),
    workspace: str = typer.Option(
        ".",
        "--workspace",
        "-w",
        help="Workspace directory",
    ),
    provider: str | None = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider (anthropic or openai)",
    ),
    mode: str = typer.Option(
        "auto",
        "--mode",
        "-m",
        help="Execution mode: auto (analyze complexity), quick (direct execution), plan (always plan)",
    ),
    no_checkpoint: bool = typer.Option(
        False,
        "--no-checkpoint",
        help="Disable checkpointing",
    ),
):
    """Execute a one-off task with intelligent planning."""
    settings = get_settings()

    # Override provider if specified
    if provider:
        settings.llm.provider = provider

    print_info(f"Executing task: {task}")
    print_info(f"Mode: {mode}")
    print_info(f"Workspace: {workspace}\n")

    # Create LLM
    llm = LLMFactory.create_llm(settings.llm, configurable=False)

    # Create tools
    tools = [
        ReadFileTool(workspace_path=workspace),
        ListDirectoryTool(workspace_path=workspace),
        FindFilesTool(workspace_path=workspace),
        WriteFileTool(workspace_path=workspace),
        ParsePythonTool(workspace_path=workspace),
        GitStatusTool(workspace_path=workspace),
        GitDiffTool(workspace_path=workspace),
        # Context retrieval tool for enhanced code understanding
        ContextRetrievalTool(workspace_path=workspace),
        # Web search tool for current information
        WebSearchTool(workspace_path=workspace),
        # Execution tools
        BashTool(workspace_path=workspace),
        PythonTool(workspace_path=workspace),
    ]

    # Execute task
    try:
        message = HumanMessage(content=task)
        thread_id = f"task-{uuid.uuid4().hex[:8]}"

        if no_checkpoint:
            # Create agent without checkpointing
            agent = create_agent(llm, tools, None, mode=mode)

            # Create initial state with task
            initial_state = create_initial_state(
                task=task,
                workspace_path=workspace,
                thread_id=thread_id,
                execution_mode=mode,
            )
            initial_state["messages"] = [message]

            # Run agent
            for event in agent.stream(
                initial_state,
                config=get_checkpoint_config(
                    thread_id, recursion_limit=settings.recursion_limit
                ),
            ):
                for node, output in event.items():
                    if "messages" in output:
                        for msg in output["messages"]:
                            format_message(msg)
        else:
            # Use checkpointer context manager
            from koder.agent.checkpoints import get_checkpointer

            with get_checkpointer(settings.storage.checkpoint_path) as checkpointer:
                # Create agent with checkpointer
                agent = create_agent(llm, tools, checkpointer, mode=mode)

                # Create initial state with task
                initial_state = create_initial_state(
                    task=task,
                    workspace_path=workspace,
                    thread_id=thread_id,
                    execution_mode=mode,
                )
                initial_state["messages"] = [message]

                # Run agent
                for event in agent.stream(
                    initial_state,
                    config=get_checkpoint_config(
                        thread_id, recursion_limit=settings.recursion_limit
                    ),
                ):
                    for node, output in event.items():
                        if "messages" in output:
                            for msg in output["messages"]:
                                format_message(msg)

        print_success("\nTask completed!")

    except Exception as e:
        print_error(f"Error executing task: {str(e)}")
        logger.error("task_error", task=task, error=str(e), exc_info=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
