# Configuration Guide

## Environment Variables

Koder uses environment variables for configuration. Copy `.env.example` to `.env` and configure:

### LLM Provider Settings

```bash
# Choose your provider
LLM_PROVIDER=anthropic  # or openai

# API Keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

# Model Configuration
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
OPENAI_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=4096
```

### Embeddings Configuration

```bash
# Google Gemini API for embeddings
GOOGLE_API_KEY=xxxxx
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

### Model Capabilities

| Model | Context Window | Max Output Tokens |
|-------|---------------|-------------------|
| Claude Opus | 200K | 16K |
| Claude Sonnet | 200K | 16K |
| Claude Haiku | 200K | 8K |
| GPT-4 Turbo | 128K | 4K |
| GPT-4o | 128K | 4K |
| GPT-4 | 8K | 4K |
| GPT-3.5 Turbo | 16K | 4K |

## Tool Configuration

### Available Tool Categories

- **code** - Code parsing and analysis
- **git** - Git operations
- **filesystem** - File system operations
- **mcp** - MCP server tools

Tools are automatically loaded based on the task context.

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

### Safe Defaults

- Read-only tools by default
- Explicit write permissions required
- Sandboxed execution environment
