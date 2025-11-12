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

    # Enhanced context with discovery results
    context = ""
    if state.get("discovery_results"):
        discovery = state["discovery_results"]
        context = f"""

**Discovery Results:**
- Project Type: {discovery.get('project_type', 'unknown')}
- Tech Stack: {', '.join(discovery.get('tech_stack', {}).get('frameworks', []))}
- Key Files: {len(discovery.get('key_files', []))} configuration files found
- User Intent: {discovery.get('user_intent_understanding', {}).get('clarified_intent', request)}
- Complexity Factors: {json.dumps(discovery.get('complexity_factors', {}), indent=2)}
"""

    # Create enhanced analysis prompt
    prompt = COMPLEXITY_ANALYSIS_PROMPT.format(
        request=request, tools=", ".join(tool_names)
    ) + context

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

    # Gather enhanced context with discovery results
    context = f"Workspace: {state['workspace_path']}\n"

    # Add discovery results if available
    if state.get("discovery_results"):
        discovery = state["discovery_results"]
        # Format discovery data safely for prompt inclusion
        tech_stack = discovery.get('tech_stack', {})
        frameworks = ', '.join(tech_stack.get('frameworks', [])) if tech_stack.get('frameworks') else 'None'
        primary_lang = tech_stack.get('primary_language', 'unknown')

        context += f"""

## Project Discovery Results
**Project Type:** {discovery.get('project_type', 'unknown')}
**Primary Language:** {primary_lang}
**Frameworks:** {frameworks}
**Key Directories:** {len(discovery.get('main_directories', []))} main directories identified
**Dependencies Found:** {len(discovery.get('dependencies', {}))} dependency files
**Relevant Patterns:** {len(discovery.get('relevant_patterns', []))} patterns identified
**User Intent Clarified:** {'Yes' if discovery.get('user_intent_understanding', {}).get('questions_asked') else 'No'}
"""

    if state.get("gathered_files"):
        context += f"\n**Files already read:** {', '.join(state['gathered_files'])}\n"
    if state.get("codebase_summary"):
        context += f"\n**Previous codebase analysis:** {state['codebase_summary']}\n"

    # Build tool list with descriptions
    tool_descriptions = [f"- {tool.name}: {tool.description}" for tool in tools]

    # Add explicit project type context at the very beginning of context
    if state.get("discovery_results"):
        discovery = state["discovery_results"]
        project_type = discovery.get('project_type', 'unknown')
        tech_stack = discovery.get('tech_stack', {})
        primary_lang = tech_stack.get('primary_language', 'unknown')

        # Prepend critical project type information
        context = f"""🎯 **CRITICAL PROJECT TYPE: {project_type.upper()}** 🎯
🎯 **PRIMARY LANGUAGE: {primary_lang.upper()}** 🎯

{context}"""

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

        # Apply language-specific tool enforcement if discovery results available
        if state.get("discovery_results"):
            print(f"🔧 Applying language-specific tool enforcement for {state['discovery_results'].get('project_type', 'unknown')} project...")
            original_plan_tools = [step.get('tool', '') for step in plan.get('steps', [])]
            plan = _enforce_language_specific_tools(plan, state["discovery_results"])
            corrected_plan_tools = [step.get('tool', '') for step in plan.get('steps', [])]
            if original_plan_tools != corrected_plan_tools:
                print(f"✅ Tools corrected: {original_plan_tools} -> {corrected_plan_tools}")
            else:
                print(f"ℹ️  No tool corrections needed")

        return {
            "plan": plan,
            "plan_status": "pending",
            "plan_created_at": plan["created_at"],
            "todos": plan["todos"],
        }

    except (json.JSONDecodeError, ValueError) as e:
        # Fallback: create simple plan with proper structure
        print(f"⚠️  Failed to parse structured plan: {e}")
        print("⚠️  Attempting to fix with language-specific tool enforcement...")

        # Try to extract and fix the plan even if JSON parsing failed
        try:
            # Extract JSON from the response content
            content = response.content.strip()

            # Look for JSON pattern in the content
            json_start = content.find('{')
            json_end = content.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = content[json_start:json_end]
                extracted_plan = json.loads(json_str)

                # Apply language-specific corrections if discovery results available
                if state.get("discovery_results"):
                    extracted_plan = _enforce_language_specific_tools(extracted_plan, state["discovery_results"])

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


