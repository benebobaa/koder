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
# Required: Choose one or more providers
ANTHROPIC_API_KEY=sk-ant-xxxxx  # Get from https://console.anthropic.com
OPENAI_API_KEY=sk-xxxxx         # Get from https://platform.openai.com
DEEPSEEK_API_KEY=sk-xxxxx       # Get from https://platform.deepseek.com

# Required: For embeddings
GOOGLE_API_KEY=xxxxx            # Get from https://aistudio.google.com

# Optional: For tracing
LANGSMITH_API_KEY=ls_xxxxx      # Get from https://smith.langchain.com

# Optional: For MCP integration
MCP_SERVER_URL=https://your-mcp-server.com
MCP_API_KEY=your-mcp-api-key
```

### 3. Set Provider

```bash
# In .env
LLM_PROVIDER=anthropic  # or openai, deepseek
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

You: Create a simple calculator module with basic operations
🤖 Assistant: I'll help you create a calculator module. Let me plan this task:

📋 Plan:
1. Analyze requirements for basic calculator operations
2. Create calculator.py file with basic arithmetic functions
3. Add error handling and type validation
4. Create simple test cases

This looks like a simple task. Let me execute it directly:
[✓] Creating calculator.py with add, subtract, multiply, divide functions
[✓] Adding proper error handling and type checking
[✓] Creating test functions for validation
[✓] Adding documentation strings

Your calculator module is ready! The file includes:
- Basic arithmetic operations (add, subtract, multiply, divide)
- Type checking and error handling
- Comprehensive documentation
- Simple test functions
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

### Provider Selection

```bash
# Use different providers at runtime
uv run koder --provider anthropic chat start
uv run koder --provider openai task run "analyze main.py"
uv run koder --provider deepseek chat start
```

## Basic Usage Examples

### 1. Code Analysis

```bash
uv run koder task run "Analyze the code structure and list all functions"
```

### 2. File Operations with Planning

```bash
uv run koder chat start
You: Read the contents of README.md
You: Create a new file called hello.py with a simple hello world function

🤖 Assistant: I'll help you create a hello.py file. Let me plan this:
📋 Plan:
1. Read README.md to understand project context
2. Create hello.py with hello world function
3. Add proper documentation

Proceed with plan? [Y/n]
```

### 3. Git Operations

```bash
uv run koder task run "Show me the git status and recent commits"
```

### 4. Complex Task with Planning

```bash
uv run koder chat start
You: Refactor the agent module to use dependency injection

🤖 Assistant: This is a complex task that requires careful planning. Let me create a detailed plan:

📋 Plan:
1. Analyze current agent module structure and dependencies
2. Design dependency injection architecture
3. Create base interfaces and abstractions
4. Implement DI container
5. Refactor existing components to use DI
6. Update configuration and initialization
7. Create migration tests
8. Update documentation

This is a complex refactoring with 8 steps. Proceed with plan? [Y/n]
```

### 5. Code Understanding

```bash
uv run koder chat start
You: Explain what the agent/graph.py file does
You: How does the planning system work in this codebase?
You: Show me the tool permission system implementation
```

## Project Structure

```
koder/
├── koder/              # Main package
│   ├── agent/          # LangGraph agent core
│   │   └── planning/   # Intelligent planning system
│   ├── cli/            # CLI interface
│   ├── config/         # Configuration
│   ├── llm/            # LLM providers
│   │   ├── providers/  # Provider implementations
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   └── deepseek.py
│   ├── memory/         # Vector store
│   ├── observability/  # Logging & tracing
│   ├── tools/          # Agent tools
│   │   ├── code/       # Code analysis tools
│   │   ├── filesystem/ # File operations
│   │   ├── git/        # Git operations
│   │   ├── mcp/        # MCP integration
│   │   └── permissions.py # Tool approval system
│   └── utils/          # Utilities
├── tests/              # Test suite
├── docs/               # Documentation
├── data/               # Runtime data (gitignored)
│   ├── vector_store/   # ChromaDB data
│   ├── checkpoints/    # Conversation state
│   └── cache/          # Application cache
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
ENABLE_PLANNING=true

# Run with verbose flag
uv run koder --verbose chat start
```

### Thread Management

List and resume conversations:

```bash
# List all conversation threads
uv run koder chat list-threads

# Resume a specific thread
uv run koder chat --thread abc-123-def start

# Start new thread with specific name
uv run koder chat --thread-name "project-refactor" start
```

## Common Tasks

### Add a New Tool

1. Create tool file in `koder/tools/<category>/`
2. Implement tool class with permissions:

```python
from koder.tools.base import KoderTool
from koder.tools.registry import registry

@registry.register("my_category", permission="write")
class MyTool(KoderTool):
    name = "my_tool"
    description = "What my tool does"
    risk_level = "medium"  # low, medium, high

    def _run(self, input: str) -> str:
        # Tool implementation
        return "result"
```

3. Tool is automatically available to the agent with appropriate approval workflow

### Test Different Providers

```bash
# Test with Anthropic Claude
uv run koder --provider anthropic --model claude-sonnet-4-5-20250929 chat start

# Test with OpenAI GPT
uv run koder --provider openai --model gpt-4o chat start

# Test with DeepSeek
uv run koder --provider deepseek --model deepseek-reasoner chat start
```

### Force Planning Mode

```bash
# Force planning for a task
uv run koder --plan task run "complex refactoring task"

# Disable planning for simple tasks
uv run koder --no-plan task run "quick question"
```

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

# Search with relevance scoring
results = retriever.search_code("function for parsing", k=5)
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

### Planning Issues

```bash
# If planning gets stuck, disable for simple tasks
uv run koder --no-plan task run "your task"

# Check planning configuration
uv run koder info | grep -i planning
```

### Provider Issues

```bash
# Test specific provider
uv run koder --provider anthropic info
uv run koder --provider openai info
uv run koder --provider deepseek info

# Check API key validity
uv run python -c "from koder.config.settings import get_settings; print(get_settings().llm.provider)"
```

## Next Steps

- Read [Architecture](architecture.md) to understand the system design
- Read [Configuration](configuration.md) for advanced settings
- Read [Planning Guide](planning.md) to understand intelligent planning
- Read [DeepSeek Provider](deepseek.md) for DeepSeek-specific configuration
- Explore the codebase and try different tasks
- Add custom tools for your specific needs

## Getting Help

- Check documentation in `docs/`
- Review example code in `tests/`
- Enable verbose logging for debugging
- Check LangSmith traces for LLM interactions
- Use `koder info` to verify configuration
- Review plan approval history for debugging

## Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Documentation](https://python.langchain.com/)
- [Anthropic API](https://docs.anthropic.com/)
- [OpenAI API](https://platform.openai.com/docs/)
- [DeepSeek API](https://platform.deepseek.com/)
- [LangSmith](https://smith.langchain.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
