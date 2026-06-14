import pytest
from mcp_server.embeddings import EmbeddingStore


class TestEmbeddingStore:
    def test_add_and_search(self, tmp_path):
        store = EmbeddingStore(
            persist_dir=str(tmp_path / "chroma"),
            model_name=None,
        )
        store.add(
            doc_id="note-1",
            text="DDP with unused parameters causes memory leak",
            metadata={"type": "checkpoint", "tags": "ddp,memory"},
        )
        store.add(
            doc_id="note-2",
            text="Use gradient checkpointing to reduce memory",
            metadata={"type": "concept", "tags": "gradient,memory"},
        )
        results = store.search("memory leak in DDP", top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "note-1"

    def test_empty_store(self, tmp_path):
        store = EmbeddingStore(
            persist_dir=str(tmp_path / "chroma"),
            model_name=None,
        )
        results = store.search("anything", top_k=5)
        assert results == []

    def test_metadata_filter(self, tmp_path):
        store = EmbeddingStore(
            persist_dir=str(tmp_path / "chroma"),
            model_name=None,
        )
        store.add("n1", "content A", {"type": "checkpoint"})
        store.add("n2", "content B", {"type": "concept"})
        results = store.search("content", top_k=5, where={"type": "checkpoint"})
        assert len(results) == 1
        assert results[0]["id"] == "n1"
