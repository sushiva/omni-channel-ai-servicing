"""
Retrieve relevant context from knowledge base using FAISS vector store.
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from omni_channel_ai_servicing.infrastructure.retrieval import (
    Retriever
)
from omni_channel_ai_servicing.infrastructure.retrieval.vector_store import FAISSVectorStore
from omni_channel_ai_servicing.infrastructure.retrieval.embedding_service import EmbeddingService
from omni_channel_ai_servicing.graph.nodes import log_node

logger = logging.getLogger(__name__)

# Initialize retrieval components (singleton pattern)
_retriever: Optional[Retriever] = None


def _get_retriever() -> Retriever:
    """Get or initialize the retriever singleton."""
    global _retriever
    if _retriever is None:
        try:
            # Path to FAISS index
            index_dir = Path(__file__).parents[3] / "faiss_index"
            
            # Initialize components
            embedding_service = EmbeddingService()
            vector_store = FAISSVectorStore(
                dimension=1536,
                index_path=str(index_dir)
            )
            # Load the saved index
            vector_store.load(index_name="knowledge_base")
            
            _retriever = Retriever(
                vector_store=vector_store,
                embedding_service=embedding_service
            )
            logger.info(f"Initialized retriever with FAISS index from {index_dir}")
        except Exception as e:
            logger.error(f"Failed to initialize retriever: {e}")
            raise
    
    return _retriever


# Intents that should skip retrieval
SKIP_RETRIEVAL_INTENTS = {
    "GREETING",
    "FAREWELL", 
    "THANK_YOU",
    "SMALL_TALK"
}


@log_node("retrieve_context")
async def retrieve_context_node(state) -> Dict[str, Any]:
    """
    Retrieve relevant context from knowledge base based on user query and intent.
    
    Skips retrieval for greetings and small talk.
    Returns retrieved documents, formatted context, and metadata.
    """
    # Skip retrieval for non-policy intents
    if state.intent and state.intent.upper() in SKIP_RETRIEVAL_INTENTS:
        logger.info(f"Skipping retrieval for intent: {state.intent}")
        return {
            "retrieved_documents": [],
            "context": None,
            "context_metadata": {
                "skipped": True,
                "reason": f"Intent {state.intent} does not require knowledge base"
            }
        }
    
    # Skip if no user message
    if not state.user_message:
        logger.warning("No user message provided, skipping retrieval")
        return {
            "retrieved_documents": [],
            "context": None,
            "context_metadata": {"skipped": True, "reason": "No user message"}
        }
    
    try:
        # Get retriever
        retriever = _get_retriever()
        
        # Retrieve relevant documents
        query = state.user_message
        intent = state.intent if state.intent else "general"
        
        logger.info(f"Retrieving context for query: '{query[:50]}...' with intent: {intent}")
        
        results = retriever.retrieve(
            query=query,
            top_k=3,  # Get top 3 most relevant chunks
            intent=intent
        )
        
        # Format context for LLM
        formatted_context = retriever.format_context(results)
        
        # Extract metadata
        metadata = {
            "num_documents": len(results),
            "query": query,
            "intent": intent,
            "skipped": False
        }
        
        logger.info(f"Retrieved {len(results)} documents")
        
        return {
            "retrieved_documents": results,
            "context": formatted_context,
            "context_metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error during retrieval: {e}", exc_info=True)
        return {
            "retrieved_documents": [],
            "context": None,
            "context_metadata": {
                "skipped": True,
                "reason": f"Retrieval error: {str(e)}"
            }
        }
