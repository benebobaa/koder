"""Vector store for semantic search."""

from pathlib import Path
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from koder.memory.embeddings import create_embeddings


class VectorStore:
    """Vector store wrapper for code and documentation search."""

    def __init__(
        self,
        persist_directory: str,
        embeddings: Embeddings | None = None,
        collection_name: str = "koder",
    ):
        """
        Initialize vector store.

        Args:
            persist_directory: Directory to persist vector store
            embeddings: Embeddings instance (creates default if None)
            collection_name: Name of the collection
        """
        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)

        # Create embeddings if not provided
        if embeddings is None:
            embeddings = create_embeddings(provider="google")

        # Create ChromaDB vector store
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_directory,
        )

    def add_documents(
        self,
        documents: list[Document],
        ids: list[str] | None = None,
    ) -> list[str]:
        """
        Add documents to vector store.

        Args:
            documents: List of documents to add
            ids: Optional list of document IDs

        Returns:
            List of document IDs
        """
        return self.vectorstore.add_documents(documents, ids=ids)

    def add_texts(
        self,
        texts: list[str],
        metadatas: list[dict] | None = None,
        ids: list[str] | None = None,
    ) -> list[str]:
        """
        Add texts to vector store.

        Args:
            texts: List of texts to add
            metadatas: Optional metadata for each text
            ids: Optional IDs for each text

        Returns:
            List of document IDs
        """
        return self.vectorstore.add_texts(texts, metadatas=metadatas, ids=ids)

    def similarity_search(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[Document]:
        """
        Search for similar documents.

        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of similar documents
        """
        return self.vectorstore.similarity_search(query, k=k, filter=filter)

    def similarity_search_with_score(
        self,
        query: str,
        k: int = 4,
        filter: dict[str, Any] | None = None,
    ) -> list[tuple[Document, float]]:
        """
        Search for similar documents with relevance scores.

        Args:
            query: Query text
            k: Number of results to return
            filter: Optional metadata filter

        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(query, k=k, filter=filter)

    def delete(self, ids: list[str] | None = None, where: dict | None = None) -> None:
        """
        Delete documents by ID or metadata filter.

        Args:
            ids: Optional list of document IDs to delete
            where: Optional metadata filter for deletion
        """
        if where:
            # Delete by metadata filter using Chroma's underlying collection
            collection = self.vectorstore._collection
            collection.delete(where=where)
        elif ids:
            # Delete by IDs
            self.vectorstore.delete(ids=ids)
        else:
            raise ValueError("Either 'ids' or 'where' must be provided")

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.vectorstore.delete_collection()

    def count(self) -> int:
        """
        Count the number of documents in the vector store.

        Returns:
            Number of documents
        """
        try:
            # Use the Chroma API to get the collection count
            collection = self.vectorstore._collection
            return collection.count()
        except Exception:
            # If getting count fails, return 0
            return 0

    def get_collection(self):
        """
        Get the underlying Chroma collection.

        Returns:
            Chroma collection object
        """
        return self.vectorstore._collection

    def as_retriever(self, **kwargs):
        """
        Get retriever interface.

        Args:
            **kwargs: Retriever configuration options

        Returns:
            Retriever instance
        """
        return self.vectorstore.as_retriever(**kwargs)


def create_vector_store(
    persist_directory: str,
    embeddings: Embeddings | None = None,
    collection_name: str = "koder",
) -> VectorStore:
    """
    Create vector store instance.

    Args:
        persist_directory: Directory to persist vector store
        embeddings: Optional embeddings instance
        collection_name: Collection name

    Returns:
        VectorStore instance
    """
    return VectorStore(
        persist_directory=persist_directory,
        embeddings=embeddings,
        collection_name=collection_name,
    )
