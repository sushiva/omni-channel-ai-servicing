"""
Unit tests for Retriever.
"""

from unittest.mock import Mock

import pytest

from omni_channel_ai_servicing.infrastructure.retrieval import Retriever


@pytest.fixture
def mock_embedding_service():
    """Mock EmbeddingService."""
    service = Mock()
    service.embed_text.return_value = [0.1] * 1536
    return service


@pytest.fixture
def mock_vector_store():
    """Mock FAISSVectorStore."""
    store = Mock()
    return store


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""

    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata

    docs = [
        MockDocument(
            "How to update your address in our system.",
            {
                "document_id": "DOC-001",
                "title": "Address Update Policy",
                "intents": ["ADDRESS_UPDATE"],
                "document_type": "policy",
                "chunk_index": 0,
                "total_chunks": 5,
            },
        ),
        MockDocument(
            "You can update your address online or by phone.",
            {
                "document_id": "DOC-001",
                "title": "Address Update Policy",
                "intents": ["ADDRESS_UPDATE"],
                "document_type": "policy",
                "chunk_index": 1,
                "total_chunks": 5,
            },
        ),
        MockDocument(
            "How to dispute a charge on your account.",
            {
                "document_id": "DOC-002",
                "title": "Dispute Process",
                "intents": ["DISPUTE"],
                "document_type": "policy",
                "chunk_index": 0,
                "total_chunks": 3,
            },
        ),
    ]
    return docs


class TestRetriever:
    """Test suite for Retriever."""

    def test_initialization(self, mock_vector_store, mock_embedding_service):
        """Test Retriever initialization."""
        retriever = Retriever(
            vector_store=mock_vector_store,
            embedding_service=mock_embedding_service,
            top_k=5,
            similarity_threshold=0.7,
        )

        assert retriever.vector_store == mock_vector_store
        assert retriever.embedding_service == mock_embedding_service
        assert retriever.top_k == 5
        assert retriever.similarity_threshold == 0.7
        assert retriever.intent_boost == 1.5
        assert retriever.metrics["retrieval_count"] == 0

    def test_retrieve_without_intent(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test retrieval without intent filter."""
        # Setup mocks
        mock_vector_store.similarity_search.return_value = [
            (sample_documents[0], 0.95),
            (sample_documents[1], 0.88),
            (sample_documents[2], 0.82),
        ]

        retriever = Retriever(mock_vector_store, mock_embedding_service)

        results = retriever.retrieve("How do I update my address?")

        # Verify embedding was generated
        mock_embedding_service.embed_text.assert_called_once_with(
            "How do I update my address?"
        )

        # Verify vector store was queried
        mock_vector_store.similarity_search.assert_called_once()

        # Verify results
        assert len(results) == 3
        assert all(isinstance(doc, type(sample_documents[0])) for doc in results)

        # Verify metrics
        assert retriever.metrics["retrieval_count"] == 1
        assert retriever.metrics["total_results"] == 3

    def test_retrieve_with_intent_filter(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test retrieval with intent filter."""
        # Only return ADDRESS_UPDATE documents
        mock_vector_store.similarity_search.return_value = [
            (sample_documents[0], 0.95),
            (sample_documents[1], 0.88),
        ]

        retriever = Retriever(mock_vector_store, mock_embedding_service)

        results = retriever.retrieve(
            "How do I update my address?", intent="ADDRESS_UPDATE"
        )

        # Verify vector store was queried with filter
        call_args = mock_vector_store.similarity_search.call_args
        assert call_args[1]["filter_metadata"] == {
            "intents": ["ADDRESS_UPDATE"]
        }

        # Verify results
        assert len(results) == 2
        assert all(
            "ADDRESS_UPDATE" in doc.metadata["intents"] for doc in results
        )

    def test_retrieve_with_similarity_threshold(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test that low similarity results are filtered out."""
        # Return documents with varying similarity scores
        mock_vector_store.similarity_search.return_value = [
            (sample_documents[0], 0.95),  # Above threshold
            (sample_documents[1], 0.75),  # Above threshold
            (sample_documents[2], 0.65),  # Below threshold (0.7)
        ]

        retriever = Retriever(
            mock_vector_store,
            mock_embedding_service,
            similarity_threshold=0.7,
        )

        results = retriever.retrieve("How do I update my address?")

        # Should only return 2 results above threshold
        assert len(results) == 2

    def test_retrieve_with_re_ranking(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test re-ranking with intent boost."""
        # Return documents where second doc has ADDRESS_UPDATE
        # but lower similarity
        mock_vector_store.similarity_search.return_value = [
            (sample_documents[2], 0.90),  # DISPUTE, no boost
            (
                sample_documents[0],
                0.80,
            ),  # ADDRESS_UPDATE, will be boosted to 1.2
        ]

        retriever = Retriever(
            mock_vector_store,
            mock_embedding_service,
            intent_boost=1.5,
        )

        results = retriever.retrieve(
            "How do I update my address?", intent="ADDRESS_UPDATE"
        )

        # First result should be the boosted ADDRESS_UPDATE doc
        # (0.80 * 1.5 = 1.20 > 0.90)
        assert results[0].metadata["document_id"] == "DOC-001"

    def test_format_context(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test context formatting for LLM."""
        retriever = Retriever(mock_vector_store, mock_embedding_service)

        context = retriever.format_context(sample_documents)

        # Verify structure
        assert "Retrieved Documents:" in context
        assert "DOC-001" in context
        assert "Address Update Policy" in context
        assert "How to update your address" in context
        assert "DOC-002" in context
        assert "Dispute Process" in context

        # Verify separators
        assert "---" in context
        assert "Document ID:" in context
        assert "Title:" in context
        assert "Content:" in context

    def test_format_context_with_max_length(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test context formatting respects max length."""
        retriever = Retriever(mock_vector_store, mock_embedding_service)

        context = retriever.format_context(sample_documents, max_length=100)

        # Context should be truncated
        assert len(context) <= 150  # 100 + ellipsis message

        # Should have truncation message
        if len(context) > 100:
            assert "truncated" in context.lower()

    def test_get_metrics(
        self, mock_vector_store, mock_embedding_service, sample_documents
    ):
        """Test metrics tracking."""
        mock_vector_store.similarity_search.return_value = [
            (sample_documents[0], 0.95),
            (sample_documents[1], 0.88),
        ]

        retriever = Retriever(mock_vector_store, mock_embedding_service)

        # Perform multiple retrievals
        retriever.retrieve("Query 1")
        retriever.retrieve("Query 2")
        retriever.retrieve("Query 3")

        metrics = retriever.get_metrics()

        assert metrics["retrieval_count"] == 3
        assert metrics["total_results"] == 6
        assert metrics["avg_results_per_query"] == 2.0

    def test_empty_results(self, mock_vector_store, mock_embedding_service):
        """Test handling of empty search results."""
        mock_vector_store.similarity_search.return_value = []

        retriever = Retriever(mock_vector_store, mock_embedding_service)

        results = retriever.retrieve("Query with no results")

        assert len(results) == 0
        assert retriever.metrics["retrieval_count"] == 1
        assert retriever.metrics["total_results"] == 0

    def test_format_context_empty(
        self, mock_vector_store, mock_embedding_service
    ):
        """Test formatting empty context."""
        retriever = Retriever(mock_vector_store, mock_embedding_service)

        context = retriever.format_context([])

        assert context == "No relevant documents found."
