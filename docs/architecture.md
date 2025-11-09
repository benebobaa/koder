# Koder Architecture

## Overview

Koder is a CLI-based AI code assistant built with LangGraph and LangChain. It uses a ReAct (Reasoning-Action) pattern to intelligently assist with code-related tasks.

## Architecture Layers

### 1. CLI Layer (`koder/cli/`)

The user-facing command-line interface built with Typer and Rich.

**Components:**
- `app.py` - Main CLI application
- `commands/` - Command modules (chat, task)
- `ui/` - UI components (console, formatters, prompts)

**Features:**
- Interactive chat mode
- One-off task execution
- Beautiful terminal output with Rich
- Command history with Prompt Toolkit

### 2. Agent Core (`koder/agent/`)

The LangGraph-based agentic workflow implementation.

**Components:**
- `graph.py` - Main graph definition
- `state.py` - State schema
- `nodes.py` - Node implementations (reasoning, action, observation)
- `edges.py` - Conditional routing logic
- `checkpoints.py` - State persistence

**Workflow:**
```
[Reasoning] → [Should Continue?]
     ↓             ↓
  [Action] ← [Observation]
     ↓
  [End]
```

### 3. LLM Layer (`koder/llm/`)

Multi-provider LLM abstraction with runtime switching.

**Components:**
- `factory.py` - LLM factory for provider switching
- `providers/` - Provider-specific configurations
  - `anthropic.py` - Claude models
  - `openai.py` - GPT models
- `config.py` - Model information utilities

**Supported Providers:**
- Anthropic Claude (Opus, Sonnet, Haiku)
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)

### 4. Tools System (`koder/tools/`)

Extensible tool system with registry pattern.

**Components:**
- `registry.py` - Central tool registry
- `base.py` - Base tool classes
- `code/` - Code intelligence tools (tree-sitter, jedi)
- `git/` - Git operation tools
- `filesystem/` - File system tools
- `mcp/` - MCP adapter tools

**Categories:**
- Code parsing and analysis
- Git operations (status, diff, log)
- File system operations (read, write, search)
- MCP server integration

### 5. Memory Layer (`koder/memory/`)

Vector store and retrieval for semantic code search.

**Components:**
- `vector_store.py` - ChromaDB wrapper
- `embeddings.py` - Embedding configurations (Google Gemini)
- `retrieval.py` - Code retrieval logic

**Features:**
- Semantic code search
- Context retrieval for agent
- File indexing

### 6. Configuration (`koder/config/`)

Pydantic-based configuration management.

**Components:**
- `settings.py` - Pydantic settings models
- `loader.py` - Configuration loading
- `defaults.py` - Default values

**Configuration Sources:**
1. Environment variables
2. `.env` file
3. CLI arguments (highest priority)

### 7. Observability (`koder/observability/`)

Logging, tracing, and metrics.

**Components:**
- `logging.py` - Structlog configuration
- `tracing.py` - LangSmith tracing
- `metrics.py` - Simple metrics collection

**Features:**
- Structured logging with structlog
- LLM call tracing with LangSmith
- Custom metrics tracking

## Data Flow

```
User Input (CLI)
    ↓
Agent Graph (LangGraph)
    ↓
LLM (Anthropic/OpenAI)
    ↓
Tools (via LangChain)
    ↓
Results → State Update
    ↓
Checkpoint (SQLite)
    ↓
Output (Rich formatting)
```

## State Management

- **State Schema:** TypedDict with messages, task info, and metadata
- **Checkpointing:** SQLite-based persistence for conversation history
- **Thread Management:** Support for multiple conversation threads

## Extensibility

### Adding New Tools

1. Create tool class inheriting from `KoderTool`
2. Register with `@registry.register("category")`
3. Implement `_run()` method
4. Tool automatically available to agent

### Adding LLM Providers

1. Create provider module in `llm/providers/`
2. Add configuration to `LLMFactory`
3. Update settings schema

### Custom Commands

1. Create command module in `cli/commands/`
2. Register with main app in `cli/app.py`

## Technology Stack

- **Runtime:** Python 3.11+
- **Orchestration:** LangGraph 0.2.0+
- **LLM Framework:** LangChain 0.3.0+
- **CLI:** Typer, Rich, Prompt Toolkit
- **Parsing:** tree-sitter, jedi
- **Vector Store:** ChromaDB
- **Embeddings:** Google Gemini Text Embeddings
- **State:** SQLite (checkpoints, threads)
- **Observability:** LangSmith, structlog
