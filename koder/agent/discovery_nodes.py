"""Discovery nodes for pre-planning phase - Claude Code style context gathering."""

import json
import os
from datetime import datetime
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import BaseTool

from koder.agent.state import AgentState
from koder.cli.ui.formatters import format_step_header
from koder.cli.ui.prompts import confirm, ask


def project_discovery_node(
    state: AgentState, llm: BaseChatModel, tools: list[BaseTool]
) -> dict[str, Any]:
    """
    Discover and analyze project structure before planning.

    This node implements Claude Code-style pre-planning discovery:
    1. Project structure analysis
    2. Technology stack identification
    3. Pattern discovery
    4. User intent clarification

    Args:
        state: Current agent state
        llm: Language model for analysis
        tools: Available tools

    Returns:
        State updates with comprehensive project discovery
    """
    from koder.tools.registry import registry

    request = state["current_task"]
    workspace = state["workspace_path"]

    # Skip if discovery already completed
    if state.get("discovery_completed"):
        return {}

    print("\n" + "="*60)
    print("🔍 PROJECT DISCOVERY PHASE")
    print("="*60)

    # Step 1: Analyze project structure
    print("\n📁 Analyzing project structure...")
    project_info = _analyze_project_structure(workspace, tools)

    # Step 2: Identify technology stack
    print("\n🛠️  Identifying technology stack...")
    tech_stack = _identify_tech_stack(project_info, tools)

    # Step 3: Search for relevant patterns
    print("\n🔎 Searching for relevant patterns...")
    relevant_patterns = _search_relevant_patterns(request, project_info, tools)

    # Step 4: Clarify user intent
    print("\n💭 Clarifying user intent...")
    user_intent = _clarify_user_intent(request, project_info, llm)

    # Step 5: Assess complexity factors
    print("\n⚖️  Assessing complexity factors...")
    complexity_factors = _assess_complexity_factors(request, project_info, tech_stack)

    # Compile comprehensive discovery results
    discovery_results = {
        "project_type": project_info.get("project_type", "unknown"),
        "main_directories": project_info.get("directories", []),
        "tech_stack": tech_stack,
        "key_files": project_info.get("key_files", []),
        "dependencies": project_info.get("dependencies", {}),
        "relevant_patterns": relevant_patterns,
        "user_intent_understanding": user_intent,
        "complexity_factors": complexity_factors,
        "discovery_completed": True,
        "discovery_timestamp": datetime.now().isoformat()
    }

    # Display discovery summary
    _display_discovery_summary(discovery_results)

    # Always return a valid state update
    return {
        "discovery_results": discovery_results,
        "messages": [],  # Ensure messages is never None
    }


def _analyze_project_structure(workspace: str, tools: list[BaseTool]) -> dict[str, Any]:
    """Analyze project structure and identify key components."""
    import os
    from pathlib import Path

    results = {
        "project_type": "unknown",
        "directories": [],
        "key_files": [],
        "dependencies": {},
        "config_files": []
    }

    try:
        # Get directory listing
        workspace_path = Path(workspace)
        if not workspace_path.exists():
            return results

        # Analyze root directory
        root_items = list(workspace_path.iterdir())

        # Identify project type based on key files
        key_indicators = {
            "package.json": "nodejs",
            "requirements.txt": "python",
            "pyproject.toml": "python",
            "Cargo.toml": "rust",
            "go.mod": "go",
            "pom.xml": "java",
            "build.gradle": "java",
            "composer.json": "php",
            "Gemfile": "ruby",
            "mix.exs": "elixir"
        }

        for item in root_items:
            if item.is_file() and item.name in key_indicators:
                results["project_type"] = key_indicators[item.name]
                results["key_files"].append(str(item))
                results["config_files"].append(str(item))

        # Identify main directories
        for item in root_items:
            if item.is_dir() and not item.name.startswith('.'):
                results["directories"].append({
                    "name": item.name,
                    "type": _classify_directory(item.name),
                    "file_count": len(list(item.rglob("*")))
                })

        # Look for dependency files
        dependency_files = {
            "package.json": "npm",
            "requirements.txt": "pip",
            "pyproject.toml": "poetry",
            "Cargo.toml": "cargo",
            "go.mod": "go modules",
            "pom.xml": "maven",
            "build.gradle": "gradle",
            "composer.json": "composer",
            "Gemfile": "bundler"
        }

        for file_name, dep_type in dependency_files.items():
            file_path = workspace_path / file_name
            if file_path.exists():
                results["dependencies"][dep_type] = str(file_path)

    except Exception as e:
        print(f"Error analyzing project structure: {e}")

    return results


