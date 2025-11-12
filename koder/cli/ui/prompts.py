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
    import sys

    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        # Non-interactive mode: read from stdin if available, default to False
        try:
            # Try to read a single line from stdin
            line = sys.stdin.readline().strip().lower()
            return line in ["y", "yes", "true", "1"]
        except:
            # If no input available, default to False (safer default)
            return False

    try:
        from prompt_toolkit.shortcuts import confirm as pt_confirm

        return pt_confirm(prompt)
    except (KeyboardInterrupt, EOFError):
        return False
    except Exception:
        # Fallback for any other prompt_toolkit errors
        try:
            # Simple text-based confirmation
            response = input(f"{prompt} (y/n): ").strip().lower()
            return response in ["y", "yes", "true", "1"]
        except:
            return False


def ask(prompt: str, options: list[str] = None) -> str:
    """
    Ask for user input with optional choices.

    Args:
        prompt: Input prompt
        options: Optional list of valid choices

    Returns:
        User input string
    """
    import sys

    # Check if we're in an interactive terminal
    if not sys.stdin.isatty():
        # Non-interactive mode: read from stdin if available
        try:
            line = sys.stdin.readline().strip()
            if options and line not in options:
                return options[0] if options else line  # Default to first option
            return line
        except:
            # If no input available, default to first option or empty
            return options[0] if options else ""

    try:
        # Create a simple prompt session
        session = create_session()

        # Add options to prompt if provided
        if options:
            prompt += f" ({'/'.join(options)})"

        response = session.prompt(prompt + ": ")
        response = response.strip()

        # Validate against options if provided
        if options and response not in options:
            print(f"Invalid choice. Please choose from: {', '.join(options)}")
            return ask(prompt, options)  # Recursively ask again

        return response

    except (KeyboardInterrupt, EOFError):
        return ""
    except Exception:
        # Fallback to basic input
        try:
            if options:
                prompt += f" ({'/'.join(options)})"
            response = input(prompt + ": ").strip()

            # Validate against options if provided
            if options and response not in options:
                print(f"Invalid choice. Please choose from: {', '.join(options)}")
                return ask(prompt, options)  # Recursively ask again

            return response
        except:
            return ""
