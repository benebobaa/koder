# Thread Management Guide

## Overview

Thread management in Koder allows you to maintain persistent conversations, switch between different projects, and resume previous discussions seamlessly. Each thread represents an independent conversation with its own context, history, and state.

## Key Concepts

### What is a Thread?

A thread is a container for:
- **Conversation History**: All messages and responses
- **Context State**: Current working directory, active files, and environment
- **Tool Execution History**: Record of tools used and their results
- **Planning State**: Active plans and TODO items
- **Checkpoints**: Saved states for rollback and recovery

### Thread Lifecycle

```
Create Thread → Active Conversation → Checkpoint → Pause/Resume → Archive/Delete
```

## Basic Operations

### 1. Starting New Threads

```bash
# Start a new thread with default name
uv run koder chat start

# Start a new thread with custom name
uv run koder chat --thread-name "project-refactor" start

# Start a thread with specific provider
uv run koder --provider deepseek --thread-name "ai-integration" chat start
```

### 2. Listing Threads

```bash
# List all threads
uv run koder chat list-threads

# Output:
┌─────────────────────────────────────┬─────────────┬──────────┬─────────────┐
│ Thread ID                           │ Name        │ Status   │ Last Active │
├─────────────────────────────────────┼─────────────┼──────────┼─────────────┤
│ abc-123-def-456                     │ chat-session│ Active   │ 2 min ago   │
│ 789-ghi-012-jkl                     │ bug-fix     │ Paused   │ 1 hour ago  │
│ mno-345-pqr-678                     │ feature-dev │ Archived │ 2 days ago  │
└─────────────────────────────────────┴─────────────┴──────────┴─────────────┘
```

### 3. Resuming Threads

```bash
# Resume by thread ID
uv run koder chat --thread abc-123-def-456 start

# Resume by thread name (if unique)
uv run koder chat --thread-name "bug-fix" start

# Resume most recent thread
uv run koder chat --resume start
```

### 4. Thread Information

```bash
# Get detailed thread information
uv run koder chat --thread-info --thread abc-123-def-456

# Output:
Thread: abc-123-def-456
Name: project-refactor
Status: Active
Created: 2024-01-15 10:30:00
Last Modified: 2024-01-15 14:45:00
Messages: 47
Tools Used: 23
Plans Created: 3
Current Working Directory: /Users/bene/Documents/bene/python/koder
```

## Advanced Thread Management

### 1. Thread Naming and Organization

```bash
# Create threads with descriptive names
uv run koder chat --thread-name "auth-system-refactor" start
uv run koder chat --thread-name "performance-optimization" start
uv run koder chat --thread-name "api-documentation" start

# Use naming conventions
# Project-specific: projectname-feature
# Task-specific: task-description
# Time-based: 2024-01-15-bugfixes
```

### 2. Thread Context Switching

```bash
# Switch between threads without losing context
uv run koder chat --thread-name "frontend-work" start
You: Let's fix the React component rendering issue...
# ... work on frontend ...

# Switch to backend thread
uv run koder chat --thread-name "backend-api" start
You: Now let's update the API endpoint...
# ... work on backend ...

# Resume frontend thread with full context
uv run koder chat --thread-name "frontend-work" start
AI: Welcome back! We were working on the React component rendering issue.
    Would you like to continue where we left off?
```

### 3. Thread Checkpoints

```bash
# Create manual checkpoint
uv run koder chat --checkpoint "before-major-refactor" start

# List checkpoints for current thread
uv run koder chat --list-checkpoints

# Restore from checkpoint
uv run koder chat --restore-checkpoint "before-major-refactor" start
```

## Thread States and Status

### Thread Status Types

| Status | Description | Use Case |
|--------|-------------|----------|
| **Active** | Currently being used | Ongoing conversations |
| **Paused** | Temporarily stopped | Interrupted work |
| **Archived** | Completed and saved | Finished projects |
| **Locked** | Read-only mode | Reference conversations |
| **Error** | Failed state | Troubleshooting needed |

### State Transitions

```
Active → Paused → Active
Active → Archived → Locked
Paused → Archived → Locked
Error → Active (after recovery)
```

## Thread Metadata and Properties

### 1. Thread Information

```python
# Thread metadata structure
thread_metadata = {
    "thread_id": "abc-123-def-456",
    "name": "project-refactor",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z",
    "last_modified": "2024-01-15T14:45:00Z",
    "workspace": "/Users/bene/projects/myapp",
    "provider": "anthropic",
    "model": "claude-sonnet-4-5-20250929",
    "message_count": 47,
    "tool_executions": 23,
    "plans_created": 3,
    "todos_completed": 15,
    "tags": ["refactoring", "architecture", "critical"]
}
```

### 2. Thread Search and Filtering

```bash
# Search threads by name
uv run koder chat --search "refactor" list-threads

# Filter by status
uv run koder chat --status "active" list-threads

# Filter by date range
uv run koder chat --since "2024-01-10" list-threads

# Filter by tags
uv run koder chat --tag "bug-fix" list-threads
```

## Thread Configuration

### 1. Thread-Specific Settings

```bash
# Create thread with specific configuration
uv run koder chat \
  --thread-name "ai-integration" \
  --provider deepseek \
  --model deepseek-reasoner \
  --temperature 0.2 \
  --enable-planning \
  --auto-approve-safe \
  start
```

### 2. Thread Templates

```bash
# Create thread from template
uv run koder chat --template "bug-investigation" start

# Available templates:
- bug-investigation: Debugging and problem-solving setup
- feature-development: New feature development workflow
- code-review: Code review and analysis setup
- documentation: Documentation writing and updates
- performance: Performance analysis and optimization
```

