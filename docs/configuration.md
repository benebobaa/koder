# Configuration Guide

## Environment Variables

Koder uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

### LLM Provider Settings

```bash
# Choose your provider
LLM_PROVIDER=anthropic  # or openai, deepseek, gemini

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx
GEMINI_API_KEY=your-gemini-api-key-here

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
OPENAI_MODEL=gpt-4-turbo-preview
DEEPSEEK_MODEL=deepseek-chat
GEMINI_MODEL=gemini-1.5-pro
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

## Provider Configuration

### Anthropic Claude

**Available Models:**
- `claude-opus-4-20250514` - Most capable, complex reasoning
- `claude-sonnet-4-5-20250929` - Balanced performance (default)
- `claude-haiku-4-20250917` - Fast, cost-effective

**When to Use Claude:**
- Complex architectural decisions
- Code requiring deep reasoning
- Large context window (200K tokens)
- High-quality code generation

**Configuration:**
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-xxxxx
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### OpenAI GPT

**Available Models:**
- `gpt-4-turbo-preview` - Latest GPT-4 capabilities (default)
- `gpt-4o` - Optimized performance
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Fast, cost-effective

**When to Use GPT:**
- General-purpose assistance
- Fast responses required
- Cost-sensitive applications
- Standard coding tasks

**Configuration:**
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-4-turbo-preview
```

### DeepSeek

**Available Models:**
- `deepseek-chat` - General purpose, cost-effective (default)
- `deepseek-reasoner` - Advanced reasoning capabilities

**When to Use DeepSeek:**
- Cost-effective code assistance
- Fast response times needed
- Complex reasoning with reasoner model
- High-volume usage scenarios

**Configuration:**
```bash
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-deepseek-api-key-here
DEEPSEEK_MODEL=deepseek-chat
```

**Advanced DeepSeek Settings:**
```bash
# Custom parameters
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=4096
DEEPSEEK_TOP_P=0.95
DEEPSEEK_FREQUENCY_PENALTY=0.0
DEEPSEEK_PRESENCE_PENALTY=0.0
```

### Google Gemini

**Available Models:**
- `gemini-1.5-pro` - Advanced reasoning, 2M token context (default)
- `gemini-1.5-flash` - Fast responses, cost-effective
- `gemini-pro-vision` - Multimodal (images + text)

**When to Use Gemini:**
- Massive context requirements (2M tokens)
- Large-scale codebase analysis
- Multimodal tasks (vision analysis)
- Fast generation with flash model

**Configuration:**
```bash
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-gemini-api-key-here
GEMINI_MODEL=gemini-1.5-pro
```

**Advanced Gemini Settings:**
```bash
# Custom parameters
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=4096
GEMINI_TOP_P=0.95
GEMINI_TOP_K=40
```

### Provider Comparison

| Provider | Best Model | Context | Speed | Cost | Strength |
|----------|------------|---------|-------|------|----------|
| Anthropic | Claude Sonnet | 200K | Fast | Medium | Balanced performance |
| OpenAI | GPT-4 Turbo | 128K | Moderate | High | General purpose |
| DeepSeek | DeepSeek Reasoner | 128K | Fast | Low | Cost-effective reasoning |
| Gemini | Gemini 1.5 Pro | 2M | Moderate | High | Large context analysis |

**Cost Optimization Tips:**
- Use **DeepSeek Chat** for 80% of routine tasks
- Use **Claude Sonnet** for balanced performance
- Use **DeepSeek Reasoner** only for complex reasoning
- Use **Gemini 1.5 Pro** for massive context analysis
- Use **Gemini 1.5 Flash** for fast, cost-effective generation

### Embeddings Configuration

```bash
# Google Gemini API for embeddings
GOOGLE_API_KEY=xxxxx
```

### Web Search Configuration

```bash
# Web Search Backend (duckduckgo, tavily, or brave)
WEB_SEARCH_BACKEND=duckduckgo  # Default: free, no API key needed

# Optional API keys for premium search backends
TAVILY_API_KEY=tvly-xxxxx     # For Tavily (1000 free searches/month)
BRAVE_API_KEY=BSA_xxxxx       # For Brave (2000 free searches/month)

# Search Configuration
WEB_SEARCH_MAX_RESULTS=5      # Default: 5
WEB_SEARCH_SAFE_SEARCH=true   # Default: true
```

