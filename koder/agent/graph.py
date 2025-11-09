"""Main agent graph definition."""

from functools import partial
from typing import Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph

from koder.agent.edges import (
    check_plan_approval,
    has_more_steps,
    route_by_complexity,
    should_analyze_complexity,
    should_continue_routing,
    should_generate_plan,
    should_observe,
)
from koder.agent.nodes import (
    action_node,
    final_response_node,
    observation_node,
    reasoning_node,
)
from koder.agent.planning_nodes import (
    complexity_analysis_node,
    plan_approval_node,
    plan_execution_node,
    plan_generation_node,
    reflection_node,
)
from koder.agent.state import AgentState


def create_agent_graph(
    llm: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: Optional[SqliteSaver] = None,
):
    """
    Create the ReAct agent graph.

    The graph implements a Reasoning-Action-Observation loop:
    1. Reasoning: LLM decides what to do
    2. Action: Execute tools if needed
    3. Observation: Process results and decide whether to continue

    Args:
        llm: Language model instance
        tools: List of available tools
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled LangGraph instance
    """
    # Create graph with agent state
    workflow = StateGraph(AgentState)

    # Create partial functions with bound dependencies
    reasoning_fn = partial(reasoning_node, llm=llm, tools=tools)
    action_fn = partial(action_node, tools=tools)
    observation_fn = partial(observation_node)
    final_response_fn = partial(final_response_node, llm=llm)

    # Add nodes
    workflow.add_node("reasoning", reasoning_fn)
    workflow.add_node("action", action_fn)
    workflow.add_node("observation", observation_fn)
    workflow.add_node("final_response", final_response_fn)

    # Set entry point
    workflow.set_entry_point("reasoning")

    # Add conditional edges from reasoning node
    workflow.add_conditional_edges(
        "reasoning",
        should_continue_routing,
        {
            "action": "action",
            "final_response": "final_response",
            "end": END,
        },
    )

    # Add edge from action to observation
    workflow.add_conditional_edges(
        "action",
        should_observe,
        {
            "observation": "observation",
            "reasoning": "reasoning",
        },
    )

    # Add edge from observation back to reasoning
    workflow.add_edge("observation", "reasoning")

    # Add edge from final_response to end
    workflow.add_edge("final_response", END)

    # Compile graph with optional checkpointing
    if checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)
    else:
        graph = workflow.compile()

    return graph


def create_planning_graph(
    llm: BaseChatModel,
    tools: list[BaseTool],
    checkpointer: Optional[SqliteSaver] = None,
):
    """
    Create intelligent planning agent graph (Claude Code style).

    The graph automatically analyzes task complexity and chooses execution mode:
    - Simple tasks: Direct execution (ReAct loop)
    - Complex tasks: Plan → Approve → Execute with TODO tracking

    Flow:
        Entry → Complexity Analysis
                  ├─ [Simple] → Quick Execution (ReAct loop)
                  └─ [Complex] → Plan Generation
                                  ↓
                            Plan Approval
                                  ├─ [Approved] → Plan Execution → Reflection
                                  └─ [Rejected] → END

    Args:
        llm: Language model instance
        tools: List of available tools
        checkpointer: Optional checkpointer for state persistence

    Returns:
        Compiled LangGraph instance with planning capabilities
    """
    workflow = StateGraph(AgentState)

    # Create partial functions
    complexity_fn = partial(complexity_analysis_node, llm=llm, tools=tools)
    plan_gen_fn = partial(plan_generation_node, llm=llm, tools=tools)
    plan_approval_fn = partial(plan_approval_node)
    plan_exec_fn = partial(plan_execution_node, llm=llm, tools=tools)
    reflection_fn = partial(reflection_node, llm=llm)

    # Quick mode nodes (existing ReAct)
    reasoning_fn = partial(reasoning_node, llm=llm, tools=tools)
    action_fn = partial(action_node, tools=tools)
    observation_fn = partial(observation_node)
    final_response_fn = partial(final_response_node, llm=llm)

    # === Add All Nodes ===

    # Planning nodes
    workflow.add_node("complexity_analysis", complexity_fn)
    workflow.add_node("plan_generation", plan_gen_fn)
    workflow.add_node("plan_approval", plan_approval_fn)
    workflow.add_node("plan_execution", plan_exec_fn)
    workflow.add_node("reflection", reflection_fn)

    # Quick execution nodes
    workflow.add_node("reasoning", reasoning_fn)
    workflow.add_node("action", action_fn)
    workflow.add_node("observation", observation_fn)
    workflow.add_node("final_response", final_response_fn)

    # === Define Flow ===

    # Entry point: Analyze complexity
    workflow.set_entry_point("complexity_analysis")

    # Route based on complexity
    workflow.add_conditional_edges(
        "complexity_analysis",
        route_by_complexity,
        {
            "quick": "reasoning",  # Simple task → ReAct loop
            "plan": "plan_generation",  # Complex task → Planning
        },
    )

    # === Quick Mode Flow (Simple ReAct) ===
    workflow.add_conditional_edges(
        "reasoning",
        should_continue_routing,
        {
            "action": "action",
            "final_response": "final_response",
            "end": END,
        },
    )

    workflow.add_conditional_edges(
        "action",
        should_observe,
        {
            "observation": "observation",
            "reasoning": "reasoning",
        },
    )

    workflow.add_edge("observation", "reasoning")
    workflow.add_edge("final_response", END)

    # === Plan Mode Flow ===

    # Generate plan → Get approval
    workflow.add_edge("plan_generation", "plan_approval")

    # Check approval status
    workflow.add_conditional_edges(
        "plan_approval",
        check_plan_approval,
        {
            "approved": "plan_execution",
            "rejected": END,
            "pending": "plan_approval",  # Wait for approval
        },
    )

    # Execute plan → Reflect
    workflow.add_edge("plan_execution", "reflection")
    workflow.add_edge("reflection", END)

    # Compile with checkpointing
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        return workflow.compile()


def create_agent(
    llm: BaseChatModel,
    tools: list[BaseTool],
    checkpoint_path: Optional[str] = None,
    mode: str = "auto",
):
    """
    Create agent with checkpointing support.

    Args:
        llm: Language model instance
        tools: List of available tools
        checkpoint_path: Path to checkpoint database (enables persistence)
        mode: Execution mode - "auto" (default, planning graph), "simple" (basic ReAct), "planning" (explicit planning)

    Returns:
        Compiled agent graph
    """
    checkpointer = None
    if checkpoint_path:
        from koder.agent.checkpoints import get_checkpointer

        checkpointer = get_checkpointer(checkpoint_path)

    # Choose graph based on mode
    if mode == "simple":
        # Legacy simple ReAct graph for backward compatibility
        return create_agent_graph(llm, tools, checkpointer)
    else:
        # Default to planning graph (mode="auto" or mode="planning")
        return create_planning_graph(llm, tools, checkpointer)
