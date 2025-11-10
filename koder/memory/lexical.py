"""Lexical (keyword-based) retrieval for codebase search.

This module provides fast, free alternative to embedding-based search
using BM25 ranking and keyword matching. Ideal for exact matches like
function names, error messages, and specific identifiers.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import math
import structlog

logger = structlog.get_logger(__name__)


class Document:
    """Simple document class for lexical retrieval."""

    def __init__(
        self,
        page_content: str,
        metadata: Optional[Dict] = None,
        score: float = 0.0
    ):
        self.page_content = page_content
        self.metadata = metadata or {}
        self.score = score

    def __repr__(self):
        return f"Document(content_len={len(self.page_content)}, score={self.score:.4f})"


class BM25Retriever:
    """
    BM25 (Best Matching 25) ranking algorithm for text retrieval.

    BM25 is a probabilistic ranking function that scores documents based
    on term frequency (TF) and inverse document frequency (IDF).

    Parameters:
        k1: Controls term frequency saturation (default: 1.5)
        b: Controls length normalization (default: 0.75)
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[Document] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_length: float = 0.0
        self.idf_scores: Dict[str, float] = {}
        self.tokenized_docs: List[List[str]] = []

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25 scoring.

        For code, we want to split on:
        - Whitespace
        - Special characters (keeping underscores for snake_case)
        - CamelCase boundaries

        Examples:
            "def my_function():" -> ["def", "my", "function"]
            "AuthSession" -> ["Auth", "Session"]
            "sign-in timeout" -> ["sign", "in", "timeout"]
        """
        # Split CamelCase
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Split on non-alphanumeric (but keep underscores temporarily)
        tokens = re.findall(r'[a-zA-Z0-9_]+', text.lower())

        # Split on underscores
        expanded_tokens = []
        for token in tokens:
            expanded_tokens.extend(token.split('_'))

        # Filter out empty strings and very short tokens
        return [t for t in expanded_tokens if len(t) >= 2]

    def index_documents(self, documents: List[Document]):
        """
        Index documents for BM25 retrieval.

        Args:
            documents: List of documents to index
        """
        self.documents = documents
        self.tokenized_docs = []
        self.doc_lengths = []

        # Tokenize all documents
        for doc in documents:
            tokens = self._tokenize(doc.page_content)
            self.tokenized_docs.append(tokens)
            self.doc_lengths.append(len(tokens))

        # Calculate average document length
        if self.doc_lengths:
            self.avg_doc_length = sum(self.doc_lengths) / len(self.doc_lengths)
        else:
            self.avg_doc_length = 0.0

        # Calculate IDF scores
        self._calculate_idf()

        logger.info(
            "bm25_indexed",
            num_documents=len(documents),
            avg_doc_length=self.avg_doc_length,
            vocab_size=len(self.idf_scores)
        )

    def _calculate_idf(self):
        """Calculate Inverse Document Frequency for all terms."""
        self.idf_scores = {}
        num_docs = len(self.documents)

        if num_docs == 0:
            return

        # Count document frequency for each term
        df = defaultdict(int)
        for tokens in self.tokenized_docs:
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] += 1

        # Calculate IDF: log((N - df + 0.5) / (df + 0.5) + 1)
        for term, doc_freq in df.items():
            self.idf_scores[term] = math.log(
                (num_docs - doc_freq + 0.5) / (doc_freq + 0.5) + 1
            )

    def _score_document(self, query_tokens: List[str], doc_idx: int) -> float:
        """
        Calculate BM25 score for a document given query tokens.

        Args:
            query_tokens: Tokenized query
            doc_idx: Index of document to score

        Returns:
            BM25 score
        """
        doc_tokens = self.tokenized_docs[doc_idx]
        doc_length = self.doc_lengths[doc_idx]

        # Count term frequencies in document
        term_freqs = Counter(doc_tokens)

        score = 0.0
        for term in query_tokens:
            if term not in self.idf_scores:
                continue

            tf = term_freqs.get(term, 0)
            idf = self.idf_scores[term]

            # BM25 formula
            numerator = tf * (self.k1 + 1)
            denominator = tf + self.k1 * (
                1 - self.b + self.b * (doc_length / self.avg_doc_length)
            )

            score += idf * (numerator / denominator)

        return score

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Search for documents matching the query using BM25.

        Args:
            query: Search query
            k: Number of top results to return

        Returns:
            List of top-k documents with scores
        """
        if not self.documents:
            return []

        query_tokens = self._tokenize(query)

        if not query_tokens:
            return []

        # Score all documents
        scored_docs = []
        for idx, doc in enumerate(self.documents):
            score = self._score_document(query_tokens, idx)
            if score > 0:  # Only include documents with positive scores
                doc_copy = Document(
                    page_content=doc.page_content,
                    metadata=doc.metadata.copy(),
                    score=score
                )
                scored_docs.append(doc_copy)

        # Sort by score (descending) and return top-k
        scored_docs.sort(key=lambda x: x.score, reverse=True)

        logger.debug(
            "bm25_search",
            query=query,
            query_tokens=query_tokens,
            num_results=len(scored_docs),
            top_k=k
        )

        return scored_docs[:k]


