"""Prompt Toolkit components for interactive input."""

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.styles import Style

# Custom style for prompts
prompt_style = Style.from_dict(
    {
        "prompt": "#00aa00 bold",
        "": "#ffffff",
    }
)


def create_session(history_file: str = ".koder_history") -> PromptSession:
    """
    Create a prompt session with history.

    Args:
        history_file: Path to history file

    Returns:
        Configured PromptSession
    """
    return PromptSession(
        history=FileHistory(history_file),
        style=prompt_style,
    )


def get_user_input(
    session: PromptSession,
    prompt: str = "You: ",
    multiline: bool = False,
) -> str:
    """
    Get user input with prompt.

    Args:
        session: Prompt session
        prompt: Prompt text
        multiline: Whether to allow multiline input

    Returns:
        User input string
    """
    try:
        text = session.prompt(
            prompt,
            multiline=multiline,
        )
        return text.strip()
    except (KeyboardInterrupt, EOFError):
        return ""


def confirm(prompt: str = "Continue?") -> bool:
    """
    Ask for yes/no confirmation.

    Args:
        prompt: Confirmation prompt

    Returns:
        True if confirmed, False otherwise
    """
    from prompt_toolkit.shortcuts import confirm as pt_confirm

    try:
        return pt_confirm(prompt)
    except (KeyboardInterrupt, EOFError):
        return False
