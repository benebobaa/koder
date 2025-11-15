#!/usr/bin/env python3
"""
Text-based visualization of Koder agent architecture.

No dependencies required - runs anywhere!

Usage:
    python show_architecture.py
"""


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def show_simple_react_graph():
    """Show simple ReAct graph in ASCII."""
    print_header("SIMPLE REACT GRAPH (Non-Planning Mode)")

    print("""
                            ┌─────────┐
                            │  ENTRY  │
                            └────┬────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │   Reasoning    │◄──────────┐
                        │  (LLM decides  │           │
                        │  next action)  │           │
                        └───┬────────┬───┘           │
                            │        │               │
                   has      │        │  done         │
                   tools    │        │  reasoning    │
                            │        │               │
                            ▼        ▼               │
                     ┌──────────┐  ┌─────────────┐  │
                     │  Action  │  │   Final     │  │
                     │ (Execute │  │  Response   │  │
                     │  tools)  │  └──────┬──────┘  │
                     └────┬─────┘         │         │
                          │               │         │
                          ▼               ▼         │
                   ┌────────────┐      ┌─────┐     │
                   │Observation │      │ END │     │
                   │  (Process  │      └─────┘     │
                   │  results)  │                  │
                   └─────┬──────┘                  │
                         │                         │
                         └─────────────────────────┘
                              (loop back)

    Key Features:
    • Continuous reasoning-action-observation loop
    • LLM can iterate multiple times until task complete
    • Full context preserved across iterations
    • Works well for simple, focused tasks
    """)


def show_planning_graph():
    """Show planning graph in ASCII."""
    print_header("PLANNING GRAPH (Complex Tasks)")

    print("""
                            ┌─────────┐
                            │  ENTRY  │
                            └────┬────┘
                                 │
                                 ▼
                        ┌────────────────┐
                        │   Complexity   │
                        │    Analysis    │
                        └───┬────────┬───┘
                            │        │
                   simple   │        │  complex
                   task     │        │  task
                            │        │
                            ▼        ▼
                    ┌────────────┐ ┌────────────┐
                    │   Simple   │ │    Plan    │
                    │   ReAct    │ │ Generation │
                    │   Loop     │ └─────┬──────┘
                    └─────┬──────┘       │
                          │              ▼
                          │      ┌────────────┐
                          │      │    Plan    │
                          │      │  Approval  │
                          │      └──┬─────┬───┘
                          │         │     │
                          │    approved rejected
                          │         │     │
                          │         ▼     │
                          │    ┌──────────────┐
                          │    │     Plan     │
                          │    │  Execution   │
                          │    │ (ReAct loop  │
                          │    │  per step)   │
                          │    └──────┬───────┘
                          │           │
                          │           ▼
                          │    ┌────────────┐
                          │    │ Reflection │
                          │    └──────┬─────┘
                          │           │
                          ▼           ▼
                        ┌─────────────────┐
                        │       END       │
                        └─────────────────┘

    Key Features:
    • Automatic complexity detection
    • Simple tasks → Direct ReAct loop (fast)
    • Complex tasks → Structured planning (thorough)
    • Each plan step uses full ReAct loop
    • Verification after each step
    """)


