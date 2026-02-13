#!/usr/bin/env python3
"""Test FAISS retrieval directly"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from omni_channel_ai_servicing.infrastructure.retrieval import Retriever
from omni_channel_ai_servicing.infrastructure.retrieval.vector_store import FAISSVectorStore
from omni_channel_ai_servicing.infrastructure.retrieval.embedding_service import EmbeddingService

def test_retrieval():
    """Test FAISS retrieval directly"""
    try:
        print("="*80)
        print("TESTING FAISS RETRIEVAL")
        print("="*80)
        
        # Path to FAISS index
        index_dir = Path(__file__).parent / "faiss_index"
        print(f"\nIndex directory: {index_dir}")
        print(f"Exists: {index_dir.exists()}")
        
        if index_dir.exists():
            files = list(index_dir.glob("*"))
            print(f"Files in index dir: {[f.name for f in files]}")
        
        # Initialize components
        print("\nInitializing embedding service...")
        embedding_service = EmbeddingService()
        
        print("Initializing vector store...")
        vector_store = FAISSVectorStore(
            dimension=1536,
            index_path=str(index_dir)
        )
        
        print("Loading index...")
        vector_store.load(index_name="knowledge_base")
        
        print("Creating retriever...")
        retriever = Retriever(
            vector_store=vector_store,
            embedding_service=embedding_service,
            similarity_threshold=0.3  # Lower threshold for testing
        )
        
        # Test query
        query = "How do I update my mailing address?"
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")
        
        print("\nRetrieving documents...")
        
        # First, test raw vector store
        print("\n--- Testing raw vector store ---")
        query_embedding = embedding_service.embed_text(query)
        print(f"Query embedding dimension: {len(query_embedding)}")
        
        raw_results = vector_store.similarity_search(
            query_embedding=query_embedding,
            k=5,
            filter_metadata=None
        )
        print(f"Raw vector store results: {len(raw_results)}")
        
        if raw_results:
            for i, (doc, score) in enumerate(raw_results[:2], 1):
                print(f"\n  Result {i}:")
                print(f"    Score: {score}")
                print(f"    Content: {doc.content[:100] if hasattr(doc, 'content') else str(doc)[:100]}...")
        
        # Now test via retriever
        print("\n--- Testing via retriever (WITHOUT intent filter) ---")
        results_no_intent = retriever.retrieve(
            query=query,
            top_k=3,
            intent=None  # No intent filter
        )
        print(f"Results without intent filter: {len(results_no_intent)}")
        
        print("\n--- Testing via retriever (WITH intent filter) ---")
        results = retriever.retrieve(
            query=query,
            top_k=3,
            intent="address_update"
        )
        
        print(f"\n✓ Retrieved {len(results)} documents")
        
        if results:
            for i, doc in enumerate(results, 1):
                print(f"\n--- Document {i} ---")
                print(f"Content: {doc.content[:200] if hasattr(doc, 'content') else str(doc)[:200]}...")
                print(f"Source: {doc.metadata.get('source', 'Unknown') if hasattr(doc, 'metadata') else 'Unknown'}")
        else:
            print("\n⚠️  No documents retrieved!")
            
        # Test formatted context
        print(f"\n{'='*80}")
        print("FORMATTED CONTEXT:")
        print(f"{'='*80}")
        formatted = retriever.format_context(results)
        print(formatted)
        
    except Exception as e:
        print(f"\n❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_retrieval()