### Observability Settings

```bash
# LangSmith Tracing (optional but recommended for development)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=ls_xxxxx
LANGSMITH_PROJECT=koder

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### MCP (Model Context Protocol) Settings

```bash
# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8080
MCP_API_KEY=your-mcp-api-key
MCP_TIMEOUT=30
```

### Planning System Settings

```bash
# Planning Configuration
ENABLE_PLANNING=true
PLANNING_AUTO_APPROVE=false
MAX_PLAN_STEPS=20
COMPLEXITY_THRESHOLD=0.7
```

### Storage Paths

```bash
# Local storage paths
VECTOR_STORE_PATH=./data/vector_store
CHECKPOINT_PATH=./data/checkpoints/checkpoints.db
CACHE_PATH=./data/cache
```

## Configuration Hierarchy

Configuration is loaded in the following order (later overrides earlier):

1. **Default values** (in `config/defaults.py`)
2. **Environment variables** (from `.env` file)
3. **CLI arguments** (highest priority)

## Runtime Configuration

### Switching LLM Providers

You can override the provider at runtime:

```bash
# Use Anthropic Claude
koder chat --provider anthropic

# Use OpenAI GPT
koder chat --provider openai

# Use DeepSeek
koder chat --provider deepseek
```

### Setting Workspace

Specify a different workspace directory:

```bash
koder chat --workspace /path/to/project
```

### Thread Management

Resume a previous conversation:

```bash
koder chat --thread chat-abc123
```

List all threads:

```bash
koder chat list-threads
```

## Advanced Configuration

### Disable Checkpointing

For stateless execution:

```bash
koder task run "analyze main.py" --no-checkpoint
```

### Planning Control

Control planning behavior:

```bash
# Force planning mode
koder task run "complex refactoring" --plan

# Disable planning (force simple mode)
koder task run "quick question" --no-plan

# Auto-approve plans (non-interactive)
koder task run "automated task" --auto-approve
```

### Verbose Logging

Enable debug logging:

```bash
koder --verbose chat start
```

### Quiet Mode

Suppress non-error output:

```bash
koder --quiet task run "fix bugs"
```

### Tool Approval Settings

Control tool approval behavior:

```bash
# Auto-approve safe tools
koder --auto-approve-safe chat start

# Require approval for all tools
koder --require-approval task run "modify files"
```

## Model Configuration

### Available Models

**Anthropic Claude:**
- `claude-opus-4-20250514` - Most capable
- `claude-sonnet-4-5-20250929` - Balanced (default)
- `claude-haiku-4-20250917` - Fast and efficient

**OpenAI:**
- `gpt-4-turbo-preview` - Latest GPT-4 Turbo (default)
- `gpt-4o` - Optimized GPT-4
- `gpt-4` - Standard GPT-4
- `gpt-3.5-turbo` - Fast and cost-effective

**DeepSeek:**
- `deepseek-chat` - General purpose chat model
- `deepseek-reasoner` - Advanced reasoning model

### Model Capabilities

| Model | Context Window | Max Output Tokens | Best For |
|-------|---------------|-------------------|-----------|
| Claude Opus | 200K | 16K | Complex reasoning, coding |
| Claude Sonnet | 200K | 16K | Balanced performance |
| Claude Haiku | 200K | 8K | Fast responses, simple tasks |
| GPT-4 Turbo | 128K | 4K | General purpose |
| GPT-4o | 128K | 4K | Optimized performance |
| GPT-4 | 8K | 4K | Standard tasks |
| GPT-3.5 Turbo | 16K | 4K | Cost-effective operations |
| DeepSeek Chat | 128K | 8K | Conversational AI |
| DeepSeek Reasoner | 128K | 8K | Complex reasoning |

## Tool Configuration

### Available Tool Categories

- **code** - Code parsing and analysis (read-only, auto-approved)
- **git** - Git operations (read/write, requires approval for destructive actions)
- **filesystem** - File system operations (read-only auto-approved, write operations require approval)
- **web** - Web search for current information (read-only, auto-approved)
- **context** - Semantic code search using embeddings (read-only, auto-approved)
- **execution** - Bash and Python execution (requires approval)
- **mcp** - MCP server tools (configurable permissions based on server)

### Tool Permission Levels

**Auto-Approved (Safe):**
- File reading operations
- Code analysis and parsing
- Git status and log viewing
- Directory listing
- Web search queries
- Semantic code search

**Requires Approval (Moderate Risk):**
- File modification and creation
- Git operations (commit, push, pull)
- Directory creation
- Search and replace operations

**Requires Explicit Confirmation (High Risk):**
- File deletion
- Git destructive operations (reset, clean)
- Directory deletion
- System modification operations

Tools are automatically loaded based on the task context and filtered by permission level.

## Observability

### LangSmith Tracing

Enable LangSmith for debugging LLM calls:

1. Sign up at [LangSmith](https://smith.langchain.com)
2. Get your API key
3. Set in `.env`:
   ```bash
   LANGSMITH_TRACING=true
   LANGSMITH_API_KEY=ls_xxxxx
   LANGSMITH_PROJECT=koder
   ```

View traces at: https://smith.langchain.com

### Structured Logging

Logs are output with structured formatting. In production, enable JSON logs:

```python
from koder.observability.logging import configure_logging

