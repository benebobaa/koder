"""Rich console configuration."""

from rich.console import Console
from rich.theme import Theme

# Custom theme for Koder
koder_theme = Theme(
    {
        "info": "cyan",
        "warning": "yellow",
        "error": "bold red",
        "success": "bold green",
        "code": "magenta",
        "tool": "blue",
        "agent": "green",
        "user": "white",
    }
)

# Global console instance
console = Console(theme=koder_theme)


def print_info(message: str) -> None:
    """Print info message."""
    console.print(f"[info]ℹ {message}[/info]")


def print_success(message: str) -> None:
    """Print success message."""
    console.print(f"[success]✓ {message}[/success]")


def print_warning(message: str) -> None:
    """Print warning message."""
    console.print(f"[warning]⚠ {message}[/warning]")


def print_error(message: str) -> None:
    """Print error message."""
    console.print(f"[error]✗ {message}[/error]")


def print_agent(message: str) -> None:
    """Print agent message."""
    console.print(f"[agent]🤖 Agent:[/agent] {message}")


def print_tool(tool_name: str, message: str) -> None:
    """Print tool execution message."""
    console.print(f"[tool]🔧 {tool_name}:[/tool] {message}")
