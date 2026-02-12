"""
Unit tests for FAISSVectorStore.
"""

import tempfile
from pathlib import Path

import numpy as np
import pytest

from omni_channel_ai_servicing.infrastructure.retrieval import FAISSVectorStore


@pytest.fixture
def temp_index_path():
    """Create a temporary index directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""

    class MockDocument:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata

    docs = [
        MockDocument(
            "Test document 1",
            {
                "document_id": "DOC-001",
                "intents": ["TEST_INTENT"],
                "document_type": "policy",
            },
        ),
        MockDocument(
            "Test document 2",
            {
                "document_id": "DOC-002",
                "intents": ["TEST_INTENT", "ANOTHER_INTENT"],
                "document_type": "faq",
            },
        ),
        MockDocument(
            "Test document 3",
            {
                "document_id": "DOC-003",
                "intents": ["ANOTHER_INTENT"],
                "document_type": "policy",
            },
        ),
    ]
    return docs


@pytest.fixture
def sample_embeddings():
    """Create sample embeddings for testing."""
    np.random.seed(42)
    embeddings = [
        np.random.rand(1536).tolist(),
        np.random.rand(1536).tolist(),
        np.random.rand(1536).tolist(),
    ]
    return embeddings


class TestFAISSVectorStore:
    """Test suite for FAISSVectorStore."""

    def test_initialization(self, temp_index_path):
        """Test FAISSVectorStore initialization."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)

        assert store.dimension == 1536
        assert store.index_path == Path(temp_index_path)
        assert store.index.ntotal == 0
        assert len(store.documents) == 0
        assert len(store.metadata) == 0

    def test_add_documents(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test adding documents to vector store."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)

        store.add_documents(sample_documents, sample_embeddings)

        assert store.index.ntotal == 3
        assert len(store.documents) == 3
        assert len(store.metadata) == 3

    def test_add_documents_mismatch(self, temp_index_path, sample_documents):
        """Test error when document and embedding counts don't match."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)

        # Only 2 embeddings for 3 documents
        embeddings = [np.random.rand(1536).tolist()] * 2

        with pytest.raises(ValueError, match="Mismatch"):
            store.add_documents(sample_documents, embeddings)

    def test_similarity_search(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test similarity search."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        # Search with first embedding (should return itself with high score)
        results = store.similarity_search(sample_embeddings[0], k=2)

        assert len(results) <= 2
        assert all(isinstance(result, tuple) for result in results)
        assert all(len(result) == 2 for result in results)

        # First result should have high similarity
        doc, score = results[0]
        assert score > 0.9  # Should be very similar to itself

    def test_similarity_search_with_filter(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test similarity search with metadata filtering."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        # Search with intent filter
        results = store.similarity_search(
            sample_embeddings[0],
            k=3,
            filter_metadata={"intents": ["TEST_INTENT"]},
        )

        # Should only return documents with TEST_INTENT
        for doc, score in results:
            assert "TEST_INTENT" in doc.metadata["intents"]

    def test_similarity_search_with_document_type_filter(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test filtering by document type."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        # Filter for policy documents only
        results = store.similarity_search(
            sample_embeddings[0],
            k=3,
            filter_metadata={"document_type": "policy"},
        )

        # Should only return policy documents
        for doc, score in results:
            assert doc.metadata["document_type"] == "policy"

    def test_save_and_load(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test saving and loading vector store."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        # Save
        store.save(index_name="test_index")

        # Verify files exist
        assert (Path(temp_index_path) / "test_index.faiss").exists()
        assert (Path(temp_index_path) / "test_index.pkl").exists()
        assert (Path(temp_index_path) / "test_index_stats.json").exists()

        # Load into new store
        new_store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        new_store.load(index_name="test_index")

        assert new_store.index.ntotal == 3
        assert len(new_store.documents) == 3
        assert len(new_store.metadata) == 3

    def test_load_nonexistent_index(self, temp_index_path):
        """Test loading non-existent index raises error."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)

        with pytest.raises(FileNotFoundError):
            store.load(index_name="nonexistent")

    def test_get_statistics(
        self, temp_index_path, sample_documents, sample_embeddings
    ):
        """Test vector store statistics."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        stats = store.get_statistics()

        assert stats["total_vectors"] == 3
        assert stats["dimension"] == 1536
        assert stats["unique_documents"] == 3
        assert "TEST_INTENT" in stats["unique_intents"]
        assert "ANOTHER_INTENT" in stats["unique_intents"]
        assert "policy" in stats["document_types"]
        assert "faq" in stats["document_types"]
        assert stats["index_size_mb"] > 0

    def test_clear(self, temp_index_path, sample_documents, sample_embeddings):
        """Test clearing vector store."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)
        store.add_documents(sample_documents, sample_embeddings)

        assert store.index.ntotal == 3

        store.clear()

        assert store.index.ntotal == 0
        assert len(store.documents) == 0
        assert len(store.metadata) == 0

    def test_empty_store_search(self, temp_index_path):
        """Test search on empty store."""
        store = FAISSVectorStore(dimension=1536, index_path=temp_index_path)

        query_embedding = np.random.rand(1536).tolist()
        results = store.similarity_search(query_embedding, k=5)

        assert len(results) == 0
