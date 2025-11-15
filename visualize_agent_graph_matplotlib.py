#!/usr/bin/env python3
"""
Visualize Koder Agent Architecture using matplotlib/networkx

Alternative visualization using networkx and matplotlib (no graphviz needed)

Requirements:
    pip install networkx matplotlib

Usage:
    python visualize_agent_graph_matplotlib.py
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import FancyBboxPatch


def create_simple_react_graph():
    """Create visualization of the simple ReAct loop graph."""
    G = nx.DiGraph()

    # Add nodes
    nodes = {
        'ENTRY': {'color': 'lightgreen', 'shape': 'o'},
        'Reasoning': {'color': 'lightblue', 'shape': 's'},
        'Action': {'color': 'lightcoral', 'shape': 's'},
        'Observation': {'color': 'lightyellow', 'shape': 's'},
        'Final Response': {'color': 'lightgreen', 'shape': 's'},
        'END': {'color': 'lightcoral', 'shape': 'o'},
    }

    for node in nodes:
        G.add_node(node)

    # Add edges with labels
    edges = [
        ('ENTRY', 'Reasoning', ''),
        ('Reasoning', 'Action', 'has tools'),
        ('Reasoning', 'Final Response', 'done'),
        ('Action', 'Observation', 'results'),
        ('Observation', 'Reasoning', 'loop'),
        ('Final Response', 'END', ''),
    ]

    for src, dst, label in edges:
        G.add_edge(src, dst, label=label)

    # Layout
    pos = {
        'ENTRY': (0, 4),
        'Reasoning': (0, 3),
        'Action': (-1, 2),
        'Observation': (-1, 1),
        'Final Response': (1, 2),
        'END': (0, 0),
    }

    return G, pos, nodes, edges


def create_planning_graph():
    """Create visualization of the planning graph."""
    G = nx.DiGraph()

    # Add nodes
    nodes = {
        'ENTRY': {'color': 'lightgreen', 'shape': 'o'},
        'Complexity\nAnalysis': {'color': 'lavender', 'shape': 's'},
        'Simple\nReAct': {'color': 'lightblue', 'shape': 's'},
        'Plan\nGeneration': {'color': 'plum', 'shape': 's'},
        'Plan\nApproval': {'color': 'gold', 'shape': 's'},
        'Plan\nExecution': {'color': 'orange', 'shape': 's'},
        'Reflection': {'color': 'lightgreen', 'shape': 's'},
        'END': {'color': 'lightcoral', 'shape': 'o'},
    }

    for node in nodes:
        G.add_node(node)

    # Add edges
    edges = [
        ('ENTRY', 'Complexity\nAnalysis', ''),
        ('Complexity\nAnalysis', 'Simple\nReAct', 'simple'),
        ('Complexity\nAnalysis', 'Plan\nGeneration', 'complex'),
        ('Simple\nReAct', 'END', ''),
        ('Plan\nGeneration', 'Plan\nApproval', ''),
        ('Plan\nApproval', 'Plan\nExecution', 'approved'),
        ('Plan\nApproval', 'END', 'rejected'),
        ('Plan\nExecution', 'Reflection', ''),
        ('Reflection', 'END', ''),
    ]

    for src, dst, label in edges:
        G.add_edge(src, dst, label=label)

    # Layout
    pos = {
        'ENTRY': (2, 5),
        'Complexity\nAnalysis': (2, 4),
        'Simple\nReAct': (0, 3),
        'Plan\nGeneration': (4, 3),
        'Plan\nApproval': (4, 2),
        'Plan\nExecution': (4, 1),
        'Reflection': (4, 0),
        'END': (2, -1),
    }

    return G, pos, nodes, edges


def create_step_execution_graph():
    """Create detailed step execution with ReAct loop."""
    G = nx.DiGraph()

    nodes = {
        'Start Step': {'color': 'lightgreen', 'shape': 'o'},
        'Load\nContext': {'color': 'lavender', 'shape': 's'},
        'LLM\nReasoning': {'color': 'lightblue', 'shape': 's'},
        'Has Tools?': {'color': 'gold', 'shape': 'd'},
        'Execute\nTools': {'color': 'lightcoral', 'shape': 's'},
        'Add Results\n(Observe)': {'color': 'lightyellow', 'shape': 's'},
        'Max Iter?': {'color': 'gold', 'shape': 'd'},
        'Verify\nCompletion': {'color': 'plum', 'shape': 's'},
        'Update\nStatus': {'color': 'orange', 'shape': 's'},
        'End Step': {'color': 'lightcoral', 'shape': 'o'},
    }

    for node in nodes:
        G.add_node(node)

    edges = [
        ('Start Step', 'Load\nContext', ''),
        ('Load\nContext', 'LLM\nReasoning', ''),
        ('LLM\nReasoning', 'Has Tools?', ''),
        ('Has Tools?', 'Execute\nTools', 'YES'),
        ('Has Tools?', 'Verify\nCompletion', 'NO'),
        ('Execute\nTools', 'Add Results\n(Observe)', ''),
        ('Add Results\n(Observe)', 'Max Iter?', ''),
        ('Max Iter?', 'LLM\nReasoning', '<5'),
        ('Max Iter?', 'Verify\nCompletion', '>=5'),
        ('Verify\nCompletion', 'Update\nStatus', ''),
        ('Update\nStatus', 'End Step', ''),
    ]

    for src, dst, label in edges:
        G.add_edge(src, dst, label=label)

    # Circular-ish layout for the ReAct loop
    pos = {
        'Start Step': (0, 5),
        'Load\nContext': (0, 4),
        'LLM\nReasoning': (0, 3),
        'Has Tools?': (0, 2),
        'Execute\nTools': (-1.5, 1.5),
        'Add Results\n(Observe)': (-1.5, 0.5),
        'Max Iter?': (-0.75, 0),
        'Verify\nCompletion': (1, 1),
        'Update\nStatus': (1, 0),
        'End Step': (0, -1),
    }

    return G, pos, nodes, edges


def plot_graph(G, pos, nodes, edges, title, filename):
    """Plot a graph with nice styling."""
    fig, ax = plt.subplots(figsize=(12, 10))
    ax.set_aspect('equal')
    ax.axis('off')

    # Draw edges with labels
    for src, dst, label in edges:
        if label:
            nx.draw_networkx_edges(
                G, pos, [(src, dst)],
                edge_color='gray',
                arrows=True,
                arrowsize=20,
                arrowstyle='->',
                connectionstyle='arc3,rad=0.1',
                width=2,
                ax=ax
            )

    # Draw edge labels
    edge_labels = {(src, dst): label for src, dst, label in edges if label}
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels,
        font_size=8,
        font_color='darkblue',
        ax=ax
    )

    # Draw nodes
    for node, attrs in nodes.items():
        x, y = pos[node]
        color = attrs['color']
        shape = attrs.get('shape', 's')

        if shape == 'o':  # Circle
            circle = plt.Circle((x, y), 0.3, color=color, ec='black', linewidth=2, zorder=3)
            ax.add_patch(circle)
        elif shape == 'd':  # Diamond
            diamond = mpatches.RegularPolygon(
                (x, y), 4, radius=0.35, orientation=0.785,
                facecolor=color, edgecolor='black', linewidth=2, zorder=3
            )
            ax.add_patch(diamond)
        else:  # Rectangle
            rect = FancyBboxPatch(
                (x - 0.4, y - 0.25), 0.8, 0.5,
                boxstyle="round,pad=0.05",
                facecolor=color,
                edgecolor='black',
                linewidth=2,
                zorder=3
            )
            ax.add_patch(rect)

        # Add text
        ax.text(x, y, node, ha='center', va='center', fontsize=9, fontweight='bold', zorder=4)

    # Set title
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)

    # Adjust limits
    x_values = [pos[node][0] for node in nodes]
    y_values = [pos[node][1] for node in nodes]
    margin = 1
    ax.set_xlim(min(x_values) - margin, max(x_values) + margin)
    ax.set_ylim(min(y_values) - margin, max(y_values) + margin)

    plt.tight_layout()
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Generated: {filename}")
    plt.close()


def create_comparison_figure():
    """Create side-by-side comparison of old vs new."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Old way (left)
    ax1.set_title("OLD: Mechanical Execution", fontsize=14, fontweight='bold')
    ax1.axis('off')
    ax1.set_xlim(0, 10)
    ax1.set_ylim(0, 10)

    # Old nodes
    old_nodes = [
        (5, 8, 'Step N', 'lightblue'),
        (5, 6, 'LLM: 1 Call', 'lightyellow'),
        (5, 4, 'Execute Tool', 'lightcoral'),
        (5, 2, 'Mark DONE', 'lightcoral'),
    ]

    for x, y, label, color in old_nodes:
        rect = FancyBboxPatch(
            (x - 1, y - 0.3), 2, 0.6,
            boxstyle="round,pad=0.05",
            facecolor=color,
            edgecolor='black',
            linewidth=2
        )
        ax1.add_patch(rect)
        ax1.text(x, y, label, ha='center', va='center', fontsize=10, fontweight='bold')

        # Draw arrows
        if y > 2:
            ax1.arrow(5, y - 0.4, 0, -1.3, head_width=0.2, head_length=0.15,
                     fc='gray', ec='gray', linewidth=2)

    # Problems text
    ax1.text(5, 0.5, 'Problems:\n• No reasoning\n• No adaptation\n• False completions',
            ha='center', va='top', fontsize=10, bbox=dict(boxstyle='round', facecolor='pink', alpha=0.7))

    # New way (right)
    ax2.set_title("NEW: ReAct Loop per Step", fontsize=14, fontweight='bold')
    ax2.axis('off')
    ax2.set_xlim(0, 10)
    ax2.set_ylim(0, 10)

    # New nodes
    new_nodes = [
        (5, 9, 'Step N\n+ Context', 'lightblue'),
        (5, 7.5, 'Reason', 'lightyellow'),
        (5, 6, 'Act', 'lightcoral'),
        (5, 4.5, 'Observe', 'lightgreen'),
        (3, 3, 'Continue?', 'gold'),
        (7, 2, 'Verify', 'plum'),
        (7, 0.5, 'Mark Status', 'green'),
    ]

    for x, y, label, color in new_nodes:
        if 'Continue?' in label:
            # Diamond
            diamond = mpatches.RegularPolygon(
                (x, y), 4, radius=0.5, orientation=0.785,
                facecolor=color, edgecolor='black', linewidth=2
            )
            ax2.add_patch(diamond)
        else:
            rect = FancyBboxPatch(
                (x - 0.8, y - 0.25), 1.6, 0.5,
                boxstyle="round,pad=0.05",
                facecolor=color,
                edgecolor='black',
                linewidth=2
            )
            ax2.add_patch(rect)
        ax2.text(x, y, label, ha='center', va='center', fontsize=9, fontweight='bold')

    # Arrows
    arrows = [
        (5, 8.7, 5, 7.8),
        (5, 7.2, 5, 6.3),
        (5, 5.7, 5, 4.8),
        (5, 4.2, 3, 3.5),
        (3.5, 2.5, 5, 7.2),  # Loop back
        (3, 2.7, 6.2, 2.2),
        (7, 1.7, 7, 0.8),
    ]

    for x1, y1, x2, y2 in arrows:
        ax2.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=2, color='gray'))

    # Benefits text
    ax2.text(5, -0.5, 'Benefits:\n• Continuous reasoning\n• Adapts to issues\n• Verified outcomes',
            ha='center', va='top', fontsize=10, bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.7))

    plt.suptitle('Comparison: Old vs New Planning Mode Step Execution', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()

    filename = 'docs/diagrams/comparison_matplotlib.png'
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"✅ Generated: {filename}")
    plt.close()


