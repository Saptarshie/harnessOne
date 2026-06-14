"""Rigorous tests for Scratchpad."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import json
from harness.memory.scratchpad import Scratchpad, ScratchpadEntry


class TestScratchpadEntryRigorous:
    """Rigorous tests for ScratchpadEntry."""

    def test_entry_with_empty_content(self):
        """Test entry with empty content."""
        entry = ScratchpadEntry(label="test", content="")
        assert entry.content == ""

    def test_entry_with_large_content(self):
        """Test entry with large content."""
        large_content = "x" * 100000
        entry = ScratchpadEntry(label="test", content=large_content)
        assert len(entry.content) == 100000

    def test_entry_with_special_characters(self):
        """Test entry with special characters."""
        entry = ScratchpadEntry(
            label="task/special_v2",
            content="Content with\nnewlines\tand\ttabs",
            priority=1,
        )
        d = entry.to_dict()
        assert d["label"] == "task/special_v2"
        assert "\n" in d["content"]

    def test_entry_with_unicode(self):
        """Test entry with unicode characters."""
        entry = ScratchpadEntry(
            label="task",
            content="Fix bug 🎉 with unicode ñ é ü",
            priority=1,
        )
        d = entry.to_dict()
        assert "🎉" in d["content"]

    def test_entry_priority_range(self):
        """Test entry with various priority values."""
        entry1 = ScratchpadEntry(label="low", content="content", priority=10)
        entry2 = ScratchpadEntry(label="high", content="content", priority=1)
        entry3 = ScratchpadEntry(label="mid", content="content", priority=5)

        assert entry1.priority == 10
        assert entry2.priority == 1
        assert entry3.priority == 5


class TestScratchpadRigorous:
    """Rigorous tests for Scratchpad."""

    def test_set_many_entries(self):
        """Test setting many entries."""
        pad = Scratchpad()
        for i in range(50):
            pad.set(f"key_{i}", f"value_{i}")
        assert len(pad.list_entries()) == 50

    def test_set_and_get_many(self):
        """Test setting and getting many entries."""
        pad = Scratchpad()
        for i in range(50):
            pad.set(f"key_{i}", f"value_{i}")
        for i in range(50):
            assert pad.get(f"key_{i}") == f"value_{i}"

    def test_overwrite_preserves_order(self):
        """Test that overwriting moves entry to most recent."""
        pad = Scratchpad()
        pad.set("a", "1")
        pad.set("b", "2")
        pad.set("c", "3")
        pad.set("a", "updated")  # Should move to end

        entries = pad.list_entries()
        # a should still be there
        assert pad.get("a") == "updated"
        assert len(entries) == 3

    def test_delete_many(self):
        """Test deleting many entries."""
        pad = Scratchpad()
        for i in range(20):
            pad.set(f"key_{i}", f"value_{i}")

        for i in range(10):
            pad.delete(f"key_{i}")

        assert len(pad.list_entries()) == 10
        for i in range(10):
            assert pad.get(f"key_{i}") is None

    def test_delete_nonexistent(self):
        """Test deleting nonexistent entry."""
        pad = Scratchpad()
        # Should not raise
        pad.delete("nonexistent")

    def test_list_entries_ordering(self):
        """Test that entries are ordered by priority."""
        pad = Scratchpad()
        pad.set("low", "content", priority=10)
        pad.set("high", "content", priority=1)
        pad.set("mid", "content", priority=5)
        pad.set("high2", "content", priority=1)
        pad.set("low2", "content", priority=10)

        entries = pad.list_entries()
        assert entries[0].priority == 1
        assert entries[1].priority == 1
        assert entries[2].priority == 5
        assert entries[3].priority == 10
        assert entries[4].priority == 10

    def test_clear_removes_all(self):
        """Test that clear removes all entries."""
        pad = Scratchpad()
        for i in range(20):
            pad.set(f"key_{i}", f"value_{i}")

        pad.clear()
        assert len(pad.list_entries()) == 0

    def test_clear_empty(self):
        """Test clearing empty scratchpad."""
        pad = Scratchpad()
        # Should not raise
        pad.clear()
        assert len(pad.list_entries()) == 0

    def test_to_context_string_empty(self):
        """Test context string with no entries."""
        pad = Scratchpad()
        assert pad.to_context_string() == ""

    def test_to_context_string_single(self):
        """Test context string with single entry."""
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        context = pad.to_context_string()
        assert "## Scratchpad" in context
        assert "**task**: Fix bug" in context

    def test_to_context_string_many(self):
        """Test context string with many entries."""
        pad = Scratchpad()
        for i in range(10):
            pad.set(f"key_{i}", f"value_{i}")

        context = pad.to_context_string()
        for i in range(10):
            assert f"**key_{i}**: value_{i}" in context

    def test_persistence_roundtrip(self, tmp_path):
        """Test persistence roundtrip."""
        pad = Scratchpad(str(tmp_path))
        for i in range(20):
            pad.set(f"key_{i}", f"value_{i}", priority=i % 10 + 1)
        pad.persist()

        pad2 = Scratchpad(str(tmp_path))
        pad2.load()
        assert len(pad2.list_entries()) == 20

        for i in range(20):
            assert pad2.get(f"key_{i}") == f"value_{i}"

    def test_persistence_with_priorities(self, tmp_path):
        """Test that priorities persist."""
        pad = Scratchpad(str(tmp_path))
        pad.set("high", "content", priority=1)
        pad.set("low", "content", priority=10)
        pad.persist()

        pad2 = Scratchpad(str(tmp_path))
        pad2.load()
        entries = pad2.list_entries()
        assert entries[0].priority == 1
        assert entries[1].priority == 10

    def test_persistence_empty(self, tmp_path):
        """Test persistence with empty scratchpad."""
        pad = Scratchpad(str(tmp_path))
        pad.persist()

        pad2 = Scratchpad(str(tmp_path))
        pad2.load()
        assert len(pad2.list_entries()) == 0

    def test_no_storage_path(self):
        """Test scratchpad without storage path."""
        pad = Scratchpad()
        pad.set("key", "value")
        # persist should be a no-op
        pad.persist()
        # load should be a no-op
        pad.load()
        assert pad.get("key") == "value"

    def test_max_entries_eviction_fifo(self):
        """Test that eviction is FIFO."""
        pad = Scratchpad(max_entries=5)
        for i in range(10):
            pad.set(f"key_{i}", f"value_{i}")

        assert len(pad.list_entries()) == 5
        # Oldest should be evicted
        assert pad.get("key_0") is None
        assert pad.get("key_4") is None
        # Newest should remain
        assert pad.get("key_5") is not None
        assert pad.get("key_9") is not None

    def test_max_entries_eviction_with_overwrite(self):
        """Test eviction with overwrites."""
        pad = Scratchpad(max_entries=3)
        pad.set("a", "1")
        pad.set("b", "2")
        pad.set("c", "3")
        pad.set("a", "updated")  # Should not evict, just update

        assert len(pad.list_entries()) == 3
        assert pad.get("a") == "updated"
        assert pad.get("b") == "2"
        assert pad.get("c") == "3"

    def test_max_entries_one(self):
        """Test scratchpad with max_entries=1."""
        pad = Scratchpad(max_entries=1)
        pad.set("first", "1")
        pad.set("second", "2")

        assert len(pad.list_entries()) == 1
        assert pad.get("first") is None
        assert pad.get("second") == "2"

    def test_corrupted_scratchpad_file(self, tmp_path):
        """Test handling of corrupted scratchpad file."""
        pad_file = tmp_path / "scratchpad.json"
        pad_file.write_text("not valid json", encoding="utf-8")

        pad = Scratchpad(str(tmp_path))
        pad.load()
        assert len(pad.list_entries()) == 0

    def test_missing_scratchpad_file(self, tmp_path):
        """Test loading when no scratchpad file exists."""
        pad = Scratchpad(str(tmp_path))
        pad.load()
        assert len(pad.list_entries()) == 0
