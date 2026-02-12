"""
Document loader for RAG system.

Loads markdown documents from knowledge base, chunks them with overlap,
and extracts metadata for vector storage.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

import frontmatter
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Document:
    """Container for document chunk with metadata."""

    def __init__(
        self,
        page_content: str,
        metadata: Optional[Dict] = None,
    ):
        """
        Initialize document.

        Args:
            page_content: Text content of the document chunk
            metadata: Optional metadata dictionary
        """
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self) -> str:
        return f"Document(page_content='{self.page_content[:50]}...', metadata={self.metadata})"


class DocumentLoader:
    """
    Loads and processes documents from knowledge base.

    Features:
    - Markdown parsing with frontmatter support
    - Configurable chunking with overlap
    - Metadata extraction (intent, policy_id, keywords)
    - Semantic boundary preservation (headers, sections)
    """

    def __init__(
        self,
        knowledge_base_path: str = "knowledge_base",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        """
        Initialize document loader.

        Args:
            knowledge_base_path: Path to knowledge base directory
            chunk_size: Target size for each chunk in tokens
            chunk_overlap: Overlap between chunks in tokens
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n## ", "\n### ", "\n---", "\n\n", "\n", " ", ""],
        )

        # Load metadata configuration
        self.metadata_config = self._load_metadata_config()

    def _load_metadata_config(self) -> Dict:
        """Load metadata configuration from metadata.json."""
        metadata_path = self.knowledge_base_path / "metadata.json"
        if not metadata_path.exists():
            return {"documents": [], "intent_mapping": {}}

        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _extract_frontmatter(self, content: str) -> tuple[Dict, str]:
        """
        Extract YAML frontmatter from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Tuple of (frontmatter_dict, content_without_frontmatter)
        """
        try:
            post = frontmatter.loads(content)
            return dict(post.metadata), post.content
        except Exception:
            # No frontmatter or parsing error
            return {}, content

    def _get_document_metadata(self, file_path: Path) -> Dict:
        """
        Get metadata for document from metadata.json.

        Args:
            file_path: Path to document file

        Returns:
            Document metadata dictionary
        """
        # Find document in metadata config
        relative_path = str(file_path.relative_to(self.knowledge_base_path.parent))
        for doc in self.metadata_config.get("documents", []):
            if doc.get("file_path") == relative_path:
                return {
                    "document_id": doc.get("id"),
                    "document_type": doc.get("document_type"),
                    "title": doc.get("title"),
                    "intents": doc.get("intents", []),
                    "keywords": doc.get("keywords", []),
                    "version": doc.get("version"),
                    "compliance_tags": doc.get("compliance_tags", []),
                }
        return {}

    def load_document(self, file_path: Path) -> List[Document]:
        """
        Load and chunk a single document.

        Args:
            file_path: Path to markdown document

        Returns:
            List of Document objects (chunks)
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Extract frontmatter
        frontmatter_meta, content = self._extract_frontmatter(content)

        # Get document metadata from config
        doc_metadata = self._get_document_metadata(file_path)

        # Merge metadata sources
        base_metadata = {
            **doc_metadata,
            **frontmatter_meta,
            "source": str(file_path),
            "file_name": file_path.name,
        }

        # Split into chunks
        chunks = self.text_splitter.split_text(content)

        # Create Document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **base_metadata,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            documents.append(Document(page_content=chunk, metadata=chunk_metadata))

        return documents

    def load_all_documents(self) -> List[Document]:
        """
        Load all documents from knowledge base.

        Returns:
            List of all Document objects (chunks) from all files
        """
        all_documents = []

        # Load policies
        policies_path = self.knowledge_base_path / "policies"
        if policies_path.exists():
            for file_path in policies_path.glob("*.md"):
                docs = self.load_document(file_path)
                all_documents.extend(docs)

        # Load FAQs
        faqs_path = self.knowledge_base_path / "faqs"
        if faqs_path.exists():
            for file_path in faqs_path.glob("*.md"):
                docs = self.load_document(file_path)
                all_documents.extend(docs)

        return all_documents

    def load_documents_by_intent(self, intent: str) -> List[Document]:
        """
        Load documents filtered by intent type.

        Args:
            intent: Intent type to filter by (e.g., "ADDRESS_UPDATE")

        Returns:
            List of Document objects matching the intent
        """
        all_documents = self.load_all_documents()

        # Filter by intent
        filtered_docs = [
            doc
            for doc in all_documents
            if intent in doc.metadata.get("intents", [])
        ]

        return filtered_docs

    def get_statistics(self) -> Dict:
        """
        Get statistics about loaded documents.

        Returns:
            Dictionary with document statistics
        """
        all_documents = self.load_all_documents()

        # Calculate statistics
        total_chunks = len(all_documents)
        total_chars = sum(len(doc.page_content) for doc in all_documents)
        unique_intents = set()
        document_types = {}

        for doc in all_documents:
            unique_intents.update(doc.metadata.get("intents", []))
            doc_type = doc.metadata.get("document_type", "unknown")
            document_types[doc_type] = document_types.get(doc_type, 0) + 1

        return {
            "total_documents": total_chunks,
            "total_characters": total_chars,
            "avg_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
            "unique_intents": list(unique_intents),
            "document_types": document_types,
        }
