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

**Project Context:**
{context}

**Available Tools:**
{tools}

**IMPORTANT INSTRUCTIONS:**
1. Analyze the project structure from the context provided
2. Use appropriate tools based on file types and languages detected
3. Always use correct file extensions for the project
4. Plan steps in a logical order

**Plan Requirements:**
- Tailor approach to the specific project context
- Use appropriate tools for the detected language/framework
- Consider dependencies between steps

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

**Step Objective:** {step_description}

**Plan Context (for reference):**
{plan_context}

**Current Step Details:**
{current_step}

**Previous Step Results:**
{previous_results}

**Instructions:**
Your goal is to ACHIEVE THE STEP OBJECTIVE, not just execute tools mechanically.

The plan suggests using {suggested_tool}, but you should:
1. **Reason** about what's needed to accomplish this step's objective
2. **Adapt** your approach if the suggested tool isn't appropriate or if you encounter issues
3. **Use tools** as many times as needed to accomplish the objective
4. **Verify** that your actions achieved the intended outcome
5. **Explain** your reasoning and what you accomplished

Treat the plan as GUIDANCE, not rigid commands. If you discover that:
- The suggested approach won't work (e.g., missing dependencies)
- A different tool would be better
- Additional steps are needed
- The step is already complete or not needed

Then ADAPT your approach accordingly.

**When to stop:**
- When you have successfully achieved the step objective
- When you encounter a blocker that requires user intervention
- When you determine the step is not needed

Think step-by-step and use tools iteratively until the objective is met.
"""

STEP_VERIFICATION_PROMPT = """Review the work done for this step:

**Step Objective:** {step_description}

**Actions Taken:**
{actions_summary}

**Question:** Did we successfully achieve the step objective?

Respond with:
- "COMPLETED" if the objective was fully achieved
- "PARTIAL" if some progress was made but objective not fully met
- "FAILED" if the objective was not achieved
- "BLOCKED" if you cannot proceed due to missing dependencies or requirements

Then explain your assessment in 1-2 sentences.
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
