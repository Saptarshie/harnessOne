"""Knowledge graph operations over the vault."""

from mcp_server.vault import Vault


class KnowledgeGraph:
    """Manages relations (triples) stored in vault notes."""

    def __init__(self, vault: Vault):
        self._vault = vault
        self._triples: list[dict] = []
        self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the triple index from all vault notes."""
        self._triples = []
        for note_type in ["checkpoint", "derivation", "concept"]:
            for note in self._vault.list_notes(note_type):
                for rel in note.get("relations", []):
                    self._triples.append({
                        "subject": rel["subject"],
                        "relation": rel["relation"],
                        "object": rel["object"],
                        "source_note": note["id"],
                    })

    def add_relation(self, subject: str, relation: str, obj: str):
        """Add a relation triple. Stores as a concept note."""
        existing = self._find_concept_note(subject)
        if existing:
            self._add_to_existing_note(existing, subject, relation, obj)
        else:
            self._vault.write_note(
                title=subject,
                content=f"Concept: {subject}",
                tags=[subject.lower().replace(" ", "-")],
                links=[],
                note_type="concept",
                relations=[{"subject": subject, "relation": relation, "object": obj}],
            )
        self._triples.append({
            "subject": subject,
            "relation": relation,
            "object": obj,
            "source_note": subject,
        })

    def _find_concept_note(self, concept: str) -> dict | None:
        """Find an existing concept note by title."""
        for note in self._vault.list_notes("concept"):
            if note["title"] == concept:
                return note
        return None

    def _add_to_existing_note(self, note: dict, subject: str, relation: str, obj: str):
        """Add a relation to an existing note's frontmatter."""
        from pathlib import Path

        path = Path(note["path"])
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n\n(.*)", text, re.DOTALL)
        if not match:
            return

        import re
        import yaml
        fm = yaml.safe_load(match.group(1))
        body = match.group(2)

        relations = fm.get("relations", [])
        relations.append({"subject": subject, "relation": relation, "object": obj})
        fm["relations"] = relations

        yaml_fm = yaml.dump(fm, default_flow_style=False)
        new_content = f"---\n{yaml_fm}---\n\n{body}"
        path.write_text(new_content, encoding="utf-8")

    def query(
        self,
        subject: str | None = None,
        relation: str | None = None,
        obj: str | None = None,
    ) -> list[dict]:
        """Query triples by any combination of subject, relation, object."""
        results = self._triples
        if subject:
            results = [t for t in results if t["subject"] == subject]
        if relation:
            results = [t for t in results if t["relation"] == relation]
        if obj:
            results = [t for t in results if t["object"] == obj]
        return results

    def get_derivation_tree(self, concept: str, depth: int = 5) -> dict:
        """Get the derivation tree for a concept."""
        if depth <= 0:
            return {"concept": concept, "derived_from": []}

        incoming = [t for t in self._triples if t["object"] == concept]

        derived_from = []
        for triple in incoming:
            derived_from.append({
                "concept": triple["subject"],
                "relation": triple["relation"],
                "derived_from": self.get_derivation_tree(triple["subject"], depth - 1)["derived_from"],
            })

        return {"concept": concept, "derived_from": derived_from}
