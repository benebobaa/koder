"""Planning-specific nodes for intelligent task execution."""

import json
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from koder.agent.prompts import (
    COMPLEXITY_ANALYSIS_PROMPT,
    COMPLEXITY_THRESHOLD,
    PLAN_EXECUTION_PROMPT,
    PLANNING_PROMPT,
    REFLECTION_PROMPT,
)
from koder.agent.state import AgentState
from koder.cli.ui.formatters import (
    format_complexity_analysis,
    format_plan,
    format_step_header,
    format_todo_list,
)
from koder.cli.ui.prompts import confirm
from koder.tools.registry import registry


def complexity_analysis_node(
    state: AgentState, llm: BaseChatModel, tools: list[BaseTool]
) -> dict[str, Any]:
    """
    Analyze task complexity to determine execution mode.

    Args:
        state: Current agent state
        llm: Language model (use fast model like Haiku)
        tools: Available tools

    Returns:
        State updates with complexity analysis
    """
    request = state["current_task"]

    # Skip if already analyzed or mode is explicit
    if state.get("task_complexity"):
        return {}

    # If mode is explicit (not auto), skip analysis
    if state.get("execution_mode") in ["quick", "plan"]:
        complexity = "simple" if state["execution_mode"] == "quick" else "complex"
        return {
            "task_complexity": complexity,
            "complexity_reasoning": f"Explicit mode: {state['execution_mode']}",
        }

    # Build tool list
    tool_names = [tool.name for tool in tools]

    # Create analysis prompt
    prompt = COMPLEXITY_ANALYSIS_PROMPT.format(
        request=request, tools=", ".join(tool_names)
    )

    # Use fast LLM for quick analysis
    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    try:
        # Parse JSON response
        analysis = json.loads(response.content)
        complexity = analysis.get("complexity", "simple")
        reasoning = analysis.get("reasoning", "No reasoning provided")
        estimated_steps = analysis.get("estimated_steps", 1)

        # Override to complex if many steps needed
        if estimated_steps >= COMPLEXITY_THRESHOLD:
            complexity = "complex"
            reasoning += f" ({estimated_steps} steps needed)"

        # Display analysis
        format_complexity_analysis(complexity, reasoning)

        return {
            "task_complexity": complexity,
            "complexity_reasoning": reasoning,
        }

    except json.JSONDecodeError:
        # Fallback to simple on parse error
        return {
            "task_complexity": "simple",
            "complexity_reasoning": "Failed to parse analysis, defaulting to simple mode",
        }


def plan_generation_node(
    state: AgentState, llm: BaseChatModel, tools: list[BaseTool]
) -> dict[str, Any]:
    """
    Generate structured execution plan for complex tasks.

    Args:
        state: Current agent state
        llm: Language model
        tools: Available tools

    Returns:
        State updates with generated plan
    """
    request = state["current_task"]

    # Gather context
    context = f"Workspace: {state['workspace_path']}\n"
    if state.get("gathered_files"):
        context += f"Files read: {', '.join(state['gathered_files'])}\n"
    if state.get("codebase_summary"):
        context += f"Codebase: {state['codebase_summary']}\n"

    # Build tool list with descriptions
    tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]

    # Create planning prompt
    prompt = PLANNING_PROMPT.format(
        request=request, context=context, tools="\n".join(tool_descriptions)
    )

    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    try:
        # Parse plan
        plan = json.loads(response.content)

        # Add metadata
        plan["created_at"] = datetime.now().isoformat()

        # Convert todos to proper format if needed
        if "todos" in plan:
            for i, todo in enumerate(plan["todos"]):
                if "id" not in todo:
                    todo["id"] = i + 1
                if "status" not in todo:
                    todo["status"] = "pending"

        return {
            "plan": plan,
            "plan_status": "pending",
            "plan_created_at": plan["created_at"],
            "todos": plan.get("todos", []),
        }

    except json.JSONDecodeError:
        # Fallback: create simple plan
        return {
            "plan": {
                "analysis": "Failed to generate structured plan",
                "steps": [
                    {"step_number": 1, "description": request, "type": "unknown"}
                ],
                "todos": [
                    {
                        "id": 1,
                        "content": request,
                        "status": "pending",
                        "activeForm": f"Working on: {request}",
                    }
                ],
            },
            "plan_status": "pending",
            "todos": [
                {
                    "id": 1,
                    "content": request,
                    "status": "pending",
                    "activeForm": f"Working on: {request}",
                }
            ],
        }


