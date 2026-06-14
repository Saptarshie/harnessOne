import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from harness.memory.global_store import GlobalMemory, MemoryEntry


class TestMemoryEntry:
    def test_create_entry(self):
        entry = MemoryEntry(
            key="python/typing",
            content="Use type hints for all function signatures.",
            category="coding",
            source_session="abc-123",
        )
        assert entry.key == "python/typing"
        assert entry.category == "coding"
        assert entry.access_count == 0

    def test_entry_to_dict(self):
        entry = MemoryEntry(
            key="test",
            content="test content",
            category="test",
        )
        d = entry.to_dict()
        assert d["key"] == "test"
        assert "timestamp" in d

    def test_entry_from_dict(self):
        d = {
            "key": "test",
            "content": "content",
            "category": "cat",
            "source_session": "sess",
            "timestamp": "2026-01-01T00:00:00Z",
            "access_count": 5,
            "metadata": {},
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.access_count == 5


class TestGlobalMemory:
    def test_store_and_retrieve(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/typing", "Use type hints.", category="coding")
        results = memory.retrieve("typing")
        assert len(results) == 1
        assert results[0].content == "Use type hints."

    def test_retrieve_by_category(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("code/style", "Follow PEP 8.", category="coding")
        memory.store("design/mvc", "Use MVC pattern.", category="architecture")
        memory.store("code/formatting", "Use black formatter.", category="coding")

        coding = memory.retrieve("code", category="coding")
        assert len(coding) == 2

    def test_update_existing(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "original")
        memory.store("key1", "updated")
        results = memory.retrieve("key1")
        assert len(results) == 1
        assert results[0].content == "updated"

    def test_delete(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content")
        assert len(memory.retrieve("key1")) == 1
        memory.delete("key1")
        assert len(memory.retrieve("key1")) == 0

    def test_list_entries(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("a/1", "content1", category="a")
        memory.store("b/1", "content2", category="b")
        memory.store("a/2", "content3", category="a")

        all_entries = memory.list_entries()
        assert len(all_entries) == 3

        a_entries = memory.list_entries(category="a")
        assert len(a_entries) == 2

    def test_increment_access_count(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content")
        memory.retrieve("key1")
        memory.retrieve("key1")
        memory.retrieve("key1")
        entries = memory.retrieve("key1")
        assert entries[0].access_count == 4  # 4 retrieves

    def test_persist_and_load(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content1")
        memory.store("key2", "content2")
        memory.persist()

        memory2 = GlobalMemory(str(tmp_path))
        memory2.load()
        assert len(memory2.list_entries()) == 2

    def test_get_stats(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("a/1", "content1", category="a")
        memory.store("b/1", "content2", category="b")
        stats = memory.get_stats()
        assert stats["total_entries"] == 2
        assert stats["categories"]["a"] == 1
        assert stats["categories"]["b"] == 1

    def test_search_with_keywords(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/types", "Use typing module for annotations", category="coding")
        memory.store("python/format", "Use black for formatting", category="coding")
        memory.store("js/types", "TypeScript for type safety", category="coding")

        results = memory.retrieve("python typing")
        # Should find python/types as most relevant
        assert len(results) >= 1
        assert any("typing" in r.content.lower() for r in results)
