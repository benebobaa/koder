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

**Workspace Context:**
{context}

**Available Tools:**
{tools}

Create a structured plan with these components:

1. **Analysis**: What needs to be done and why
2. **Steps**: Numbered steps with tool usage
3. **Files**: What files will be read/created/modified
4. **Dependencies**: What depends on what
5. **Risks**: Potential issues or edge cases

Respond with JSON:
{{
  "analysis": "High-level approach and reasoning",
  "steps": [
    {{
      "step_number": 1,
      "description": "What to do",
      "tool": "tool_name",
      "type": "read" | "write",
      "file": "path/to/file.py",
      "rationale": "Why this step"
    }}
  ],
  "todos": [
    {{
      "id": 1,
      "content": "Task description (imperative form)",
      "activeForm": "Task description (present continuous)",
      "step_index": 1,
      "estimated_time": "30s"
    }}
  ],
  "files_to_create": ["file1.py", "file2.py"],
  "files_to_modify": ["existing.py"],
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