configure_logging(level="INFO", json_logs=True)
```

## Storage

### Vector Store

ChromaDB stores embeddings for semantic code search:

- **Location:** `./data/vector_store`
- **Persistence:** Automatic
- **Cleanup:** Delete directory to reset

### Checkpoints

SQLite database stores conversation state:

- **Location:** `./data/checkpoints/checkpoints.db`
- **Purpose:** Resume conversations, undo/redo
- **Cleanup:** Delete file to reset all threads

### Cache

Application cache for performance:

- **Location:** `./data/cache`
- **Purpose:** Temporary data storage
- **Cleanup:** Safe to delete anytime

## MCP Configuration

### Setting Up MCP Servers

Koder supports Model Context Protocol (MCP) for extended tool integration, allowing AI models to securely connect to external data sources and tools.

#### Basic MCP Configuration

```bash
# MCP Server Configuration
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your-mcp-api-key
MCP_TIMEOUT=30
MCP_ENABLED=true
```

#### Multiple MCP Servers

```bash
# Configure multiple MCP servers
MCP_SERVERS=github,jira,database

MCP_GITHUB_URL=https://github-mcp.example.com
MCP_GITHUB_API_KEY=ghp_your_github_token

MCP_JIRA_URL=https://jira-mcp.example.com
MCP_JIRA_API_KEY=your_jira_api_token

MCP_DATABASE_URL=https://database-mcp.example.com
MCP_DATABASE_API_KEY=your_db_api_key
```

#### Authentication Methods

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

### What MCP Enables

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

### MCP Testing

```bash
# Test MCP connection
koder --mcp-test info

# List available MCP tools
koder --mcp-list-tools info

# Test specific MCP server
koder --mcp-server github info
```

### MCP Tool Integration

- MCP tools are automatically discovered and registered
- Tools inherit permission levels from server configuration
- Real-time tool availability updates
- Support for custom tool schemas and parameters
- Interactive approval follows same security model as built-in tools

## Security

### API Keys

- Never commit `.env` files to version control
- Use `.env.example` as a template
- Rotate keys regularly
- Use environment-specific keys for development/production

### Workspace Isolation

Write operations are restricted to the workspace directory:

```python
# This will fail if outside workspace
tool.validate_write_path("/etc/passwd")
```

### Tool Approval Security

- Interactive approval for destructive operations
- Clear risk descriptions for each tool
- Approval history tracking for accountability
- Emergency stop capability for long-running operations

### Safe Defaults

- Read-only tools by default
- Explicit write permissions required
- Sandboxed execution environment
- Automatic timeout protection for long operations