def _identify_tech_stack(project_info: dict, tools: list[BaseTool]) -> dict[str, Any]:
    """Identify technology stack from project analysis."""
    tech_stack = {
        "primary_language": "unknown",
        "frameworks": [],
        "databases": [],
        "testing_frameworks": [],
        "build_tools": [],
        "deployment": []
    }

    project_type = project_info.get("project_type", "unknown")

    # Language detection based on project type
    language_map = {
        "nodejs": "javascript",
        "python": "python",
        "rust": "rust",
        "go": "go",
        "java": "java",
        "php": "php",
        "ruby": "ruby"
    }

    tech_stack["primary_language"] = language_map.get(project_type, "unknown")

    # Look for framework indicators in directory names
    framework_indicators = {
        "react": ["react", "next", "gatsby"],
        "vue": ["vue", "nuxt"],
        "angular": ["angular"],
        "django": ["django"],
        "flask": ["flask", "app"],
        "fastapi": ["fastapi", "api"],
        "rails": ["rails", "app"],
        "laravel": ["laravel", "app"]
    }

    for framework, indicators in framework_indicators.items():
        for directory in project_info.get("directories", []):
            dir_name = directory["name"].lower()
            if any(indicator in dir_name for indicator in indicators):
                tech_stack["frameworks"].append(framework)

    # Look for database indicators
    db_indicators = {
        "postgresql": ["postgres", "postgresql"],
        "mysql": ["mysql"],
        "mongodb": ["mongo"],
        "redis": ["redis"],
        "sqlite": ["sqlite"]
    }

    for db, indicators in db_indicators.items():
        for directory in project_info.get("directories", []):
            dir_name = directory["name"].lower()
            if any(indicator in dir_name for indicator in indicators):
                tech_stack["databases"].append(db)

    return tech_stack


def _search_relevant_patterns(request: str, project_info: dict, tools: list[BaseTool]) -> list[dict]:
    """Search for patterns relevant to the user's request."""
    patterns = []

    try:
        # Extract key terms from request
        key_terms = _extract_key_terms(request)

        # For now, just note what terms we're interested in
        # In a full implementation, we would use the grep tool here
        for term in key_terms:
            patterns.append({
                "search_term": term,
                "found_files": [],  # Would be populated by actual search
                "relevance": "medium",
                "note": "Pattern search would scan for existing implementations"
            })

    except Exception as e:
        print(f"Error in pattern analysis: {e}")

    return patterns


def _clarify_user_intent(request: str, project_info: dict, llm: BaseChatModel) -> dict[str, Any]:
    """Clarify user intent through targeted questions."""
    intent_info = {
        "original_request": request,
        "clarified_intent": request,
        "constraints": [],
        "preferences": [],
        "success_criteria": [],
        "questions_asked": []
    }

    try:
        # Generate clarification questions based on request and project
        clarification_prompt = f"""
        Based on this user request: "{request}"
        And this project context: {json.dumps(project_info, indent=2)}

        Generate 2-3 targeted clarification questions that would help better understand:
        1. What specific outcome the user wants
        2. Any constraints or requirements
        3. Success criteria

        Return JSON with:
        {{
            "questions": [
                {{
                    "question": "The clarification question",
                    "purpose": "What this helps clarify",
                    "options": ["optional", "multiple", "choice", "answers"]
                }}
            ],
            "assumed_answers": {{
                "key_points": ["assumed", "requirements", "based", "on", "context"]
            }}
        }}
        """

        messages = [SystemMessage(content=clarification_prompt)]
        response = llm.invoke(messages)

        try:
            clarification_data = json.loads(response.content)
            questions = clarification_data.get("questions", [])

            # Ask questions if needed
            for question_data in questions[:2]:  # Limit to 2 questions
                question = question_data.get("question", "")
                options = question_data.get("options", [])

                if question:
                    intent_info["questions_asked"].append(question)

                    # Ask user with options if provided
                    if options and len(options) > 1:
                        answer = ask(question, options=options)
                    else:
                        answer = ask(question)

                    # Store answer
                    intent_info["preferences"].append(f"{question}: {answer}")

        except json.JSONDecodeError:
            print("Could not parse clarification questions, using default approach")

    except Exception as e:
        print(f"Error in intent clarification: {e}")

    return intent_info


