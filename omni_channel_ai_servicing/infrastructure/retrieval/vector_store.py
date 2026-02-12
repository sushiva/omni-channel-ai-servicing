"""
FAISS vector store for RAG system.

Provides vector storage and similarity search using Facebook's FAISS library
with metadata filtering and persistence support.
"""

import json
import pickle
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import faiss
import numpy as np


class FAISSVectorStore:
    """
    FAISS-based vector store for document retrieval.

    Features:
    - FAISS index for fast similarity search (sub-10ms)
    - Metadata storage and filtering
    - Local persistence (save/load index)
    - Cosine similarity search
    - Top-k retrieval with scores
    """

    def __init__(
        self,
        dimension: int = 1536,
        index_path: str = "faiss_index",
    ):
        """
        Initialize vector store.

        Args:
            dimension: Embedding vector dimension (1536 for text-embedding-3-small)
            index_path: Directory to save/load index
        """
        self.dimension = dimension
        self.index_path = Path(index_path)
        self.index_path.mkdir(exist_ok=True)

        # Initialize FAISS index (cosine similarity via normalized L2)
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine

        # Storage for documents and metadata
        self.documents: List = []
        self.metadata: List[Dict] = []

    def add_documents(
        self,
        documents: List,
        embeddings: List[List[float]],
    ) -> None:
        """
        Add documents to vector store.

        Args:
            documents: List of Document objects
            embeddings: List of embedding vectors
        """
        if len(documents) != len(embeddings):
            raise ValueError(
                f"Mismatch: {len(documents)} documents but {len(embeddings)} embeddings"
            )

        # Convert to numpy array and normalize (for cosine similarity)
        embeddings_array = np.array(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings_array)

        # Add to FAISS index
        self.index.add(embeddings_array)

        # Store documents and metadata
        self.documents.extend(documents)
        self.metadata.extend([doc.metadata for doc in documents])

    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict] = None,
    ) -> List[Tuple[object, float]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            k: Number of results to return
            filter_metadata: Optional metadata filter (e.g., {"intents": ["ADDRESS_UPDATE"]})

        Returns:
            List of (Document, similarity_score) tuples
        """
        # Normalize query embedding
        query_array = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(query_array)

        # Search FAISS index
        # Request more results if filtering is needed
        search_k = k * 3 if filter_metadata else k
        distances, indices = self.index.search(query_array, search_k)

        # Build results with metadata filtering
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx == -1:  # FAISS returns -1 for missing results
                continue

            doc = self.documents[idx]
            metadata = self.metadata[idx]

            # Apply metadata filter
            if filter_metadata:
                match = True
                for key, value in filter_metadata.items():
                    if key not in metadata:
                        match = False
                        break
                    # Handle list membership (e.g., intent in intents list)
                    if isinstance(metadata[key], list):
                        if isinstance(value, list):
                            # Check if any value matches
                            if not any(v in metadata[key] for v in value):
                                match = False
                                break
                        else:
                            if value not in metadata[key]:
                                match = False
                                break
                    else:
                        if metadata[key] != value:
                            match = False
                            break

                if not match:
                    continue

            # Convert distance to similarity score (cosine similarity is inner product for normalized vectors)
            similarity_score = float(distance)
            results.append((doc, similarity_score))

            # Stop once we have enough results
            if len(results) >= k:
                break

        return results

    def save(self, index_name: str = "vector_store") -> None:
        """
        Save vector store to disk.

        Args:
            index_name: Name for saved index files
        """
        # Save FAISS index
        index_file = self.index_path / f"{index_name}.faiss"
        faiss.write_index(self.index, str(index_file))

        # Save documents and metadata
        data_file = self.index_path / f"{index_name}.pkl"
        with open(data_file, "wb") as f:
            pickle.dump(
                {
                    "documents": self.documents,
                    "metadata": self.metadata,
                    "dimension": self.dimension,
                },
                f,
            )

        # Save statistics
        stats_file = self.index_path / f"{index_name}_stats.json"
        stats = self.get_statistics()
        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=2)

    def load(self, index_name: str = "vector_store") -> None:
        """
        Load vector store from disk.

        Args:
            index_name: Name of saved index files
        """
        # Load FAISS index
        index_file = self.index_path / f"{index_name}.faiss"
        if not index_file.exists():
            raise FileNotFoundError(f"Index not found: {index_file}")

        self.index = faiss.read_index(str(index_file))

        # Load documents and metadata
        data_file = self.index_path / f"{index_name}.pkl"
        with open(data_file, "rb") as f:
            data = pickle.load(f)
            self.documents = data["documents"]
            self.metadata = data["metadata"]
            self.dimension = data["dimension"]

    def get_statistics(self) -> Dict:
        """
        Get vector store statistics.

        Returns:
            Dictionary with statistics
        """
        unique_intents = set()
        document_types = {}
        document_ids = set()

        for meta in self.metadata:
            unique_intents.update(meta.get("intents", []))
            doc_type = meta.get("document_type", "unknown")
            document_types[doc_type] = document_types.get(doc_type, 0) + 1
            doc_id = meta.get("document_id")
            if doc_id:
                document_ids.add(doc_id)

        return {
            "total_vectors": self.index.ntotal,
            "dimension": self.dimension,
            "unique_documents": len(document_ids),
            "unique_intents": list(unique_intents),
            "document_types": document_types,
            "index_size_mb": self.index.ntotal * self.dimension * 4 / (1024 * 1024),
        }

    def clear(self) -> None:
        """Clear all vectors and documents from store."""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.metadata = []
