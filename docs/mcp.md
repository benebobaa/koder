# Model Context Protocol (MCP) Integration

## Overview

The Model Context Protocol (MCP) is an open standard that enables AI models to securely connect to external data sources and tools. Koder provides comprehensive MCP integration, allowing you to extend the AI's capabilities with custom tools, databases, APIs, and services.

## What MCP Enables

### Extended Tool Capabilities

With MCP, Koder can access:
- **External APIs** (GitHub, Jira, Slack, etc.)
- **Databases** (PostgreSQL, MongoDB, Redis, etc.)
- **Cloud Services** (AWS, Google Cloud, Azure)
- **Development Tools** (Docker, Kubernetes, CI/CD)
- **Monitoring Systems** (Prometheus, Grafana, DataDog)
- **Custom Business Logic** (internal services, proprietary tools)

### Real-World Use Cases

```bash
# Query GitHub issues directly
koder> "Show me all open bugs assigned to me in the webapp repo"
→ MCP Tool: github.list_issues(assignee="me", state="open", labels=["bug"])

# Update Jira tickets
koder> "Update ticket PROJ-123 status to In Progress and add comment"
→ MCP Tool: jira.update_issue(key="PROJ-123", status="In Progress", comment="...")

# Deploy to staging environment
koder> "Deploy the current branch to staging environment"
→ MCP Tool: kubernetes.deploy(image="myapp:latest", namespace="staging")

# Monitor application performance
koder> "Check the error rate for the past hour"
→ MCP Tool: prometheus.query(query="rate(http_requests_total{status=~'5..'}[1h])")
```

## Configuration

### 1. MCP Server Setup

Add to your `.env` file:

```bash
# MCP Server Configuration
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your-mcp-api-key
MCP_TIMEOUT=30
MCP_ENABLED=true

# Optional: Multiple MCP servers
MCP_SERVERS=github,jira,database
MCP_GITHUB_URL=https://github-mcp.example.com
MCP_GITHUB_API_KEY=ghp_your_github_token
MCP_JIRA_URL=https://jira-mcp.example.com
MCP_JIRA_API_KEY=your_jira_api_token
```

### 2. Server Authentication

Different authentication methods are supported:

```bash
# API Key Authentication
MCP_AUTH_TYPE=api_key
MCP_API_KEY=your-secret-key

# OAuth2 Authentication
MCP_AUTH_TYPE=oauth2
MCP_OAUTH_CLIENT_ID=your_client_id
MCP_OAUTH_CLIENT_SECRET=your_client_secret
MCP_OAUTH_TOKEN_URL=https://oauth.example.com/token

# Certificate Authentication
MCP_AUTH_TYPE=certificate
MCP_CERT_PATH=/path/to/client.crt
MCP_KEY_PATH=/path/to/client.key
MCP_CA_PATH=/path/to/ca.crt
```

### 3. Connection Testing

```bash
# Test MCP connection
uv run koder --mcp-test info

# List available MCP tools
uv run koder --mcp-list-tools info

# Test specific MCP server
uv run koder --mcp-server github info
```

## MCP Server Examples

### GitHub Integration Server

```python
# Example MCP server for GitHub integration
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
import github

app = Server("github-mcp")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available GitHub tools."""
    return [
        types.Tool(
            name="github_list_issues",
            description="List GitHub issues with filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "state": {"type": "string", "enum": ["open", "closed", "all"]},
                    "assignee": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}}
                }
            }
        ),
        types.Tool(
            name="github_create_issue",
            description="Create a new GitHub issue",
            inputSchema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "title": {"type": "string"},
                    "body": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["repo", "title"]
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls."""
    if name == "github_list_issues":
        g = github.Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(arguments["repo"])
        issues = repo.get_issues(
            state=arguments.get("state", "open"),
            assignee=arguments.get("assignee"),
            labels=arguments.get("labels", [])
        )

        result = []
        for issue in issues:
            result.append(f"#{issue.number}: {issue.title} ({issue.state})")

        return [types.TextContent(type="text", text="\n".join(result))]

    elif name == "github_create_issue":
        g = github.Github(os.getenv("GITHUB_TOKEN"))
        repo = g.get_repo(arguments["repo"])
        issue = repo.create_issue(
            title=arguments["title"],
            body=arguments.get("body", ""),
            labels=arguments.get("labels", [])
        )

        return [types.TextContent(
            type="text",
            text=f"Created issue #{issue.number}: {issue.title}"
        )]

    else:
        raise ValueError(f"Unknown tool: {name}")
```

### Database Integration Server

