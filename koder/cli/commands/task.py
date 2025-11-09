"""Task command for one-off executions."""

from typing import Optional

import typer
from langchain_core.messages import HumanMessage

from koder.agent.graph import create_agent
from koder.cli.ui.console import print_error, print_info, print_success
from koder.cli.ui.formatters import format_message
from koder.config.settings import get_settings
from koder.llm.factory import LLMFactory
from koder.observability.logging import get_logger
from koder.tools.code.parser import ParsePythonTool
from koder.tools.filesystem.read import FindFilesTool, ListDirectoryTool, ReadFileTool
from koder.tools.filesystem.write import WriteFileTool
from koder.tools.git.status import GitDiffTool, GitStatusTool

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
    provider: Optional[str] = typer.Option(
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
    ]

    # Create agent with planning support
    checkpoint_path = None if no_checkpoint else settings.storage.checkpoint_path
    agent = create_agent(llm, tools, checkpoint_path, mode=mode)

    # Execute task
    try:
        message = HumanMessage(content=task)

        # Run agent
        for event in agent.stream({"messages": [message]}):
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
