"""Vault read/write operations with frontmatter parsing."""

import uuid
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml


class Vault:
    """Manages an Obsidian-style markdown vault."""

    def __init__(self, vault_path: str):
        self._path = Path(vault_path)
        self._path.mkdir(parents=True, exist_ok=True)
        for subdir in ["checkpoints", "derivations", "concepts"]:
            (self._path / subdir).mkdir(exist_ok=True)

    def write_note(
        self,
        title: str,
        content: str,
        tags: list[str],
        links: list[str],
        note_type: str,
        relations: list[dict] | None = None,
    ) -> dict:
        """Create a new note in the vault.

        Returns:
            Dict with id, path, title.
        """
        note_id = str(uuid.uuid4())[:8]
        subdir = {
            "checkpoint": "checkpoints",
            "derivation": "derivations",
            "concept": "concepts",
        }.get(note_type, "concepts")

        frontmatter = {
            "id": note_id,
            "type": note_type,
            "created": datetime.now(timezone.utc).isoformat(),
            "tags": tags,
            "links": [f"[[{link}]]" for link in links],
        }
        if relations:
            frontmatter["relations"] = relations

        yaml_fm = yaml.dump(frontmatter, default_flow_style=False)
        file_content = f"---\n{yaml_fm}---\n\n# {title}\n\n{content}\n"

        file_path = self._path / subdir / f"{note_id}.md"
        file_path.write_text(file_content, encoding="utf-8")

        return {"id": note_id, "path": str(file_path), "title": title}

    def read_note(self, note_id: str) -> dict | None:
        """Read a note by ID. Searches all subdirectories."""
        for subdir in ["checkpoints", "derivations", "concepts"]:
            file_path = self._path / subdir / f"{note_id}.md"
            if file_path.exists():
                return self._parse_note(file_path)
        return None

    def list_notes(self, note_type: str) -> list[dict]:
        """List all notes of a given type."""
        subdir = {
            "checkpoint": "checkpoints",
            "derivation": "derivations",
            "concept": "concepts",
        }.get(note_type, "concepts")

        notes = []
        for file_path in (self._path / subdir).glob("*.md"):
            parsed = self._parse_note(file_path)
            if parsed:
                notes.append(parsed)
        return notes

    def _parse_note(self, file_path: Path) -> dict | None:
        """Parse a markdown note with YAML frontmatter."""
        try:
            text = file_path.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---\n\n(.*)", text, re.DOTALL)
            if not match:
                return None

            fm = yaml.safe_load(match.group(1))
            body = match.group(2)

            title_match = re.match(r"# (.+)\n\n", body)
            title = title_match.group(1) if title_match else file_path.stem

            content_start = body.find("\n\n", body.find("# ")) + 2 if "# " in body else 0
            content = body[content_start:].strip()

            relations = fm.get("relations", [])

            return {
                "id": fm.get("id", file_path.stem),
                "type": fm.get("type", "unknown"),
                "created": fm.get("created", ""),
                "tags": fm.get("tags", []),
                "links": fm.get("links", []),
                "relations": relations,
                "title": title,
                "content": content,
                "path": str(file_path),
            }
        except Exception:
            return None
