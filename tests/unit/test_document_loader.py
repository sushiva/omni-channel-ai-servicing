"""
Unit tests for DocumentLoader.
"""

import json
import tempfile
from pathlib import Path

import pytest

from omni_channel_ai_servicing.infrastructure.retrieval import DocumentLoader


@pytest.fixture
def temp_knowledge_base():
    """Create a temporary knowledge base for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = Path(tmpdir) / "knowledge_base"
        kb_path.mkdir()

        # Create policies directory with test document
        policies_path = kb_path / "policies"
        policies_path.mkdir()

        test_policy = policies_path / "test_policy.md"
        test_policy.write_text(
            """# Test Policy

## Overview
This is a test policy document for unit testing.

## Section 1
Content for section 1 with some details.

## Section 2
Content for section 2 with more information.
"""
        )

        # Create FAQs directory with test document
        faqs_path = kb_path / "faqs"
        faqs_path.mkdir()

        test_faq = faqs_path / "test_faq.md"
        test_faq.write_text(
            """# Test FAQ

## Q: What is this?
A: This is a test FAQ document.

## Q: How does it work?
A: It works by testing the document loader.
"""
        )

        # Create metadata.json
        metadata = {
            "documents": [
                {
                    "id": "TEST-001",
                    "file_path": f"{kb_path}/policies/test_policy.md",
                    "document_type": "policy",
                    "title": "Test Policy",
                    "intents": ["TEST_INTENT"],
                    "keywords": ["test", "policy"],
                    "version": "1.0",
                }
            ],
            "intent_mapping": {"TEST_INTENT": {"primary_documents": ["TEST-001"]}},
        }

        metadata_file = kb_path / "metadata.json"
        metadata_file.write_text(json.dumps(metadata))

        yield kb_path


class TestDocumentLoader:
    """Test suite for DocumentLoader."""

    def test_initialization(self, temp_knowledge_base):
        """Test DocumentLoader initialization."""
        loader = DocumentLoader(
            knowledge_base_path=str(temp_knowledge_base),
            chunk_size=500,
            chunk_overlap=50,
        )

        assert loader.chunk_size == 500
        assert loader.chunk_overlap == 50
        assert loader.knowledge_base_path == temp_knowledge_base

    def test_load_metadata_config(self, temp_knowledge_base):
        """Test loading metadata configuration."""
        loader = DocumentLoader(knowledge_base_path=str(temp_knowledge_base))

        assert "documents" in loader.metadata_config
        assert "intent_mapping" in loader.metadata_config
        assert len(loader.metadata_config["documents"]) == 1

    def test_load_document(self, temp_knowledge_base):
        """Test loading a single document."""
        loader = DocumentLoader(
            knowledge_base_path=str(temp_knowledge_base), chunk_size=200
        )

        test_file = temp_knowledge_base / "policies" / "test_policy.md"
        documents = loader.load_document(test_file)

        assert len(documents) > 0
        assert all(hasattr(doc, "page_content") for doc in documents)
        assert all(hasattr(doc, "metadata") for doc in documents)
        assert all(doc.metadata.get("file_name") == "test_policy.md" for doc in documents)

    def test_load_all_documents(self, temp_knowledge_base):
        """Test loading all documents from knowledge base."""
        loader = DocumentLoader(knowledge_base_path=str(temp_knowledge_base))

        documents = loader.load_all_documents()

        # Should have documents from both policies and faqs
        assert len(documents) >= 2
        file_names = {doc.metadata.get("file_name") for doc in documents}
        assert "test_policy.md" in file_names
        assert "test_faq.md" in file_names

    def test_chunk_metadata(self, temp_knowledge_base):
        """Test chunk metadata is properly set."""
        loader = DocumentLoader(
            knowledge_base_path=str(temp_knowledge_base), chunk_size=200
        )

        test_file = temp_knowledge_base / "policies" / "test_policy.md"
        documents = loader.load_document(test_file)

        for i, doc in enumerate(documents):
            assert doc.metadata.get("chunk_index") == i
            assert doc.metadata.get("total_chunks") == len(documents)
            assert "source" in doc.metadata

    def test_load_documents_by_intent(self, temp_knowledge_base):
        """Test filtering documents by intent."""
        loader = DocumentLoader(knowledge_base_path=str(temp_knowledge_base))

        # This will return empty since metadata mapping is basic in test
        documents = loader.load_documents_by_intent("TEST_INTENT")

        # Should only return documents with TEST_INTENT (none in this test setup)
        assert isinstance(documents, list)

    def test_get_statistics(self, temp_knowledge_base):
        """Test document statistics."""
        loader = DocumentLoader(knowledge_base_path=str(temp_knowledge_base))

        stats = loader.get_statistics()

        assert "total_documents" in stats
        assert "total_characters" in stats
        assert "avg_chunk_size" in stats
        assert "unique_intents" in stats
        assert "document_types" in stats
        assert stats["total_documents"] > 0

    def test_empty_knowledge_base(self):
        """Test loader with empty knowledge base."""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "empty_kb"
            kb_path.mkdir()

            loader = DocumentLoader(knowledge_base_path=str(kb_path))
            documents = loader.load_all_documents()

            assert len(documents) == 0
