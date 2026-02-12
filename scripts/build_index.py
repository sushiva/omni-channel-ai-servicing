"""
Build FAISS index from knowledge base documents.

This script loads all documents from the knowledge base, generates embeddings,
and creates a FAISS index for fast retrieval.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from omni_channel_ai_servicing.infrastructure.retrieval import (
    DocumentLoader,
    EmbeddingService,
    FAISSVectorStore,
)

# Load environment variables
load_dotenv()


def main():
    """Build FAISS index from knowledge base."""
    print("=" * 70)
    print("Building FAISS Index for RAG System")
    print("=" * 70)

    # Initialize components
    print("\n[1/5] Initializing components...")
    doc_loader = DocumentLoader(
        knowledge_base_path="knowledge_base",
        chunk_size=500,
        chunk_overlap=50,
    )

    embedding_service = EmbeddingService(
        model="text-embedding-3-small",
        cache_dir=".embedding_cache",
    )

    vector_store = FAISSVectorStore(
        dimension=1536,
        index_path="faiss_index",
    )

    # Load documents
    print("\n[2/5] Loading documents from knowledge base...")
    documents = doc_loader.load_all_documents()
    print(f"  ✓ Loaded {len(documents)} document chunks")

    # Show statistics
    stats = doc_loader.get_statistics()
    print(f"  ✓ Total characters: {stats['total_characters']:,}")
    print(f"  ✓ Avg chunk size: {stats['avg_chunk_size']} chars")
    print(f"  ✓ Unique intents: {len(stats['unique_intents'])}")
    print(f"  ✓ Document types: {stats['document_types']}")

    # Generate embeddings
    print("\n[3/5] Generating embeddings...")
    print("  (This may take a few minutes on first run)")
    embeddings = embedding_service.embed_documents(documents, use_cache=True)
    print(f"  ✓ Generated {len(embeddings)} embeddings")

    # Show cache statistics
    cache_stats = embedding_service.get_cache_statistics()
    print(f"  ✓ Cache hits: {cache_stats['cache_hits']}")
    print(f"  ✓ Cache misses: {cache_stats['cache_misses']}")
    print(f"  ✓ Cache hit rate: {cache_stats['hit_rate']}")

    # Add to vector store
    print("\n[4/5] Building FAISS index...")
    vector_store.add_documents(documents, embeddings)
    print(f"  ✓ Added {len(documents)} vectors to index")

    # Save index
    print("\n[5/5] Saving index to disk...")
    vector_store.save(index_name="knowledge_base")
    print("  ✓ Saved to faiss_index/knowledge_base.faiss")
    print("  ✓ Saved to faiss_index/knowledge_base.pkl")

    # Show final statistics
    index_stats = vector_store.get_statistics()
    print("\n" + "=" * 70)
    print("Index Statistics:")
    print("=" * 70)
    print(f"Total vectors:      {index_stats['total_vectors']}")
    print(f"Vector dimension:   {index_stats['dimension']}")
    print(f"Unique documents:   {index_stats['unique_documents']}")
    print(f"Unique intents:     {len(index_stats['unique_intents'])}")
    print(f"  → {', '.join(index_stats['unique_intents'])}")
    print(f"Index size:         {index_stats['index_size_mb']:.2f} MB")
    print("=" * 70)

    print("\n✅ Index built successfully!")
    print("\nNext steps:")
    print("  1. Test retrieval: python scripts/test_retrieval.py")
    print("  2. Run application: python app.py")


if __name__ == "__main__":
    main()
