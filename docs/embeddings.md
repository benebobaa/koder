# Embedding System Documentation

## Overview

The Koder embedding system provides semantic code understanding and retrieval capabilities using Google Gemini embeddings and ChromaDB vector storage. This system enables the AI assistant to understand code relationships, find similar implementations, and provide better contextual assistance.

## Features

### 🔍 **Semantic Search**
- Natural language queries to find relevant code
- Context-aware code retrieval
- Similarity-based code matching

### 📁 **Multi-Language Support**
- Python, JavaScript, TypeScript, Java, C++, Go, Rust
- Markdown, JSON, YAML, SQL, Shell scripts
- Configuration files and documentation

### ⚡ **Intelligent Indexing**
- Incremental updates (only changed files)
- File watching for automatic re-indexing
- Smart chunking that preserves code structure

### 📊 **Performance Monitoring**
- Indexing and search metrics
- Health monitoring and alerts
- Performance analytics

## Quick Start

### 1. Initialize Your Workspace

```bash
# Quick setup for semantic search
koder embedding quickstart

# Or specify workspace
koder embedding quickstart --workspace ./my-project
```

This will:
- Index all supported files in your workspace
- Set up the vector database
- Configure automatic indexing

### 2. Test Semantic Search

```bash
# Search for code using natural language
koder embedding search "authentication logic"
koder embedding search "database connection code"
koder embedding search "error handling patterns"
```

### 3. Validate System (Recommended)

```bash
# Validate the embedding system
koder embedding validate
```

This confirms:
- ✅ Google Gemini API connectivity
- ✅ Vector store health
- ✅ Performance metrics
- ✅ Sample embedding generation

### 4. Use in Chat/Task Mode

```bash
# Start chat with semantic context
koder chat start

# Ask questions that leverage embeddings
"Show me similar authentication patterns in this codebase"
"Find examples of API error handling"
"How is file processing implemented here?"
```

The AI will now use semantic search to find relevant code context before responding.

## CLI Commands

### `koder embedding quickstart`
Quick setup for semantic search.

```bash
koder embedding quickstart [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -f, --force            Force re-initialization
```

### `koder embedding index`
Manually index files for semantic search.

```bash
koder embedding index [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -p, --pattern TEXT      File pattern (e.g., '**/*.py')
  -c, --chunk-size INTEGER  Text chunk size [default: 1500]
  -f, --force            Force re-indexing
  -v, --verbose          Verbose output
```

### `koder embedding search`
Search indexed code using semantic search.

```bash
koder embedding search QUERY [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -k, --max-results INTEGER  Max results [default: 5]
  -f, --file-filter TEXT  Filter by file pattern
  --no-show-content      Hide file content in results
```

### `koder embedding validate`
Validate embedding system connectivity and performance.

```bash
koder embedding validate
```

This command provides comprehensive validation including:
- Google Gemini API connectivity test
- Vector store health check
- Performance metrics and response times
- Sample embedding values verification

### `koder embedding watch`
Watch for file changes and automatically update embeddings.

```bash
koder embedding watch [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -d, --debounce INTEGER  Debounce delay in seconds [default: 2]
```

### `koder embedding status`
Show embedding system status and statistics.

```bash
koder embedding status [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -d, --details          Show detailed file information
```

### `koder embedding metrics`
Display performance metrics and health monitoring.

```bash
koder embedding metrics [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -d, --detailed         Show detailed metrics
  -r, --reset            Reset all metrics
```

### `koder embedding clear`
Clear all indexed embeddings.

```bash
koder embedding clear [OPTIONS]

Options:
  -w, --workspace TEXT    Workspace directory [default: .]
  -y, --confirm          Skip confirmation prompt
```

## Integration with Agent Tools

The embedding system provides a `ContextRetrievalTool` that's automatically available in chat and task modes:

```python
# Tool automatically available to AI agent
context_retrieval_tool = ContextRetrievalTool(workspace_path=".")

# Usage examples the AI can use:
context_retrieval_tool._run("find authentication patterns")
context_retrieval_tool._run("database error handling", max_results=5)
context_retrieval_tool._run("React component structure", file_filter="*.tsx")
```

## Validation & Monitoring

### System Validation

Validate your embedding system to ensure everything is working correctly:

```bash
# Complete system validation
koder embedding validate
```

**Expected Output:**
```
🔍 Enhanced Embedding System Validation
==================================================
📊 Overall Status: fully_operational
🤖 Google Gemini: ✅ Connected
   Model: models/text-embedding-004
   Dimensions: 768
   Response Time: 570ms
   Sample Values: [-0.006005, 0.017773, -0.122081, 0.046063, 0.036993]
📦 Vector Store: ✅ Operational (7 docs)
```