def _enforce_language_specific_tools(plan: dict, discovery_results: dict) -> dict:
    """
    Enforce correct tool selection based on discovery results.

    This fixes the issue where LLM ignores discovery context and uses wrong tools.
    """
    if not discovery_results:
        return plan

    project_type = discovery_results.get('project_type', 'unknown')
    tech_stack = discovery_results.get('tech_stack', {})
    primary_lang = tech_stack.get('primary_language', 'unknown')

    # Create mapping of wrong tools to correct tools
    tool_corrections = {}

    if primary_lang == 'go':
        tool_corrections = {
            'parse_python_code': 'parse_go_code',
            'ParsePythonTool': 'ParseGoTool'
        }
    elif primary_lang == 'python':
        tool_corrections = {
            'parse_go_code': 'parse_python_code',
            'ParseGoTool': 'ParsePythonTool'
        }

    # Fix steps
    if 'steps' in plan and isinstance(plan['steps'], list):
        for step in plan['steps']:
            if 'tool' in step and step['tool'] in tool_corrections:
                old_tool = step['tool']
                step['tool'] = tool_corrections[old_tool]
                # Update description to reflect correct language
                if old_tool == 'parse_python_code' and primary_lang == 'go':
                    step['description'] = step['description'].replace('Python', 'Go')
                    step['description'] = step['description'].replace('.py', '.go')
                elif old_tool == 'parse_go_code' and primary_lang == 'python':
                    step['description'] = step['description'].replace('Go', 'Python')
                    step['description'] = step['description'].replace('.go', '.py')

    # Fix file patterns
    if primary_lang == 'go':
        # Replace .py patterns with .go patterns
        for step in plan.get('steps', []):
            if 'file' in step and '**/*.py' in step['file']:
                step['file'] = step['file'].replace('**/*.py', '**/*.go')
    elif primary_lang == 'python':
        # Replace .go patterns with .py patterns
        for step in plan.get('steps', []):
            if 'file' in step and '**/*.go' in step['file']:
                step['file'] = step['file'].replace('**/*.go', '**/*.py')

    # Fix analysis text
    if 'analysis' in plan:
        if primary_lang == 'go':
            plan['analysis'] = plan['analysis'].replace('Python project', 'Go project')
            plan['analysis'] = plan['analysis'].replace('Python-specific tools', 'Go-specific tools')
        elif primary_lang == 'python':
            plan['analysis'] = plan['analysis'].replace('Go project', 'Python project')
            plan['analysis'] = plan['analysis'].replace('Go-specific tools', 'Python-specific tools')

    return plan


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
            # Execute step using LLM with tools (this handles both specified tools and LLM-determined tools)
            result = _execute_step_with_llm(state, llm, tools, step, i)

            # Store result in tool outputs for reflection
            step_result = {
                "step_number": step_number,
                "description": description,
                "tool_name": tool_name,
                "result": result,
                "status": "completed",
            }

            # Mark TODO as completed
            if i < len(todos):
                todos[i]["status"] = "completed"

            completed_steps.append(i)

            # Update state with tool output
            state.setdefault("tool_outputs", []).append(step_result)

        except Exception as e:
            # Mark TODO as failed
            if i < len(todos):
                todos[i]["status"] = "failed"

            error_result = f"Step {step_number} failed: {str(e)}"
            step_result = {
                "step_number": step_number,
                "description": description,
                "tool_name": tool_name,
                "result": error_result,
                "status": "failed",
            }

            state.setdefault("tool_outputs", []).append(step_result)

            return {
                "error": error_result,
                "current_step": i,
                "completed_steps": completed_steps,
                "failed_steps": [i],
                "todos": todos,
                "tool_outputs": state.get("tool_outputs", []),
            }

    # All steps completed
    format_todo_list(todos, title="Completed")

    return {
        "plan_status": "completed",
        "current_step": total_steps,
        "completed_steps": completed_steps,
        "todos": todos,
        "should_continue": False,
        "tool_outputs": state.get("tool_outputs", []),
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
    from koder.cli.ui.console import console
    from rich.panel import Panel

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

                # Display tool being used
                console.print(f"🔧 Using tool: {tool_name}")

                # Execute tool
                result = tool.invoke(tool_args)
                results.append(result)

                # Display tool result
                if hasattr(result, "__len__") and len(str(result)) > 300:
                    # Truncate long results
                    result_str = str(result)[:300] + "..."
                else:
                    result_str = str(result)

                console.print(
                    Panel(
                        result_str,
                        title=f"Tool Result: {tool_name}",
                        border_style="blue",
                    )
                )

        return " | ".join(str(r) for r in results) if results else response.content

    return response.content


def reflection_node(state: AgentState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Reflect on completed execution and provide summary.

    Args:
        state: Current agent state
        llm: Language model

    Returns:
        State updates with reflection and final response message
    """
    from langchain_core.messages import AIMessage

    request = state["current_task"]
    plan = state.get("plan", {})
    results = state.get("tool_outputs", [])
    files_modified = state.get("gathered_files", [])

    # Create a summary of what was accomplished
    summary_parts = []
    summary_parts.append(f"## Project Analysis Complete ✅")
    summary_parts.append(f"**Original Request:** {request}")

    if results:
        summary_parts.append(f"\n### What I Found:")
        for i, result in enumerate(results):
            if result.get("status") == "completed":
                summary_parts.append(
                    f"**{result.get('description', 'Step ' + str(i + 1))}** ✅"
                )
                # Extract key information from tool results
                tool_result = result.get("result", "")
                if "Contents of" in str(tool_result) or "Found" in str(tool_result):
                    summary_parts.append(f"  {str(tool_result)[:200]}...")

    # Create final response
    final_response = "\n\n".join(summary_parts)

    # Create AIMessage for the chat interface
    ai_message = AIMessage(content=final_response)

    return {
        "reflection": {"summary": final_response},
        "should_continue": False,
        "messages": [ai_message],  # Add the response message for display
    }
