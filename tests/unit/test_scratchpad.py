import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from harness.memory.scratchpad import Scratchpad, ScratchpadEntry


class TestScratchpadEntry:
    def test_create_entry(self):
        entry = ScratchpadEntry(
            label="current_task",
            content="Fix the memory leak in training loop",
            priority=1,
        )
        assert entry.label == "current_task"
        assert entry.priority == 1

    def test_entry_to_dict(self):
        entry = ScratchpadEntry(label="test", content="content")
        d = entry.to_dict()
        assert d["label"] == "test"


class TestScratchpad:
    def test_set_and_get(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug #123")
        assert pad.get("task") == "Fix bug #123"

    def test_get_nonexistent(self):
        pad = Scratchpad()
        assert pad.get("missing") is None
        assert pad.get("missing", "default") == "default"

    def test_overwrite(self):
        pad = Scratchpad()
        pad.set("task", "Old task")
        pad.set("task", "New task")
        assert pad.get("task") == "New task"

    def test_delete(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.delete("task")
        assert pad.get("task") is None

    def test_list_entries(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        pad.set("goal", "No memory leaks")
        entries = pad.list_entries()
        assert len(entries) == 3

    def test_priority_ordering(self):
        pad = Scratchpad()
        pad.set("low", "low priority", priority=3)
        pad.set("high", "high priority", priority=1)
        pad.set("medium", "medium priority", priority=2)
        entries = pad.list_entries()
        assert entries[0].label == "high"
        assert entries[1].label == "medium"
        assert entries[2].label == "low"

    def test_clear(self):
        pad = Scratchpad()
        pad.set("a", "1")
        pad.set("b", "2")
        pad.clear()
        assert len(pad.list_entries()) == 0

    def test_to_context_string(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        context = pad.to_context_string()
        assert "**task**:" in context
        assert "Fix bug" in context
        assert "**context**:" in context

    def test_persist_and_load(self, tmp_path):
        pad = Scratchpad(str(tmp_path))
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        pad.persist()

        pad2 = Scratchpad(str(tmp_path))
        pad2.load()
        assert pad2.get("task") == "Fix bug"
        assert len(pad2.list_entries()) == 2

    def test_max_entries(self):
        pad = Scratchpad(max_entries=3)
        pad.set("a", "1")
        pad.set("b", "2")
        pad.set("c", "3")
        pad.set("d", "4")  # Should evict oldest
        assert len(pad.list_entries()) == 3
        assert pad.get("a") is None  # Evicted
