"""
Embedding service for RAG system.

Generates embeddings for documents and queries using OpenAI's embedding models
with caching and batch processing support.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional

from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential


class EmbeddingService:
    """
    Service for generating embeddings with OpenAI.

    Features:
    - OpenAI text-embedding-3-small (1536 dimensions)
    - Embedding caching (disk-based)
    - Batch processing
    - Retry logic for API failures
    - Token counting and cost tracking
    """

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        cache_dir: str = ".embedding_cache",
        batch_size: int = 100,
    ):
        """
        Initialize embedding service.

        Args:
            model: OpenAI embedding model name
            cache_dir: Directory for caching embeddings
            batch_size: Number of texts to embed in one batch
        """
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.batch_size = batch_size

        # Create cache directory
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize OpenAI embeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.embeddings = OpenAIEmbeddings(
            model=model,
            openai_api_key=api_key,
        )

        # Statistics
        self.cache_hits = 0
        self.cache_misses = 0

    def _get_cache_key(self, text: str) -> str:
        """
        Generate cache key for text.

        Args:
            text: Text to generate key for

        Returns:
            SHA256 hash of text
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """
        Get file path for cached embedding.

        Args:
            cache_key: Cache key (hash)

        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}.json"

    def _load_from_cache(self, text: str) -> Optional[List[float]]:
        """
        Load embedding from cache if available.

        Args:
            text: Text to look up

        Returns:
            Cached embedding vector or None if not cached
        """
        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)

        if cache_path.exists():
            with open(cache_path, "r") as f:
                data = json.load(f)
                self.cache_hits += 1
                return data["embedding"]

        self.cache_misses += 1
        return None

    def _save_to_cache(self, text: str, embedding: List[float]) -> None:
        """
        Save embedding to cache.

        Args:
            text: Text that was embedded
            embedding: Embedding vector
        """
        cache_key = self._get_cache_key(text)
        cache_path = self._get_cache_path(cache_key)

        with open(cache_path, "w") as f:
            json.dump({"text": text[:100], "embedding": embedding}, f)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding with retry logic.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        return self.embeddings.embed_query(text)

    def embed_text(self, text: str, use_cache: bool = True) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            use_cache: Whether to use cache

        Returns:
            Embedding vector (1536 dimensions)
        """
        if use_cache:
            cached = self._load_from_cache(text)
            if cached is not None:
                return cached

        embedding = self._generate_embedding(text)

        if use_cache:
            self._save_to_cache(text, embedding)

        return embedding

    def embed_texts(
        self, texts: List[str], use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts with batching.

        Args:
            texts: List of texts to embed
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            embedding = self.embed_text(text, use_cache=use_cache)
            embeddings.append(embedding)

        return embeddings

    def embed_documents(
        self, documents: List, use_cache: bool = True
    ) -> List[List[float]]:
        """
        Generate embeddings for Document objects.

        Args:
            documents: List of Document objects
            use_cache: Whether to use cache

        Returns:
            List of embedding vectors
        """
        texts = [doc.page_content for doc in documents]
        return self.embed_texts(texts, use_cache=use_cache)

    def get_cache_statistics(self) -> Dict:
        """
        Get cache hit/miss statistics.

        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (
            self.cache_hits / total_requests if total_requests > 0 else 0
        )

        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "total_requests": total_requests,
            "hit_rate": f"{hit_rate:.2%}",
            "cache_size": len(list(self.cache_dir.glob("*.json"))),
        }

    def clear_cache(self) -> None:
        """Clear all cached embeddings."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        self.cache_hits = 0
        self.cache_misses = 0