def _assess_complexity_factors(request: str, project_info: dict, tech_stack: dict) -> dict[str, Any]:
    """Assess various complexity factors for the task."""
    factors = {
        "technical_complexity": "low",
        "project_familiarity_required": "medium",
        "integration_points": [],
        "potential_risks": [],
        "estimated_effort": "unknown"
    }

    # Assess technical complexity based on request keywords
    complex_keywords = ["refactor", "architecture", "implement", "design", "optimize"]
    simple_keywords = ["check", "show", "list", "read", "find"]

    request_lower = request.lower()

    if any(keyword in request_lower for keyword in complex_keywords):
        factors["technical_complexity"] = "high"
    elif any(keyword in request_lower for keyword in simple_keywords):
        factors["technical_complexity"] = "low"
    else:
        factors["technical_complexity"] = "medium"

    # Assess project familiarity requirements
    if "existing" in request_lower or "current" in request_lower:
        factors["project_familiarity_required"] = "high"
    elif "new" in request_lower or "create" in request_lower:
        factors["project_familiarity_required"] = "medium"

    # Identify potential integration points
    if "database" in request_lower or "api" in request_lower:
        factors["integration_points"].append("external_services")

    if "test" in request_lower:
        factors["integration_points"].append("testing_framework")

    # Assess potential risks
    if "delete" in request_lower or "remove" in request_lower:
        factors["potential_risks"].append("data_loss")

    if "production" in request_lower or "deploy" in request_lower:
        factors["potential_risks"].append("production_impact")

    return factors


def _classify_directory(name: str) -> str:
    """Classify directory type based on name."""
    name_lower = name.lower()

    if any(term in name_lower for term in ["src", "source", "lib", "library"]):
        return "source_code"
    elif any(term in name_lower for term in ["test", "spec", "__tests__"]):
        return "testing"
    elif any(term in name_lower for term in ["doc", "docs", "documentation"]):
        return "documentation"
    elif any(term in name_lower for term in ["config", "configuration", "settings"]):
        return "configuration"
    elif any(term in name_lower for term in ["build", "dist", "target", "out"]):
        return "build_output"
    elif any(term in name_lower for term in ["node_modules", "vendor", "deps"]):
        return "dependencies"
    else:
        return "other"


def _extract_key_terms(request: str) -> list[str]:
    """Extract key search terms from user request."""
    # Simple keyword extraction
    import re

    # Remove common words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "must", "can", "this", "that", "these", "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them", "my", "your", "his", "her", "its", "our", "their"}

    # Extract words
    words = re.findall(r'\b\w+\b', request.lower())
    key_terms = [word for word in words if word not in stop_words and len(word) > 2]

    # Prioritize technical terms
    technical_terms = []
    for term in key_terms:
        if any(tech_indicator in term for tech_indicator in ["api", "db", "test", "config", "route", "model", "view", "controller", "service", "util", "helper"]):
            technical_terms.append(term)

    return technical_terms[:3]  # Return top 3 terms


def _display_discovery_summary(discovery_results: dict[str, Any]) -> None:
    """Display discovery results in a formatted summary."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()

    # Create summary table
    table = Table(title="Project Discovery Summary", show_header=True, header_style="bold cyan")
    table.add_column("Aspect", style="green")
    table.add_column("Discovery", style="white")

    # Add rows
    table.add_row("Project Type", discovery_results.get("project_type", "Unknown"))
    table.add_row("Primary Language", discovery_results.get("tech_stack", {}).get("primary_language", "Unknown"))
    table.add_row("Frameworks", ", ".join(discovery_results.get("tech_stack", {}).get("frameworks", [])) or "None detected")
    table.add_row("Key Directories", str(len(discovery_results.get("main_directories", []))))
    table.add_row("Relevant Patterns Found", str(len(discovery_results.get("relevant_patterns", []))))
    table.add_row("User Intent Clarified", "Yes" if discovery_results.get("user_intent_understanding", {}).get("questions_asked") else "No")

    # Create complexity assessment
    complexity_factors = discovery_results.get("complexity_factors", {})
    complexity_text = f"""
**Technical Complexity:** {complexity_factors.get('technical_complexity', 'Unknown')}
**Familiarity Required:** {complexity_factors.get('project_familiarity_required', 'Unknown')}
**Potential Risks:** {', '.join(complexity_factors.get('potential_risks', [])) or 'None identified'}
    """

    # Display panels
    console.print(Panel(table, title="🔍 Discovery Results", border_style="blue"))
    console.print(Panel(complexity_text, title="⚖️ Complexity Assessment", border_style="yellow"))

    # Show relevant patterns if found
    patterns = discovery_results.get("relevant_patterns", [])
    if patterns:
        pattern_text = "\n".join([
            f"• {p['search_term']}: {len(p['found_files'])} files found"
            for p in patterns
        ])
        console.print(Panel(pattern_text, title="🔎 Relevant Patterns Found", border_style="green"))