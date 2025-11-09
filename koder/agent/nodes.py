"""Agent node implementations."""

from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from koder.agent.state import AgentState


SYSTEM_PROMPT = """You are Koder, an AI-powered code assistant.

You help developers with:
- Understanding and analyzing code
- Writing and refactoring code
- Debugging and fixing issues
- Explaining technical concepts
- Working with git repositories

Use the available tools to complete tasks. Think step-by-step about what needs to be done.
"""


def reasoning_node(
    state: AgentState, llm: BaseChatModel, tools: list[BaseTool]
) -> dict[str, Any]:
    """
    Reasoning node: LLM decides what to do next.

    Args:
        state: Current agent state
        llm: Language model instance
        tools: Available tools

    Returns:
        State updates with LLM response
    """
    messages = state["messages"]

    # Add system prompt if this is the first message
    if not messages:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["current_task"]),
        ]

    # Bind tools to LLM and invoke
    llm_with_tools = llm.bind_tools(tools)
    response = llm_with_tools.invoke(messages)

    return {
        "messages": [response],
        "iteration": state["iteration"] + 1,
    }


def action_node(state: AgentState, tools: list[BaseTool]) -> dict[str, Any]:
    """
    Action node: Execute tool calls from LLM.

    Args:
        state: Current agent state
        tools: Available tools

    Returns:
        State updates with tool execution results
    """
    # Get the last message (should be AIMessage with tool calls)
    last_message = state["messages"][-1]

    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"error": "No tool calls found in last message"}

    # Create tool lookup
    tool_lookup = {tool.name: tool for tool in tools}

    # Execute each tool call
    tool_messages = []
    tool_outputs = []

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name not in tool_lookup:
            result = f"Error: Tool '{tool_name}' not found"
        else:
            try:
                tool = tool_lookup[tool_name]
                result = tool.invoke(tool_args)
            except Exception as e:
                result = f"Error executing tool: {str(e)}"

        # Create tool message
        tool_message = ToolMessage(
            content=str(result),
            tool_call_id=tool_call["id"],
        )
        tool_messages.append(tool_message)

        # Store tool output
        tool_outputs.append(
            {
                "tool": tool_name,
                "args": tool_args,
                "result": result,
            }
        )

    return {
        "messages": tool_messages,
        "tool_outputs": state["tool_outputs"] + tool_outputs,
    }


def observation_node(state: AgentState) -> dict[str, Any]:
    """
    Observation node: Process tool results and prepare for next iteration.

    Args:
        state: Current agent state

    Returns:
        State updates after processing observations
    """
    # Check if we should continue based on iteration count
    should_continue = state["iteration"] < state["max_iterations"]

    # Check if there was an error
    if state.get("error"):
        should_continue = False

    return {
        "should_continue": should_continue,
    }


def final_response_node(state: AgentState, llm: BaseChatModel) -> dict[str, Any]:
    """
    Final response node: Generate final response without tool calls.

    Args:
        state: Current agent state
        llm: Language model instance

    Returns:
        State updates with final response
    """
    # Add instruction to provide final answer
    messages = state["messages"] + [
        HumanMessage(
            content="Please provide your final response based on the information gathered."
        )
    ]

    response = llm.invoke(messages)

    return {
        "messages": [response],
        "should_continue": False,
    }
