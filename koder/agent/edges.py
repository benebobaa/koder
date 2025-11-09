"""Conditional edge logic for agent graph."""

from typing import Literal

from langchain_core.messages import AIMessage

from koder.agent.state import AgentState


def should_continue_routing(
    state: AgentState,
) -> Literal["action", "final_response", "end"]:
    """
    Determine whether to continue with actions or end execution.

    Args:
        state: Current agent state

    Returns:
        Next node name to route to
    """
    # Check if we've hit iteration limit
    if state["iteration"] >= state["max_iterations"]:
        return "final_response"

    # Check if there's an error
    if state.get("error"):
        return "end"

    # Check if should_continue flag is False
    if not state.get("should_continue", True):
        return "end"

    # Check last message for tool calls
    messages = state["messages"]
    if not messages:
        return "end"

    last_message = messages[-1]

    # If last message is AIMessage with tool calls, execute them
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "action"

    # If last message is AIMessage without tool calls, agent is done
    if isinstance(last_message, AIMessage):
        return "end"

    # Default: continue reasoning
    return "final_response"


def should_observe(state: AgentState) -> Literal["observation", "reasoning"]:
    """
    Determine whether to observe or continue reasoning.

    Args:
        state: Current agent state

    Returns:
        Next node name
    """
    # After tool execution, always observe
    return "observation"


# ===== Planning Mode Routing Edges =====


def should_analyze_complexity(state: AgentState) -> Literal["analyze", "skip"]:
    """
    Determine if complexity analysis is needed.

    Args:
        state: Current agent state

    Returns:
        "analyze" if analysis needed, "skip" if already determined
    """
    # Skip if already analyzed
    if state.get("task_complexity"):
        return "skip"

    # Skip if explicit mode (not auto)
    if state.get("execution_mode") in ["quick", "plan"]:
        return "skip"

    return "analyze"


def route_by_complexity(state: AgentState) -> Literal["quick", "plan"]:
    """
    Route to quick execution or planning based on complexity.

    Args:
        state: Current agent state

    Returns:
        Execution mode to use
    """
    # Check explicit mode first
    mode = state.get("execution_mode")
    if mode == "quick":
        return "quick"
    elif mode == "plan":
        return "plan"

    # Route based on complexity analysis
    complexity = state.get("task_complexity", "simple")

    if complexity == "simple":
        return "quick"
    else:
        return "plan"


def should_generate_plan(state: AgentState) -> Literal["generate", "skip"]:
    """
    Determine if plan generation is needed.

    Args:
        state: Current agent state

    Returns:
        "generate" if plan needed, "skip" if already exists
    """
    # Skip if plan already exists
    if state.get("plan"):
        return "skip"

    # Skip if in quick mode
    if state.get("task_complexity") == "simple":
        return "skip"

    return "generate"


def check_plan_approval(state: AgentState) -> Literal["approved", "rejected", "pending"]:
    """
    Check plan approval status.

    Args:
        state: Current agent state

    Returns:
        Approval status
    """
    plan_status = state.get("plan_status")

    if plan_status == "approved":
        return "approved"
    elif plan_status == "rejected":
        return "rejected"
    else:
        return "pending"


def has_more_steps(state: AgentState) -> Literal["continue", "done", "failed"]:
    """
    Check if there are more plan steps to execute.

    Args:
        state: Current agent state

    Returns:
        "continue" if more steps, "done" if complete, "failed" if error
    """
    # Check for errors
    if state.get("error"):
        return "failed"

    plan = state.get("plan")
    if not plan:
        return "done"

    total_steps = len(plan.get("steps", []))
    current_step = state.get("current_step", 0)

    if current_step >= total_steps:
        return "done"
    else:
        return "continue"
