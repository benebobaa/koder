#!/usr/bin/env python3
"""
Visualize Koder Agent Architecture

This script creates visual representations of:
1. Simple ReAct Graph (non-planning mode)
2. Planning Graph (planning mode with ReAct loop in steps)

Requirements:
    pip install graphviz

Usage:
    python visualize_agent_graph.py
"""

from graphviz import Digraph


def create_simple_react_graph():
    """Create visualization of the simple ReAct loop graph."""
    dot = Digraph(comment='Simple ReAct Graph', format='png')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Add nodes
    dot.node('entry', 'ENTRY', shape='circle', fillcolor='green')
    dot.node('reasoning', 'Reasoning Node\n(LLM decides next action)')
    dot.node('action', 'Action Node\n(Execute tools)', fillcolor='lightcoral')
    dot.node('observation', 'Observation Node\n(Process results)', fillcolor='lightyellow')
    dot.node('final', 'Final Response Node\n(Generate summary)', fillcolor='lightgreen')
    dot.node('end', 'END', shape='circle', fillcolor='red')

    # Add edges with labels
    dot.edge('entry', 'reasoning')

    # From reasoning
    dot.edge('reasoning', 'action', label='has tool calls')
    dot.edge('reasoning', 'final', label='done reasoning')
    dot.edge('reasoning', 'end', label='max iterations')

    # From action
    dot.edge('action', 'observation', label='observe results')
    dot.edge('action', 'reasoning', label='continue')

    # From observation
    dot.edge('observation', 'reasoning', label='continue loop')

    # From final
    dot.edge('final', 'end')

    dot.attr(label='Simple ReAct Graph (Non-Planning Mode)\n\nContinuous reasoning-action-observation loop')
    dot.attr(fontsize='16')

    return dot


def create_planning_graph():
    """Create visualization of the planning graph with ReAct loop in execution."""
    dot = Digraph(comment='Planning Graph', format='png')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Add nodes
    dot.node('entry', 'ENTRY', shape='circle', fillcolor='green')
    dot.node('complexity', 'Complexity Analysis\n(Determine task complexity)', fillcolor='lavender')

    # Quick path (simple tasks)
    dot.node('reasoning_quick', 'Reasoning\n(Simple ReAct Loop)', fillcolor='lightblue')
    dot.node('action_quick', 'Action', fillcolor='lightcoral')
    dot.node('observation_quick', 'Observation', fillcolor='lightyellow')
    dot.node('final_quick', 'Final Response', fillcolor='lightgreen')

    # Plan path (complex tasks)
    dot.node('plan_gen', 'Plan Generation\n(Create structured plan)', fillcolor='plum')
    dot.node('plan_approval', 'Plan Approval\n(User reviews plan)', fillcolor='gold')
    dot.node('plan_exec', 'Plan Execution\n(Execute steps with ReAct)', fillcolor='orange')
    dot.node('reflection', 'Reflection\n(Analyze outcomes)', fillcolor='lightgreen')

    dot.node('end', 'END', shape='circle', fillcolor='red')

    # Main flow
    dot.edge('entry', 'complexity')

    # Quick path
    dot.edge('complexity', 'reasoning_quick', label='simple task')
    dot.edge('reasoning_quick', 'action_quick', label='tool calls')
    dot.edge('reasoning_quick', 'final_quick', label='done')
    dot.edge('action_quick', 'observation_quick')
    dot.edge('observation_quick', 'reasoning_quick', label='loop')
    dot.edge('final_quick', 'end')

    # Plan path
    dot.edge('complexity', 'plan_gen', label='complex task')
    dot.edge('plan_gen', 'plan_approval')
    dot.edge('plan_approval', 'plan_exec', label='approved')
    dot.edge('plan_approval', 'end', label='rejected')
    dot.edge('plan_exec', 'reflection')
    dot.edge('reflection', 'end')

    dot.attr(label='Planning Graph\n\nRoutes by complexity: Simple → ReAct Loop | Complex → Plan → ReAct per Step')
    dot.attr(fontsize='16')

    return dot


