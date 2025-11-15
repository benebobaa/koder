# Koder

> The AI assistant that plans multi-file changes like a senior developer

[![GitHub stars](https://img.shields.io/github/stars/bene/koder?style=social)](https://github.com/bene/koder/stargazers)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

🚀 **Turns "Add user authentication" into a step-by-step implementation plan** - Automatically detects complex refactoring, breaks it into manageable steps, and executes across multiple files. Instant answers for simple questions, intelligent planning for complex ones.

## Quick Start

```bash
# Install and setup in one command
curl -sSL https://koder.dev/install | bash

# Start coding
koder chat start
```

<details>
<summary>🔧 Alternative installation methods</summary>

### Using pip
```bash
pip install koder
koder chat start
```

### Using uv (recommended for development)
```bash
uv add koder
koder chat start
```

### From source
```bash
git clone https://github.com/bene/koder.git
cd koder
uv sync --all-extras
uv run koder chat start
```

</details>

## See It In Action

### Simple Questions → Instant Answers
```bash
$ koder chat start
You: What's in main.py?
[File contents displayed immediately]
```

### Complex Tasks → Intelligent Planning

![Planning Flow](docs/diagrams/planning_matplotlib.png)

```bash
$ koder task run "Add user authentication to the API"

📋 Plan Mode: Multi-file implementation detected

✅ Step 1: Create user model (src/models/user.py)
✅ Step 2: Implement auth endpoints (src/api/auth.py)
✅ Step 3: Add JWT middleware (src/middleware/auth.py)

[3 files created, 1 modified in 2.3 seconds]
```

**Unlike autocomplete tools (Copilot, Cursor) that suggest single lines, Koder plans and executes complex multi-file changes automatically.**

<details>
<summary>📊 What makes Koder different</summary>

| Feature | Autocomplete Tools | Koder |
|---------|-------------------|-------|
| **Multi-file changes** | ❌ Manual work | ✅ Automatic planning |
| **Context awareness** | ⚠️ Limited file scope | ✅ Whole codebase understanding |
| **LLM flexibility** | 🔒 Provider-specific | ✅ Switch Claude/OpenAI/DeepSeek instantly |
| **Complex task handling** | ❌ Line-by-line only | ✅ Step-by-step implementation |

![Comparison](docs/diagrams/comparison_matplotlib.png)

</details>

<details>
<summary>🔧 Advanced Features</summary>

### Multiple LLM Providers
```bash
koder chat start --provider anthropic  # Claude
koder chat start --provider openai     # GPT-4
koder chat start --provider deepseek   # DeepSeek
koder chat start --provider gemini     # Gemini
```

### Custom Workspace
```bash
koder chat start --workspace /path/to/your/project
```

### One-Off Tasks
```bash
koder task run "Analyze the codebase structure"
koder task run "What changed in the last commit?"
koder task run "Refactor this function to be more efficient"
```

### Thread Management
```bash
koder chat list-threads                    # List all conversations
koder chat --thread chat-abc123 start      # Resume specific thread
koder chat --thread-name "project-x" start # Named conversation
```

### Execution Control
```bash
koder chat start --mode auto      # Automatic complexity detection (default)
koder chat start --mode quick     # Always execute directly (no planning)
koder chat start --mode plan      # Always create plan first
```

## 🔒 Security & Tool Permissions

Koder protects your codebase with intelligent tool approval:

**Auto-Approved (Safe) 🟢**
- Read operations: File reading, directory listing
- Code analysis: Function analysis, dependency finding
- Git info: Status, logs, file properties
- Search: Code search, pattern matching

**Requires Approval (Medium Risk) 🟡**
- File modifications: Creating, editing files
- Git operations: Commits, pushes, branches
- Build/deploy: Running tests, building projects

**Explicit Confirmation (High Risk) 🔴**
- File deletion: Removing files or directories
- Destructive git: Reset, clean, branch deletion
- System operations: Service management, config changes

Interactive approval with clear risk descriptions for every operation.

</details>

<details>
<summary>📚 Documentation</summary>

- **[Getting Started](docs/getting-started.md)** - Complete setup guide
- **[Architecture](docs/architecture.md)** - How Koder works
- **[Configuration](docs/configuration.md)** - All available options

</details>

## Built With ❤️

Powered by [LangGraph](https://github.com/langchain-ai/langgraph) and inspired by [Anthropic Claude Code](https://claude.com/claude-code)

---

**MIT License** - see [LICENSE](LICENSE) file for details