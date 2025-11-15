# Tool Permissions and Approval System

## Overview

The tool permissions system in Koder provides a comprehensive security framework that protects your codebase while enabling powerful AI assistance. It uses a multi-tiered permission model with interactive approval workflows to ensure safe and controlled tool execution.

## Permission Levels

### 1. Auto-Approved (Safe) Tools 🟢

These tools are automatically approved without user interaction:

**Characteristics:**
- Read-only operations
- No file system modifications
- No external system changes
- Reversible operations
- Low risk of unintended consequences

**Examples:**
```bash
# File reading operations
file_read("src/main.py")
directory_list("./src")

# Code analysis
analyze_function("calculate_total()")
find_dependencies("requirements.txt")

# Git information
git_status()
git_log(--oneline -5)

# Search operations
search_code("TODO:.*fix")
find_files("*.py", recursive=True)
```

**Auto-Approved Categories:**
- **Code Analysis**: Function analysis, dependency finding, code parsing
- **File Reading**: Reading file contents, directory listings
- **Information**: Git status, system information, file properties
- **Search**: Code search, pattern matching, file finding

### 2. Requires Approval (Medium Risk) 🟡

These tools require explicit user approval before execution:

**Characteristics:**
- File system modifications
- External API calls
- Configuration changes
- Reversible but potentially impactful changes

**Examples:**
```bash
# File modification
file_write("new_feature.py", content)
file_edit("config.py", old_string, new_string)

# Git operations
git_commit("Add new feature")
git_push("origin main")
git_create_branch("feature/user-auth")

# Build and test operations
run_tests("pytest tests/")
build_project("npm run build")

# API calls
api_request("POST", "https://api.github.com/repos/...", data)
```

**Approval Required Categories:**
- **File Modification**: Creating, editing, moving files
- **Git Operations**: Commits, pushes, branch creation
- **Build/Deploy**: Running builds, executing tests
- **External APIs**: Making HTTP requests to external services

### 3. Requires Explicit Confirmation (High Risk) 🔴

These tools require explicit confirmation with detailed warnings:

**Characteristics:**
- Destructive operations
- Difficult to reverse changes
- System-level modifications
- Potential data loss

**Examples:**
```bash
# File deletion
file_delete("old_feature.py")
directory_remove("./temp_files")

# Destructive git operations
git_reset_hard("HEAD~1")
git_clean("-fd")
git_branch_delete("-D", "feature/old-branch")

# Database operations
database_drop_table("temp_data")
database_delete_records("users", "created_at < '2020-01-01'")

# System operations
system_restart_service("nginx")
network_change_firewall("allow", 8080)
```

**High Risk Categories:**
- **File Deletion**: Removing files or directories
- **Destructive Git**: Reset, clean, branch deletion
- **Database**: Data deletion, schema changes
- **System**: Service management, configuration changes

## Approval Workflow

### 1. Interactive Approval Process

When a tool requiring approval is invoked, Koder displays an approval dialog:

```
🔒 Tool Approval Required

Tool: file_write
Risk Level: Medium
Description: Create or modify file content

Operation:
  File: ./src/new_feature.py
  Action: Create new file with 245 lines of code

Risk Assessment:
  ⚠️  This will create a new file in your codebase
  ⚠️  Changes will be tracked by git
  ⚠️  Operation is reversible (can delete file)

Details:
  • File size: ~8KB
  • Language: Python
  • Dependencies: requests, json

Options:
  [Y] Approve - Execute this operation
  [N] Reject - Cancel this operation
  [D] Details - Show more information
  [M] Modify - Change operation parameters
  [A] Approve All - Approve all operations in this plan
  [C] Cancel Plan - Stop entire execution plan

Your choice [Y/N/D/M/A/C]:
```

### 2. Batch Approval for Plans

When executing a plan with multiple operations:

```
📋 Plan Approval: "Refactor Authentication System"

This plan contains 8 operations requiring approval:

🟢 Auto-approved (3):
  1. analyze_code("src/auth/")
  2. git_status()
  3. search_code("password.*hash")

🟡 Requires approval (4):
  4. file_write("src/auth/user_service.py", ...)
  5. file_edit("src/config.py", ..., ...)
  6. git_add("src/auth/user_service.py")
  7. run_tests("pytest tests/test_auth.py")

🔴 High risk (1):
  8. file_delete("src/auth/legacy_auth.py")

Approval Options:
  [1] Approve All - Execute all operations
  [2] Approve Safe Only - Execute only auto-approved operations
  [3] Review Individually - Approve each operation separately
  [4] Modify Plan - Change specific operations
  [5] Cancel Plan - Stop execution

Your choice [1/2/3/4/5]:
```