def create_step_execution_detail():
    """Create detailed visualization of step execution with ReAct loop."""
    dot = Digraph(comment='Step Execution Detail', format='png')
    dot.attr(rankdir='TB')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # Add title
    dot.attr(label='Plan Step Execution (New ReAct Loop Architecture)\n\nEach step now has full reasoning capability')
    dot.attr(fontsize='16')

    # Cluster for context
    with dot.subgraph(name='cluster_context') as c:
        c.attr(label='Context Preservation', style='dashed', color='blue')
        c.node('msg_history', 'Full Message History\nfrom Previous Steps', fillcolor='lightyellow')

    # Step execution flow
    dot.node('step_start', 'Start Step Execution', shape='ellipse', fillcolor='lightgreen')
    dot.node('load_context', 'Load Full Context\n+ Step Objective', fillcolor='lavender')
    dot.node('react_reasoning', 'LLM Reasoning\n(What to do next?)', fillcolor='lightblue')
    dot.node('check_tools', 'Has Tool Calls?', shape='diamond', fillcolor='gold')
    dot.node('execute_tools', 'Execute Tools\n(Action Phase)', fillcolor='lightcoral')
    dot.node('add_results', 'Add Tool Results\n(Observation Phase)', fillcolor='lightyellow')
    dot.node('check_iter', 'Max Iterations?', shape='diamond', fillcolor='gold')
    dot.node('verify', 'Verify Step Completion\n(LLM validates objective)', fillcolor='plum')
    dot.node('update_status', 'Update Status\n(completed/failed/blocked)', fillcolor='orange')
    dot.node('step_end', 'End Step', shape='ellipse', fillcolor='red')

    # Flow
    dot.edge('msg_history', 'load_context', label='provides')
    dot.edge('step_start', 'load_context')
    dot.edge('load_context', 'react_reasoning')
    dot.edge('react_reasoning', 'check_tools')
    dot.edge('check_tools', 'execute_tools', label='YES\nuse tools')
    dot.edge('check_tools', 'verify', label='NO\nno more tools')
    dot.edge('execute_tools', 'add_results')
    dot.edge('add_results', 'check_iter')
    dot.edge('check_iter', 'react_reasoning', label='NO\niterate < 5')
    dot.edge('check_iter', 'verify', label='YES\nmax reached')
    dot.edge('verify', 'update_status')
    dot.edge('update_status', 'step_end')
    dot.edge('step_end', 'msg_history', label='accumulate\nfor next step', style='dashed')

    return dot


def create_comparison_diagram():
    """Create side-by-side comparison of old vs new planning mode."""
    dot = Digraph(comment='Old vs New Planning', format='png')
    dot.attr(rankdir='LR')
    dot.attr('node', shape='box', style='rounded,filled')

    # Old way
    with dot.subgraph(name='cluster_old') as c:
        c.attr(label='OLD: Mechanical Execution', style='filled', color='lightgray', fillcolor='mistyrose')
        c.node('old_step', 'Step N', fillcolor='lightblue')
        c.node('old_llm', 'LLM: 1 Call', fillcolor='lightyellow')
        c.node('old_tool', 'Execute Tool', fillcolor='lightcoral')
        c.node('old_done', 'Mark DONE', fillcolor='red')

        c.edge('old_step', 'old_llm')
        c.edge('old_llm', 'old_tool')
        c.edge('old_tool', 'old_done')

    # New way
    with dot.subgraph(name='cluster_new') as c:
        c.attr(label='NEW: ReAct Loop per Step', style='filled', color='lightgray', fillcolor='lightcyan')
        c.node('new_step', 'Step N\n+ Full Context', fillcolor='lightblue')
        c.node('new_reason', 'Reason', fillcolor='lightyellow')
        c.node('new_action', 'Act', fillcolor='lightcoral')
        c.node('new_observe', 'Observe', fillcolor='lightgreen')
        c.node('new_loop', 'Continue?', shape='diamond', fillcolor='gold')
        c.node('new_verify', 'Verify\nObjective', fillcolor='plum')
        c.node('new_status', 'Mark Status\n(verified)', fillcolor='green')

        c.edge('new_step', 'new_reason')
        c.edge('new_reason', 'new_action')
        c.edge('new_action', 'new_observe')
        c.edge('new_observe', 'new_loop')
        c.edge('new_loop', 'new_reason', label='YES')
        c.edge('new_loop', 'new_verify', label='NO')
        c.edge('new_verify', 'new_status')

    # Comparison labels
    dot.node('old_label', 'Problems:\n• No reasoning\n• No adaptation\n• False completions',
             shape='note', fillcolor='pink', fontsize='10')
    dot.node('new_label', 'Benefits:\n• Continuous reasoning\n• Adapts to issues\n• Verified outcomes',
             shape='note', fillcolor='lightgreen', fontsize='10')

    dot.attr(label='Comparison: Old vs New Planning Mode Step Execution')
    dot.attr(fontsize='16')

    return dot


