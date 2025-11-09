"""Agent state schema definitions."""

from typing import Annotated, Any, Literal, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    """
    State schema for the agent (supports both simple ReAct and planning modes).

    The state is passed between nodes in the graph and maintains
    the conversation context, task information, and execution state.

    Note: total=False makes all fields optional for backward compatibility.
    """

    # ===== Core Fields (Required) =====

    # Messages with automatic list merging using add_messages reducer
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Current task/goal
    current_task: str

    # Tool execution results
    tool_outputs: list[dict[str, Any]]

    # Iteration tracking
    iteration: int
    max_iterations: int

    # Context information
    workspace_path: str
    file_context: list[str]

    # Metadata
    thread_id: str
    user_id: str

    # Control flow
    should_continue: bool
    error: str | None

    # ===== Planning Fields (Optional) =====

    # Execution mode: how the agent operates
    execution_mode: Literal["quick", "plan", "auto"] | None

    # Task complexity analysis result
    task_complexity: Literal["simple", "complex"] | None
    complexity_reasoning: str | None

    # Plan structure
    plan: dict[str, Any] | None  # {steps: [...], reasoning: str, estimated_time: str}
    plan_status: (
        Literal["pending", "approved", "rejected", "executing", "completed"] | None
    )
    plan_created_at: str | None
    plan_approved_at: str | None

    # TODO tracking (like Claude Code)
    todos: list[dict[str, Any]]  # [{id, content, status, activeForm, step_index}]
    current_step: int | None
    completed_steps: list[int]
    failed_steps: list[int]

    # Approval state
    pending_approval: bool
    approval_type: Literal["plan", "tool_execution", "destructive_operation"] | None
    approval_details: dict[str, Any] | None

    # Gathered context (for planning)
    gathered_files: list[str]
    codebase_summary: str | None


def create_initial_state(
    task: str,
    workspace_path: str = ".",
    thread_id: str = "default",
    user_id: str = "default",
    max_iterations: int = 10,
    execution_mode: Literal["quick", "plan", "auto"] = "auto",
) -> AgentState:
    """
    Create initial agent state.

    Args:
        task: The task description
        workspace_path: Path to workspace directory
        thread_id: Thread identifier for checkpointing
        user_id: User identifier
        max_iterations: Maximum number of reasoning iterations
        execution_mode: Execution mode (auto=analyze complexity, quick=direct, plan=always plan)

    Returns:
        Initial agent state with all required and optional planning fields
    """
    return {
        # Core fields
        "messages": [],
        "current_task": task,
        "tool_outputs": [],
        "iteration": 0,
        "max_iterations": max_iterations,
        "workspace_path": workspace_path,
        "file_context": [],
        "thread_id": thread_id,
        "user_id": user_id,
        "should_continue": True,
        "error": None,
        # Planning fields
        "execution_mode": execution_mode,
        "task_complexity": None,
        "complexity_reasoning": None,
        "plan": None,
        "plan_status": None,
        "plan_created_at": None,
        "plan_approved_at": None,
        "todos": [],
        "current_step": None,
        "completed_steps": [],
        "failed_steps": [],
        "pending_approval": False,
        "approval_type": None,
        "approval_details": None,
        "gathered_files": [],
        "codebase_summary": None,
    }