```python
# Example MCP server for database access
from mcp.server import Server
import mcp.types as types
import asyncpg
import json

app = Server("database-mcp")

@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available database tools."""
    return [
        types.Tool(
            name="db_query",
            description="Execute SQL query on database",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "params": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="db_get_schema",
            description="Get database schema information",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string"}
                }
            }
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle database tool calls."""
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))

    try:
        if name == "db_query":
            query = arguments["query"]
            params = arguments.get("params", [])

            rows = await conn.fetch(query, *params)
            result = [dict(row) for row in rows]

            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

        elif name == "db_get_schema":
            table = arguments.get("table")
            if table:
                query = """
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1
                    ORDER BY ordinal_position
                """
                rows = await conn.fetch(query, table)
            else:
                query = """
                    SELECT table_name, table_type
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """
                rows = await conn.fetch(query)

            result = [dict(row) for row in rows]
            return [types.TextContent(
                type="text",
                text=json.dumps(result, indent=2, default=str)
            )]

    finally:
        await conn.close()
```

## Usage Examples

### 1. GitHub Integration

```bash
# Start chat with GitHub MCP tools
uv run koder chat start

You: Show me all open bugs in the koder repository
🤖 Assistant: I'll check the GitHub repository for open bug issues.

🔧 Using MCP Tool: github_list_issues
Parameters: {"repo": "anthropics/koder", "state": "open", "labels": ["bug"]}

Found 5 open bug issues:
#123: Memory leak in long-running conversations
#124: Tool approval workflow not working for destructive operations
#125: DeepSeek provider configuration issues
#126: Planning system gets stuck on complex tasks
#127: MCP server connection timeouts

Would you like me to investigate any of these issues?
```

### 2. Database Operations

```bash
You: Show me the user table schema
🤖 Assistant: I'll retrieve the user table schema from the database.

🔧 Using MCP Tool: db_get_schema
Parameters: {"table": "users"}

User Table Schema:
```json
[
  {
    "column_name": "id",
    "data_type": "integer",
    "is_nullable": "NO",
    "column_default": "nextval('users_id_seq'::regclass)"
  },
  {
    "column_name": "email",
    "data_type": "character varying",
    "is_nullable": "NO",
    "column_default": null
  },
  {
    "column_name": "username",
    "data_type": "character varying",
    "is_nullable": "NO",
    "column_default": null
  },
  {
    "column_name": "created_at",
    "data_type": "timestamp with time zone",
    "is_nullable": "NO",
    "column_default": "now()"
  }
]
```

The users table has 4 columns with id as the primary key. Would you like me to query any specific data?
```

### 3. Cloud Deployment

```bash
You: Deploy the current application to staging
🤖 Assistant: I'll deploy the current application to the staging environment using Kubernetes.

📋 Plan:
1. Build Docker image with current code
2. Push image to container registry
3. Update Kubernetes deployment
4. Verify deployment status
5. Run health checks

Proceed with deployment? [Y/n]

🔧 Using MCP Tool: docker.build
Parameters: {"tag": "myapp:staging-2024-01-15", "context": "."}

🔧 Using MCP Tool: registry.push
Parameters: {"image": "myapp:staging-2024-01-15", "registry": "my-registry.com"}

🔧 Using MCP Tool: kubernetes.deploy
Parameters: {
  "namespace": "staging",
  "deployment": "myapp-staging",
  "image": "my-registry.com/myapp:staging-2024-01-15"
}

✅ Deployment completed successfully!
- Pods: 3/3 ready
- Services: All endpoints responding
- Health checks: All passing
```

## Security Considerations

### 1. Access Control

MCP servers should implement proper access controls:

```python
# Example: Role-based access control
@app.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    # Check user permissions
    user_role = get_user_role_from_context()

    if name == "admin_delete_data" and user_role != "admin":
        raise PermissionError("Admin access required")

    # Validate input parameters
    if not validate_arguments(name, arguments):
        raise ValueError("Invalid arguments")

    # Execute tool
    return await execute_tool(name, arguments)
```

### 2. Input Validation

Always validate and sanitize inputs:

```python
def validate_sql_query(query: str) -> bool:
    """Prevent SQL injection through query validation."""
    dangerous_patterns = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER",
        "EXEC", "UNION", "CREATE", "TRUNCATE"
    ]

    query_upper = query.upper()
    return not any(pattern in query_upper for pattern in dangerous_patterns)

@app.call_tool()
async def handle_db_query(arguments: dict) -> list[types.TextContent]:
    query = arguments["query"]

    if not validate_sql_query(query):
        raise ValueError("Potentially dangerous query detected")

    # Execute safe query
    return await execute_safe_query(query)
```

### 3. Rate Limiting

Implement rate limiting to prevent abuse:

