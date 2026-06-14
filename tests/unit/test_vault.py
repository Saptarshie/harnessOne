import pytest
from mcp_server.vault import Vault


class TestVault:
    def test_create_note(self, tmp_path):
        vault = Vault(str(tmp_path))
        vault.write_note(
            title="DDP Memory Leak",
            content="Premise: DDP with unused parameters.\nConclusion: Use static_graph=True.",
            tags=["ddp", "memory-leak"],
            links=["concept-ddp"],
            note_type="checkpoint",
        )
        notes = list((tmp_path / "checkpoints").glob("*.md"))
        assert len(notes) == 1
        content = notes[0].read_text()
        assert "DDP Memory Leak" in content
        assert "ddp" in content

    def test_read_note(self, tmp_path):
        vault = Vault(str(tmp_path))
        vault.write_note(
            title="Test Note",
            content="Some content.",
            tags=["test"],
            links=[],
            note_type="concept",
        )
        notes = vault.list_notes("concept")
        assert len(notes) == 1
        note = vault.read_note(notes[0]["id"])
        assert note["title"] == "Test Note"
        assert note["content"] == "Some content."

    def test_parse_frontmatter(self, tmp_path):
        vault = Vault(str(tmp_path))
        vault.write_note(
            title="Relations Test",
            content="Testing relations.",
            tags=["test"],
            links=["concept-a"],
            note_type="concept",
            relations=[
                {"subject": "A", "relation": "implies", "object": "B"},
            ],
        )
        notes = vault.list_notes("concept")
        note = vault.read_note(notes[0]["id"])
        assert len(note["relations"]) == 1
        assert note["relations"][0]["subject"] == "A"

    def test_list_notes_by_type(self, tmp_path):
        vault = Vault(str(tmp_path))
        vault.write_note("CP1", "content", [], [], "checkpoint")
        vault.write_note("CP2", "content", [], [], "checkpoint")
        vault.write_note("C1", "content", [], [], "concept")
        assert len(vault.list_notes("checkpoint")) == 2
        assert len(vault.list_notes("concept")) == 1

    def test_empty_vault(self, tmp_path):
        vault = Vault(str(tmp_path))
        assert vault.list_notes("checkpoint") == []