def create_full_system_architecture():
    """Create complete system architecture showing all components."""
    dot = Digraph(comment='Full System Architecture', format='png')
    dot.attr(rankdir='TB', size='16,12')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

    # User interaction layer
    with dot.subgraph(name='cluster_user') as c:
        c.attr(label='User Interface', style='filled', fillcolor='aliceblue')
        c.node('cli', 'CLI\n(Typer)', fillcolor='lightsteelblue')
        c.node('chat', 'Chat Mode', fillcolor='lightskyblue')
        c.node('task', 'Task Mode', fillcolor='lightskyblue')

    # Agent core
    with dot.subgraph(name='cluster_agent') as c:
        c.attr(label='Agent Core (LangGraph)', style='filled', fillcolor='lavender')
        c.node('graph_router', 'Mode Router', shape='diamond', fillcolor='gold')
        c.node('simple_graph', 'Simple ReAct\nGraph', fillcolor='lightblue')
        c.node('planning_graph', 'Planning\nGraph', fillcolor='plum')

    # Planning components
    with dot.subgraph(name='cluster_planning') as c:
        c.attr(label='Planning Components', style='filled', fillcolor='mistyrose')
        c.node('complexity_node', 'Complexity\nAnalysis', fillcolor='lavender')
        c.node('plan_gen_node', 'Plan\nGeneration', fillcolor='plum')
        c.node('plan_exec_node', 'Plan Execution\n(ReAct per Step)', fillcolor='orange')
        c.node('reflect_node', 'Reflection', fillcolor='lightgreen')

    # Tools layer
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(label='Tools & Integrations', style='filled', fillcolor='lightyellow')
        c.node('tool_registry', 'Tool Registry', fillcolor='gold')
        c.node('file_tools', 'File I/O\nTools', fillcolor='wheat')
        c.node('git_tools', 'Git\nTools', fillcolor='wheat')
        c.node('code_tools', 'Code Parsing\nTools', fillcolor='wheat')
        c.node('web_tools', 'Web Search\nTools', fillcolor='wheat')

    # LLM layer
    with dot.subgraph(name='cluster_llm') as c:
        c.attr(label='LLM Providers', style='filled', fillcolor='lightcyan')
        c.node('llm_factory', 'LLM Factory', fillcolor='skyblue')
        c.node('anthropic', 'Anthropic\nClaude', fillcolor='lightcyan')
        c.node('openai', 'OpenAI\nGPT', fillcolor='lightcyan')
        c.node('deepseek', 'DeepSeek', fillcolor='lightcyan')

    # Memory layer
    with dot.subgraph(name='cluster_memory') as c:
        c.attr(label='Memory & State', style='filled', fillcolor='lightgoldenrodyellow')
        c.node('state', 'Agent State', fillcolor='khaki')
        c.node('chromadb', 'ChromaDB\n(Vector Store)', fillcolor='khaki')
        c.node('sqlite', 'SQLite\n(Checkpointing)', fillcolor='khaki')

    # Connections
    dot.edge('cli', 'chat')
    dot.edge('cli', 'task')
    dot.edge('chat', 'graph_router')
    dot.edge('task', 'graph_router')

    dot.edge('graph_router', 'simple_graph', label='mode=simple')
    dot.edge('graph_router', 'planning_graph', label='mode=auto/plan')

    dot.edge('planning_graph', 'complexity_node')
    dot.edge('complexity_node', 'plan_gen_node', label='complex')
    dot.edge('plan_gen_node', 'plan_exec_node')
    dot.edge('plan_exec_node', 'reflect_node')

    dot.edge('simple_graph', 'tool_registry', style='dashed')
    dot.edge('plan_exec_node', 'tool_registry', style='dashed')

    dot.edge('tool_registry', 'file_tools')
    dot.edge('tool_registry', 'git_tools')
    dot.edge('tool_registry', 'code_tools')
    dot.edge('tool_registry', 'web_tools')

    dot.edge('simple_graph', 'llm_factory', style='dashed')
    dot.edge('planning_graph', 'llm_factory', style='dashed')

    dot.edge('llm_factory', 'anthropic')
    dot.edge('llm_factory', 'openai')
    dot.edge('llm_factory', 'deepseek')

    dot.edge('simple_graph', 'state', style='dashed', dir='both')
    dot.edge('planning_graph', 'state', style='dashed', dir='both')
    dot.edge('state', 'chromadb')
    dot.edge('state', 'sqlite')

    dot.attr(label='Koder Agent - Full System Architecture')
    dot.attr(fontsize='20')

    return dot


def main():
    """Generate all visualizations."""
    print("🎨 Generating agent architecture visualizations...\n")

    # Create output directory
    import os
    output_dir = "docs/diagrams"
    os.makedirs(output_dir, exist_ok=True)

    # Generate diagrams
    diagrams = {
        'simple_react_graph': (create_simple_react_graph(), "Simple ReAct Graph"),
        'planning_graph': (create_planning_graph(), "Planning Graph"),
        'step_execution_detail': (create_step_execution_detail(), "Step Execution Detail"),
        'comparison': (create_comparison_diagram(), "Old vs New Comparison"),
        'full_architecture': (create_full_system_architecture(), "Full System Architecture"),
    }

    for name, (graph, description) in diagrams.items():
        filepath = f"{output_dir}/{name}"
        graph.render(filepath, cleanup=True)
        print(f"✅ Generated: {filepath}.png - {description}")

    print(f"\n🎉 All diagrams generated in '{output_dir}/' directory!")
    print("\nGenerated diagrams:")
    print("1. simple_react_graph.png - Shows the basic ReAct loop")
    print("2. planning_graph.png - Shows the planning graph with routing")
    print("3. step_execution_detail.png - Detailed view of ReAct loop in step execution")
    print("4. comparison.png - Side-by-side comparison of old vs new")
    print("5. full_architecture.png - Complete system architecture")


if __name__ == "__main__":
    main()
