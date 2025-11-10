"""Embeddings configuration."""

from typing import Optional

import google.generativeai as genai
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from koder.config.settings import EmbeddingsSettings


class GoogleEmbeddings(Embeddings):
    """Google Gemini Text Embeddings wrapper for LangChain."""

    def __init__(
        self,
        api_key: str,
        model: str = "models/text-embedding-004",
        dimension: Optional[int] = None
    ):
        """
        Initialize Google embeddings.

        Args:
            api_key: Google API key
            model: Embedding model name
            dimension: Optional output dimensionality (e.g., 768, 512)
                      If specified, reduces embedding size for cost savings.
                      Only supported by models like text-embedding-004.
        """
        genai.configure(api_key=api_key)
        self.model = model
        self.dimension = dimension

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed multiple documents.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        kwargs = {
            "model": self.model,
            "content": texts,
            "task_type": "retrieval_document",
        }

        # Add output_dimensionality if specified
        if self.dimension is not None:
            kwargs["output_dimensionality"] = self.dimension

        result = genai.embed_content(**kwargs)
        return result["embedding"]

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        kwargs = {
            "model": self.model,
            "content": text,
            "task_type": "retrieval_query",
        }

        # Add output_dimensionality if specified
        if self.dimension is not None:
            kwargs["output_dimensionality"] = self.dimension

        result = genai.embed_content(**kwargs)
        return result["embedding"]


def create_embeddings(
    settings: Optional[EmbeddingsSettings] = None,
    provider: str = "google",
) -> Embeddings:
    """
    Create embeddings instance.

    Args:
        settings: Embeddings configuration
        provider: Embeddings provider ('google' or 'local')

    Returns:
        Configured embeddings instance
    """
    if settings is None:
        from koder.config.settings import get_settings

        settings = get_settings().embeddings

    if provider == "google":
        if not settings.google_api_key:
            raise ValueError("Google API key not configured")

        return GoogleEmbeddings(
            api_key=settings.google_api_key,
            model=settings.model,
            dimension=settings.dimension if settings.dimension != 768 else None,
        )

    elif provider == "local":
        # Fallback to local embeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
        )

    else:
        raise ValueError(f"Unknown embeddings provider: {provider}")
