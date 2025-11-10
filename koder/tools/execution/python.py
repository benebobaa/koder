"""Python script execution tool with isolation."""

import os
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from koder.tools.base import KoderTool, WriteToolMixin
from koder.tools.registry import registry


@registry.register("execution", needs_approval=True, is_read_only=False)
class PythonTool(KoderTool, WriteToolMixin):
    """Execute Python code with isolation and safety controls."""

    name: str = "python"
    description: str = (
        "Execute Python code or scripts with isolation. "
        "Supports timeout, output limits, and virtual environment usage. "
        "Can execute code directly or run Python files. "
        "Use with caution - requires approval for code execution."
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

    use_venv: bool = Field(
        default=True,
        description="Use virtual environment for isolation",
    )

    working_directory: str = Field(
        default=".",
        description="Working directory for execution (relative to workspace)",
    )

    python_version: Optional[str] = Field(
        default=None,
        description="Python version to use (e.g., '3.9', '3.10'). None = system default",
    )

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

    def _get_python_executable(self) -> str:
        """
        Get the Python executable to use.

        Returns:
            Path to Python executable
        """
        if self.python_version:
            # Try to find specific version
            python_cmd = f"python{self.python_version}"
            try:
                result = subprocess.run(
                    ["which", python_cmd],
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            except subprocess.CalledProcessError:
                pass

        return sys.executable

    def _create_temp_venv(self, base_dir: str) -> Optional[str]:
        """
        Create a temporary virtual environment.

        Args:
            base_dir: Base directory for the venv

        Returns:
            Path to venv python executable or None if failed
        """
        if not self.use_venv:
            return None

        try:
            venv_dir = Path(base_dir) / ".temp_venv"

            # Create virtual environment
            subprocess.run(
                [sys.executable, "-m", "venv", str(venv_dir)],
                capture_output=True,
                check=True,
            )

            # Determine python executable in venv
            if os.name == "nt":  # Windows
                venv_python = venv_dir / "Scripts" / "python.exe"
            else:  # Unix-like
                venv_python = venv_dir / "bin" / "python"

            return str(venv_python) if venv_python.exists() else None

        except (subprocess.CalledProcessError, OSError):
            return None

    def _execute_code(
        self, code: str, cwd: str, python_executable: str
    ) -> tuple[int, str, str]:
        """
        Execute Python code with safety controls.

        Args:
            code: Python code to execute
            cwd: Working directory
            python_executable: Path to Python executable

        Returns:
            Tuple of (exit_code, stdout, stderr)
        """
        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, dir=cwd
            ) as f:
                f.write(code)
                temp_file = f.name

            try:
                # Prepare environment
                env = os.environ.copy()
                env.update(
                    {
                        "PYTHONPATH": cwd,
                        "PYTHONIOENCODING": "utf-8",
                        "PYTHONDONTWRITEBYTECODE": "1",
                    }
                )

                # Start the process
                process = subprocess.Popen(
                    [python_executable, temp_file],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    cwd=cwd,
                    env=env,
                    text=True,
                    bufsize=1,
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

                    # Read stdout and stderr concurrently
                    def read_stream(stream, output_lines):
                        for line in iter(stream.readline, ""):
                            if (
                                self.max_output_size > 0
                                and len(output_lines) * 100 > self.max_output_size
                            ):
                                output_lines.append("[OUTPUT TRUNCATED]")
                                break
                            output_lines.append(line.rstrip())

                    stdout_thread = threading.Thread(
                        target=read_stream, args=(process.stdout, stdout_lines)
                    )
                    stderr_thread = threading.Thread(
                        target=read_stream, args=(process.stderr, stderr_lines)
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

            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass

        except subprocess.TimeoutExpired:
            process.kill()
            return (
                -1,
                "",
                f"Python execution timed out after {self.timeout_seconds} seconds",
            )
        except Exception as e:
            return -1, "", f"Failed to execute Python code: {str(e)}"

    def _run(self, code: str) -> str:
        """
        Execute Python code with isolation and safety controls.

        Args:
            code: Python code to execute

        Returns:
            Formatted execution result
        """
        try:
            # Basic input validation
            if not code or not code.strip():
                return "Error: Empty Python code"

            code = code.strip()

            # Validate working directory
            try:
                cwd = self._validate_working_directory()
            except ValueError as e:
                return f"Error: {str(e)}"

            # Get Python executable (with optional venv)
            python_executable = self._get_python_executable()
            venv_python = self._create_temp_venv(cwd)
            if venv_python:
                python_executable = venv_python

            # Execute the code
            exit_code, stdout, stderr = self._execute_code(code, cwd, python_executable)

            # Format the output
            output_lines = [
                f"Python Version: {python_executable}",
                f"Working Directory: {cwd}",
                f"Virtual Environment: {'Yes' if venv_python else 'No'}",
                f"Exit Code: {exit_code}",
                "",
            ]

            if stdout:
                output_lines.extend(
                    [
                        "OUTPUT:",
                        stdout,
                        "",
                    ]
                )

            if stderr:
                output_lines.extend(
                    [
                        "ERRORS:",
                        stderr,
                        "",
                    ]
                )

            if exit_code == 0:
                output_lines.append("✅ Python code executed successfully")
            else:
                output_lines.append(f"❌ Python code failed with exit code {exit_code}")

            # Clean up venv if created
            if venv_python:
                try:
                    import shutil

                    venv_dir = Path(venv_python).parent.parent
                    if venv_dir.name == ".temp_venv":
                        shutil.rmtree(venv_dir, ignore_errors=True)
                except Exception:
                    pass

            return "\n".join(output_lines)

        except Exception as e:
            return self._handle_error(e)
