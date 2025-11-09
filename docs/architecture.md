# Koder Architecture

## Overview

Koder is a sophisticated CLI-based AI code assistant built with LangGraph and LangChain. It features an intelligent planning system, multi-provider LLM support, and advanced tool management with permission controls. The system uses both ReAct (Reasoning-Action) patterns and complex planning workflows to intelligently assist with code-related tasks.

## Architecture Layers

### 1. CLI Layer (`koder/cli/`)

The user-facing command-line interface built with Typer and Rich.

**Components:**
- `app.py` - Main CLI application
- `commands/` - Command modules (chat, task)
- `ui/` - UI components (console, formatters, prompts)

**Features:**
- Interactive chat mode with intelligent planning
- One-off task execution with complexity analysis
- Beautiful terminal output with Rich
- Command history with Prompt Toolkit
- Thread management and conversation persistence
- Tool approval workflows for destructive operations

### 2. Agent Core (`koder/agent/`)

The LangGraph-based agentic workflow implementation.

**Components:**
- `graph.py` - Main graph definition with planning support
- `state.py` - Enhanced state schema with planning fields
- `nodes.py` - Node implementations (reasoning, planning, action, observation)
- `edges.py` - Conditional routing logic with complexity analysis
- `checkpoints.py` - State persistence with thread management
- `planning/` - Intelligent planning system components
  - `planner.py` - Plan generation and complexity analysis
  - `executor.py` - Plan execution with TODO tracking
  - `approver.py` - Interactive plan approval workflow

**Workflow:**
```
[Complexity Analysis] → [Planning] → [Approval?] → [Reasoning] → [Should Continue?]
        ↓                   ↓           ↓              ↓             ↓
   [Simple Mode]      [Plan Rejected] [Yes]         [Action] ← [Observation]
        ↓                   ↓           ↓              ↓
     [Reasoning]        [End]     [Execute Plan]    [End]
        ↓                                     ↓
     [Action]                             [Update TODOs]
        ↓                                     ↓
     [End]                                [End]
```

**Planning System Features:**
- Automatic task complexity detection
- Multi-step plan generation with reasoning
- Interactive plan approval with user feedback
- Live TODO tracking and progress updates
- Plan execution with rollback capabilities

### 3. LLM Layer (`koder/llm/`)

Multi-provider LLM abstraction with runtime switching.

**Components:**
- `factory.py` - LLM factory for provider switching
- `providers/` - Provider-specific configurations
  - `anthropic.py` - Claude models
  - `openai.py` - GPT models
  - `deepseek.py` - DeepSeek models
- `config.py` - Model information utilities

**Supported Providers:**
- Anthropic Claude (Opus, Sonnet, Haiku)
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)
- DeepSeek (DeepSeek Chat, DeepSeek Reasoner)

**Provider Features:**
- Runtime provider switching via CLI arguments
- Configurable model parameters per provider
- Unified interface across all providers
- Provider-specific capability mapping

### 4. Tools System (`koder/tools/`)

Extensible tool system with registry pattern.

**Components:**
- `registry.py` - Central tool registry with permission system
- `base.py` - Base tool classes with approval workflows
- `code/` - Code intelligence tools (tree-sitter, jedi)
- `git/` - Git operation tools
- `filesystem/` - File system tools with permission controls
- `mcp/` - MCP adapter tools
- `permissions.py` - Tool permission and approval system

**Categories:**
- Code parsing and analysis (read-only)
- Git operations (read/write with approval)
- File system operations (read-only by default, write operations require approval)
- MCP server integration (configurable permissions)

**Permission System:**
- **Read-Only Tools**: Automatically approved (file reading, code analysis)
- **Write Tools**: Require user approval (file modification, git operations)
- **Destructive Tools**: Require explicit confirmation (file deletion, git reset)
- **Approval Metadata**: Tool descriptions, risk levels, and safety warnings
- **Interactive Approval**: Real-time user confirmation during execution

### 5. Memory Layer (`koder/memory/`)

Vector store and retrieval for semantic code search.

**Components:**
- `vector_store.py` - ChromaDB wrapper with full API support
- `embeddings.py` - Embedding configurations (Google Gemini)
- `retrieval.py` - Code retrieval logic with filtering
- `documents.py` - Document management and operations

**Features:**
- Semantic code search with relevance scoring
- Context retrieval for agent with configurable context windows
- File indexing with pattern-based filtering
- Document chunking and metadata management
- Persistent vector storage with automatic updates
- Multi-query support for complex searches

### 6. Configuration (`koder/config/`)

Pydantic-based configuration management.

**Components:**
- `settings.py` - Pydantic settings models with nested configuration
- `loader.py` - Configuration loading with validation
- `defaults.py` - Default values for all settings

**Configuration Sections:**
- **LLM Settings**: Multi-provider configuration (Anthropic, OpenAI, DeepSeek)
- **MCP Settings**: Model Context Protocol server configuration
- **Memory Settings**: Vector store and embedding configuration
- **Planning Settings**: Intelligent planning system configuration
- **Tool Settings**: Permission and approval system settings
- **Observability Settings**: Logging, tracing, and debugging

**Configuration Sources:**
1. Default values (in `config/defaults.py`)
2. Environment variables (from `.env` file)
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
Complexity Analysis
    ↓
Planning System (if complex task)
    ↓
Plan Approval (interactive)
    ↓
Agent Graph (LangGraph)
    ↓
LLM (Anthropic/OpenAI/DeepSeek)
    ↓
Tools (via LangChain with approval)
    ↓
Results → State Update
    ↓
Checkpoint (SQLite with thread metadata)
    ↓
Output (Rich formatting with TODO tracking)
```

## State Management

- **Enhanced State Schema:** TypedDict with messages, task info, planning fields, TODO tracking, and approval metadata
- **Checkpointing:** SQLite-based persistence for conversation history with namespace support
- **Thread Management:** Full conversation thread lifecycle with metadata and resumption
- **Planning State:** Plan storage, execution tracking, and rollback capabilities
- **Approval State:** Tool approval tracking with user decision history
- **TODO Tracking:** Live task progress updates with completion status

## Extensibility

### Adding New Tools

1. Create tool class inheriting from `KoderTool`
2. Define permission level and risk metadata
3. Register with `@registry.register("category")`
4. Implement `_run()` method with proper error handling
5. Tool automatically available to agent with appropriate approval workflow

### Adding LLM Providers

1. Create provider module in `llm/providers/`
2. Add configuration to `LLMFactory`
3. Update settings schema with provider-specific options
4. Add model capabilities and context window information
5. Test provider integration with example requests

### Custom Commands

1. Create command module in `cli/commands/`
2. Implement Typer app with proper argument parsing
3. Register with main app in `cli/app.py`
4. Add command documentation and help text

### Adding Planning Strategies

1. Create planning strategy in `agent/planning/strategies/`
2. Implement complexity analysis logic
3. Add plan generation templates
4. Register strategy in planner configuration

## Technology Stack

- **Runtime:** Python 3.11+
- **Orchestration:** LangGraph 0.2.0+
- **LLM Framework:** LangChain 0.3.0+
- **CLI:** Typer, Rich, Prompt Toolkit
- **Parsing:** tree-sitter, jedi
- **Vector Store:** ChromaDB
- **Embeddings:** Google Gemini Text Embeddings
- **State:** SQLite (checkpoints, threads, metadata)
- **Observability:** LangSmith, structlog
- **Multi-Provider:** Anthropic, OpenAI, DeepSeek APIs
- **MCP:** Model Context Protocol support
- **Planning:** Custom planning engine with complexity analysis