## Thread Persistence and Storage

### 1. Storage Locations

```bash
# Default thread storage
./data/checkpoints/checkpoints.db  # SQLite database
./data/threads/                    # Thread-specific data
├── abc-123-def-456/
│   ├── messages.json
│   ├── context.json
│   ├── plans.json
│   └── checkpoints/
└── 789-ghi-012-jkl/
    ├── messages.json
    ├── context.json
    └── ...
```

### 2. Thread Backup and Export

```bash
# Export thread to JSON
uv run koder chat --export-thread --thread abc-123-def-456 --output thread-backup.json

# Export all threads
uv run koder chat --export-all-threads --output ./backup/

# Import thread from backup
uv run koder chat --import-thread --input thread-backup.json
```

### 3. Thread Cleanup

```bash
# Archive inactive threads
uv run koder chat --archive-inactive --days 30

# Delete old threads
uv run koder chat --cleanup --days 90

# Compact thread storage
uv run koder chat --compact-storage
```

## Use Case Examples

### 1. Multi-Project Development

```bash
# Start thread for Project A
uv run koder --workspace ./project-a --thread-name "project-a-api" chat start
You: Let's implement the REST API for user management...
# ... work on Project A ...

# Switch to Project B
uv run koder --workspace ./project-b --thread-name "project-b-frontend" chat start
You: Now let's fix the React components...
# ... work on Project B ...

# Both projects maintain separate contexts and histories
```

### 2. Long-Term Feature Development

```bash
# Day 1: Start feature development
uv run koder --thread-name "user-authentication" chat start
You: Let's start implementing user authentication...
AI: I'll help you implement user authentication. Let me create a plan:
📋 Plan:
1. Design authentication flow
2. Implement user model
3. Create authentication endpoints
4. Add JWT token handling
5. Implement session management
6. Add input validation
7. Create tests
8. Update documentation

# Day 2: Resume work
uv run koder chat --thread-name "user-authentication" start
AI: Welcome back! We were working on user authentication.
    Current status: Steps 1-3 completed, currently on step 4 (JWT token handling).
    Would you like to continue with the implementation?
```

### 3. Bug Investigation and Fix

```bash
# Start bug investigation thread
uv run koder --thread-name "memory-leak-bug" chat start
You: We're experiencing memory leaks in production. Let's investigate.

# Thread saves all investigation steps
AI: I'll help you investigate the memory leak. Let me create a systematic approach:
📋 Investigation Plan:
1. Analyze memory usage patterns
2. Check for common memory leak causes
3. Review recent code changes
4. Set up memory profiling
5. Identify root cause
6. Implement fix
7. Test and verify solution

# Investigation can be paused and resumed
uv run koder chat --thread-name "memory-leak-bug" start
AI: Resuming memory leak investigation. We've identified the issue in the
    authentication service and are ready to implement the fix.
```

## Thread Collaboration

### 1. Thread Sharing

```bash
# Export thread for sharing
uv run koder chat --export-thread --thread abc-123-def-456 \
  --format markdown --output investigation-report.md

# Create shareable thread link
uv run koder chat --share-thread --thread abc-123-def-456 \
  --expire-days 7 --permission read-only
```

### 2. Team Thread Templates

```bash
# Create team-specific thread template
uv run koder --create-template "team-workflow" \
  --config .team-template.json \
  --include "provider,workspace,tags,planning-settings"
```

## Performance and Optimization

### 1. Thread Performance

```bash
# Monitor thread performance
uv run koder chat --thread-stats --thread abc-123-def-456

# Output:
Thread Performance Stats:
├─ Message Count: 47
├─ Average Response Time: 2.3s
├─ Tool Execution Time: 45s total
├─ Memory Usage: 23MB
├─ Storage Size: 1.2MB
└─ Cache Hit Rate: 87%
```

### 2. Optimization Tips

- **Regular Cleanup**: Archive completed threads
- **Message Limits**: Consider splitting very long conversations
- **Storage Management**: Use thread-specific storage quotas
- **Context Optimization**: Clear unnecessary context periodically

## Troubleshooting

### Common Thread Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Thread won't resume | Corrupted checkpoint | Restore from backup checkpoint |
| Missing context | Context cleared during pause | Use `--restore-context` flag |
| Slow thread loading | Large message history | Archive old messages |
| Thread conflicts | Multiple sessions same thread | Use thread locking |

### Recovery Procedures

```bash
# Recover corrupted thread
uv run koder chat --recover-thread --thread abc-123-def-456

# Restore from backup
uv run koder chat --restore-backup --thread abc-123-def-456 \
  --backup-file backup-2024-01-15.json

# Reset thread state
uv run koder chat --reset-state --thread abc-123-def-456
```

## Best Practices

### 1. Thread Organization

- **Descriptive Names**: Use clear, searchable thread names
- **Consistent Tagging**: Apply relevant tags for easy filtering
- **Regular Archiving**: Archive completed projects monthly
- **Context Management**: Clear context when switching between unrelated tasks

### 2. Thread Lifecycle Management

- **Start Right**: Choose appropriate names and templates
- **Maintain Regularly**: Review and update thread metadata
- **End Cleanly**: Archive or delete threads properly
- **Backup Important**: Export critical threads before major changes

### 3. Collaboration Guidelines

- **Share Selectively**: Only share threads with appropriate permissions
- **Document Context**: Include context information for shared threads
- **Version Control**: Use version numbers for evolving threads
- **Access Control**: Implement proper access controls for team threads

Thread management in Koder provides a powerful way to maintain context across complex, multi-session development workflows, ensuring that no context is lost and work can seamlessly continue across time and projects.