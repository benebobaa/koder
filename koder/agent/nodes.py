"""Agent node implementations."""

import hashlib
import time
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool

from koder.agent.state import AgentState


# Simple context cache to minimize API calls
_context_cache = {}
_cache_ttl = 300  # 5 minutes


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

    Enhanced with automatic context retrieval for better decision making.

    Args:
        state: Current agent state
        llm: Language model instance
        tools: Available tools

    Returns:
        State updates with LLM response
    """
    messages = state["messages"]

    # If this is the first reasoning call (iteration == 0), add context
    if state["iteration"] == 0:
        # Auto-gather context using embeddings if available
        context = _auto_gather_context(state["current_task"], tools)

        # Create enhanced messages with context
        enhanced_messages = [SystemMessage(content=SYSTEM_PROMPT)]

        # Add context if available
        if context and context != "Context retrieval is not available.":
            context_message = SystemMessage(content=f"""CONTEXT FROM CODEBASE:
{context}

Use this context to better understand the codebase and make more informed decisions.
The context above provides relevant information about similar patterns, existing implementations,
and code structure that should inform your approach to the task.""")
            enhanced_messages.append(context_message)

        # Add the original messages (usually contains the task)
        enhanced_messages.extend(messages)

        messages = enhanced_messages

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


def _auto_gather_context(task: str, tools: list[BaseTool]) -> str:
    """
    Automatically gather relevant context using embeddings before reasoning.

    This function makes the embedding investment worthwhile by providing
    intelligent context to the agent before it makes decisions.

    Includes caching to minimize API calls and improve performance.

    Args:
        task: The current task description
        tools: List of available tools

    Returns:
        Relevant context from the codebase or empty string if unavailable
    """
    try:
        # Create cache key from task
        cache_key = hashlib.md5(task.encode()).hexdigest()
        current_time = time.time()

        # Check cache first
        if cache_key in _context_cache:
            cached_data = _context_cache[cache_key]
            if current_time - cached_data['timestamp'] < _cache_ttl:
                return cached_data['context']

        # Find the context retrieval tool
        context_tool = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == "context_retrieval":
                context_tool = tool
                break

        if not context_tool:
            return ""

        # Use semantic search to get relevant context
        # Get more results for better context (5 instead of default 3)
        context = context_tool._run(task, max_results=5)

        # Filter out unhelpful responses
        if (not context or
            context == "Context retrieval is not available." or
            context == "No relevant context found." or
            "Error retrieving context:" in context or
            len(context.strip()) < 50):
            return ""

        # Add context quality indicator
        lines = context.split('\n')
        file_count = len([line for line in lines if line.strip().startswith('[') and 'From ' in line])

        if file_count > 0:
            result = f"{context}\n\n*(Found {file_count} relevant files using semantic search)*"

            # Cache the result
            _context_cache[cache_key] = {
                'context': result,
                'timestamp': current_time
            }

            return result
        else:
            return ""

    except Exception as e:
        # Silently fail - context is enhancement, not requirement
        return ""
