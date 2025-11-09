"""Output formatters for CLI."""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from rich.markdown import Markdown
from rich.syntax import Syntax

from koder.cli.ui.console import console


def format_message(message: Any) -> None:
    """
    Format and print a message.

    Args:
        message: Message to format
    """
    if isinstance(message, HumanMessage):
        console.print(f"[user]👤 User:[/user] {message.content}")

    elif isinstance(message, AIMessage):
        # Format AI message
        console.print("[agent]🤖 Assistant:[/agent]")

        # Check for tool calls
        if hasattr(message, "tool_calls") and message.tool_calls:
            console.print("  [tool]Using tools:[/tool]")
            for tool_call in message.tool_calls:
                tool_name = tool_call.get("name", "unknown")
                console.print(f"    - {tool_name}")
        else:
            # Regular message content
            if message.content:
                # Try to render as markdown
                try:
                    md = Markdown(message.content)
                    console.print(md)
                except Exception:
                    console.print(f"  {message.content}")

    elif isinstance(message, ToolMessage):
        console.print(f"[tool]🔧 Tool Result:[/tool]")
        console.print(f"  {message.content[:500]}")  # Truncate long outputs
        if len(message.content) > 500:
            console.print("  [dim]...(truncated)[/dim]")

    elif isinstance(message, SystemMessage):
        console.print(f"[dim]System: {message.content}[/dim]")

    else:
        console.print(str(message))


def format_code(code: str, language: str = "python") -> None:
    """
    Format and print code with syntax highlighting.

    Args:
        code: Code to format
        language: Programming language
    """
    syntax = Syntax(code, language, theme="monokai", line_numbers=True)
    console.print(syntax)


def format_code_inline(code: str, language: str = "python") -> str:
    """
    Format code for inline display.

    Args:
        code: Code to format
        language: Programming language

    Returns:
        Formatted code string
    """
    try:
        lexer = get_lexer_by_name(language)
        formatter = TerminalFormatter()
        return highlight(code, lexer, formatter)
    except Exception:
        return code


def format_dict(data: dict[str, Any], title: str = "Data") -> None:
    """
    Format and print a dictionary.

    Args:
        data: Dictionary to format
        title: Title for the output
    """
    from rich.table import Table

    table = Table(title=title)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="white")

    for key, value in data.items():
        table.add_row(str(key), str(value))

    console.print(table)


# ===== Planning-Specific Formatters =====


def format_plan(plan: dict[str, Any]) -> None:
    """
    Format and display an execution plan (Claude Code style).

    Args:
        plan: Plan dictionary with steps, analysis, files, etc.
    """
    from rich.panel import Panel
    from rich.table import Table

    # Build plan display
    plan_text = f"## Analysis\n{plan.get('analysis', 'N/A')}\n\n"

    # Steps
    if "steps" in plan and plan["steps"]:
        plan_text += "## Steps\n"
        for step in plan["steps"]:
            step_num = step.get("step_number", "?")
            desc = step.get("description", "")
            tool = step.get("tool", "")
            file = step.get("file", "")
            plan_text += f"{step_num}. **{desc}**\n"
            if tool:
                plan_text += f"   - Tool: `{tool}`\n"
            if file:
                plan_text += f"   - File: `{file}`\n"
        plan_text += "\n"

    # Files affected
    files_to_create = plan.get("files_to_create", [])
    files_to_modify = plan.get("files_to_modify", [])

    if files_to_create or files_to_modify:
        plan_text += "## Files Affected\n"
        if files_to_create:
            plan_text += f"**To Create:** {', '.join(files_to_create)}\n"
        if files_to_modify:
            plan_text += f"**To Modify:** {', '.join(files_to_modify)}\n"
        plan_text += "\n"

    # Metadata
    estimated_time = plan.get("estimated_time", "Unknown")
    complexity = plan.get("estimated_complexity", "medium")
    plan_text += f"**Estimated Time:** {estimated_time}\n"
    plan_text += f"**Complexity:** {complexity}\n"

    # Risks
    if "risks" in plan and plan["risks"]:
        plan_text += "\n## Potential Risks\n"
        for risk in plan["risks"]:
            plan_text += f"- {risk}\n"

    # Display in panel
    console.print()
    console.print(
        Panel(
            Markdown(plan_text),
            title="📋 Execution Plan",
            border_style="blue",
            padding=(1, 2),
        )
    )
    console.print()