### Performance Monitoring

Monitor system performance and health:

```bash
# View performance metrics
koder embedding metrics --detailed

# Check system status
koder embedding status --details

# Real-time monitoring
koder embedding watch
```

### LangSmith Observability

The embedding system includes comprehensive tracing via LangSmith:

**Configuration:**
```bash
# LangSmith is automatically configured with your .env settings
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=pr-loyal-hospitality-39
```

**What's Tracked:**
- Embedding generation start/end times
- Model usage (`models/text-embedding-004`)
- Performance metrics (response times, dimensions)
- Success/failure rates
- Error tracking

**Access Dashboard:**
1. Visit: https://smith.langchain.com
2. Project: `pr-loyal-hospitality-39`
3. Look for runs with names like `embed_query_success`, `embed_documents_start`

### Logging

Every embedding operation creates structured logs:

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG

# View embedding operations
koder embedding index --verbose
```

**Log Examples:**
```
embed_query_start              model=models/text-embedding-004 text_length=36
embed_query_success            dimensions=768 duration_seconds=0.5
embed_documents_start         count=5 model=models/text-embedding-004
embed_documents_success       count=5 dimensions=768 duration_seconds=2.3
```

## Configuration

### Environment Variables

```bash
# Required: Google API key for embeddings
GOOGLE_API_KEY=your_google_api_key

# Optional: Custom embedding model
EMBEDDINGS_MODEL=models/text-embedding-004

# Optional: Embedding dimensions
EMBEDDINGS_DIMENSION=768

# Optional: Storage paths
VECTOR_STORE_PATH=./data/vector_store
CACHE_PATH=./data/cache

# LangSmith Observability (optional but recommended)
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=koder
```

### File Type Patterns

The system automatically detects and indexes these file types:

**Source Code:**
- Python (`*.py`)
- JavaScript (`*.js`)
- TypeScript (`*.ts`, `*.tsx`)
- React (`*.jsx`)
- Go (`*.go`)
- Rust (`*.rs`)
- Java (`*.java`)
- C/C++ (`*.c`, `*.cpp`, `*.h`)

**Configuration & Docs:**
- Markdown (`*.md`)
- JSON (`*.json`)
- YAML (`*.yaml`, `*.yml`)
- SQL (`*.sql`)
- Shell scripts (`*.sh`)
- Docker (`Dockerfile*`, `*.dockerfile`)

**Ignored Directories:**
- `.git`, `.vscode`, `.idea`
- `__pycache__`, `node_modules`
- `.venv`, `venv`, `env`
- `dist`, `build`, `target`
- `.pytest_cache`, `.mypy_cache`

## Performance Optimization

### Intelligent Chunking

The system uses smart chunking strategies based on file types:

- **Code Files**: Preserves function/class boundaries
- **Markdown**: Maintains section structure
- **Generic Text**: Paragraph-based chunking

### Incremental Indexing

- Only re-indexes changed files using content hashing
- Automatic change detection
- Efficient batch processing

### Caching

- File content hash caching
- Embedding result caching
- Metadata persistence

## Monitoring and Health

### Metrics Tracked

- **Indexing Performance**: Files processed, time taken, error rates
- **Search Performance**: Query time, result counts, success rates
- **System Health**: Storage usage, error patterns, performance trends

### Health Checks

The system monitors:
- Error rates (indexing and searching)
- Performance benchmarks
- Storage status
- Recent activity levels

### Status Indicators

- 🟢 **Healthy**: All systems normal
- 🟡 **Degraded**: Performance issues or warnings
- 🔴 **Unhealthy**: High error rates or critical issues
- 🔥 **Error**: System malfunction

## Troubleshooting

### Common Issues

1. **"No indexed documents found"**
   ```bash
   # Run quickstart to index your workspace
   koder embedding quickstart
   ```

2. **Embedding system not working**
   ```bash
   # Validate the entire system
   koder embedding validate

   # Check configuration
   koder embedding status --details
   ```

3. **Google API connectivity issues**
   ```bash
   # Verify API key is set
   echo $GOOGLE_API_KEY

   # Test API connectivity
   koder embedding validate

   # Check API key in .env file
   cat .env | grep GOOGLE_API_KEY
   ```

4. **Slow indexing performance**
   ```bash
   # Check metrics for bottlenecks
   koder embedding metrics --detailed

   # Monitor performance in real-time
   koder embedding watch
   ```

5. **Search returning no results**
   ```bash
   # Check what's actually indexed
   koder embedding status --details

   # Try re-indexing
   koder embedding index --force

   # Validate search functionality
   koder embedding search "test query" --verbose
   ```

6. **High memory usage**
   ```bash
   # Clear and re-index with smaller chunks
   koder embedding clear
   koder embedding index --chunk-size 1000
   ```

7. **LangSmith tracing not working**
   ```bash
   # Check LangSmith configuration
   koder info

   # Verify environment variables
   echo "LANGSMITH_TRACING: $LANGSMITH_TRACING"
   echo "LANGSMITH_PROJECT: $LANGSMITH_PROJECT"
   ```

### Debug Mode

Enable verbose logging:

```bash
# Verbose indexing
koder embedding index --verbose

