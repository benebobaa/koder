"""Retrieval logic for context management."""

from pathlib import Path
from typing import Optional

from langchain_core.documents import Document

from koder.memory.vector_store import VectorStore


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
        Split text into chunks.

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]

        # Simple chunking by lines
        lines = text.split("\n")
        chunks = []
        current_chunk = []
        current_size = 0

        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            if current_size + line_size > chunk_size and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_size = line_size
            else:
                current_chunk.append(line)
                current_size += line_size

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        return chunks
