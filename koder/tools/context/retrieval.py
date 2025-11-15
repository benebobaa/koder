"""Context retrieval tool using hybrid search (lexical + embeddings) for enhanced code understanding."""

from pathlib import Path

from pydantic import BaseModel, Field

from koder.config.settings import get_settings
from koder.memory.embeddings import GoogleEmbeddings
from koder.memory.retrieval import CodebaseRetriever, HybridRetriever
from koder.memory.vector_store import VectorStore
from koder.tools.base import ReadOnlyTool
from koder.tools.registry import registry


class ContextRetrievalInput(BaseModel):
    """Input schema for context retrieval tool."""

    query: str = Field(
        description="Query or task description to find relevant context for"
    )
    max_results: int = Field(
        default=3, description="Maximum number of context results to retrieve"
    )
    file_filter: str | None = Field(
        default=None, description="Optional file path filter (e.g., '*.py' or 'src/**')"
    )


@registry.register("code", needs_approval=False, is_read_only=True)
class ContextRetrievalTool(ReadOnlyTool):
    """Tool for retrieving relevant code context using hybrid search (lexical + embeddings)."""

    name: str = "context_retrieval"
    description: str = (
        "Retrieves relevant code context using hybrid search (keyword + semantic). "
        "Use this when you need to understand existing code patterns, find similar implementations, "
        "or get context about the codebase before making changes. "
        "Automatically adapts search strategy based on configuration: "
        "lexical-only (fast/free), embeddings-only (semantic), or hybrid (recommended)."
    )
    args_schema: type[BaseModel] = ContextRetrievalInput

    def __init__(self, workspace_path: str, **kwargs):
        """Initialize the context retrieval tool."""
        super().__init__(workspace_path=workspace_path, **kwargs)
        self._hybrid_retriever = None
        self._codebase_retriever = None  # For backward compatibility
        self._initialized = False

    def _ensure_initialized(self):
        """Initialize the retriever on first use."""
        if self._initialized:
            return

        try:
            settings = get_settings()

            # Check if embeddings are enabled and mode requires them
            if not settings.embeddings.enabled or settings.embeddings.mode == "off":
                print(
                    "ℹ️  Context retrieval disabled (EMBEDDINGS_ENABLED=false or mode=off)"
                )
                self._initialized = True
                return

            # Initialize based on mode
            mode = settings.embeddings.mode
            workspace_path = Path(self.workspace_path)

            # Initialize codebase retriever if needed (for primary or reranker modes)
            if mode in ["primary", "reranker"]:
                try:
                    # Initialize embedding system
                    embeddings = GoogleEmbeddings(
                        api_key=settings.embeddings.google_api_key,
                        model=settings.embeddings.model,
                        dimension=settings.embeddings.dimension,
                    )

                    # Initialize vector store
                    vector_store = VectorStore(
                        embeddings=embeddings,
                        persist_directory=settings.storage.vector_store_path,
                    )

                    # Initialize retriever
                    self._codebase_retriever = CodebaseRetriever(
                        vector_store=vector_store, workspace_path=self.workspace_path
                    )

                except Exception as e:
                    print(f"⚠️  Embedding initialization failed: {e}")
                    print("   Falling back to lexical-only mode")
                    mode = "lexical"

            # Initialize hybrid retriever
            self._hybrid_retriever = HybridRetriever(
                workspace_path=workspace_path,
                codebase_retriever=self._codebase_retriever,
                mode=mode,
            )

            # Auto-index workspace if needed
            if mode == "lexical" or (
                mode == "reranker" and self._codebase_retriever is None
            ):
                # Lexical mode always needs indexing
                self._auto_index_workspace_lexical()
            elif mode in ["primary", "reranker"] and self._codebase_retriever:
                # Check if embedding data exists
                try:
                    test_results = (
                        self._codebase_retriever.vector_store.similarity_search(
                            "test", k=1
                        )
                    )
                    has_data = len(test_results) > 0
                except Exception:
                    has_data = False

                if not has_data:
                    self._auto_index_workspace()

            self._initialized = True

        except Exception as e:
            print(f"❌ Context retrieval initialization failed: {e}")
            self._hybrid_retriever = None
            self._initialized = True

    def _auto_index_workspace_lexical(self):
        """Auto-index workspace for lexical search only (fast, no API calls)."""
        try:
            print("🔍 Auto-indexing workspace for lexical search...")
            if self._hybrid_retriever:
                stats = self._hybrid_retriever.index_workspace(lexical_only=True)
                files_indexed = stats.get("lexical", {}).get("files_indexed", 0)
                if files_indexed > 0:
                    print(f"✅ Indexed {files_indexed} files for keyword search")
        except Exception as e:
            print(f"⚠️  Lexical indexing failed: {e}")

    def _auto_index_workspace(self):
        """Automatically index the workspace on first use with smart file selection."""
        try:
            workspace_path = Path(self.workspace_path)

            # Skip common non-source directories
            skip_dirs = {
                ".git",
                ".vscode",
                ".idea",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build",
                "target",
                ".pytest_cache",
                ".mypy_cache",
                ".tox",
                "coverage",
                ".next",
                ".nuxt",
                "site-packages",
                "vendor",
                "cache",
                "logs",
            }

            # Define file priorities for intelligent indexing
            file_priorities = {
                # High priority - core project files
                "setup.py": 10,
                "pyproject.toml": 10,
                "package.json": 10,
                "requirements.txt": 10,
                "Cargo.toml": 10,
                "go.mod": 10,
                "main.py": 10,
                "app.py": 10,
                "index.js": 10,
                "main.go": 10,
                # High priority - configuration files
                "README.md": 9,
                "CHANGELOG.md": 8,
                "CONTRIBUTING.md": 7,
                ".env.example": 8,
                "Dockerfile": 9,
                "docker-compose.yml": 9,
                # Medium priority - source files
                ".py": 7,
                ".js": 7,
                ".ts": 7,
                ".go": 7,
                ".rs": 7,
                ".java": 7,
                ".jsx": 6,
                ".tsx": 6,
                ".vue": 6,
                ".svelte": 6,
                # Medium priority - documentation
                ".md": 5,
                ".rst": 5,
                ".txt": 4,
                # Lower priority - config and data
                ".json": 5,
                ".yaml": 5,
                ".yml": 5,
                ".toml": 5,
                ".ini": 4,
                ".sh": 5,
                ".sql": 5,
                ".dockerfile": 6,
                # Test files (important but lower priority)
                "test_": 4,
                "_test.py": 4,
                ".test.js": 4,
                "spec.": 4,
            }

            # Collect all files with their priorities
            files_to_index = []

            # Walk through directory structure
            for file_path in workspace_path.rglob("*"):
                if not file_path.is_file():
                    continue

                # Skip if in ignored directory
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue

                # Calculate priority based on file extension and name
                priority = 1  # Default priority
                file_str = str(file_path.name).lower()

                for pattern, prio in file_priorities.items():
                    if pattern.startswith("."):
                        # File extension match
                        if file_path.suffix.lower() == pattern:
                            priority = max(priority, prio)
                    elif pattern.startswith("test_") or pattern.endswith("_test.py"):
                        # Test file patterns
                        if pattern in file_str:
                            priority = max(priority, prio)
                    else:
                        # Exact filename match
                        if pattern == file_str:
                            priority = max(priority, prio)

                # Skip very small or very large files
                try:
                    file_size = file_path.stat().st_size
                    if file_size < 10 or file_size > 1024 * 1024:  # Skip <10B or >1MB
                        continue
                except OSError:
                    continue

                files_to_index.append((file_path, priority))

            # Sort by priority (highest first) and limit to reasonable number
            files_to_index.sort(key=lambda x: x[1], reverse=True)
            max_files = 500  # Limit to prevent excessive indexing

            print(
                f"🔍 Smart indexing: Found {len(files_to_index)} eligible files, indexing top {max_files}"
            )

            # Index files in priority order
            indexed_count = 0
            for file_path, priority in files_to_index[:max_files]:
                try:
                    # Use the retriever's smart index method
                    success = self._retriever.index_file(
                        str(file_path), chunk_size=1500
                    )
                    if success:
                        indexed_count += 1

                        # Progress indicator for larger workspaces
                        if indexed_count % 50 == 0:
                            print(f"  Indexed {indexed_count} files...")

                except Exception:
                    # Skip problematic files
                    continue

            if indexed_count > 0:
                print(
                    f"✅ Successfully indexed {indexed_count} files for semantic search"
                )

                # Log what was indexed
                [str(f[0]) for f in files_to_index[:indexed_count]]
                high_priority_count = sum(
                    1 for _, p in files_to_index[:indexed_count] if p >= 7
                )
                print(
                    f"   • {high_priority_count} high-priority files (setup, main, config)"
                )
                print(f"   • {indexed_count - high_priority_count} other source files")
            else:
                print(
                    "⚠️  No files were indexed. Check file permissions and workspace structure."
                )

        except Exception as e:
            print(f"❌ Auto-indexing failed: {str(e)}")
            # Don't raise - allow tool to continue without context

    def _run(
        self, query: str, max_results: int = 3, file_filter: str | None = None
    ) -> str:
        """Execute the context retrieval using hybrid search."""
        self._ensure_initialized()

        if not self._hybrid_retriever:
            return "Context retrieval is not available."

        try:
            # Get relevant context using hybrid retriever
            context = self._hybrid_retriever.get_relevant_context(query, k=max_results)

            # Apply file filtering if specified
            if file_filter and context != "No relevant context found.":
                try:
                    filtered_docs = self._hybrid_retriever.search(
                        query, k=max_results, file_filter=file_filter
                    )
                    if filtered_docs:
                        lines = ["Filtered Context:", ""]
                        for i, doc in enumerate(filtered_docs, 1):
                            file_path = doc.metadata.get("file_path", "unknown")
                            score = getattr(doc, "score", 0.0)
                            lines.append(
                                f"[{i}] From {file_path} (score: {score:.2f}):"
                            )
                            lines.append(doc.page_content)
                            lines.append("")
                        context = "\n".join(lines)
                except Exception:
                    # Fall back to original context if filtering fails
                    pass

            return context

        except Exception as e:
            return f"Error retrieving context: {str(e)}"

    async def _arun(
        self, query: str, max_results: int = 3, file_filter: str | None = None
    ) -> str:
        """Execute the context retrieval asynchronously."""
        # TODO: Implement true async retrieval
        # For now, just wrap the sync version
        return self._run(query, max_results, file_filter)