```python
from collections import defaultdict
import time

class RateLimiter:
    def __init__(self, max_requests_per_minute: int = 60):
        self.max_requests = max_requests_per_minute
        self.requests = defaultdict(list)

    def is_allowed(self, user_id: str) -> bool:
        now = time.time()
        minute_ago = now - 60

        # Remove old requests
        self.requests[user_id] = [
            req_time for req_time in self.requests[user_id]
            if req_time > minute_ago
        ]

        # Check if under limit
        if len(self.requests[user_id]) < self.max_requests:
            self.requests[user_id].append(now)
            return True

        return False

rate_limiter = RateLimiter(max_requests_per_minute=30)

@app.call_tool()
async def handle_tool_call(user_id: str, name: str, arguments: dict):
    if not rate_limiter.is_allowed(user_id):
        raise Exception("Rate limit exceeded")

    return await execute_tool(name, arguments)
```

## Advanced Features

### 1. Tool Composition

MCP tools can be composed for complex workflows:

```bash
You: Create a GitHub issue for the production bug and assign it to the senior developer
🤖 Assistant: I'll create a GitHub issue and assign it.

🔧 Using MCP Tool: github_create_issue
Parameters: {
  "repo": "myorg/myapp",
  "title": "Production Bug: High memory usage in API server",
  "body": "Memory usage exceeded 80% on production servers. Need immediate investigation.",
  "labels": ["bug", "production", "critical"]
}

🔧 Using MCP Tool: github_assign_issue
Parameters: {
  "issue_number": 456,
  "assignee": "senior-dev"
}

✅ Created issue #456 and assigned to senior-dev
```

### 2. Streaming Responses

For long-running operations, use streaming:

```python
@app.call_tool()
async def handle_long_operation(arguments: dict) -> AsyncIterator[types.TextContent]:
    """Stream progress for long-running operations."""

    yield types.TextContent(
        type="text",
        text="🚀 Starting deployment...\n"
    )

    # Step 1
    await deploy_step1()
    yield types.TextContent(
        type="text",
        text="✅ Step 1 completed: Build image\n"
    )

    # Step 2
    await deploy_step2()
    yield types.TextContent(
        type="text",
        text="✅ Step 2 completed: Push to registry\n"
    )

    # Final step
    await deploy_step3()
    yield types.TextContent(
        type="text",
        text="✅ Deployment completed successfully!\n"
    )
```

### 3. Error Handling and Recovery

Implement robust error handling:

```python
@app.call_tool()
async def handle_resilient_operation(arguments: dict) -> list[types.TextContent]:
    """Handle operations with automatic retry."""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            result = await perform_operation(arguments)
            return [types.TextContent(
                type="text",
                text=f"✅ Operation completed on attempt {attempt + 1}"
            )]

        except TemporaryError as e:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt  # Exponential backoff
            await asyncio.sleep(wait_time)

            yield types.TextContent(
                type="text",
                text=f"⚠️ Attempt {attempt + 1} failed, retrying in {wait_time}s...\n"
            )
```

## Best Practices

### 1. Tool Design

- **Atomic Operations**: Each tool should do one thing well
- **Clear Naming**: Use descriptive names like `github_create_issue` not `create_issue`
- **Consistent Parameters**: Use standard parameter names across tools
- **Good Documentation**: Provide clear descriptions and examples

### 2. Error Messages

- **User-Friendly**: Explain what went wrong in simple terms
- **Actionable**: Suggest how to fix the problem
- **Contextual**: Include relevant context for debugging

### 3. Performance

- **Connection Pooling**: Reuse connections for database/API tools
- **Caching**: Cache results for expensive operations
- **Batching**: Batch multiple operations when possible

## Troubleshooting

### Common MCP Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection timeout | Server unreachable | Check MCP_SERVER_URL and network connectivity |
| Authentication failed | Invalid credentials | Verify MCP_API_KEY and authentication method |
| Tool not found | Server not configured | Check MCP_SERVERS configuration |
| Permission denied | Insufficient access | Verify user permissions on MCP server |

### Debug Mode

Enable MCP debugging:

```bash
# Enable verbose MCP logging
MCP_DEBUG=true uv run koder chat start

# Test MCP server connection
uv run koder --mcp-debug --mcp-server github info

# View MCP tool execution logs
uv run koder --mcp-logs task run "test mcp tool"
```

### Health Checks

Implement health checks for your MCP servers:

```python
@app.health_check()
async def health_check() -> dict:
    """Return server health status."""
    try:
        # Test database connection
        await test_database_connection()

        # Test external API access
        await test_api_access()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0"
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
```

The MCP integration transforms Koder into a powerful orchestrator that can interact with virtually any external system, making it an indispensable tool for complex development workflows.