def plan_approval_node(state: AgentState) -> dict[str, Any]:
    """
    Display plan and wait for user approval.

    Args:
        state: Current agent state

    Returns:
        State updates with approval status
    """
    plan = state.get("plan")
    task = state["current_task"]

    if not plan:
        return {"plan_status": "rejected", "error": "No plan to approve"}

    # Display plan
    format_plan(plan)

    # Show TODO list
    if state.get("todos"):
        format_todo_list(state["todos"], title="Planned Tasks")

    # Prompt for approval
    approved = confirm("\nApprove this plan?")

    if approved:
        return {
            "plan_status": "approved",
            "plan_approved_at": datetime.now().isoformat(),
            "pending_approval": False,
        }
    else:
        return {
            "plan_status": "rejected",
            "pending_approval": False,
            "error": "Plan rejected by user",
        }


def plan_execution_node(
    state: AgentState, llm: BaseChatModel, tools: list[BaseTool]
) -> dict[str, Any]:
    """
    Execute plan steps sequentially with progress tracking.

    Args:
        state: Current agent state
        llm: Language model
        tools: Available tools

    Returns:
        State updates after execution
    """
    plan = state.get("plan")
    todos = state.get("todos", [])

    if not plan or not plan.get("steps"):
        return {"error": "No plan steps to execute"}

    steps = plan["steps"]
    total_steps = len(steps)
    completed_steps = state.get("completed_steps", [])
    current_step_idx = state.get("current_step", 0)

    # Execute remaining steps
    for i in range(current_step_idx, total_steps):
        step = steps[i]
        step_number = step.get("step_number", i + 1)
        description = step.get("description", "")
        tool_name = step.get("tool", "")

        # Update TODO status
        if i < len(todos):
            todos[i]["status"] = "in_progress"
            format_todo_list(todos, title="Progress")

        # Show step header
        format_step_header(step_number, total_steps, description)

        # Execute step
        try:
            # Find and execute tool
            if tool_name:
                tool = registry.get_tool(tool_name)
                if tool:
                    # Execute tool
                    # Note: This is simplified - real execution would use LLM to determine args
                    result = f"Executed {tool_name} for step {step_number}"
                else:
                    result = f"Tool {tool_name} not found"
            else:
                # Use LLM to execute without specific tool
                result = _execute_step_with_llm(state, llm, tools, step, i)

            # Mark TODO as completed
            if i < len(todos):
                todos[i]["status"] = "completed"

            completed_steps.append(i)

        except Exception as e:
            # Mark TODO as failed
            if i < len(todos):
                todos[i]["status"] = "failed"

            return {
                "error": f"Step {step_number} failed: {str(e)}",
                "current_step": i,
                "completed_steps": completed_steps,
                "failed_steps": [i],
                "todos": todos,
            }

    # All steps completed
    format_todo_list(todos, title="Completed")

    return {
        "plan_status": "completed",
        "current_step": total_steps,
        "completed_steps": completed_steps,
        "todos": todos,
        "should_continue": False,
    }


def _execute_step_with_llm(
    state: AgentState,
    llm: BaseChatModel,
    tools: list[BaseTool],
    step: dict,
    step_index: int,
) -> str:
    """
    Execute a plan step using LLM with tools.

    Args:
        state: Current agent state
        llm: Language model
        tools: Available tools
        step: Step dictionary
        step_index: Index of current step

    Returns:
        Execution result string
    """
    plan = state.get("plan", {})
    previous_results = [
        state["tool_outputs"][i] if i < len(state.get("tool_outputs", [])) else {}
        for i in range(step_index)
    ]

    prompt = PLAN_EXECUTION_PROMPT.format(
        step_number=step.get("step_number", step_index + 1),
        total_steps=len(plan.get("steps", [])),
        plan_context=json.dumps(plan, indent=2),
        current_step=json.dumps(step, indent=2),
        previous_results=json.dumps(previous_results, indent=2),
    )

    messages = [SystemMessage(content=prompt)]

    # Bind tools and invoke
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(messages)

    # Execute tool calls if any
    if hasattr(response, "tool_calls") and response.tool_calls:
        tool_lookup = {tool.name: tool for tool in tools}
        results = []

        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            if tool_name in tool_lookup:
                tool = tool_lookup[tool_name]
                result = tool.invoke(tool_args)
                results.append(result)

        return " | ".join(str(r) for r in results)

    return response.content


def reflection_node(state: AgentState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Reflect on completed execution and provide summary.

    Args:
        state: Current agent state
        llm: Language model

    Returns:
        State updates with reflection
    """
    request = state["current_task"]
    plan = state.get("plan", {})
    results = state.get("tool_outputs", [])
    files_modified = state.get("gathered_files", [])

    prompt = REFLECTION_PROMPT.format(
        request=request,
        plan=json.dumps(plan, indent=2),
        results=json.dumps(results, indent=2),
        files_modified=", ".join(files_modified) if files_modified else "None",
    )

    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    try:
        reflection = json.loads(response.content)
        return {
            "reflection": reflection,
            "should_continue": False,
        }
    except json.JSONDecodeError:
        return {
            "reflection": {"summary": response.content},
            "should_continue": False,
        }
