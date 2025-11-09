# Getting Started with Koder

## Installation

### Prerequisites

- Python 3.11 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url> koder
cd koder

# Install dependencies
uv sync

# Install development dependencies
uv sync --extra dev
```

## Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure API Keys

Edit `.env` and add your API keys:

```bash
# Required: Choose one provider
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com
# OR
OPENAI_API_KEY=sk-xxxxx         # Get from https://platform.openai.com

# Required: For embeddings
GOOGLE_API_KEY=xxxxx            # Get from https://aistudio.google.com

# Optional: For tracing
LANGSMITH_API_KEY=ls_xxxxx      # Get from https://smith.langchain.com
```

### 3. Set Provider

```bash
# In .env
LLM_PROVIDER=anthropic  # or openai
```

## Quick Start

### Interactive Chat

Start an interactive chat session:

```bash
# Using uv
uv run python main.py chat start

# Or after uv sync, using the koder command
uv run koder chat start
```

Example session:
```
You: List all Python files in this directory
🤖 Assistant: Using tools:
  - list_directory
  - find_files

Found 5 Python files:
- main.py
- koder/__init__.py
- koder/cli/app.py
...
```

### One-Off Tasks

Execute a single task:

```bash
uv run koder task run "Analyze the structure of main.py"
```

### View System Info

```bash
uv run koder info
```

## Basic Usage Examples

### 1. Code Analysis

```bash
uv run koder task run "Analyze the code structure and list all functions"
```

### 2. File Operations

```bash
uv run koder chat start
You: Read the contents of README.md
You: Create a new file called hello.py with a simple hello world function
```

### 3. Git Operations

```bash
uv run koder task run "Show me the git status and recent commits"
```

### 4. Code Understanding

```bash
uv run koder chat start
You: Explain what the agent/graph.py file does
You: How does the ReAct pattern work in this codebase?
```

## Project Structure

```
koder/
├── koder/              # Main package
│   ├── agent/          # LangGraph agent core
│   ├── cli/            # CLI interface
│   ├── config/         # Configuration
│   ├── llm/            # LLM providers
│   ├── memory/         # Vector store
│   ├── observability/  # Logging & tracing
│   ├── tools/          # Agent tools
│   └── utils/          # Utilities
├── tests/              # Test suite
├── docs/               # Documentation
├── data/               # Runtime data (gitignored)
└── main.py             # Entry point
```

## Development Workflow

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=koder

# Run specific test file
uv run pytest tests/unit/test_tools.py
```

### Code Quality

```bash
# Format code
uv run ruff format .

# Lint code
uv run ruff check .

# Type checking
uv run mypy koder/
```

### Development Mode

Enable verbose logging and tracing:

```bash
# In .env
LOG_LEVEL=DEBUG
LANGSMITH_TRACING=true

# Run with verbose flag
uv run koder --verbose chat start
```

## Common Tasks

### Add a New Tool

1. Create tool file in `koder/tools/<category>/`
2. Implement tool class:

```python
from koder.tools.base import KoderTool
from koder.tools.registry import registry

@registry.register("my_category")
class MyTool(KoderTool):
    name = "my_tool"
    description = "What my tool does"

    def _run(self, input: str) -> str:
        # Tool implementation
        return "result"
```

3. Tool is automatically available to the agent

### Add a New CLI Command

1. Create command file in `koder/cli/commands/`
2. Implement Typer app
3. Register in `koder/cli/app.py`

### Index Codebase for Search

```python
from koder.memory.vector_store import create_vector_store
from koder.memory.retrieval import CodebaseRetriever

# Create vector store
store = create_vector_store("./data/vector_store")

# Create retriever
retriever = CodebaseRetriever(store, workspace_path=".")

# Index Python files
retriever.index_directory(".", pattern="**/*.py")

# Search
results = retriever.search_code("function for parsing")
```

## Troubleshooting

### API Key Issues

```bash
# Verify API keys are set
uv run koder info

# Test LLM connection
uv run python -c "from koder.config.settings import get_settings; print(get_settings().llm.provider)"
```

### Import Errors

```bash
# Reinstall dependencies
uv sync --reinstall

# Clear cache
rm -rf .venv
uv sync
```

### Database Locked

```bash
# If checkpoint database is locked
rm ./data/checkpoints/checkpoints.db
```

## Next Steps

- Read [Architecture](architecture.md) to understand the system design
- Read [Configuration](configuration.md) for advanced settings
- Explore the codebase and try different tasks
- Add custom tools for your specific needs

## Getting Help

- Check documentation in `docs/`
- Review example code in `tests/`
- Enable verbose logging for debugging
- Check LangSmith traces for LLM interactions

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Anthropic API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [LangSmith](https://smith.langchain.com/)
