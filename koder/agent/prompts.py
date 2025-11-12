"""Specialized prompts for planning mode."""

COMPLEXITY_ANALYSIS_PROMPT = """You are analyzing a user's request to determine if it requires planning or can be executed immediately.

Classify the task as SIMPLE or COMPLEX based on these criteria:

**SIMPLE tasks** (execute immediately):
- Single file read operations (show me file.py, what's in README)
- Simple questions about code (what does this function do)
- Git status checks (show git status, what changed)
- Directory listings
- Code parsing/analysis of single files
- Any single read-only operation

**COMPLEX tasks** (require planning):
- Creating or modifying multiple files
- Refactoring code across files
- Implementing new features
- Bug fixes that span multiple files
- Any task with 3+ steps
- Destructive operations (delete, force push)
- Tasks requiring coordination between files

**User Request:**
{request}

**Available Tools:**
{tools}

Respond with JSON only:
{{
  "complexity": "simple" | "complex",
  "reasoning": "Brief explanation of why",
  "estimated_steps": number,
  "tools_needed": ["tool1", "tool2"]
}}
"""

PLANNING_PROMPT = """You are creating a detailed execution plan for a complex task.

**User Request:**
{request}

**Project Context from Discovery:**
{context}

**Available Tools:**
{tools}

**IMPORTANT INSTRUCTIONS:**
1. **CRITICAL**: Look at the project type and primary language shown above in 🎯 markers
2. **CRITICAL**: Only use ParsePythonTool if primary language is PYTHON
3. **CRITICAL**: Only use ParseGoTool if primary language is GO
4. **CRITICAL**: Do NOT mention "Python project" if the primary language is GO
5. **CRITICAL**: Do NOT use ParsePythonTool for Go projects
6. For other languages: Use general tools like ReadFileTool to examine code
7. Always use language-appropriate file extensions
8. Your analysis MUST start with: "This is a [LANGUAGE] project, so I'll..."

**Plan Requirements:**
- Tailor approach to the specific project type discovered
- Use appropriate tools for the detected language
- Use correct file extensions for the project type

Respond with JSON:
{{
  "analysis": "Approach based on the discovered project type",
  "steps": [
    {{
      "step_number": 1,
      "description": "What to do",
      "tool": "tool_name",
      "type": "read" | "write",
      "file": "path/to/file.ext",
      "rationale": "Why this step"
    }}
  ],
  "todos": [
    {{
      "id": 1,
      "content": "Task description",
      "activeForm": "Working on task",
      "step_index": 1,
      "estimated_time": "30s"
    }}
  ],
  "files_to_create": ["file1.ext", "file2.ext"],
  "files_to_modify": ["existing.ext"],
  "estimated_complexity": "low" | "medium" | "high",
  "estimated_time": "2 minutes",
  "risks": ["Risk 1", "Risk 2"]
}}
"""

PLAN_EXECUTION_PROMPT = """You are executing step {step_number} of {total_steps} in a plan.

**Plan Context:**
{plan_context}

**Current Step:**
{current_step}

**Previous Results:**
{previous_results}

Execute this step carefully:
1. Use the specified tool
2. Handle errors gracefully
3. Verify the result
4. Provide clear output

If you encounter an error:
- Explain what went wrong
- Suggest how to fix it
- Ask for guidance if needed

Proceed with the execution.
"""

REFLECTION_PROMPT = """Reflect on the completed task execution.

**Original Request:**
{request}

**Plan:**
{plan}

**Execution Results:**
{results}

**Files Modified:**
{files_modified}

Provide a reflection:
{{
  "success": true | false,
  "summary": "What was accomplished",
  "quality_assessment": "How well it was done",
  "potential_improvements": ["Improvement 1", "Improvement 2"],
  "next_steps": ["Next 1", "Next 2"],
  "learned": "What was learned from this task"
}}
"""

APPROVAL_REQUEST_PROMPT = """Present the plan to the user for approval.

Format the plan in a clear, readable way:

# 📋 Plan for: {task}

## Analysis
{analysis}

## Steps to Execute
{steps}

## Files Affected
**To Create:** {files_to_create}
**To Modify:** {files_to_modify}

## Estimated Time
{estimated_time}

## Potential Risks
{risks}

---
**Approve this plan?** (yes/no/modify)
"""

COMPLEXITY_THRESHOLD = 3  # Number of steps that triggers planning mode

# Discovery prompts for pre-planning phase
DISCOVERY_ANALYSIS_PROMPT = """You are analyzing a user's request and project context to prepare for effective planning.

**User Request:**
{request}

**Project Discovery Results:**
{discovery_results}

**Available Tools:**
{tools}

Based on the discovery results, provide insights on:
1. How the project structure affects the approach
2. What existing patterns or technologies should be considered
3. Any potential challenges or opportunities
4. Recommended strategy based on project context

Respond with a concise analysis that will help create a better execution plan."""

DISCOVERY_PROJECT_ANALYSIS_PROMPT = """Analyze this project structure and provide insights:

**Project Information:**
{project_info}

**Technology Stack:**
{tech_stack}

**User Request Context:**
{request}

Provide analysis on:
1. Project type and architecture
2. Key technologies and frameworks
3. Existing patterns that are relevant
4. Potential integration points
5. Development approach that fits this project

Keep the analysis focused and actionable for planning purposes."""

DISCOVERY_INTENT_CLARIFICATION_PROMPT = """Help clarify user intent for this request:

**Original Request:**
{request}

**Project Context:**
{project_context}

**What we know so far:**
{current_understanding}

Generate 2-3 specific clarification questions that would help:
1. Understand the exact outcome desired
2. Identify any constraints or requirements
3. Determine the appropriate scope and approach

Make questions specific to this project context and request type."""