class LexicalRetriever:
    """
    Lexical retrieval system combining BM25 ranking with keyword search.

    Features:
    - Fast keyword-based search (no API costs)
    - BM25 ranking for relevance scoring
    - CamelCase and snake_case aware tokenization
    - Good for exact matches (function names, error messages)
    - Fallback when embeddings unavailable or disabled
    """

    def __init__(self, workspace_path: Path):
        """
        Initialize lexical retriever.

        Args:
            workspace_path: Root path of the codebase
        """
        self.workspace_path = workspace_path
        self.bm25 = BM25Retriever()
        self.indexed = False

    def index_files(
        self,
        file_patterns: List[str] = None,
        max_files: int = 1000
    ) -> int:
        """
        Index files from workspace for lexical search.

        Args:
            file_patterns: Glob patterns for files to index (defaults to common code files)
            max_files: Maximum number of files to index

        Returns:
            Number of files indexed
        """
        if file_patterns is None:
            file_patterns = [
                "**/*.py",
                "**/*.js",
                "**/*.ts",
                "**/*.tsx",
                "**/*.java",
                "**/*.go",
                "**/*.rs",
                "**/*.cpp",
                "**/*.c",
                "**/*.h",
                "**/*.md",
            ]

        documents = []
        files_processed = 0

        for pattern in file_patterns:
            for file_path in self.workspace_path.glob(pattern):
                if files_processed >= max_files:
                    break

                # Skip common non-source directories
                if any(part in file_path.parts for part in [
                    ".git", "__pycache__", "node_modules", ".venv",
                    "venv", "build", "dist", ".pytest_cache"
                ]):
                    continue

                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                    # Create document with metadata
                    doc = Document(
                        page_content=content,
                        metadata={
                            "file_path": str(file_path.relative_to(self.workspace_path)),
                            "file_name": file_path.name,
                            "file_size": len(content),
                        }
                    )

                    documents.append(doc)
                    files_processed += 1

                except Exception as e:
                    logger.warning(
                        "file_read_error",
                        file_path=str(file_path),
                        error=str(e)
                    )
                    continue

        # Index documents in BM25
        self.bm25.index_documents(documents)
        self.indexed = True

        logger.info(
            "lexical_indexing_complete",
            files_indexed=files_processed,
            total_documents=len(documents)
        )

        return files_processed

    def search(
        self,
        query: str,
        k: int = 5,
        file_filter: Optional[str] = None
    ) -> List[Document]:
        """
        Search for documents matching the query.

        Args:
            query: Search query (natural language or keywords)
            k: Number of results to return
            file_filter: Optional filter for file paths (substring match)

        Returns:
            List of top-k documents with scores
        """
        if not self.indexed:
            logger.warning("lexical_search_not_indexed")
            return []

        # Perform BM25 search
        results = self.bm25.search(query, k=k * 2 if file_filter else k)

        # Apply file filter if specified
        if file_filter:
            results = [
                doc for doc in results
                if file_filter in doc.metadata.get("file_path", "")
            ]
            results = results[:k]

        logger.info(
            "lexical_search_complete",
            query=query,
            num_results=len(results),
            k=k,
            file_filter=file_filter
        )

        return results

    def get_stats(self) -> Dict:
        """Get indexing statistics."""
        return {
            "indexed": self.indexed,
            "num_documents": len(self.bm25.documents),
            "avg_doc_length": self.bm25.avg_doc_length,
            "vocab_size": len(self.bm25.idf_scores),
        }