def show_step_execution_detail():
    """Show detailed step execution with ReAct loop."""
    print_header("STEP EXECUTION DETAIL (New ReAct Loop Architecture)")

    print("""
                    ┌──────────────────────┐
                    │   Full Message       │
                    │   History from       │
                    │   Previous Steps     │
                    └──────────┬───────────┘
                               │ provides context
                               ▼
                    ┌─────────────────────┐
                    │   Start Step N      │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Load Full Context  │
                    │  + Step Objective   │
                    └──────────┬──────────┘
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │          ReAct Loop (max 5 iterations)       │
        │                                              │
        │  ┌─────────────────────┐                    │
        │  │   LLM Reasoning     │                    │
        │  │ (What to do next?)  │                    │
        │  └──────────┬──────────┘                    │
        │             │                                │
        │             ▼                                │
        │      ┌─────────────┐                        │
        │      │ Has Tool    │                        │
        │      │ Calls?      │                        │
        │      └──┬──────┬───┘                        │
        │         │      │                            │
        │    YES  │      │  NO                        │
        │         │      │                            │
        │         ▼      │                            │
        │  ┌──────────────┐                          │
        │  │  Execute     │                          │
        │  │  Tools       │                          │
        │  │ (Action)     │                          │
        │  └──────┬───────┘                          │
        │         │                                  │
        │         ▼                                  │
        │  ┌──────────────┐                          │
        │  │  Add Tool    │                          │
        │  │  Results to  │                          │
        │  │  Messages    │                          │
        │  │ (Observe)    │                          │
        │  └──────┬───────┘                          │
        │         │                                  │
        │         ▼                                  │
        │  ┌──────────────┐                          │
        │  │ Max          │                          │
        │  │ Iterations?  │                          │
        │  └──┬────────┬──┘                          │
        │     │        │                             │
        │  <5 │        │ ≥5                          │
        │     │        │                             │
        │     └────────┘ (loop back)                 │
        │              │                             │
        └──────────────┼─────────────────────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Verify Step        │
            │  Completion         │
            │  (LLM validates)    │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Update Status:     │
            │  • completed        │
            │  • partial          │
            │  • failed           │
            │  • blocked          │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   End Step N        │
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Accumulate to      │
            │  Message History    │
            │  (for next step)    │
            └─────────────────────┘

    Key Features:
    • Full message history preserved across steps
    • ReAct loop allows multiple tool uses per step
    • LLM observes results and adapts
    • Verification ensures objective achieved
    • Status based on actual outcomes, not just execution
    """)


def show_comparison():
    """Show comparison of old vs new."""
    print_header("COMPARISON: Old vs New Planning Mode")

    print("""
    ╔═══════════════════════════════╗    ╔═══════════════════════════════╗
    ║   OLD: Mechanical Execution   ║    ║   NEW: ReAct Loop per Step    ║
    ╚═══════════════════════════════╝    ╚═══════════════════════════════╝

              Step N                               Step N
                │                                  + Full Context
                ▼                                      │
         ┌──────────────┐                             ▼
         │  LLM: 1 Call │                     ┌──────────────┐
         └──────┬───────┘                     │   Reasoning  │◄───┐
                │                             └──────┬───────┘    │
                ▼                                    │            │
         ┌──────────────┐                           ▼            │
         │ Execute Tool │                     ┌──────────────┐   │
         └──────┬───────┘                     │    Action    │   │
                │                             └──────┬───────┘   │
                ▼                                    │            │
         ┌──────────────┐                           ▼            │
         │  Mark DONE   │                     ┌──────────────┐   │
         │  (always!)   │                     │ Observation  │   │
         └──────────────┘                     └──────┬───────┘   │
                                                     │            │
                                                     └────────────┘
                                                     (loop until done)
                                                           │
                                                           ▼
                                                   ┌──────────────┐
                                                   │   Verify     │
                                                   │  Objective   │
                                                   └──────┬───────┘
                                                          │
                                                          ▼
                                                   ┌──────────────┐
                                                   │ Mark Status  │
                                                   │  (verified)  │
                                                   └──────────────┘

    Problems with OLD:                      Benefits of NEW:
    ✗ No reasoning between actions          ✓ Continuous reasoning
    ✗ Cannot adapt to failures              ✓ Adapts when issues found
    ✗ Steps marked done without check      ✓ Verified completion
    ✗ Lost context between steps            ✓ Full context preserved
    ✗ Single tool use per step              ✓ Multiple tools as needed
    ✗ Superficial reflection                ✓ Honest outcome analysis
    """)


