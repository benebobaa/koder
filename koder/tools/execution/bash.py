"""Bash command execution tool with safety controls."""

import os
import subprocess
import threading
from pathlib import Path

from pydantic import Field

from koder.tools.base import KoderTool, WriteToolMixin
from koder.tools.registry import registry


@registry.register("execution", needs_approval=True, is_read_only=False)
class BashTool(KoderTool, WriteToolMixin):
    """Execute bash commands with comprehensive safety controls."""

    name: str = "bash"
    description: str = (
        "Execute bash commands in the workspace directory. "
        "Supports timeout, output limits, and safety controls. "
        "Commands are executed with workspace as working directory. "
        "Use with caution - requires approval for potentially dangerous commands."
    )

    # Safety and control parameters
    timeout_seconds: int = Field(
        default=30,
        description="Maximum execution time in seconds (0 = no limit)",
        ge=0,
    )

    max_output_size: int = Field(
        default=10000,
        description="Maximum output size in characters",
        ge=0,
    )

    allow_dangerous: bool = Field(
        default=True,
        description="Allow potentially dangerous commands (requires explicit approval)",
    )

    working_directory: str = Field(
        default=".",
        description="Working directory for command execution (relative to workspace)",
    )

    # Dangerous command patterns
    DANGEROUS_PATTERNS: set[str] = {
        # File system dangers
        "rm -rf /",
        "sudo rm",
        "chmod -R 777",
        "dd if=",
        # System dangers
        "sudo su",
        "sudo bash",
        "sudo sh",
        ":(){ :|:& };:",  # fork bomb
        "chmod +s",
        # Network dangers
        "nc -l",
        "python -m http.server",
        # Package management (might be wanted but need approval)
        "pip install",
        "npm install",
        "yum install",
        "apt-get install",
    }

    def _is_dangerous_command(self, command: str) -> tuple[bool, str | None]:
        """
        Check if a command contains dangerous patterns.

        Args:
            command: Command to check

        Returns:
            Tuple of (is_dangerous, matching_pattern)
        """
        command_lower = command.lower()

        for pattern in self.DANGEROUS_PATTERNS:
            if pattern in command_lower:
                return True, pattern

        return False, None

    def _validate_working_directory(self) -> str:
        """
        Validate and return the absolute working directory.

        Returns:
            Absolute working directory path

        Raises:
            ValueError: If working directory is outside workspace
        """
        workspace_path = Path(self.workspace_path).resolve()
        work_dir = workspace_path / self.working_directory
        work_dir = work_dir.resolve()

        # Ensure working directory is within workspace
        try:
            work_dir.relative_to(workspace_path)
        except ValueError:
            raise ValueError(
                f"Working directory {work_dir} is outside workspace {workspace_path}"
            )

        # Create directory if it doesn't exist
        work_dir.mkdir(parents=True, exist_ok=True)

        return str(work_dir)

    def _execute_command(self, command: str, cwd: str) -> tuple[int, str, str]:
        """
        Execute a command with safety controls.

        Args:
            command: Command to execute
            cwd: Working directory

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Prepare environment with limited variables
            env = os.environ.copy()
            env.update(
                {
                    "PATH": "/usr/bin:/bin:/usr/local/bin",  # Restricted PATH
                    "HOME": str(Path.home()),
                    "PWD": cwd,
                    "SHELL": "/bin/bash",
                }
            )

            # Start the process
            process = subprocess.Popen(
                ["bash", "-c", command],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                cwd=cwd,
                env=env,
                text=True,
                bufsize=1,  # Line buffered
            )

            # Setup timeout handling
            if self.timeout_seconds > 0:
                timer = threading.Timer(
                    self.timeout_seconds,
                    lambda: process.kill() if process.poll() is None else None,
                )
                timer.start()
            else:
                timer = None

            try:
                # Read output with size limits
                stdout_lines = []
                stderr_lines = []
                stdout_size = 0

                # Read stdout and stderr concurrently
                def read_stream(stream, output_lines, size_limit):
                    for line in iter(stream.readline, ""):
                        if size_limit > 0 and stdout_size + len(line) > size_limit:
                            output_lines.append("[OUTPUT TRUNCATED]")
                            break
                        output_lines.append(line.rstrip())
                        if size_limit > 0:
                            size_limit += len(line)

                stdout_thread = threading.Thread(
                    target=read_stream,
                    args=(process.stdout, stdout_lines, self.max_output_size),
                )
                stderr_thread = threading.Thread(
                    target=read_stream,
                    args=(process.stderr, stderr_lines, self.max_output_size),
                )

                stdout_thread.start()
                stderr_thread.start()

                # Wait for process completion
                exit_code = process.wait()

                # Wait for output threads
                stdout_thread.join(timeout=1)
                stderr_thread.join(timeout=1)

                stdout = "\n".join(stdout_lines) if stdout_lines else ""
                stderr = "\n".join(stderr_lines) if stderr_lines else ""

                return exit_code, stdout, stderr

            finally:
                if timer:
                    timer.cancel()
                    if timer.is_alive():
                        timer.join()

        except subprocess.TimeoutExpired:
            process.kill()
            return -1, "", f"Command timed out after {self.timeout_seconds} seconds"
        except Exception as e:
            return -1, "", f"Failed to execute command: {str(e)}"

    def _run(self, command: str) -> str:
        """
        Execute a bash command with safety controls.

        Args:
            command: Bash command to execute

        Returns:
            Formatted execution result
        """
        try:
            # Basic input validation
            if not command or not command.strip():
                return "Error: Empty command"

            command = command.strip()

            # Check for dangerous commands
            is_dangerous, pattern = self._is_dangerous_command(command)
            if is_dangerous and not self.allow_dangerous:
                return (
                    f"Error: Dangerous command detected: '{pattern}'. "
                    f"Set allow_dangerous=True to override this safety check."
                )

            # Validate working directory
            try:
                cwd = self._validate_working_directory()
            except ValueError as e:
                return f"Error: {str(e)}"

            # Execute the command
            exit_code, stdout, stderr = self._execute_command(command, cwd)

            # Format the output
            output_lines = [
                f"Command: {command}",
                f"Working Directory: {cwd}",
                f"Exit Code: {exit_code}",
                "",
            ]

            if stdout:
                output_lines.extend(
                    [
                        "STDOUT:",
                        stdout,
                        "",
                    ]
                )

            if stderr:
                output_lines.extend(
                    [
                        "STDERR:",
                        stderr,
                        "",
                    ]
                )

            if exit_code == 0:
                output_lines.append("✅ Command executed successfully")
            else:
                output_lines.append(f"❌ Command failed with exit code {exit_code}")

            return "\n".join(output_lines)

        except Exception as e:
            return self._handle_error(e)