# Check detailed status
koder embedding status --details

# Debug search
koder embedding search "test query" --verbose
```

### Reset System

If you encounter persistent issues:

```bash
# Clear all embeddings
koder embedding clear

# Reset metrics
koder embedding metrics --reset

# Start fresh
koder embedding quickstart --force
```

## Best Practices

### 1. **Regular Usage**
- Use `koder embedding watch` during development
- Run `koder embedding metrics` weekly to monitor health
- Re-index after major code changes

### 2. **Query Optimization**
- Use specific, descriptive search queries
- Include relevant technical terms
- Filter by file types when appropriate

### 3. **Performance Management**
- Monitor chunk sizes for very large files
- Use file filters to narrow search scope
- Regular health checks prevent issues

### 4. **Team Collaboration**
- Share embedding indexes in team environments
- Use consistent file organization
- Document custom patterns for team members

## Advanced Usage

### Custom File Patterns

```bash
# Index specific file types
koder embedding index --pattern "**/*.proto"
koder embedding index --pattern "docs/**/*.md"

# Search with file filters
koder embedding search "api endpoints" --file-filter "**/*.py"
```

### Integration with Scripts

```python
from koder.memory.retrieval import CodebaseRetriever
from koder.memory.vector_store import VectorStore
from koder.memory.embeddings import GoogleEmbeddings

# Programmatic access
embeddings = GoogleEmbeddings(api_key="your_key")
vector_store = VectorStore(embeddings, "./data/vector_store")
retriever = CodebaseRetriever(vector_store, "./my-project")

# Search code
results = retriever.search_code("authentication logic", k=5)
for doc in results:
    print(f"{doc.metadata['file_path']}: {doc.page_content[:100]}...")
```

## Google Gemini Integration

### Model Details

**Current Configuration:**
- **Model**: `models/text-embedding-004`
- **Dimensions**: 768
- **Provider**: Google Generative AI
- **API**: Google AI Studio

### Performance Characteristics

**Benchmarks:**
- **Response Time**: ~400-600ms per query
- **Batch Processing**: Supported for documents
- **Rate Limits**: Dependent on Google AI Studio quota
- **Quality**: High-quality semantic understanding

**Usage Examples:**
```python
# Single query embedding
embedding = embeddings.embed_query("semantic search query")

# Batch document embedding
embeddings = embeddings.embed_documents([
    "function definition",
    "class implementation",
    "database query"
])
```

### API Configuration

**Required Setup:**
```bash
# Get API key from Google AI Studio
# https://aistudio.google.com/app/apikey

export GOOGLE_API_KEY=your_google_api_key
```

**Model Selection:**
```python
# Current model (fixed)
model = "models/text-embedding-004"

# Future models may be supported
# model = "models/text-multilingual-embedding-002"
```

## Architecture

### Components

1. **Embedding Engine** (`GoogleEmbeddings`)
   - Google Gemini `text-embedding-004`
   - 768-dimensional vectors
   - Batch processing support
   - Real-time API calls

2. **Vector Store** (`VectorStore`)
   - ChromaDB backend
   - Persistent storage
   - Metadata filtering

3. **Retrieval System** (`CodebaseRetriever`)
   - Intelligent chunking
   - Incremental indexing
   - Semantic search

4. **File Watcher** (`FileWatcher`)
   - Real-time change detection
   - Automatic re-indexing
   - Debounced updates

5. **Metrics System** (`EmbeddingMetrics`)
   - Performance tracking
   - Health monitoring
   - Usage analytics

6. **Validation System** (`TracedGoogleEmbeddings`)
   - API connectivity testing
   - Performance validation
   - LangSmith tracing integration

### Data Flow

```
Files → Chunking → Gemini API → Vector Store → Search → Results
  ↓         ↓           ↓            ↓         ↓        ↓
Watch  Hash Cache  Embeddings  ChromaDB  Similarity  Context
```

This embedding system significantly enhances the AI's understanding of your codebase by providing semantic context and intelligent code retrieval capabilities.