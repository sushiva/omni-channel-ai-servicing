"""
Test retrieval system with example queries.

This script tests the retrieval system by loading the FAISS index and
running sample queries to verify the system is working correctly.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from omni_channel_ai_servicing.infrastructure.retrieval import (
    EmbeddingService,
    FAISSVectorStore,
    Retriever,
)

# Load environment variables
load_dotenv()


def print_results(query: str, documents, intent: str = None):
    """Print retrieval results in a formatted way."""
    print("\n" + "=" * 70)
    print(f"Query: {query}")
    if intent:
        print(f"Intent: {intent}")
    print("=" * 70)

    if not documents:
        print("❌ No documents retrieved")
        return

    print(f"\n✓ Retrieved {len(documents)} documents:\n")

    for i, doc in enumerate(documents, 1):
        doc_id = doc.metadata.get("document_id", "UNKNOWN")
        title = doc.metadata.get("title", "Untitled")
        intents = ", ".join(doc.metadata.get("intents", []))
        chunk_idx = doc.metadata.get("chunk_index", 0)

        print(f"[{i}] {doc_id} - {title}")
        print(f"    Intents: {intents}")
        print(f"    Chunk: {chunk_idx}")
        print(f"    Content: {doc.page_content[:150]}...")
        print()


def main():
    """Test retrieval with sample queries."""
    print("=" * 70)
    print("Testing RAG Retrieval System")
    print("=" * 70)

    # Initialize components
    print("\n[1/3] Loading FAISS index...")
    vector_store = FAISSVectorStore(dimension=1536, index_path="faiss_index")

    try:
        vector_store.load(index_name="knowledge_base")
        stats = vector_store.get_statistics()
        print(f"  ✓ Loaded index with {stats['total_vectors']} vectors")
    except FileNotFoundError:
        print("  ❌ Index not found. Run 'python scripts/build_index.py' first.")
        sys.exit(1)

    print("\n[2/3] Initializing retriever...")
    embedding_service = EmbeddingService(
        model="text-embedding-3-small",
        cache_dir=".embedding_cache",
    )

    retriever = Retriever(
        vector_store=vector_store,
        embedding_service=embedding_service,
        top_k=3,
        similarity_threshold=0.5,
        intent_boost=1.5,
    )
    print("  ✓ Retriever ready")

    # Test queries
    print("\n[3/3] Running test queries...")

    test_cases = [
        {
            "query": "How do I update my address?",
            "intent": "ADDRESS_UPDATE",
        },
        {
            "query": "I was charged twice for the same purchase",
            "intent": "DISPUTE",
        },
        {
            "query": "Someone used my card without permission",
            "intent": "FRAUD_REPORT",
        },
        {
            "query": "My payment failed. What should I do?",
            "intent": "PAYMENT_ISSUE",
        },
        {
            "query": "How do I activate my new card?",
            "intent": "CARD_ACTIVATION",
        },
        {
            "query": "What's my account balance?",
            "intent": "BALANCE_INQUIRY",
        },
    ]

    for test_case in test_cases:
        query = test_case["query"]
        intent = test_case.get("intent")

        # Retrieve documents
        documents = retriever.retrieve(query=query, intent=intent, top_k=3)

        # Print results
        print_results(query, documents, intent)

    # Show retrieval metrics
    print("\n" + "=" * 70)
    print("Retrieval Metrics:")
    print("=" * 70)
    metrics = retriever.get_metrics()
    for key, value in metrics.items():
        print(f"{key}: {value}")
    print("=" * 70)

    # Test context formatting
    print("\n" + "=" * 70)
    print("Testing Context Formatting:")
    print("=" * 70)
    query = "How do I update my address?"
    documents = retriever.retrieve(query=query, intent="ADDRESS_UPDATE", top_k=2)
    context = retriever.format_context(documents, max_length=1000)
    print(context)

    print("\n✅ Retrieval system working correctly!")


if __name__ == "__main__":
    # Allow command-line query
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        print(f"Testing query: {query}\n")

        vector_store = FAISSVectorStore(dimension=1536, index_path="faiss_index")
        vector_store.load(index_name="knowledge_base")

        embedding_service = EmbeddingService(
            model="text-embedding-3-small",
            cache_dir=".embedding_cache",
        )

        retriever = Retriever(
            vector_store=vector_store,
            embedding_service=embedding_service,
            top_k=3,
        )

        documents = retriever.retrieve(query=query)
        print_results(query, documents)
    else:
        main()
