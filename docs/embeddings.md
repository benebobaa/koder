# Embedding System Guide

## Overview

The Koder embedding system provides semantic code understanding using Google Gemini embeddings and ChromaDB vector storage. This enables the AI assistant to understand code relationships and find relevant implementations.

## Quick Start

### 1. Setup

```bash
# Quick setup for semantic search
koder embedding quickstart

# Specify workspace
koder embedding quickstart --workspace ./my-project
```

### 2. Test Search

```bash
# Search using natural language
koder embedding search "authentication logic"
koder embedding search "database connection code"
koder embedding search "error handling patterns"
```

### 3. Validate

```bash
# Validate the embedding system
koder embedding validate
```

## Configuration

Add to your `.env` file:

```bash
# Google Gemini API for embeddings
GOOGLE_API_KEY=your-gemini-api-key-here

# Embedding settings (optional)
EMBEDDING_MODEL=gemini-embedding
EMBEDDING_CHUNK_SIZE=1000
EMBEDDING_OVERLAP=200
```

## Features

### Semantic Search
- Natural language queries to find relevant code
- Context-aware code retrieval
- Similarity-based code matching

### Multi-Language Support
- Python, JavaScript, TypeScript, Java, C++, Go, Rust
- Markdown, JSON, YAML, SQL, Shell scripts
- Configuration files and documentation

### Intelligent Indexing
- Incremental updates (only changed files)
- File watching for automatic re-indexing
- Smart chunking that preserves code structure

## Usage Examples

### Chat Mode with Context
```bash
koder chat start

# Ask questions leveraging embeddings
"Show me similar authentication patterns in this codebase"
"Find examples of API error handling"
"How is file processing implemented here?"
```

### Direct Search Commands
```bash
# Find specific patterns
koder embedding search "user authentication flow"
koder embedding search "API rate limiting"
koder embedding search "async database operations"

# Search in specific directories
koder embedding search "test utilities" --directory ./tests/
koder embedding search "configuration management" --directory ./config/
```

### Task Mode with Context
```bash
# Tasks automatically use embeddings for context
koder task run "Refactor the authentication module using best practices"
koder task run "Add comprehensive error handling to the API endpoints"
```

## Indexing Management

### Manual Indexing
```bash
# Index entire workspace
koder embedding index

# Index specific directory
koder embedding index --directory ./src/

# Re-index everything
koder embedding index --force
```

### Status and Health
```bash
# Check indexing status
koder embedding status

# Detailed health check
koder embedding health

# Performance metrics
koder embedding stats
```

## File Support

### Automatically Indexed
- **Code files**: `.py`, `.js`, `.ts`, `.java`, `.cpp`, `.c`, `.go`, `.rs`
- **Config files**: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.conf`
- **Documentation**: `.md`, `.rst`, `.txt`
- **Scripts**: `.sh`, `.bash`, `.zsh`, `.fish`
- **Web**: `.html`, `.css`, `.scss`, `.less`
- **Data**: `.sql`, `.csv`

### Excluded Files
- Large files (>1MB by default)
- Binary files
- Files in `.git/`, `node_modules/`, `__pycache__/`
- Files matching patterns in `.koderignore`

## Performance Optimization

### Search Optimization
```bash
# Limit search results
koder embedding search "pattern" --limit 10

# Increase similarity threshold
koder embedding search "pattern" --threshold 0.8

# Search specific file types
koder embedding search "pattern" --extension py
```

### Indexing Optimization
```bash
# Configure chunk size for large files
EMBEDDING_CHUNK_SIZE=2000

# Set overlap for better context
EMBEDDING_OVERLAP=300

# Parallel indexing
EMBEDDING_WORKERS=4
```

## Troubleshooting

### Common Issues

#### API Key Problems
```bash
# Test Gemini API connection
koder embedding test --api-key

# Verify API key format
echo $GOOGLE_API_KEY
```

#### Indexing Issues
```bash
# Clear corrupted index
koder embedding clear

# Rebuild from scratch
koder embedding index --force --clear
```

#### Search Not Working
```bash
# Check index status
koder embedding status

# Validate embeddings
koder embedding validate --detailed
```

### Performance Issues

```bash
# Monitor indexing performance
koder embedding index --verbose --stats

# Check memory usage
koder embedding health --memory
```

## Advanced Configuration

### Custom File Patterns
```bash
# Include additional file types
EMBEDDING_PATTERNS=*.py,*.js,*.ts,*.vue,*.svelte

# Exclude specific directories
EMBEDDING_EXCLUDE=tests/,temp/,logs/
```

### Index Storage
```bash
# Custom vector store location
VECTOR_STORE_PATH=./custom/vector_store

# Persistent storage settings
EMBEDDING_PERSISTENCE=true
EMBEDDING_CACHE_SIZE=1000
```

### Model Configuration
```bash
# Alternative embedding models
EMBEDDING_MODEL=gemini-text-embedding
EMBEDDING_DIMENSIONS=768
EMBEDDING_BATCH_SIZE=100
```