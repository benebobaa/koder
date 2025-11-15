"""Planning-specific nodes for intelligent task execution."""

import json
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from koder.agent.prompts import (
    COMPLEXITY_ANALYSIS_PROMPT,
    COMPLEXITY_THRESHOLD,
    PLAN_EXECUTION_PROMPT,
    PLANNING_PROMPT,
    REFLECTION_PROMPT,
    STEP_VERIFICATION_PROMPT,
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
    Analyze task complexity to determine execution mode - now enhanced with discovery results.

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
        context += f"\n**Files already read:** {', '.join(state['gathered_files'])}\n"
    if state.get("codebase_summary"):
        context += f"\n**Previous codebase analysis:** {state['codebase_summary']}\n"

    # Build tool list with descriptions
    tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]

    # Create planning prompt
    prompt = PLANNING_PROMPT.format(
        request=request, context=context, tools="\n".join(tool_descriptions)
    )

    messages = [SystemMessage(content=prompt)]
    response = llm.invoke(messages)

    try:
        # Extract JSON from response (handle markdown code blocks)
        content = response.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()

        # Parse plan
        plan = json.loads(content)

        # Validate plan structure
        if not isinstance(plan, dict):
            raise ValueError("Plan is not a dictionary")

        if "steps" not in plan or not isinstance(plan["steps"], list):
            # Add default steps if missing
            plan["steps"] = [
                {
                    "step_number": 1,
                    "description": request,
                    "tool": "",
                    "type": "unknown",
                    "file": "",
                    "rationale": "Direct execution",
                }
            ]

        # Add metadata
        plan["created_at"] = datetime.now().isoformat()

        # Convert todos to proper format if needed
        if "todos" not in plan or not isinstance(plan["todos"], list):
            plan["todos"] = [
                {
                    "id": 1,
                    "content": request,
                    "status": "pending",
                    "activeForm": f"Working on: {request}",
                    "step_index": 0,
                    "estimated_time": "Unknown",
                }
            ]
        else:
            for i, todo in enumerate(plan["todos"]):
                if "id" not in todo:
                    todo["id"] = i + 1
                if "status" not in todo:
                    todo["status"] = "pending"
                if "step_index" not in todo:
                    todo["step_index"] = i

        return {
            "plan": plan,
            "plan_status": "pending",
            "plan_created_at": plan["created_at"],
            "todos": plan["todos"],
        }

    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: create simple plan with proper structure
        print(f"⚠️  Failed to parse structured plan: {e}")
        print("⚠️  Creating fallback plan...")

        # Try to extract the plan even if JSON parsing failed
        try:
            # Extract JSON from the response content
            content = response.content.strip()

            # Look for JSON pattern in the content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                extracted_plan = json.loads(json_str)
                extracted_plan["created_at"] = datetime.now().isoformat()

                return {
                    "plan": extracted_plan,
                    "plan_status": "pending",
                    "plan_created_at": extracted_plan["created_at"],
                    "todos": extracted_plan["todos"],
                }
        except Exception as fix_error:
            print(f"⚠️  Could not fix plan: {fix_error}")
        # Fallback: create simple plan with proper structure
        fallback_plan = {
            "analysis": f"Failed to generate structured plan for: {request}. Will execute directly.",
            "steps": [
                {
                    "step_number": 1,
                    "description": request,
                    "tool": "",
                    "type": "unknown",
                    "file": "",
                    "rationale": "Direct execution due to planning failure",
                }
            ],
            "todos": [
                {
                    "id": 1,
                    "content": request,
                    "status": "pending",
                    "activeForm": f"Working on: {request}",
                    "step_index": 0,
                    "estimated_time": "Unknown",
                }
            ],
            "files_to_create": [],
            "files_to_modify": [],
            "estimated_complexity": "medium",
            "estimated_time": "Unknown",
            "risks": ["Planning system failed, may need manual intervention"],
            "created_at": datetime.now().isoformat(),
        }

        return {
            "plan": fallback_plan,
            "plan_status": "pending",
            "plan_created_at": fallback_plan["created_at"],
            "todos": fallback_plan["todos"],
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

    if not plan:
        return {"error": "No plan available for execution"}

    steps = plan.get("steps")
    if not steps or not isinstance(steps, list):
        return {"error": "Invalid plan: no steps found or steps is not a list"}

    total_steps = len(steps)
    if total_steps == 0:
        return {"error": "Plan contains no steps to execute"}

    completed_steps = state.get("completed_steps", [])
    current_step_idx = state.get("current_step", 0)

    # Validate current_step_idx
    if current_step_idx is None or not isinstance(current_step_idx, int):
        current_step_idx = 0
    elif current_step_idx >= total_steps:
        current_step_idx = 0  # Reset if out of bounds

    # Keep track of all messages across steps to preserve context
    all_messages = list(state.get("messages", []))
    failed_steps = []
    blocked_steps = []

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

        # Execute step with ReAct loop
        try:
            # Pass updated state with accumulated messages
            execution_state = dict(state)
            execution_state["messages"] = all_messages

            result_dict = _execute_step_with_llm(execution_state, llm, tools, step, i)

            # Extract results
            status = result_dict.get("status", "completed")
            summary = result_dict.get("summary", "")
            actions_taken = result_dict.get("actions_taken", [])
            new_messages = result_dict.get("messages", [])

            # Add new messages to accumulated history
            all_messages.extend(new_messages)

            # Store result in tool outputs for reflection
            step_result = {
                "step_number": step_number,
                "description": description,
                "tool_name": tool_name,
                "result": summary,
                "status": status,
                "actions_taken": actions_taken,
            }

            # Update TODO and tracking based on verification status
            if status == "completed":
                if i < len(todos):
                    todos[i]["status"] = "completed"
                completed_steps.append(i)
            elif status == "blocked":
                if i < len(todos):
                    todos[i]["status"] = "failed"
                blocked_steps.append(i)
                # Stop execution on blocked step - requires user intervention
                state.setdefault("tool_outputs", []).append(step_result)
                state["messages"] = all_messages

                from koder.cli.ui.console import console
                console.print(f"\n⚠️  Step {step_number} is blocked: {summary}", style="yellow")
                console.print("This step requires user intervention or external dependencies.", style="yellow")

                return {
                    "error": f"Step {step_number} blocked: {summary}",
                    "current_step": i,
                    "completed_steps": completed_steps,
                    "failed_steps": failed_steps,
                    "blocked_steps": blocked_steps,
                    "todos": todos,
                    "tool_outputs": state.get("tool_outputs", []),
                    "messages": all_messages,
                }
            elif status in ["failed", "partial"]:
                if i < len(todos):
                    todos[i]["status"] = "failed"
                failed_steps.append(i)
                # Continue with other steps but track failure

            # Update state with tool output
            state.setdefault("tool_outputs", []).append(step_result)

        except Exception as e:
            # Mark TODO as failed
            if i < len(todos):
                todos[i]["status"] = "failed"

            error_result = f"Step {step_number} failed with exception: {str(e)}"
            step_result = {
                "step_number": step_number,
                "description": description,
                "tool_name": tool_name,
                "result": error_result,
                "status": "failed",
            }

            failed_steps.append(i)
            state.setdefault("tool_outputs", []).append(step_result)
            state["messages"] = all_messages

            from koder.cli.ui.console import console
            console.print(f"\n❌ Step {step_number} failed with exception: {str(e)}", style="red")

            # Decide whether to continue or stop based on error severity
            if "blocked" in str(e).lower() or "cannot proceed" in str(e).lower():
                return {
                    "error": error_result,
                    "current_step": i,
                    "completed_steps": completed_steps,
                    "failed_steps": failed_steps,
                    "blocked_steps": blocked_steps,
                    "todos": todos,
                    "tool_outputs": state.get("tool_outputs", []),
                    "messages": all_messages,
                }
            # Otherwise continue with next steps

    # All steps completed
    format_todo_list(todos, title="Completed")

    # Update state with accumulated messages
    state["messages"] = all_messages

    # Determine overall status
    if failed_steps or blocked_steps:
        plan_status = "completed_with_issues"
    else:
        plan_status = "completed"

    return {
        "plan_status": plan_status,
        "current_step": total_steps,
        "completed_steps": completed_steps,
        "failed_steps": failed_steps,
        "blocked_steps": blocked_steps,
        "todos": todos,
        "should_continue": False,
        "tool_outputs": state.get("tool_outputs", []),
        "messages": all_messages,
    }


def _execute_step_with_llm(
    state: AgentState,
    llm: BaseChatModel,
    tools: list[BaseTool],
    step: dict,
    step_index: int,
) -> dict[str, Any]:
    """
    Execute a plan step using LLM with ReAct loop.

    This implements the same reasoning-action-observation pattern as non-planning mode,
    allowing the LLM to iterate until the step objective is achieved.

    Args:
        state: Current agent state
        llm: Language model
        tools: Available tools
        step: Step dictionary
        step_index: Index of current step

    Returns:
        Dict with execution results, status, and messages
    """
    from koder.cli.ui.console import console
    from rich.panel import Panel

    plan = state.get("plan", {})
    previous_results = [
        state["tool_outputs"][i] if i < len(state.get("tool_outputs", [])) else {}
        for i in range(step_index)
    ]

    # Build step context prompt
    step_description = step.get("description", "")
    suggested_tool = step.get("tool", "any appropriate tool")

    step_prompt = PLAN_EXECUTION_PROMPT.format(
        step_number=step.get("step_number", step_index + 1),
        total_steps=len(plan.get("steps", [])),
        step_description=step_description,
        plan_context=json.dumps(plan.get("analysis", ""), indent=2)[:500],  # Truncate to avoid token limits
        current_step=json.dumps(step, indent=2),
        previous_results=json.dumps(previous_results[-3:], indent=2) if previous_results else "None",  # Last 3 results
        suggested_tool=suggested_tool,
    )

    # Start with full message history from state (preserve context)
    messages = list(state.get("messages", []))

    # Add step context as system message
    messages.append(SystemMessage(content=step_prompt))

    # ReAct loop: reasoning -> action -> observation -> repeat
    tool_lookup = {tool.name: tool for tool in tools}
    llm_with_tools = llm.bind_tools(tools)

    max_iterations = 5  # Prevent infinite loops
    iteration = 0
    actions_taken = []

    while iteration < max_iterations:
        iteration += 1

        # Reasoning: LLM decides what to do
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        # Check if LLM wants to use tools (Action phase)
        if not hasattr(response, "tool_calls") or not response.tool_calls:
            # No more tool calls - LLM is done reasoning for this step
            break

        # Execute tools and observe results
        tool_messages = []
        for tool_call in response.tool_calls:
            tool_name = tool_call.get("name")
            tool_args = tool_call.get("args", {})

            # Display tool being used
            console.print(f"🔧 Using tool: {tool_name}")

            if tool_name not in tool_lookup:
                result = f"Error: Tool '{tool_name}' not found"
            else:
                try:
                    tool = tool_lookup[tool_name]
                    result = tool.invoke(tool_args)
                    actions_taken.append({
                        "tool": tool_name,
                        "args": tool_args,
                        "result": str(result)[:200]  # Truncate for summary
                    })
                except Exception as e:
                    result = f"Error executing tool: {str(e)}"

            # Display tool result
            result_str = str(result)
            if len(result_str) > 300:
                result_str = result_str[:300] + "..."

            console.print(
                Panel(
                    result_str,
                    title=f"Tool Result: {tool_name}",
                    border_style="blue",
                )
            )

            # Add tool result to messages (Observation phase)
            tool_message = ToolMessage(
                content=str(result),
                tool_call_id=tool_call.get("id", ""),
            )
            tool_messages.append(tool_message)

        # Add all tool messages to conversation
        messages.extend(tool_messages)

        # Loop continues - LLM will see tool results and reason about next action

    # After ReAct loop completes, verify if step objective was achieved
    verification_status = _verify_step_completion(
        llm=llm,
        step_description=step_description,
        actions_taken=actions_taken,
        final_response=response.content if hasattr(response, "content") else "",
    )

    # Extract final summary from LLM's last response
    final_summary = response.content if hasattr(response, "content") else "Step executed"

    return {
        "status": verification_status,
        "summary": final_summary,
        "actions_taken": actions_taken,
        "messages": messages[len(state.get("messages", [])):],  # Return only new messages
        "iterations": iteration,
    }


def _verify_step_completion(
    llm: BaseChatModel,
    step_description: str,
    actions_taken: list[dict],
    final_response: str,
) -> str:
    """
    Verify if a step's objective was actually achieved.

    Args:
        llm: Language model
        step_description: The step's objective description
        actions_taken: List of actions/tools used
        final_response: The LLM's final response

    Returns:
        Status: "completed", "partial", "failed", or "blocked"
    """
    if not actions_taken:
        # No actions taken - check if step was deemed unnecessary
        if "not needed" in final_response.lower() or "already" in final_response.lower():
            return "completed"
        return "failed"

    # Build actions summary
    actions_summary = "\n".join([
        f"- Used {action['tool']} with args {action['args']}: {action['result'][:100]}"
        for action in actions_taken
    ])

    # Ask LLM to verify completion
    verification_prompt = STEP_VERIFICATION_PROMPT.format(
        step_description=step_description,
        actions_summary=actions_summary,
    )

    try:
        verification_response = llm.invoke([SystemMessage(content=verification_prompt)])
        response_text = verification_response.content.lower()

        if "completed" in response_text:
            return "completed"
        elif "partial" in response_text:
            return "partial"
        elif "blocked" in response_text:
            return "blocked"
        else:
            return "failed"
    except Exception:
        # If verification fails, assume completed if actions were taken
        return "completed" if actions_taken else "failed"


def reflection_node(state: AgentState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Reflect on completed execution and provide accurate analysis.

    This node analyzes what was actually accomplished versus what was requested,
    providing honest feedback about success, failures, and next steps.

    Args:
        state: Current agent state
        llm: Language model

    Returns:
        State updates with reflection and final response message
    """
    request = state["current_task"]
    plan = state.get("plan", {})
    results = state.get("tool_outputs", [])
    completed_steps = state.get("completed_steps", [])
    failed_steps = state.get("failed_steps", [])
    blocked_steps = state.get("blocked_steps", [])

    # Build comprehensive context for reflection
    total_steps = len(results)
    successful_steps = [r for r in results if r.get("status") == "completed"]
    failed_step_results = [r for r in results if r.get("status") in ["failed", "partial", "blocked"]]

    # Create detailed summary of what happened
    execution_summary = {
        "total_steps": total_steps,
        "completed": len(successful_steps),
        "failed": len(failed_step_results),
        "steps_details": []
    }

    for result in results:
        step_summary = {
            "description": result.get("description", ""),
            "status": result.get("status", "unknown"),
            "summary": result.get("result", "")[:200],
            "actions": len(result.get("actions_taken", []))
        }
        execution_summary["steps_details"].append(step_summary)

    # Use LLM to generate meaningful reflection
    reflection_prompt = REFLECTION_PROMPT.format(
        request=request,
        plan=json.dumps(plan.get("analysis", ""), indent=2)[:300],
        results=json.dumps(execution_summary, indent=2),
        files_modified=", ".join(state.get("gathered_files", [])) or "None"
    )

    try:
        reflection_response = llm.invoke([SystemMessage(content=reflection_prompt)])
        reflection_content = reflection_response.content
    except Exception:
        # Fallback if LLM reflection fails
        reflection_content = _create_fallback_reflection(
            request, successful_steps, failed_step_results, total_steps
        )

    # Create AIMessage for the chat interface
    ai_message = AIMessage(content=reflection_content)

    return {
        "reflection": {
            "summary": reflection_content,
            "completed_steps": len(successful_steps),
            "failed_steps": len(failed_step_results),
            "total_steps": total_steps
        },
        "should_continue": False,
        "messages": [ai_message],
    }


def _create_fallback_reflection(
    request: str,
    successful_steps: list,
    failed_steps: list,
    total_steps: int
) -> str:
    """Create a basic reflection when LLM reflection fails."""
    parts = []
    parts.append(f"## Task Execution Summary\n")
    parts.append(f"**Original Request:** {request}\n")

    # Success summary
    if successful_steps:
        parts.append(f"\n### ✅ Completed Steps ({len(successful_steps)}/{total_steps}):")
        for step in successful_steps[:5]:  # Show first 5
            desc = step.get("description", "Unknown step")
            parts.append(f"- {desc}")

    # Failure summary
    if failed_steps:
        parts.append(f"\n### ❌ Failed/Blocked Steps ({len(failed_steps)}):")
        for step in failed_steps[:5]:
            desc = step.get("description", "Unknown step")
            status = step.get("status", "failed")
            parts.append(f"- {desc} ({status})")

    # Overall assessment
    if not failed_steps:
        parts.append("\n### Assessment\n✅ Task completed successfully!")
    elif len(successful_steps) > len(failed_steps):
        parts.append("\n### Assessment\n⚠️ Task partially completed with some issues.")
    else:
        parts.append("\n### Assessment\n❌ Task encountered significant issues.")

    return "\n".join(parts)
