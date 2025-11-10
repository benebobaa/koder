# Koder

> AI-powered code assistant using LangGraph and LangChain

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.0+-green.svg)](https://github.com/langchain-ai/langgraph)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Koder is a CLI-based AI code assistant powered by LangGraph, inspired by Anthropic Claude Code. It implements a ReAct (Reasoning-Action) pattern for intelligent code assistance with support for multiple LLM providers.

## Features

- 🤖 **Agentic AI Assistant** - ReAct pattern with reasoning and action loops
- 🔄 **Multi-Provider Support** - Anthropic Claude, OpenAI GPT, and DeepSeek with runtime switching
- 💬 **Interactive Chat Mode** - Conversational interface with history
- ⚡ **One-Off Tasks** - Execute single tasks without interaction
- 🧰 **Extensible Tools** - Code parsing, git operations, file system access
- 🔍 **Semantic Search** - Vector-based code search with ChromaDB
- 💾 **State Persistence** - Resume conversations with SQLite checkpointing
- 📊 **Observability** - LangSmith tracing and structured logging
- 🎨 **Beautiful CLI** - Rich terminal UI with syntax highlighting

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- API key for Anthropic Claude, OpenAI GPT, or DeepSeek
- Google API key for embeddings

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and setup
git clone <your-repo-url> koder
cd koder

# Install dependencies
uv sync
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
ANTHROPIC_API_KEY=sk-ant-xxxxx
GOOGLE_API_KEY=xxxxx
LLM_PROVIDER=anthropic
```

### Run

```bash
# Interactive chat
uv run koder chat start

# Execute a task
uv run koder task run "Analyze the code structure"

# Show system info
uv run koder info
```

## Intelligent Planning (Claude Code Style)

Koder automatically analyzes task complexity and chooses the best execution mode:

### Simple Tasks → Quick Execution
```bash
$ uv run koder chat start

You: Show me main.py
⚡ Quick Execution: Single file read operation

[File contents displayed immediately]
```

### Complex Tasks → Plan Mode
```bash
$ uv run koder task run "Add user authentication to the API"

📋 Plan Mode: Multi-file implementation task

📋 Execution Plan

## Analysis
Implement user authentication with JWT tokens including login, signup,
and protected endpoints.

## Steps
1. **Create user model**
   - Tool: `write_file`
   - File: `src/models/user.py`

2. **Implement authentication endpoints**
   - Tool: `write_file`
   - File: `src/api/auth.py`

3. **Add JWT middleware**
   - Tool: `write_file`
   - File: `src/middleware/auth.py`

## Files Affected
**To Create:** src/models/user.py, src/api/auth.py, src/middleware/auth.py
**To Modify:** src/api/__init__.py

**Estimated Time:** 5 minutes
**Complexity:** medium

Approve this plan? (yes/no) yes

✅ Tasks
🔄  Creating user model...
⏳  Implement authentication endpoints
⏳  Add JWT middleware

[Execution with live TODO updates...]
```

## Usage Examples

### Execution Modes

```bash
# Auto mode (default) - Analyzes complexity automatically
uv run koder chat start --mode auto

# Quick mode - Always execute directly (no planning)
uv run koder chat start --mode quick

# Plan mode - Always create plan first (even for simple tasks)
uv run koder chat start --mode plan
```

### Interactive Chat

```bash
$ uv run koder chat start

You: List all Python files in this directory
🤖 Assistant: Using tools:
  - list_directory
  - find_files

Found 15 Python files:
- main.py
- koder/__init__.py
- koder/agent/graph.py
...

You: Explain what graph.py does
🤖 Assistant: The graph.py file defines the main LangGraph workflow...
```

### One-Off Tasks

```bash
# Code analysis
uv run koder task run "Show me the structure of the agent module"

# Git operations
uv run koder task run "What are the recent commits?"

# File operations
uv run koder task run "Read README.md and summarize it"
```

### Custom Workspace

```bash
uv run koder chat start --workspace /path/to/project
```

### Provider Switching

```bash
# Use Anthropic Claude
uv run koder chat start --provider anthropic

# Use OpenAI GPT
uv run koder chat start --provider openai

# Use DeepSeek
uv run koder chat start --provider deepseek
```

## Architecture

```
┌─────────────────────────────────────────────┐
│              CLI Layer (Typer)              │
│        Interactive Chat | One-Off Tasks     │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│           Agent Core (LangGraph)            │
│  ┌─────────┐  ┌────────┐  ┌─────────────┐  │
│  │Reasoning│→ │ Action │→ │Observation  │  │
│  └────┬────┘  └───┬────┘  └──────┬──────┘  │
│       └───────────┴──────────────┘          │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│        LLM Layer (Multi-Provider)           │
│  Anthropic Claude | OpenAI GPT | DeepSeek   │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              Tools System                   │
│  Code | Git | Filesystem | MCP              │
└─────────────────────────────────────────────┘
```

### Key Components

- **Agent Core** - LangGraph-based ReAct workflow
- **LLM Layer** - Multi-provider support with factory pattern
- **Tools** - Extensible tool system with registry
- **Memory** - ChromaDB vector store for semantic search
- **State** - SQLite checkpointing for conversation persistence
- **CLI** - Typer + Rich for beautiful terminal UI
- **Observability** - LangSmith tracing + structlog

## Available Tools

### Code Intelligence
- `parse_python_code` - Extract functions, classes, imports
- Code completion (jedi)
- Syntax analysis (tree-sitter)

### Git Operations
- `git_status` - Repository status
- `git_diff` - Show changes
- `git_log` - Commit history

### Filesystem
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `find_files` - Search files by pattern

### MCP Integration
- Adapter for MCP server tools
- FastMCP server support

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=koder

# Lint and format
uv run ruff check .
uv run ruff format .

# Type checking
uv run mypy koder/
```

### Project Structure

```
koder/
├── koder/              # Main package
│   ├── agent/          # LangGraph agent (graph, state, nodes)
│   ├── cli/            # CLI application (commands, UI)
│   ├── config/         # Configuration (settings, loader)
│   ├── llm/            # LLM providers (factory, Anthropic, OpenAI)
│   ├── memory/         # Vector store (ChromaDB, embeddings)
│   ├── observability/  # Logging, tracing, metrics
│   ├── tools/          # Agent tools (code, git, filesystem)
│   └── utils/          # Utilities and errors
├── tests/              # Test suite
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── e2e/            # End-to-end tests
├── docs/               # Documentation
├── data/               # Runtime data (gitignored)
└── main.py             # Entry point
```

### Adding Custom Tools

```python
from koder.tools.base import KoderTool
from koder.tools.registry import registry

@registry.register("my_category")
class MyCustomTool(KoderTool):
    name = "my_tool"
    description = "What this tool does"

    def _run(self, input: str) -> str:
        # Your implementation
        return "result"
```

## Configuration

### Environment Variables

See `.env.example` for all configuration options:

- **LLM_PROVIDER** - Provider to use (anthropic/openai/deepseek)
- **ANTHROPIC_API_KEY** - Anthropic API key
- **OPENAI_API_KEY** - OpenAI API key
- **DEEPSEEK_API_KEY** - DeepSeek API key
- **GOOGLE_API_KEY** - Google API key for embeddings
- **LANGSMITH_TRACING** - Enable LangSmith tracing
- **LOG_LEVEL** - Logging level (DEBUG/INFO/WARNING/ERROR)

### Runtime Configuration

```bash
# Override provider
koder chat start --provider openai

# Set workspace
koder chat start --workspace /path/to/project

# Verbose logging
koder --verbose chat start

# Quiet mode
koder --quiet task run "analyze code"
```

## Documentation

- [Getting Started](docs/getting-started.md) - Detailed setup guide
- [Architecture](docs/architecture.md) - System design and components
- [Configuration](docs/configuration.md) - Configuration options

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Python | 3.11+ |
| Orchestration | LangGraph | 0.2.0+ |
| LLM Framework | LangChain | 0.3.0+ |
| CLI Framework | Typer | 0.12+ |
| Terminal UI | Rich | 13.7+ |
| Code Parsing | tree-sitter | 0.23+ |
| Vector DB | ChromaDB | 0.5+ |
| Embeddings | Google Gemini | Latest |
| State Management | SQLite | Built-in |
| Observability | LangSmith | Latest |
| Logging | structlog | 24.0+ |

## License

MIT License - see [LICENSE](LICENSE) file for details

## Acknowledgments

- Inspired by [Anthropic Claude Code](https://claude.com/claude-code)
- Built with [LangGraph](https://github.com/langchain-ai/langgraph) and [LangChain](https://github.com/langchain-ai/langchain)
- UI powered by [Rich](https://github.com/Textualize/rich) and [Typer](https://github.com/tiangolo/typer)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [documentation](docs/)
- Enable verbose logging for debugging
