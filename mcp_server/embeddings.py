"""ChromaDB embedding store with local embedding model."""

import logging
from typing import Any

import chromadb

logger = logging.getLogger(__name__)


class EmbeddingStore:
    """Manages embeddings in ChromaDB with a local embedding model."""

    def __init__(self, persist_dir: str, model_name: str | None = None):
        self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="vault_notes",
            metadata={"hnsw:space": "cosine"},
        )
        self._model = None
        if model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(model_name)
                logger.info(f"Loaded embedding model: {model_name}")
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}. Using ChromaDB defaults.")

    def _embed(self, texts: list[str]) -> list[list[float]] | None:
        """Embed texts using the local model or ChromaDB default."""
        if self._model:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        return None

    def add(self, doc_id: str, text: str, metadata: dict[str, Any]):
        """Add a document to the embedding store."""
        embedding = self._embed([text])
        kwargs: dict[str, Any] = {
            "ids": [doc_id],
            "documents": [text],
            "metadatas": [metadata],
        }
        if embedding:
            kwargs["embeddings"] = embedding
        self._collection.add(**kwargs)

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: dict | None = None,
    ) -> list[dict]:
        """Search for similar documents.

        Returns:
            List of dicts with id, text, metadata, distance.
        """
        if self._collection.count() == 0:
            return []

        embedding = self._embed([query])
        kwargs: dict[str, Any] = {
            "n_results": min(top_k, self._collection.count()),
        }
        if embedding:
            kwargs["query_embeddings"] = embedding
        else:
            kwargs["query_texts"] = [query]
        if where:
            kwargs["where"] = where

        results = self._collection.query(**kwargs)

        docs = []
        for i in range(len(results["ids"][0])):
            docs.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else 0,
            })
        return docs

    def delete(self, doc_id: str):
        """Delete a document by ID."""
        self._collection.delete(ids=[doc_id])

    def count(self) -> int:
        """Return the number of documents in the store."""
        return self._collection.count()
