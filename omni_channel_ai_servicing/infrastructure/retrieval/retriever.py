"""
High-level retriever for RAG system.

Provides unified interface for document retrieval with re-ranking,
intent filtering, and context formatting.
"""

from typing import Dict, List, Optional

from omni_channel_ai_servicing.infrastructure.retrieval.document_loader import (
    Document,
)
from omni_channel_ai_servicing.infrastructure.retrieval.embedding_service import (
    EmbeddingService,
)
from omni_channel_ai_servicing.infrastructure.retrieval.vector_store import (
    FAISSVectorStore,
)


class Retriever:
    """
    High-level retrieval service for RAG.

    Features:
    - Intent-aware retrieval (filter by intent type)
    - Re-ranking by relevance
    - Context formatting for LLM prompts
    - Retrieval metrics tracking
    """

    def __init__(
        self,
        vector_store: FAISSVectorStore,
        embedding_service: EmbeddingService,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
        intent_boost: float = 1.5,
    ):
        """
        Initialize retriever.

        Args:
            vector_store: Vector store instance
            embedding_service: Embedding service instance
            top_k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score
            intent_boost: Boost multiplier for intent-matched documents
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.intent_boost = intent_boost

        # Metrics
        self.retrieval_count = 0
        self.total_results = 0

    def retrieve(
        self,
        query: str,
        intent: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> List[Document]:
        """
        Retrieve relevant documents for query.

        Args:
            query: Query text
            intent: Optional intent filter (e.g., "ADDRESS_UPDATE")
            top_k: Override default top_k

        Returns:
            List of Document objects (most relevant first)
        """
        k = top_k or self.top_k

        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Prepare metadata filter
        filter_metadata = None
        if intent:
            # Convert intent to uppercase to match FAISS metadata
            intent_upper = intent.upper()
            filter_metadata = {"intents": [intent_upper]}

        # Search vector store
        results = self.vector_store.similarity_search(
            query_embedding=query_embedding,
            k=k * 2,  # Get extra results for re-ranking
            filter_metadata=filter_metadata,
        )

        # Apply similarity threshold
        filtered_results = [
            (doc, score)
            for doc, score in results
            if score >= self.similarity_threshold
        ]

        # Re-rank with intent boost
        reranked_results = self._rerank_by_intent(filtered_results, intent)

        # Take top-k after re-ranking
        final_results = reranked_results[:k]

        # Update metrics
        self.retrieval_count += 1
        self.total_results += len(final_results)

        # Return documents only (without scores)
        return [doc for doc, _ in final_results]

    def _rerank_by_intent(
        self,
        results: List[tuple],
        intent: Optional[str],
    ) -> List[tuple]:
        """
        Re-rank results by boosting intent-matched documents.

        Args:
            results: List of (Document, score) tuples
            intent: Intent to boost

        Returns:
            Re-ranked list of (Document, score) tuples
        """
        if not intent:
            return results

        reranked = []
        for doc, score in results:
            boosted_score = score
            # Boost if document matches intent
            if intent in doc.metadata.get("intents", []):
                boosted_score *= self.intent_boost

            reranked.append((doc, boosted_score))

        # Sort by boosted score (descending)
        reranked.sort(key=lambda x: x[1], reverse=True)

        return reranked

    def format_context(
        self,
        documents: List[Document],
        max_length: int = 2000,
    ) -> str:
        """
        Format retrieved documents as context for LLM.

        Args:
            documents: List of Document objects
            max_length: Maximum context length in characters

        Returns:
            Formatted context string
        """
        if not documents:
            return "No relevant context found."

        context_parts = []
        current_length = 0

        for i, doc in enumerate(documents, 1):
            # Format document
            doc_id = doc.metadata.get("document_id", "UNKNOWN")
            title = doc.metadata.get("title", "Untitled")

            doc_text = f"[Document {i} - {doc_id}: {title}]\n{doc.page_content}\n"

            # Check length
            if current_length + len(doc_text) > max_length:
                break

            context_parts.append(doc_text)
            current_length += len(doc_text)

        context = "\n---\n\n".join(context_parts)

        return f"**Relevant Policy Context:**\n\n{context}"

    def get_metrics(self) -> Dict:
        """
        Get retrieval metrics.

        Returns:
            Dictionary with metrics
        """
        avg_results = (
            self.total_results / self.retrieval_count
            if self.retrieval_count > 0
            else 0
        )

        return {
            "retrieval_count": self.retrieval_count,
            "total_results": self.total_results,
            "avg_results_per_query": f"{avg_results:.2f}",
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "intent_boost": self.intent_boost,
        }
