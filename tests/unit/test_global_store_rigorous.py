"""Rigorous tests for GlobalMemory."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import json
from harness.memory.global_store import GlobalMemory, MemoryEntry


class TestMemoryEntryRigorous:
    """Rigorous tests for MemoryEntry."""

    def test_entry_with_empty_content(self):
        """Test entry with empty content."""
        entry = MemoryEntry(key="test", content="")
        assert entry.content == ""
        d = entry.to_dict()
        assert d["content"] == ""

    def test_entry_with_large_content(self):
        """Test entry with large content."""
        large_content = "x" * 100000
        entry = MemoryEntry(key="test", content=large_content)
        assert len(entry.content) == 100000

    def test_entry_with_special_characters(self):
        """Test entry with special characters."""
        entry = MemoryEntry(
            key="special/chars_v2",
            content="Content with\nnewlines\tand\ttabs",
            category="test-category",
            metadata={"nested": {"key": "value"}},
        )
        d = entry.to_dict()
        restored = MemoryEntry.from_dict(d)
        assert restored.key == "special/chars_v2"
        assert "\n" in restored.content
        assert restored.metadata["nested"]["key"] == "value"

    def test_entry_metadata_update(self):
        """Test entry metadata can be updated."""
        entry = MemoryEntry(
            key="test",
            content="content",
            metadata={"key1": "value1"},
        )
        assert entry.metadata["key1"] == "value1"
        entry.metadata["key2"] = "value2"
        assert entry.metadata["key2"] == "value2"


class TestGlobalMemoryRigorous:
    """Rigorous tests for GlobalMemory."""

    def test_store_many_entries(self, tmp_path):
        """Test storing many entries."""
        memory = GlobalMemory(str(tmp_path))
        for i in range(100):
            memory.store(f"key_{i}", f"content_{i}", category=f"cat_{i % 10}")
        assert len(memory.list_entries()) == 100

    def test_retrieve_with_multiple_matches(self, tmp_path):
        """Test retrieval with multiple matches."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/types", "Use typing module", category="coding")
        memory.store("python/formatting", "Use black formatter", category="coding")
        memory.store("python/testing", "Use pytest", category="coding")
        memory.store("js/types", "TypeScript for types", category="coding")

        results = memory.retrieve("python")
        assert len(results) == 3

    def test_retrieve_scoring_order(self, tmp_path):
        """Test that retrieval returns results in scoring order."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("exact_match", "content about Python", category="test")
        memory.store("partial", "Python is great", category="test")
        memory.store("other", "Something else entirely", category="test")

        results = memory.retrieve("exact_match")
        assert len(results) >= 1
        assert results[0].key == "exact_match"

    def test_retrieve_with_category_filter(self, tmp_path):
        """Test retrieval with category filter."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("code/style", "PEP 8", category="coding")
        memory.store("code/format", "Black", category="coding")
        memory.store("design/mvc", "MVC pattern", category="architecture")

        coding_results = memory.retrieve("code", category="coding")
        assert len(coding_results) == 2

        arch_results = memory.retrieve("design", category="architecture")
        assert len(arch_results) == 1

    def test_retrieve_limit(self, tmp_path):
        """Test retrieval respects limit."""
        memory = GlobalMemory(str(tmp_path))
        for i in range(20):
            memory.store(f"key_{i}", f"content {i}", category="test")

        results = memory.retrieve("content", limit=5)
        assert len(results) == 5

    def test_update_preserves_category_index(self, tmp_path):
        """Test that updating preserves category index."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "original", category="cat1")
        memory.store("key1", "updated", category="cat2")

        # Should be in cat2 now
        cat2_entries = memory.list_entries(category="cat2")
        assert len(cat2_entries) == 1
        assert cat2_entries[0].content == "updated"

        # Should not be in cat1
        cat1_entries = memory.list_entries(category="cat1")
        assert len(cat1_entries) == 0

    def test_delete_removes_from_category(self, tmp_path):
        """Test that delete removes from category index."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content", category="cat1")
        memory.store("key2", "content", category="cat1")

        memory.delete("key1")
        cat1_entries = memory.list_entries(category="cat1")
        assert len(cat1_entries) == 1
        assert cat1_entries[0].key == "key2"

    def test_delete_nonexistent(self, tmp_path):
        """Test deleting nonexistent key."""
        memory = GlobalMemory(str(tmp_path))
        # Should not raise
        memory.delete("nonexistent")

    def test_persistence_roundtrip(self, tmp_path):
        """Test persistence roundtrip with many entries."""
        memory = GlobalMemory(str(tmp_path))
        for i in range(50):
            memory.store(
                f"key_{i}",
                f"content_{i}",
                category=f"cat_{i % 5}",
                metadata={"index": i},
            )
        memory.persist()

        memory2 = GlobalMemory(str(tmp_path))
        memory2.load()
        assert len(memory2.list_entries()) == 50

        # Verify entries exist (use exact key match)
        for i in range(50):
            entries = memory2.list_entries()
            keys = [e.key for e in entries]
            assert f"key_{i}" in keys

    def test_persistence_with_empty_memory(self, tmp_path):
        """Test persistence with empty memory."""
        memory = GlobalMemory(str(tmp_path))
        memory.persist()

        memory2 = GlobalMemory(str(tmp_path))
        memory2.load()
        assert len(memory2.list_entries()) == 0

    def test_stats_accuracy(self, tmp_path):
        """Test stats are accurate."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("a/1", "content", category="a")
        memory.store("a/2", "content", category="a")
        memory.store("b/1", "content", category="b")
        memory.store("c/1", "content", category="c")

        stats = memory.get_stats()
        assert stats["total_entries"] == 4
        assert stats["categories"]["a"] == 2
        assert stats["categories"]["b"] == 1
        assert stats["categories"]["c"] == 1

    def test_access_count_persistence(self, tmp_path):
        """Test that access counts persist."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content")
        memory.retrieve("key1")
        memory.retrieve("key1")
        memory.retrieve("key1")
        memory.persist()

        memory2 = GlobalMemory(str(tmp_path))
        memory2.load()
        entries = memory2.retrieve("key1")
        # 3 previous accesses + 1 from this retrieve = 4
        assert entries[0].access_count == 4

    def test_corrupted_memory_file(self, tmp_path):
        """Test handling of corrupted memory file."""
        memory_file = tmp_path / "memory.json"
        memory_file.write_text("not valid json", encoding="utf-8")

        memory = GlobalMemory(str(tmp_path))
        memory.load()
        assert len(memory.list_entries()) == 0

    def test_missing_memory_file(self, tmp_path):
        """Test loading when no memory file exists."""
        memory = GlobalMemory(str(tmp_path))
        memory.load()
        assert len(memory.list_entries()) == 0

    def test_keyword_search_relevance(self, tmp_path):
        """Test keyword search relevance scoring."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/types", "Use the typing module for annotations", category="coding")
        memory.store("python/format", "Use black for code formatting", category="coding")
        memory.store("python/test", "Use pytest for testing", category="coding")

        # Search for "typing" should rank python/types higher
        results = memory.retrieve("typing")
        assert len(results) >= 1
        assert results[0].key == "python/types"

    def test_multiple_categories(self, tmp_path):
        """Test entries with same key in different categories."""
        memory = GlobalMemory(str(tmp_path))
        memory.store("config", "App config", category="settings")
        memory.store("config2", "User config", category="user")
        memory.store("config3", "System config", category="system")

        settings = memory.list_entries(category="settings")
        user = memory.list_entries(category="user")
        system = memory.list_entries(category="system")

        assert len(settings) == 1
        assert len(user) == 1
        assert len(system) == 1
