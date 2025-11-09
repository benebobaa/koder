"""Retrieval logic for context management."""

import hashlib
import time
from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from koder.memory.vector_store import VectorStore
from koder.observability.logging import get_logger

logger = get_logger(__name__)


class CodebaseRetriever:
    """Retriever for codebase context."""

    def __init__(self, vector_store: VectorStore, workspace_path: str = "."):
        """
        Initialize codebase retriever.

        Args:
            vector_store: Vector store instance
            workspace_path: Path to workspace
        """
        self.vector_store = vector_store
        self.workspace_path = Path(workspace_path)
        self._file_hash_cache = {}  # Cache for file content hashes

    def index_file(self, file_path: str, chunk_size: int = 1000) -> list[str]:
        """
        Index a single file into vector store.

        Args:
            file_path: Path to file to index
            chunk_size: Size of text chunks

        Returns:
            List of document IDs
        """
        path = self.workspace_path / file_path

        if not path.exists() or not path.is_file():
            raise ValueError(f"File not found: {file_path}")

        # Read file content
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Skip binary files
            return []

        # Create chunks if content is large
        chunks = self._chunk_text(content, chunk_size)

        # Create documents
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "file_path": str(file_path),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                },
            )
            for i, chunk in enumerate(chunks)
        ]

        # Add to vector store
        ids = self.vector_store.add_documents(documents)
        return ids

    def index_directory(
        self,
        directory_path: str = ".",
        pattern: str = "**/*.py",
        chunk_size: int = 1000,
    ) -> int:
        """
        Index files in a directory.

        Args:
            directory_path: Directory to index
            pattern: Glob pattern for files
            chunk_size: Size of text chunks

        Returns:
            Number of files indexed
        """
        dir_path = self.workspace_path / directory_path

        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        # Find matching files
        files = list(dir_path.glob(pattern))

        indexed_count = 0
        for file in files:
            try:
                rel_path = file.relative_to(self.workspace_path)
                self.index_file(str(rel_path), chunk_size)
                indexed_count += 1
            except Exception:
                # Skip files that can't be indexed
                continue

        return indexed_count

    def search_code(
        self,
        query: str,
        k: int = 4,
        file_filter: Optional[str] = None,
    ) -> list[Document]:
        """
        Search for code snippets.

        Args:
            query: Search query
            k: Number of results
            file_filter: Optional file path filter

        Returns:
            List of relevant documents
        """
        filter_dict = None
        if file_filter:
            filter_dict = {"file_path": file_filter}

        return self.vector_store.similarity_search(query, k=k, filter=filter_dict)

    def get_relevant_context(
        self,
        query: str,
        k: int = 3,
    ) -> str:
        """
        Get relevant context for a query.

        Args:
            query: Query text
            k: Number of results

        Returns:
            Formatted context string
        """
        documents = self.search_code(query, k=k)

        if not documents:
            return "No relevant context found."

        lines = ["Relevant Context:", ""]

        for i, doc in enumerate(documents, 1):
            file_path = doc.metadata.get("file_path", "unknown")
            lines.append(f"[{i}] From {file_path}:")
            lines.append(doc.page_content)
            lines.append("")

        return "\n".join(lines)

    def _chunk_text(self, text: str, chunk_size: int) -> list[str]:
        """
        Split text into intelligent chunks preserving code structure.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks with preserved context
        """
        if len(text) <= chunk_size:
            return [text]

        # Detect file type for intelligent chunking
        file_extension = self._detect_file_type(text)

        if file_extension in ["py", "js", "ts", "jsx", "tsx", "java", "cpp", "c", "h", "go", "rs"]:
            return self._chunk_code(text, chunk_size)
        elif file_extension in ["md", "txt"]:
            return self._chunk_markdown(text, chunk_size)
        else:
            return self._chunk_generic(text, chunk_size)

    def _detect_file_type(self, text: str) -> str:
        """
        Detect file type based on content patterns.

        Args:
            text: File content

        Returns:
            File extension string
        """
        # Python detection
        if any(pattern in text for pattern in ["import ", "from ", "def ", "class ", "    "]):
            return "py"

        # JavaScript/TypeScript detection
        if any(pattern in text for pattern in ["function ", "const ", "let ", "var ", "=>", "import "]):
            return "js"

        # Markdown detection
        if text.startswith("#") or "##" in text or "**" in text:
            return "md"

        # JSON detection
        if text.strip().startswith("{") and text.strip().endswith("}"):
            return "json"

        # YAML detection
        if ":" in text and (text.strip().startswith("---") or "\n  " in text):
            return "yaml"

        return "txt"

    def _chunk_code(self, text: str, chunk_size: int) -> list[str]:
        """
        Chunk code while preserving function/class structure.

        Args:
            text: Code text
            chunk_size: Maximum chunk size

        Returns:
            List of code chunks
        """
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_size = 0
        indent_level = 0
        function_start = None

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            line_size = len(line) + 1

            # Detect function/class definitions
            if (line_stripped.startswith(("def ", "class ", "function ", "const ", "let ", "var ")) and
                "(" in line or "=" in line):
                function_start = i

            # Detect indentation changes (code blocks)
            if line and not line.startswith(" "):
                new_indent = 0
            else:
                new_indent = len(line) - len(line.lstrip())

            # If we're starting a new block and chunk is getting large
            if (new_indent < indent_level and current_size + line_size > chunk_size * 0.8 and
                current_chunk and function_start is not None):
                # Complete current chunk at good boundary
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0
                function_start = None

            # Add line to current chunk
            current_chunk.append(line)
            current_size += line_size
            indent_level = new_indent

            # If chunk exceeds size, try to find a good split point
            if current_size >= chunk_size:
                # Look for recent function/class boundary
                if function_start is not None and i - function_start < 20:
                    # Include the complete function
                    continue
                else:
                    # Split at current position
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                    function_start = None

        # Add remaining content
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _chunk_markdown(self, text: str, chunk_size: int) -> list[str]:
        """
        Chunk markdown while preserving section structure.

        Args:
            text: Markdown text
            chunk_size: Maximum chunk size

        Returns:
            List of markdown chunks
        """
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1

            # If this is a header and current chunk is large, start new chunk
            if (line.startswith("#") and current_size > chunk_size * 0.5 and
                current_chunk):
                chunks.append("\n".join(current_chunk))
                current_chunk = []
                current_size = 0

            current_chunk.append(line)
            current_size += line_size

            # If chunk exceeds size, try to split at paragraph
            if current_size >= chunk_size:
                # Look for recent paragraph break
                for j in range(len(current_chunk) - 1, max(0, len(current_chunk) - 10), -1):
                    if current_chunk[j].strip() == "":
                        # Split at paragraph break
                        chunks.append("\n".join(current_chunk[:j + 1]))
                        current_chunk = current_chunk[j + 1:]
                        current_size = sum(len(l) + 1 for l in current_chunk)
                        break
                else:
                    # No good break found, split anyway
                    chunks.append("\n".join(current_chunk))
                    current_chunk = []
                    current_size = 0

        # Add remaining content
        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks

    def _chunk_generic(self, text: str, chunk_size: int) -> list[str]:
        """
        Generic chunking for non-code files.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        # Split by paragraphs or natural breaks
        paragraphs = text.split("\n\n")
        chunks = []
        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph) + 2  # +2 for newlines

            if current_size + paragraph_size > chunk_size and current_chunk:
                chunks.append(current_chunk.rstrip())
                current_chunk = paragraph + "\n\n"
                current_size = paragraph_size
            else:
                current_chunk += paragraph + "\n\n"
                current_size += paragraph_size

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        return chunks

    def _get_file_hash(self, file_path: str) -> str:
        """
        Get hash of file content for change detection.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash of file content
        """
        path = self.workspace_path / file_path

        if not path.exists():
            return ""

        try:
            # Get file modification time and size for quick check
            stat = path.stat()
            cache_key = f"{file_path}:{stat.st_mtime}:{stat.st_size}"

            if cache_key in self._file_hash_cache:
                return self._file_hash_cache[cache_key]

            # Read file and compute hash
            content = path.read_text(encoding="utf-8")
            file_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

            # Cache the hash
            self._file_hash_cache[cache_key] = file_hash

            return file_hash

        except (OSError, UnicodeDecodeError):
            return ""

    def index_file_incremental(self, file_path: str, chunk_size: int = 1500, force: bool = False) -> bool:
        """
        Index a single file with incremental updates.

        Args:
            file_path: Path to file to index
            chunk_size: Size of text chunks
            force: Force re-indexing even if unchanged

        Returns:
            True if file was indexed/updated, False if unchanged
        """
        path = self.workspace_path / file_path

        if not path.exists() or not path.is_file():
            # File was deleted, remove from index
            try:
                self.vector_store.delete(where={"file_path": file_path})
                logger.info("file_removed_from_index", file_path=file_path)
                return True
            except Exception as e:
                logger.error("file_removal_failed", file_path=file_path, error=str(e))
                return False

        # Check if file has changed
        current_hash = self._get_file_hash(file_path)
        if not current_hash:
            return False  # Binary file or error

        # Check if file is already indexed with same content
        if not force:
            try:
                collection = self.vector_store.get_collection()
                existing_docs = collection.get(
                    where={"file_path": file_path},
                    limit=1,
                    include=["metadatas"]
                )

                if existing_docs["metadatas"]:
                    existing_metadata = existing_docs["metadatas"][0]
                    if existing_metadata.get("content_hash") == current_hash:
                        return False  # File unchanged

            except Exception:
                pass  # Fall back to full indexing

        try:
            # Read file content
            content = path.read_text(encoding="utf-8")

            # Remove existing embeddings for this file
            self.vector_store.delete(where={"file_path": file_path})

            # Create chunks
            chunks = self._chunk_text(content, chunk_size)

            # Create documents with hash metadata
            documents = [
                Document(
                    page_content=chunk,
                    metadata={
                        "file_path": str(file_path),
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        "content_hash": current_hash,
                        "file_size": len(content),
                        "indexed_at": time.time(),
                    },
                )
                for i, chunk in enumerate(chunks)
            ]

            # Add to vector store
            ids = self.vector_store.add_documents(documents)

            logger.info("file_indexed_incremental",
                       file_path=file_path,
                       chunks=len(ids),
                       hash=current_hash[:8])

            return True

        except Exception as e:
            logger.error("incremental_index_failed", file_path=file_path, error=str(e))
            return False

    def index_directory_incremental(
        self,
        directory_path: str = ".",
        pattern: str = "**/*.py",
        chunk_size: int = 1500,
        force: bool = False,
    ) -> dict[str, int]:
        """
        Index files in a directory with incremental updates.

        Args:
            directory_path: Directory to index
            pattern: Glob pattern for files
            chunk_size: Size of text chunks
            force: Force re-indexing all files

        Returns:
            Dictionary with indexing statistics
        """
        dir_path = self.workspace_path / directory_path

        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory not found: {directory_path}")

        # Find matching files
        files = list(dir_path.glob(pattern))

        stats = {
            "total_files": len(files),
            "indexed_files": 0,
            "updated_files": 0,
            "skipped_files": 0,
            "error_files": 0,
            "total_chunks": 0,
        }

        for file in files:
            try:
                rel_path = file.relative_to(self.workspace_path)

                # Skip large files
                if file.stat().st_size > 1024 * 1024:  # 1MB
                    stats["skipped_files"] += 1
                    continue

                # Try incremental indexing
                was_indexed = self.index_file_incremental(str(rel_path), chunk_size, force)

                if was_indexed:
                    stats["updated_files"] += 1
                    stats["indexed_files"] += 1
                else:
                    stats["skipped_files"] += 1

            except Exception as e:
                stats["error_files"] += 1
                logger.error("directory_index_file_failed", file=str(file), error=str(e))

        # Get total chunk count
        try:
            stats["total_chunks"] = self.vector_store.count()
        except Exception:
            pass

        logger.info("directory_indexed_incremental", **stats)
        return stats

    def smart_index_directory(
        self,
        directory_path: str = ".",
        patterns: Optional[list[str]] = None,
        chunk_size: int = 1500,
        force: bool = False,
    ) -> dict[str, int]:
        """
        Smart indexing with multiple patterns and comprehensive stats.

        Args:
            directory_path: Directory to index
            patterns: List of file patterns to index
            chunk_size: Size of text chunks
            force: Force re-indexing all files

        Returns:
            Dictionary with comprehensive indexing statistics
        """
        if patterns is None:
            patterns = [
                "**/*.py", "**/*.js", "**/*.ts", "**/*.jsx", "**/*.tsx",
                "**/*.md", "**/*.json", "**/*.yaml", "**/*.yml", "**/*.txt",
                "**/*.sql", "**/*.sh", "**/*.go", "**/*.rs", "**/*.java",
                "**/*.cpp", "**/*.c", "**/*.h", "**/*.dockerfile",
                "**/Dockerfile*"
            ]

        # Skip common non-source directories
        skip_dirs = {
            ".git", ".vscode", ".idea", "__pycache__", "node_modules",
            ".venv", "venv", "env", ".env", "dist", "build", "target",
            ".pytest_cache", ".mypy_cache", ".tox", "coverage", ".next",
            ".nuxt", "site-packages", "spm-packages"
        }

        dir_path = self.workspace_path / directory_path
        total_stats = {
            "patterns_processed": len(patterns),
            "total_files_found": 0,
            "indexed_files": 0,
            "updated_files": 0,
            "skipped_files": 0,
            "error_files": 0,
            "total_chunks": 0,
            "start_time": time.time(),
        }

        for pattern in patterns:
            try:
                files = [
                    f for f in dir_path.glob(pattern)
                    if f.is_file() and not any(skip_dir in f.parts for skip_dir in skip_dirs)
                ]

                total_stats["total_files_found"] += len(files)

                pattern_stats = self.index_directory_incremental(
                    directory_path=directory_path,
                    pattern=pattern.replace("**/", ""),
                    chunk_size=chunk_size,
                    force=force,
                )

                # Merge stats
                total_stats["indexed_files"] += pattern_stats["indexed_files"]
                total_stats["updated_files"] += pattern_stats["updated_files"]
                total_stats["skipped_files"] += pattern_stats["skipped_files"]
                total_stats["error_files"] += pattern_stats["error_files"]

            except Exception as e:
                logger.error("pattern_index_failed", pattern=pattern, error=str(e))

        total_stats["total_chunks"] = self.vector_store.count()
        total_stats["end_time"] = time.time()
        total_stats["duration"] = total_stats["end_time"] - total_stats["start_time"]

        logger.info("smart_indexing_completed", **total_stats)
        return total_stats