def show_full_architecture():
    """Show complete system architecture."""
    print_header("FULL SYSTEM ARCHITECTURE")

    print("""
    ┌─────────────────────────────────────────────────────────────────┐
    │                      USER INTERFACE LAYER                       │
    │  ┌──────────┐    ┌──────────────┐    ┌──────────────┐         │
    │  │   CLI    │───▶│  Chat Mode   │    │  Task Mode   │         │
    │  │ (Typer)  │    │ (Interactive)│    │ (One-shot)   │         │
    │  └──────────┘    └──────┬───────┘    └──────┬───────┘         │
    └────────────────────────┼────────────────────┼──────────────────┘
                             │                    │
                             └────────┬───────────┘
                                      │
    ┌─────────────────────────────────┼───────────────────────────────┐
    │                 AGENT CORE (LangGraph)     ▼                    │
    │                                    ┌──────────────┐             │
    │                                    │ Mode Router  │             │
    │                                    └───┬──────┬───┘             │
    │                                        │      │                 │
    │                          mode=simple   │      │  mode=auto/plan │
    │                                        │      │                 │
    │                    ┌───────────────────┘      └─────────────┐  │
    │                    ▼                                         ▼  │
    │          ┌─────────────────┐                  ┌─────────────────┐
    │          │  Simple ReAct   │                  │ Planning Graph  │
    │          │     Graph       │                  │                 │
    │          └─────────────────┘                  └─────────────────┘
    └────────────────────────────────────────────────────────────────┘
                             │                              │
    ┌────────────────────────┼──────────────────────────────┼─────────┐
    │         PLANNING COMPONENTS             │             │         │
    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐           │
    │  │ Complexity   │ │     Plan     │ │     Plan     │           │
    │  │  Analysis    │ │  Generation  │ │  Execution   │           │
    │  └──────────────┘ └──────────────┘ │ (ReAct Loop) │           │
    │  ┌──────────────┐                  └──────────────┘           │
    │  │  Reflection  │                                              │
    │  └──────────────┘                                              │
    └──────────────────────────────┬──────────────────────────────────┘
                                   │
    ┌──────────────────────────────┼───────────────────────────────────┐
    │              TOOLS & INTEGRATIONS     ▼                          │
    │                           ┌────────────────┐                     │
    │                           │ Tool Registry  │                     │
    │                           └────────┬───────┘                     │
    │              ┌──────────────┬──────┴──────┬─────────────┐       │
    │              ▼              ▼             ▼             ▼       │
    │      ┌────────────┐  ┌──────────┐  ┌──────────┐ ┌──────────┐  │
    │      │  File I/O  │  │   Git    │  │   Code   │ │   Web    │  │
    │      │   Tools    │  │  Tools   │  │ Parsing  │ │  Search  │  │
    │      └────────────┘  └──────────┘  └──────────┘ └──────────┘  │
    └──────────────────────────────────────────────────────────────────┘
                                   │
    ┌──────────────────────────────┼───────────────────────────────────┐
    │                 LLM PROVIDERS        ▼                           │
    │                           ┌────────────────┐                     │
    │                           │  LLM Factory   │                     │
    │                           └────────┬───────┘                     │
    │              ┌──────────────┬──────┴──────┬──────────────┐      │
    │              ▼              ▼             ▼              ▼      │
    │      ┌────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
    │      │ Anthropic  │  │  OpenAI  │  │ DeepSeek │  │  Others  │ │
    │      │   Claude   │  │   GPT    │  │          │  │          │ │
    │      └────────────┘  └──────────┘  └──────────┘  └──────────┘ │
    └──────────────────────────────────────────────────────────────────┘
                                   │
    ┌──────────────────────────────┼───────────────────────────────────┐
    │              MEMORY & STATE          ▼                           │
    │              ┌──────────────────────────────┐                    │
    │              │      Agent State             │                    │
    │              │ (Messages, Context, Status)  │                    │
    │              └──────────┬───────────────────┘                    │
    │                         │                                        │
    │              ┌──────────┴──────────┐                             │
    │              ▼                     ▼                             │
    │      ┌────────────────┐    ┌────────────────┐                   │
    │      │   ChromaDB     │    │    SQLite      │                   │
    │      │ (Vector Store) │    │(Checkpointing) │                   │
    │      └────────────────┘    └────────────────┘                   │
    └──────────────────────────────────────────────────────────────────┘
    """)


def main():
    """Show all architecture diagrams."""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "KODER AGENT ARCHITECTURE" + " " * 34 + "║")
    print("║" + " " * 15 + "Text-Based Visualization (No Dependencies)" + " " * 22 + "║")
    print("╚" + "=" * 78 + "╝")

    show_simple_react_graph()
    input("\nPress Enter to continue...")

    show_planning_graph()
    input("\nPress Enter to continue...")

    show_step_execution_detail()
    input("\nPress Enter to continue...")

    show_comparison()
    input("\nPress Enter to continue...")

    show_full_architecture()

    print("\n")
    print("=" * 80)
    print("  For high-quality graphical diagrams, run:")
    print("    python visualize_agent_graph.py           (requires graphviz)")
    print("  OR")
    print("    python visualize_agent_graph_matplotlib.py (requires matplotlib)")
    print("=" * 80)
    print("\n")


if __name__ == "__main__":
    main()