### 3. Risk Warnings and Safety Information

High-risk operations include detailed warnings:

```
⚠️  HIGH RISK OPERATION WARNING ⚠️

Operation: git_reset_hard
Target: HEAD~1 (commit 7f3a8b2)

This operation will:
  ❌ Permanently discard all uncommitted changes
  ❌ Reset working directory to previous state
  ❌ Cannot be undone without git reflog

Files that will be affected:
  • src/main.py (23 lines modified)
  • tests/test_main.py (15 lines added)
  • config.yaml (configuration changes)

Alternative safer options:
  • Use git_reset_soft to keep changes staged
  • Use git_stash to save changes temporarily
  • Create backup branch before reset

Confirmation required: Type "RESET HARD" to confirm:
> RESET HARD
```

## Configuration

### 1. Permission Settings

Configure permission behavior in `.env`:

```bash
# Approval settings
TOOL_AUTO_APPROVE_SAFE=true          # Auto-approve safe tools
TOOL_REQUIRE_APPROVAL_MEDIUM=true    # Require approval for medium risk
TOOL_REQUIRE_CONFIRMATION_HIGH=true  # Require confirmation for high risk

# Approval behavior
TOOL_APPROVAL_TIMEOUT=300            # Approval timeout in seconds
TOOL_APPROVAL_CACHE_DURATION=600     # Cache approval decisions
TOOL_SHOW_DETAILS_BY_DEFAULT=false   # Show detailed risk info

# Safety settings
TOOL_WORKSPACE_RESTRICTION=true      # Restrict to workspace directory
TOOL_BACKUP_BEFORE_DESTRUCTIVE=true  # Create backups before destructive ops
TOOL_DRY_RUN_BY_DEFAULT=false        # Show what would happen without executing
```

### 2. Runtime Permission Control

```bash
# Auto-approve safe tools
uv run koder --auto-approve-safe chat start

# Require approval for all tools
uv run koder --require-approval-all task run "modify files"

# Skip approvals (dangerous - use with caution)
uv run koder --auto-approve-all task run "automated deployment"

# Show dry run for all operations
uv run koder --dry-run task run "complex refactoring"
```

### 3. Custom Permission Rules

Create custom permission rules in `config/permissions.yaml`:

```yaml
custom_permissions:
  - name: "project-specific-rules"
    rules:
      - pattern: "src/critical/*"
        permission: "high_risk"
        reason: "Critical production code"

      - pattern: "tests/*"
        permission: "auto_approve"
        reason: "Test files are safe to modify"

      - pattern: "*.md"
        permission: "medium_risk"
        reason: "Documentation changes"

      - tool: "git_commit"
        condition: "branch == 'main'"
        permission: "high_risk"
        reason: "Commits to main branch require extra care"
```

## Tool Categories and Permissions

### Code Analysis Tools (Auto-Approved 🟢)

```python
@register("code", permission="auto_approve")
class AnalyzeFunction(KoderTool):
    name = "analyze_function"
    description = "Analyze function structure and dependencies"
    risk_level = "low"

@register("code", permission="auto_approve")
class FindDependencies(KoderTool):
    name = "find_dependencies"
    description = "Find dependencies in Python code"
    risk_level = "low"
```

### File System Tools (Mixed Permissions)

```python
@register("filesystem", permission="auto_approve")
class ReadFile(KoderTool):
    name = "file_read"
    description = "Read file contents"
    risk_level = "low"

@register("filesystem", permission="medium_risk")
class WriteFile(KoderTool):
    name = "file_write"
    description = "Write or create file"
    risk_level = "medium"
    warning = "This will modify file system"

@register("filesystem", permission="high_risk")
class DeleteFile(KoderTool):
    name = "file_delete"
    description = "Delete file permanently"
    risk_level = "high"
    warning = "This operation cannot be undone"
    confirmation_required = True
```

### Git Operations (Tiered Permissions)

