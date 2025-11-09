# Configuration Guide

## Environment Variables

Koder uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

### LLM Provider Settings

```bash
# Choose your provider
LLM_PROVIDER=anthropic  # or openai, deepseek

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx
DEEPSEEK_API_KEY=sk-xxxxx

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
OPENAI_MODEL=gpt-4-turbo-preview
DEEPSEEK_MODEL=deepseek-chat
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

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

Koder supports Model Context Protocol (MCP) for extended tool integration:

```bash
# Configure MCP server in .env
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your-mcp-api-key
MCP_TIMEOUT=30
MCP_ENABLED=true
```

### MCP Tool Integration

- MCP tools are automatically discovered and registered
- Tools inherit permission levels from server configuration
- Real-time tool availability updates
- Support for custom tool schemas and parameters

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
