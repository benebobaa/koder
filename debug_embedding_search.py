"""Debug script to investigate embedding search discrepancies."""

import json
import time
from koder.config.loader import load_env_file
from koder.memory.embeddings import GoogleEmbeddings
from koder.memory.vector_store import VectorStore
from koder.tools.context import ContextRetrievalTool


def debug_search_comparison():
    """Debug why vector store and ContextRetrievalTool give different results."""

    load_env_file()

    print("🔍 Debugging Embedding Search Discrepancies")
    print("=" * 50)

    # Initialize components
    embeddings = GoogleEmbeddings(
        api_key="AIzaSyD2Lmun2MWtIHbkpem-Ofdy9COU_deBwnM",
        model="models/text-embedding-004",
    )

    vector_store = VectorStore(
        embeddings=embeddings, persist_directory="./data/vector_store"
    )

    context_tool = ContextRetrievalTool(".")

    test_queries = ["main", "hello world", "application", "python", "def main"]

    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")

        # Test 1: Direct vector store search
        try:
            start_time = time.time()
            vs_results = vector_store.similarity_search(query, k=3)
            vs_time = (time.time() - start_time) * 1000
            print(f"  Vector Store: {len(vs_results)} results in {vs_time:.1f}ms")
            for i, result in enumerate(vs_results):
                content_preview = result.page_content[:50].replace("\n", "\\n")
                print(f"    {i + 1}. {content_preview}...")
        except Exception as e:
            print(f"  Vector Store Error: {e}")

        # Test 2: ContextRetrievalTool
        try:
            start_time = time.time()
            ct_result = context_tool._run(query, max_results=3)
            ct_time = (time.time() - start_time) * 1000
            print(
                f"  Context Tool: {ct_result.count('[') if 'From ' in ct_result else 0} files in {ct_time:.1f}ms"
            )
            # Extract file paths from context
            file_paths = [line for line in ct_result.split("\n") if "From " in line]
            for path in file_paths[:3]:
                print(f"    {path}")
        except Exception as e:
            print(f"  Context Tool Error: {e}")

        # Test 3: Test vector store get_collection
        try:
            collection = vector_store.get_collection()
            all_docs = collection.get(include=["documents", "metadatas"])
            doc_count = len(all_docs.get("ids", []))
            print(f"  Chroma Collection: {doc_count} documents")
        except Exception as e:
            print(f"  Collection Error: {e}")


def test_embedding_generation():
    """Test embedding generation directly."""
    print("\n" + "=" * 50)
    print("🔍 Testing Embedding Generation")
    print("=" * 50)

    load_env_file()

    embeddings = GoogleEmbeddings(
        api_key="AIzaSyD2Lmun2MWtIHbkpem-Ofdy9COU_deBwnM",
        model="models/text-embedding-004",
    )

    test_texts = [
        "main function definition",
        "Hello World program",
        "Python CLI application",
        "koder setup command",
    ]

    print(f"Testing {len(test_texts)} different text types:")

    for text in test_texts:
        try:
            start_time = time.time()
            embedding = embeddings.embed_query(text)
            response_time = (time.time() - start_time) * 1000

            print(f"  '{text[:30]}...'")
            print(f"    Dimensions: {len(embedding)}")
            print(f"    Response: {response_time:.1f}ms")
            print(f"    First 3 values: {embedding[:3]}")
            print(f"    Sample value: {embedding[0]:.6f}")
        except Exception as e:
            print(f"  Error: {e}")


if __name__ == "__main__":
    debug_search_comparison()
    test_embedding_generation()