def main():
    """Generate all visualizations."""
    print("🎨 Generating agent architecture visualizations (matplotlib)...\n")

    # Create output directory
    import os
    output_dir = "docs/diagrams"
    os.makedirs(output_dir, exist_ok=True)

    # Generate diagrams
    print("Generating graphs...")

    # 1. Simple ReAct Graph
    G, pos, nodes, edges = create_simple_react_graph()
    plot_graph(G, pos, nodes, edges,
              "Simple ReAct Graph (Non-Planning Mode)\n\nContinuous reasoning-action-observation loop",
              f"{output_dir}/simple_react_matplotlib.png")

    # 2. Planning Graph
    G, pos, nodes, edges = create_planning_graph()
    plot_graph(G, pos, nodes, edges,
              "Planning Graph\n\nRoutes by complexity: Simple → ReAct | Complex → Plan → ReAct",
              f"{output_dir}/planning_matplotlib.png")

    # 3. Step Execution Detail
    G, pos, nodes, edges = create_step_execution_graph()
    plot_graph(G, pos, nodes, edges,
              "Plan Step Execution (New ReAct Loop Architecture)\n\nEach step has full reasoning capability",
              f"{output_dir}/step_execution_matplotlib.png")

    # 4. Comparison
    create_comparison_figure()

    print(f"\n🎉 All diagrams generated in '{output_dir}/' directory!")
    print("\nGenerated diagrams (matplotlib versions):")
    print("1. simple_react_matplotlib.png - Basic ReAct loop")
    print("2. planning_matplotlib.png - Planning graph with routing")
    print("3. step_execution_matplotlib.png - Detailed ReAct in steps")
    print("4. comparison_matplotlib.png - Old vs new comparison")


if __name__ == "__main__":
    main()
