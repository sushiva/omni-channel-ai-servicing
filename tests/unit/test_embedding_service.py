"""
Unit tests for EmbeddingService.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from omni_channel_ai_servicing.infrastructure.retrieval import EmbeddingService


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_openai_embeddings():
    """Mock OpenAI embeddings."""
    with patch(
        "omni_channel_ai_servicing.infrastructure.retrieval.embedding_service.OpenAIEmbeddings"
    ) as mock:
        mock_instance = Mock()
        mock_instance.embed_query.return_value = [0.1] * 1536
        mock_instance.embed_documents.return_value = [[0.1] * 1536] * 5
        mock.return_value = mock_instance
        yield mock


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    def test_initialization(self, temp_cache_dir, mock_openai_embeddings):
        """Test EmbeddingService initialization."""
        os.environ["OPENAI_API_KEY"] = "test-key"

        service = EmbeddingService(
            model="text-embedding-3-small",
            cache_dir=temp_cache_dir,
            batch_size=100,
        )

        assert service.model == "text-embedding-3-small"
        assert service.cache_dir == Path(temp_cache_dir)
        assert service.batch_size == 100
        assert service.cache_hits == 0
        assert service.cache_misses == 0

    def test_initialization_without_api_key(self, temp_cache_dir):
        """Test initialization fails without API key."""
        # Remove API key if set
        os.environ.pop("OPENAI_API_KEY", None)

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            EmbeddingService(cache_dir=temp_cache_dir)

    def test_embed_text(self, temp_cache_dir, mock_openai_embeddings):
        """Test embedding a single text."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        embedding = service.embed_text("Test text")

        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert service.cache_misses == 1

    def test_embed_text_with_cache(self, temp_cache_dir, mock_openai_embeddings):
        """Test embedding with caching."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        text = "Test text for caching"

        # First call - cache miss
        embedding1 = service.embed_text(text, use_cache=True)
        assert service.cache_misses == 1
        assert service.cache_hits == 0

        # Second call - cache hit
        embedding2 = service.embed_text(text, use_cache=True)
        assert service.cache_hits == 1
        assert embedding1 == embedding2

    def test_embed_text_without_cache(self, temp_cache_dir, mock_openai_embeddings):
        """Test embedding without caching."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        text = "Test text"

        # Both calls should be cache misses
        service.embed_text(text, use_cache=False)
        service.embed_text(text, use_cache=False)

        assert service.cache_hits == 0
        assert service.cache_misses == 2

    def test_embed_texts(self, temp_cache_dir, mock_openai_embeddings):
        """Test embedding multiple texts."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        texts = ["Text 1", "Text 2", "Text 3"]
        embeddings = service.embed_texts(texts, use_cache=True)

        assert len(embeddings) == 3
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_embed_documents(self, temp_cache_dir, mock_openai_embeddings):
        """Test embedding Document objects."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        # Mock Document class
        class MockDocument:
            def __init__(self, content):
                self.page_content = content

        documents = [MockDocument("Doc 1"), MockDocument("Doc 2")]
        embeddings = service.embed_documents(documents, use_cache=True)

        assert len(embeddings) == 2
        assert all(len(emb) == 1536 for emb in embeddings)

    def test_get_cache_statistics(self, temp_cache_dir, mock_openai_embeddings):
        """Test cache statistics."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        # Generate some cache activity
        service.embed_text("Text 1", use_cache=True)
        service.embed_text("Text 1", use_cache=True)  # Cache hit
        service.embed_text("Text 2", use_cache=True)

        stats = service.get_cache_statistics()

        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 2
        assert stats["total_requests"] == 3
        assert "hit_rate" in stats
        assert stats["cache_size"] >= 0

    def test_clear_cache(self, temp_cache_dir, mock_openai_embeddings):
        """Test clearing cache."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        # Add some cached embeddings
        service.embed_text("Text 1", use_cache=True)
        service.embed_text("Text 2", use_cache=True)

        # Clear cache
        service.clear_cache()

        assert service.cache_hits == 0
        assert service.cache_misses == 0
        stats = service.get_cache_statistics()
        assert stats["cache_size"] == 0

    def test_cache_key_generation(self, temp_cache_dir, mock_openai_embeddings):
        """Test cache key generation is deterministic."""
        os.environ["OPENAI_API_KEY"] = "test-key"
        service = EmbeddingService(cache_dir=temp_cache_dir)

        text = "Consistent text"
        key1 = service._get_cache_key(text)
        key2 = service._get_cache_key(text)

        assert key1 == key2
        assert len(key1) == 64  # SHA256 hex length
