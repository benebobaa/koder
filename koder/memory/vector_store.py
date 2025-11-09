"""Vector store for semantic search."""

from pathlib import Path
from typing import Any, Optional

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from koder.memory.embeddings import create_embeddings


class VectorStore:
    """Vector store wrapper for code and documentation search."""

    def __init__(
        self,
        persist_directory: str,
        embeddings: Optional[Embeddings] = None,
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
        ids: Optional[list[str]] = None,
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
        metadatas: Optional[list[dict]] = None,
        ids: Optional[list[str]] = None,
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
        filter: Optional[dict[str, Any]] = None,
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
        filter: Optional[dict[str, Any]] = None,
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

    def delete(self, ids: list[str]) -> None:
        """
        Delete documents by ID.

        Args:
            ids: List of document IDs to delete
        """
        self.vectorstore.delete(ids=ids)

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.vectorstore.delete_collection()

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
    embeddings: Optional[Embeddings] = None,
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