def format_todo_list(todos: list[dict[str, Any]], title: str = "Tasks") -> None:
    """
    Format and display TODO list with status (Claude Code style).

    Args:
        todos: List of TODO items with status
        title: Title for the table
    """
    from rich.table import Table

    if not todos:
        return

    table = Table(title=title, show_header=True, header_style="bold cyan")
    table.add_column("Status", style="cyan", width=8)
    table.add_column("Task", style="white")

    status_icons = {
        "pending": "⏳",
        "in_progress": "🔄",
        "completed": "✅",
        "failed": "❌",
    }

    for todo in todos:
        status = todo.get("status", "pending")
        icon = status_icons.get(status, "⏳")

        # Use activeForm for in_progress, otherwise content
        if status == "in_progress":
            text = todo.get("activeForm", todo.get("content", ""))
            style = "yellow italic"
        elif status == "completed":
            text = todo.get("content", "")
            style = "green dim"
        elif status == "failed":
            text = todo.get("content", "")
            style = "red"
        else:
            text = todo.get("content", "")
            style = "white"

        table.add_row(icon, f"[{style}]{text}[/{style}]")

    console.print(table)


def format_progress(current: int, total: int, message: str = "") -> None:
    """
    Format and display progress indicator.

    Args:
        current: Current step number
        total: Total steps
        message: Optional message to display
    """
    from rich.progress import Progress, SpinnerColumn, TextColumn

    percentage = (current / total * 100) if total > 0 else 0

    progress_text = f"Step {current}/{total}"
    if message:
        progress_text += f" - {message}"

    console.print(f"[cyan]{progress_text}[/cyan] ({percentage:.0f}%)")


def format_approval_prompt(plan: dict[str, Any], task: str) -> None:
    """
    Format approval prompt for a plan.

    Args:
        plan: The plan to approve
        task: Original task description
    """
    from rich.panel import Panel

    # First show the plan
    format_plan(plan)

    # Then show approval prompt
    prompt_text = (
        f"[bold]Task:[/bold] {task}\n\n"
        f"[yellow]⚠️  This plan will modify {len(plan.get('files_to_modify', []))} files "
        f"and create {len(plan.get('files_to_create', []))} new files.[/yellow]\n\n"
        f"[bold cyan]Approve this plan?[/bold cyan]"
    )

    console.print(
        Panel(
            prompt_text,
            title="Approval Required",
            border_style="yellow",
            padding=(1, 2),
        )
    )


def format_complexity_analysis(complexity: str, reasoning: str) -> None:
    """
    Format complexity analysis result.

    Args:
        complexity: "simple" or "complex"
        reasoning: Explanation
    """
    if complexity == "simple":
        icon = "⚡"
        color = "green"
        mode = "Quick Execution"
    else:
        icon = "📋"
        color = "blue"
        mode = "Plan Mode"

    console.print(f"\n{icon} [bold {color}]{mode}[/bold {color}]: {reasoning}\n")


def format_step_header(step_number: int, total_steps: int, description: str) -> None:
    """
    Format step execution header.

    Args:
        step_number: Current step number
        total_steps: Total number of steps
        description: Step description
    """
    from rich.panel import Panel

    header = f"[bold cyan]Step {step_number}/{total_steps}:[/bold cyan] {description}"

    console.print()
    console.print(Panel(header, border_style="cyan"))
    console.print()