```python
@register("git", permission="auto_approve")
class GitStatus(KoderTool):
    name = "git_status"
    description = "Show git repository status"
    risk_level = "low"

@register("git", permission="medium_risk")
class GitCommit(KoderTool):
    name = "git_commit"
    description = "Commit changes to git"
    risk_level = "medium"
    warning = "This will create a permanent commit"

@register("git", permission="high_risk")
class GitResetHard(KoderTool):
    name = "git_reset_hard"
    description = "Reset repository to previous commit"
    risk_level = "high"
    warning = "This will permanently discard changes"
    confirmation_phrase = "RESET HARD"
```

## Advanced Features

### 1. Conditional Permissions

Permissions can be conditional based on context:

```python
@register("git", permission="conditional")
class GitPush(KoderTool):
    name = "git_push"
    description = "Push changes to remote repository"

    def get_permission_level(self, context):
        if context.branch == "main":
            return "high_risk"
        elif context.branch.startswith("release/"):
            return "medium_risk"
        else:
            return "auto_approve"
```

### 2. Time-Based Permissions

Restrict certain operations during specific times:

```python
@register("system", permission="conditional")
class RestartService(KoderTool):
    name = "restart_service"
    description = "Restart system service"

    def can_execute(self, context):
        # Don't allow service restarts during business hours
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:
            return False, "Service restarts not allowed during business hours"
        return True, ""
```

### 3. Approval Delegation

Delegate approval authority for specific operations:

```python
approval_delegates = {
    "team_lead": ["git_commit", "git_push", "file_write"],
    "senior_dev": ["git_reset_hard", "file_delete", "database_modify"],
    "admin": ["system_restart", "config_change", "user_management"]
}

def check_delegated_approval(tool_name, user_role):
    if user_role in approval_delegates:
        if tool_name in approval_delegates[user_role]:
            return True
    return False
```

## Safety Features

### 1. Workspace Isolation

```python
def validate_path(path, workspace):
    """Ensure operations stay within workspace."""
    abs_path = os.path.abspath(path)
    workspace_path = os.path.abspath(workspace)

    if not abs_path.startswith(workspace_path):
        raise PermissionError(
            f"Operation outside workspace not allowed: {path}"
        )
    return True
```

### 2. Backup Creation

```python
@register("filesystem", permission="high_risk")
class DeleteFile(KoderTool):
    def _run(self, file_path):
        # Create backup before deletion
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup.{int(time.time())}"
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Delete original file
        os.remove(file_path)
        return f"Deleted {file_path} (backup: {backup_path})"
```

### 3. Operation Logging

All tool operations are logged with:

```python
operation_log = {
    "timestamp": "2024-01-15T10:30:00Z",
    "tool": "file_write",
    "user": "bene@company.com",
    "thread_id": "abc-123-def-456",
    "operation": {
        "file": "./src/new_feature.py",
        "size": 8192,
        "backup_created": False
    },
    "approval": {
        "required": True,
        "granted_by": "user",
        "timestamp": "2024-01-15T10:30:15Z"
    },
    "result": {
        "status": "success",
        "duration": 0.23
    }
}
```

## Best Practices

### 1. Tool Design Guidelines

- **Clear Risk Assessment**: Always provide accurate risk levels
- **Descriptive Warnings**: Explain what the operation does
- **Reversible Operations**: Prefer operations that can be undone
- **Fail-Safe Defaults**: Default to the safest option

### 2. Permission Management

- **Principle of Least Privilege**: Only request necessary permissions
- **Regular Review**: Periodically review permission settings
- **Context-Aware**: Consider context when determining permissions
- **User Education**: Help users understand risks

### 3. Security Considerations

- **Workspace Boundaries**: Enforce strict workspace isolation
- **Input Validation**: Validate all tool parameters
- **Audit Trail**: Maintain comprehensive operation logs
- **Error Handling**: Handle permission errors gracefully

## Troubleshooting

### Common Permission Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Permission denied | Tool outside permission level | Check tool risk level and settings |
| Approval timeout | No response within time limit | Increase timeout or use auto-approve |
| Workspace violation | Operation outside workspace | Check file paths and workspace setting |
| Confirmation failed | Incorrect confirmation phrase | Check tool requirements carefully |

### Debug Mode

Enable permission debugging:

```bash
# Show permission decisions
uv run koder --debug-permissions task run "test operation"

# Dry run to see what would require approval
uv run koder --dry-run --verbose task run "complex operation"

# Check current permission settings
uv run koder --permission-settings info
```

The tool permissions system ensures that Koder provides powerful assistance while maintaining the security and integrity of your codebase. By implementing intelligent risk assessment and user-controlled approval workflows, it creates a safe environment for AI-assisted development.