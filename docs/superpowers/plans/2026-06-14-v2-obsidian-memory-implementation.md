# v2: Obsidian MCP Memory System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add persistent knowledge graph memory to the Cognitive Harness via an MCP server managing an Obsidian-style vault with hybrid retrieval (keyword + local embeddings).

**Architecture:** MCP server (stdio) exposes vault operations as tools. The harness calls these tools via an MCP client. New plugin nodes query memory before reasoning and write checkpoints after compaction. ChromaDB stores embeddings; Qwen3 0.6B int8 runs locally.

**Tech Stack:** Python 3.11+, MCP SDK, sentence-transformers, ChromaDB, Qwen3-Embedding-0.6B

**Spec:** `docs/superpowers/specs/2026-06-14-v2-obsidian-memory-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `mcp_server/__init__.py` | Package init |
| `mcp_server/server.py` | MCP server entry point, tool registration |
| `mcp_server/vault.py` | Vault read/write, frontmatter parsing |
| `mcp_server/graph.py` | Knowledge graph: parse wikilinks, query triples |
| `mcp_server/embeddings.py` | ChromaDB + Qwen3 embedding management |
| `src/harness/memory/__init__.py` | Memory package init |
| `src/harness/memory/mcp_client.py` | MCP client: start server, call tools |
| `src/harness/memory/retriever.py` | Hybrid retrieval: keyword + embedding fusion |
| `src/harness/memory/writer.py` | Write checkpoints and relations to vault |
| `src/harness/plugins/memory_query.py` | MemoryQueryNode plugin |
| `src/harness/plugins/memory_writer.py` | MemoryWriterNode plugin |
| `tests/unit/test_vault.py` | Vault operations tests |
| `tests/unit/test_graph.py` | Graph query tests |
| `tests/unit/test_embeddings.py` | Embedding operations tests |
| `tests/unit/test_retriever.py` | Retriever tests |
| `tests/unit/test_mcp_client.py` | MCP client tests |
| `tests/unit/test_memory_query.py` | MemoryQueryNode tests |
| `tests/unit/test_memory_writer.py` | MemoryWriterNode tests |
| `tests/integration/test_mcp_server.py` | Real MCP server tests |
| `tests/integration/test_memory_flow.py` | Full harness with memory |

---

## Task 0: Dependencies & Config

**Files:**
- Modify: `pyproject.toml`
- Modify: `config/default.yaml`
- Create: `mcp_server/__init__.py`

- [ ] **Step 1: Add v2 dependencies to pyproject.toml**

Add to `dependencies`:
```toml
    "mcp>=1.0.0",
    "sentence-transformers>=3.0.0",
    "chromadb>=0.5.0",
```

- [ ] **Step 2: Add memory config to config/default.yaml**

Append:
```yaml
memory:
  vault_path: "vault"
  embedding_model: "Qwen/Qwen3-Embedding-0.6B"
  embedding_device: "cpu"
  embedding_quantize: true
  top_k: 5
  keyword_weight: 0.4
  embedding_weight: 0.6
  mcp_server_path: "mcp_server/server.py"
```

- [ ] **Step 3: Update config.py to parse memory section**

Add to `HarnessConfig`:
```python
    # Memory settings
    vault_path: str = "vault"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    embedding_device: str = "cpu"
    embedding_quantize: bool = True
    memory_top_k: int = 5
    keyword_weight: float = 0.4
    embedding_weight: float = 0.6
    mcp_server_path: str = "mcp_server/server.py"
```

Add to `load_config`:
```python
    memory = raw.get("memory", {})
    vault_path = memory.get("vault_path", "vault")
    embedding_model = memory.get("embedding_model", "Qwen/Qwen3-Embedding-0.6B")
    embedding_device = memory.get("embedding_device", "cpu")
    embedding_quantize = memory.get("embedding_quantize", True)
    memory_top_k = memory.get("top_k", 5)
    keyword_weight = memory.get("keyword_weight", 0.4)
    embedding_weight = memory.get("embedding_weight", 0.6)
    mcp_server_path = memory.get("mcp_server_path", "mcp_server/server.py")
```

And include in the `HarnessConfig(...)` constructor call.

- [ ] **Step 4: Create mcp_server package**

`mcp_server/__init__.py`:
```python
"""MCP server for Obsidian-style vault operations."""
```

- [ ] **Step 5: Install dependencies**

Run: `pip install -e ".[dev]"`

- [ ] **Step 6: Run existing tests to verify nothing broke**

Run: `pytest tests/unit/ -v`
Expected: All 37 tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add .
git commit -m "feat(v2): add memory config, dependencies, mcp_server package"
```

---

## Task 1: Vault Operations

**Files:**
- Create: `mcp_server/vault.py`
- Create: `tests/unit/test_vault.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_vault.py`:
```python
import pytest
import os
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
        # Verify file exists
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_vault.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mcp_server.vault'`

- [ ] **Step 3: Implement vault operations**

`mcp_server/vault.py`:
```python
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
        # Create subdirectories
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

            # Extract title from first heading
            title_match = re.match(r"# (.+)\n\n", body)
            title = title_match.group(1) if title_match else file_path.stem

            # Extract content (everything after title)
            content_start = body.find("\n\n", body.find("# ")) + 2 if "# " in body else 0
            content = body[content_start:].strip()

            # Parse relations
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_vault.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add mcp_server/vault.py tests/unit/test_vault.py
git commit -m "feat(v2): vault read/write with frontmatter parsing"
```

---

## Task 2: Knowledge Graph

**Files:**
- Create: `mcp_server/graph.py`
- Create: `tests/unit/test_graph.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_graph.py`:
```python
import pytest
from mcp_server.graph import KnowledgeGraph
from mcp_server.vault import Vault


class TestKnowledgeGraph:
    def test_add_relation(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("DDP", "implies", "GPU_Memory_Fragmentation")
        triples = graph.query(subject="DDP")
        assert len(triples) == 1
        assert triples[0]["relation"] == "implies"

    def test_query_by_relation(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("C", "fixes", "D")
        triples = graph.query(relation="implies")
        assert len(triples) == 1
        assert triples[0]["subject"] == "A"

    def test_query_all(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("C", "fixes", "D")
        triples = graph.query()
        assert len(triples) == 2

    def test_derivation_tree(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("B", "implies", "C")
        graph.add_relation("C", "implies", "D")
        tree = graph.get_derivation_tree("D")
        assert "C" in str(tree)
        assert "B" in str(tree)

    def test_empty_graph(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        assert graph.query() == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_graph.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement knowledge graph**

`mcp_server/graph.py`:
```python
"""Knowledge graph operations over the vault."""

from mcp_server.vault import Vault


class KnowledgeGraph:
    """Manages relations (triples) stored in vault notes."""

    def __init__(self, vault: Vault):
        self._vault = vault
        # In-memory index of all triples
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
        # Check if a concept note for this subject exists
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
        # Read the file, update frontmatter, write back
        from pathlib import Path
        import re
        import yaml

        path = Path(note["path"])
        text = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n\n(.*)", text, re.DOTALL)
        if not match:
            return

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
        """Get the derivation tree for a concept (what it was derived from)."""
        if depth <= 0:
            return {"concept": concept, "derived_from": []}

        # Find all triples where this concept is the object
        incoming = [t for t in self._triples if t["object"] == concept]

        derived_from = []
        for triple in incoming:
            derived_from.append({
                "concept": triple["subject"],
                "relation": triple["relation"],
                "derived_from": self.get_derivation_tree(triple["subject"], depth - 1)["derived_from"],
            })

        return {"concept": concept, "derived_from": derived_from}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_graph.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add mcp_server/graph.py tests/unit/test_graph.py
git commit -m "feat(v2): knowledge graph with triple queries and derivation trees"
```

---

## Task 3: Embeddings (ChromaDB + Qwen3)

**Files:**
- Create: `mcp_server/embeddings.py`
- Create: `tests/unit/test_embeddings.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_embeddings.py`:
```python
import pytest
from unittest.mock import patch, MagicMock
from mcp_server.embeddings import EmbeddingStore


class TestEmbeddingStore:
    def test_add_and_search(self, tmp_path):
        store = EmbeddingStore(
            persist_dir=str(tmp_path / "chroma"),
            model_name=None,  # Use mock
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
        assert results[0]["id"] == "note-1"  # Most relevant

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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_embeddings.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement embedding store**

`mcp_server/embeddings.py`:
```python
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

    def _embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using the local model or ChromaDB default."""
        if self._model:
            embeddings = self._model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()
        return None  # ChromaDB will use its default embedding

    def add(self, doc_id: str, text: str, metadata: dict[str, Any]):
        """Add a document to the embedding store."""
        embedding = self._embed([text])
        kwargs = {
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
            "query_texts": [query] if not embedding else None,
            "query_embeddings": embedding if embedding else None,
            "n_results": min(top_k, self._collection.count()),
        }
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_embeddings.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add mcp_server/embeddings.py tests/unit/test_embeddings.py
git commit -m "feat(v2): ChromaDB embedding store with local model support"
```

---

## Task 4: MCP Server

**Files:**
- Create: `mcp_server/server.py`
- Create: `tests/integration/test_mcp_server.py`

- [ ] **Step 1: Write failing tests**

`tests/integration/test_mcp_server.py`:
```python
import pytest
import asyncio
import json
import subprocess
import sys
from pathlib import Path


class TestMCPServer:
    """Integration tests that start the real MCP server and call tools."""

    @pytest.fixture
    def vault_path(self, tmp_path):
        return str(tmp_path / "vault")

    def test_server_starts_and_stops(self, vault_path):
        """Verify the MCP server process starts and responds to init."""
        proc = subprocess.Popen(
            [sys.executable, "mcp_server/server.py", "--vault", vault_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # Send initialize request
        init_msg = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "0.1"},
            },
        })
        proc.stdin.write(f"Content-Length: {len(init_msg)}\r\n\r\n{init_msg}".encode())
        proc.stdin.flush()

        # Read response (with timeout)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            # If it didn't exit, it's running (good for a server)
            pass
```

- [ ] **Step 2: Implement MCP server**

`mcp_server/server.py`:
```python
"""MCP server for Obsidian-style vault operations."""

import sys
import json
import logging
import argparse
from pathlib import Path

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from mcp_server.vault import Vault
from mcp_server.graph import KnowledgeGraph
from mcp_server.embeddings import EmbeddingStore

logger = logging.getLogger(__name__)


def create_server(vault_path: str, embedding_model: str | None = None) -> Server:
    """Create and configure the MCP server."""
    vault = Vault(vault_path)
    graph = KnowledgeGraph(vault)

    chroma_path = str(Path(vault_path) / ".chromadb")
    embed_store = EmbeddingStore(
        persist_dir=chroma_path,
        model_name=embedding_model,
    )

    server = Server("cognitive-harness-vault")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="query_graph",
                description="Query the knowledge graph for triples (subject, relation, object).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": {"type": "string"},
                        "object": {"type": "string"},
                    },
                },
            ),
            Tool(
                name="get_derivation_tree",
                description="Get the derivation tree for a concept.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "concept": {"type": "string"},
                    },
                    "required": ["concept"],
                },
            ),
            Tool(
                name="write_note",
                description="Create or update a note in the vault.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "links": {"type": "array", "items": {"type": "string"}},
                        "note_type": {"type": "string", "enum": ["checkpoint", "concept", "derivation"]},
                        "relations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "subject": {"type": "string"},
                                    "relation": {"type": "string"},
                                    "object": {"type": "string"},
                                },
                            },
                        },
                    },
                    "required": ["title", "content", "note_type"],
                },
            ),
            Tool(
                name="add_relation",
                description="Add a relation triple to the knowledge graph.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "subject": {"type": "string"},
                        "relation": {"type": "string"},
                        "object": {"type": "string"},
                    },
                    "required": ["subject", "relation", "object"],
                },
            ),
            Tool(
                name="search_vault",
                description="Search the vault using hybrid retrieval (keyword + embedding).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        if name == "query_graph":
            triples = graph.query(
                subject=arguments.get("subject"),
                relation=arguments.get("relation"),
                object=arguments.get("object"),
            )
            return [TextContent(type="text", text=json.dumps(triples))]

        elif name == "get_derivation_tree":
            tree = graph.get_derivation_tree(arguments["concept"])
            return [TextContent(type="text", text=json.dumps(tree))]

        elif name == "write_note":
            result = vault.write_note(
                title=arguments["title"],
                content=arguments["content"],
                tags=arguments.get("tags", []),
                links=arguments.get("links", []),
                note_type=arguments["note_type"],
                relations=arguments.get("relations"),
            )
            # Index in embedding store
            embed_store.add(
                doc_id=result["id"],
                text=arguments["content"],
                metadata={"type": arguments["note_type"], "title": arguments["title"]},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        elif name == "add_relation":
            graph.add_relation(
                arguments["subject"],
                arguments["relation"],
                arguments["object"],
            )
            return [TextContent(type="text", text=json.dumps({"success": True}))]

        elif name == "search_vault":
            results = embed_store.search(
                query=arguments["query"],
                top_k=arguments.get("top_k", 5),
            )
            return [TextContent(type="text", text=json.dumps(results))]

        else:
            raise ValueError(f"Unknown tool: {name}")

    return server


async def run_server(vault_path: str, embedding_model: str | None = None):
    """Run the MCP server on stdio."""
    server = create_server(vault_path, embedding_model)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    parser = argparse.ArgumentParser(description="Cognitive Harness Vault MCP Server")
    parser.add_argument("--vault", default="vault", help="Path to vault directory")
    parser.add_argument("--embedding-model", default=None, help="Embedding model name")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_server(args.vault, args.embedding_model))


if __name__ == "__main__":
    import asyncio
    main()
```

- [ ] **Step 3: Run tests to verify they pass**

Run: `pytest tests/integration/test_mcp_server.py -v`
Expected: PASS (server starts and responds).

- [ ] **Step 4: Commit**

```powershell
git add mcp_server/server.py tests/integration/test_mcp_server.py
git commit -m "feat(v2): MCP server with all 5 tools"
```

---

## Task 5: MCP Client

**Files:**
- Create: `src/harness/memory/__init__.py`
- Create: `src/harness/memory/mcp_client.py`
- Create: `tests/unit/test_mcp_client.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_mcp_client.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from harness.memory.mcp_client import MCPClient


class TestMCPClient:
    @pytest.mark.asyncio
    async def test_call_tool(self):
        client = MCPClient("mcp_server/server.py", "vault")
        # Mock the internal session
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='[{"subject":"A","relation":"implies","object":"B"}]')]
        client._session = MagicMock()
        client._session.call_tool = AsyncMock(return_value=mock_result)

        result = await client.call_tool("query_graph", {"subject": "A"})
        assert result == [{"subject": "A", "relation": "implies", "object": "B"}]

    @pytest.mark.asyncio
    async def test_call_tool_error(self):
        client = MCPClient("mcp_server/server.py", "vault")
        client._session = MagicMock()
        client._session.call_tool = AsyncMock(side_effect=Exception("connection lost"))

        with pytest.raises(Exception, match="connection lost"):
            await client.call_tool("query_graph", {})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_mcp_client.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement MCP client**

`src/harness/memory/__init__.py`:
```python
"""Memory subsystem: MCP client, retriever, writer."""
```

`src/harness/memory/mcp_client.py`:
```python
"""MCP client for communicating with the vault server."""

import json
import logging
import asyncio
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for calling MCP tools on the vault server."""

    def __init__(self, server_path: str, vault_path: str, embedding_model: str | None = None):
        self._server_path = server_path
        self._vault_path = vault_path
        self._embedding_model = embedding_model
        self._session: ClientSession | None = None
        self._context = None

    async def start(self):
        """Start the MCP server subprocess and connect."""
        import sys
        args = [sys.executable, self._server_path, "--vault", self._vault_path]
        if self._embedding_model:
            args.extend(["--embedding-model", self._embedding_model])

        server_params = StdioServerParameters(
            command=args[0],
            args=args[1:],
        )

        self._context = stdio_client(server_params)
        read_stream, write_stream = await self._context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        logger.info("MCP server started and connected")

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call an MCP tool and return the parsed result.

        Args:
            name: Tool name.
            arguments: Tool arguments.

        Returns:
            Parsed JSON result from the tool.
        """
        if not self._session:
            raise RuntimeError("MCP client not started. Call start() first.")

        result = await self._session.call_tool(name, arguments)
        # Parse the text content
        if result.content:
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    async def shutdown(self):
        """Shut down the MCP server and clean up."""
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._context:
            await self._context.__aexit__(None, None, None)
        logger.info("MCP server shut down")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_mcp_client.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/memory/ tests/unit/test_mcp_client.py
git commit -m "feat(v2): MCP client for vault communication"
```

---

## Task 6: Hybrid Retriever

**Files:**
- Create: `src/harness/memory/retriever.py`
- Create: `tests/unit/test_retriever.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_retriever.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.memory.retriever import Retriever


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    mcp.call_tool = AsyncMock()
    return mcp


class TestRetriever:
    @pytest.mark.asyncio
    async def test_retrieve_merges_results(self, mock_mcp):
        # search_vault returns embedding results
        # query_graph returns keyword results
        call_count = 0

        async def side_effect(name, args):
            nonlocal call_count
            call_count += 1
            if name == "search_vault":
                return [
                    {"id": "n1", "text": "DDP memory leak fix", "metadata": {"type": "checkpoint"}, "distance": 0.1},
                    {"id": "n2", "text": "GPU memory management", "metadata": {"type": "concept"}, "distance": 0.3},
                ]
            elif name == "query_graph":
                return [
                    {"subject": "DDP", "relation": "implies", "object": "Memory_Leak"},
                ]
            return []

        mock_mcp.call_tool = AsyncMock(side_effect=side_effect)

        retriever = Retriever(mock_mcp, top_k=3, keyword_weight=0.4, embedding_weight=0.6)
        results = await retriever.retrieve("Fix DDP memory leak")

        assert len(results) > 0
        # Should have both graph triples and note results
        types = [r.get("type", r.get("relation", "")) for r in results]

    @pytest.mark.asyncio
    async def test_retrieve_empty(self, mock_mcp):
        mock_mcp.call_tool = AsyncMock(return_value=[])

        retriever = Retriever(mock_mcp, top_k=3)
        results = await retriever.retrieve("nonexistent query")
        assert results == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_retriever.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement hybrid retriever**

`src/harness/memory/retriever.py`:
```python
"""Hybrid retrieval: keyword extraction + embedding search with RRF fusion."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant context from the vault using hybrid search."""

    def __init__(
        self,
        mcp_client: Any,
        top_k: int = 5,
        keyword_weight: float = 0.4,
        embedding_weight: float = 0.6,
    ):
        self._mcp = mcp_client
        self._top_k = top_k
        self._kw_weight = keyword_weight
        self._emb_weight = embedding_weight

    async def retrieve(self, query: str) -> list[dict]:
        """Retrieve relevant context for a query.

        Uses RRF to fuse keyword (graph) and embedding (vector) results.

        Returns:
            List of ranked results with text, type, and score.
        """
        # Run both searches in parallel
        import asyncio

        embedding_task = asyncio.create_task(
            self._mcp.call_tool("search_vault", {"query": query, "top_k": self._top_k})
        )
        keyword_task = asyncio.create_task(
            self._extract_and_query_graph(query)
        )

        embedding_results, keyword_results = await asyncio.gather(
            embedding_task, keyword_task
        )

        if not embedding_results and not keyword_results:
            return []

        # RRF fusion
        scores: dict[str, float] = {}
        items: dict[str, dict] = {}

        # Embedding results
        if embedding_results:
            for rank, result in enumerate(embedding_results):
                item_id = result.get("id", f"emb_{rank}")
                scores[item_id] = scores.get(item_id, 0) + self._emb_weight / (60 + rank)
                items[item_id] = {
                    "text": result.get("text", ""),
                    "type": result.get("metadata", {}).get("type", "unknown"),
                    "id": item_id,
                }

        # Keyword (graph) results
        if keyword_results:
            for rank, triple in enumerate(keyword_results):
                item_id = f"graph_{triple.get('subject', '')}_{triple.get('relation', '')}"
                scores[item_id] = scores.get(item_id, 0) + self._kw_weight / (60 + rank)
                items[item_id] = {
                    "text": f"{triple['subject']} --{triple['relation']}--> {triple['object']}",
                    "type": "graph_triple",
                    "subject": triple.get("subject"),
                    "relation": triple.get("relation"),
                    "object": triple.get("object"),
                }

        # Sort by score and return top-K
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[: self._top_k]
        return [items[item_id] for item_id, _ in ranked]

    async def _extract_and_query_graph(self, query: str) -> list[dict]:
        """Extract keywords and query the graph."""
        # Simple keyword extraction: split on spaces, take key terms
        keywords = self._extract_keywords(query)

        all_triples = []
        for keyword in keywords:
            triples = await self._mcp.call_tool("query_graph", {"subject": keyword})
            if triples:
                all_triples.extend(triples)
            triples = await self._mcp.call_tool("query_graph", {"object": keyword})
            if triples:
                all_triples.extend(triples)

        return all_triples

    def _extract_keywords(self, query: str) -> list[str]:
        """Extract keywords from a query (simple approach)."""
        # Remove common words and extract key terms
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "through", "during", "before", "after", "above",
            "below", "between", "out", "off", "over", "under", "again",
            "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "both", "each", "few", "more", "most",
            "other", "some", "such", "no", "nor", "not", "only", "own",
            "same", "so", "than", "too", "very", "just", "because", "but",
            "and", "or", "if", "while", "about", "up", "it", "its", "this",
            "that", "these", "those", "i", "me", "my", "we", "our", "you",
            "your", "he", "him", "his", "she", "her", "they", "them", "their",
            "fix", "help", "want", "need", "use", "make", "get",
        }
        words = query.lower().split()
        keywords = [w.strip(".,!?;:") for w in words if w.lower() not in stop_words and len(w) > 2]
        return keywords[:5]  # Top 5 keywords
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_retriever.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/memory/retriever.py tests/unit/test_retriever.py
git commit -m "feat(v2): hybrid retriever with RRF fusion"
```

---

## Task 7: Memory Writer

**Files:**
- Create: `src/harness/memory/writer.py`
- Create: `tests/unit/test_memory_writer.py`

- [ ] **Step 1: Write failing tests**

`tests/unit/test_memory_writer.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.memory.writer import MemoryWriter


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    mcp.call_tool = AsyncMock(return_value={"id": "test-id", "path": "/test/path", "title": "Test"})
    return mcp


class TestMemoryWriter:
    @pytest.mark.asyncio
    async def test_write_checkpoint(self, mock_mcp):
        writer = MemoryWriter(mock_mcp)
        result = await writer.write_checkpoint(
            checkpoint_text="Premise: DDP issue. Conclusion: Use static_graph=True.",
            source_checkpoint="A",
            tags=["ddp", "memory"],
        )
        assert result["id"] == "test-id"
        mock_mcp.call_tool.assert_called_once()
        call_args = mock_mcp.call_tool.call_args
        assert call_args[0][0] == "write_note"
        assert call_args[0][1]["note_type"] == "checkpoint"

    @pytest.mark.asyncio
    async def test_write_relation(self, mock_mcp):
        writer = MemoryWriter(mock_mcp)
        await writer.write_relation("DDP", "implies", "Memory_Leak")
        call_args = mock_mcp.call_tool.call_args
        assert call_args[0][0] == "add_relation"
        assert call_args[0][1]["subject"] == "DDP"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_memory_writer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement memory writer**

`src/harness/memory/writer.py`:
```python
"""Write checkpoints and relations to the vault via MCP."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemoryWriter:
    """Writes verified knowledge to the vault."""

    def __init__(self, mcp_client: Any):
        self._mcp = mcp_client

    async def write_checkpoint(
        self,
        checkpoint_text: str,
        source_checkpoint: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Write a checkpoint to the vault.

        Args:
            checkpoint_text: The checkpoint content.
            source_checkpoint: What this was derived from (e.g., "A+B'").
            tags: Tags for the note.

        Returns:
            Dict with id, path, title.
        """
        title = f"Checkpoint: {checkpoint_text[:50]}..."
        links = []
        if source_checkpoint:
            links.append(f"checkpoint-{source_checkpoint}")

        result = await self._mcp.call_tool("write_note", {
            "title": title,
            "content": checkpoint_text,
            "tags": tags or [],
            "links": links,
            "note_type": "checkpoint",
        })
        logger.info(f"Wrote checkpoint to vault: {result.get('id', 'unknown')}")
        return result

    async def write_relation(self, subject: str, relation: str, obj: str):
        """Write a relation triple to the vault.

        Args:
            subject: Subject of the triple.
            relation: Relation type (e.g., "implies", "fixes", "derived_from").
            obj: Object of the triple.
        """
        await self._mcp.call_tool("add_relation", {
            "subject": subject,
            "relation": relation,
            "object": obj,
        })
        logger.info(f"Wrote relation: {subject} --{relation}--> {obj}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_memory_writer.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/memory/writer.py tests/unit/test_memory_writer.py
git commit -m "feat(v2): memory writer for checkpoints and relations"
```

---

## Task 8: Memory Plugins (MemoryQueryNode + MemoryWriterNode)

**Files:**
- Create: `src/harness/plugins/memory_query.py`
- Create: `src/harness/plugins/memory_writer.py`
- Create: `tests/unit/test_memory_query.py`
- Create: `tests/unit/test_memory_writer_node.py`

- [ ] **Step 1: Write failing tests for MemoryQueryNode**

`tests/unit/test_memory_query.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.memory_query import MemoryQueryNode
from harness.state import HarnessState


@pytest.fixture
def state():
    return HarnessState(
        checkpoints=[],
        working_buffer=[{"role": "user", "content": "Fix the DDP memory leak"}],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestMemoryQueryNode:
    @pytest.mark.asyncio
    async def test_injects_context_into_system_prompt(self, state):
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(side_effect=lambda name, args: {
            "search_vault": [
                {"id": "n1", "text": "DDP memory leak: use static_graph=True", "metadata": {"type": "checkpoint"}},
            ],
            "query_graph": [
                {"subject": "DDP", "relation": "implies", "object": "Memory_Leak"},
            ],
        }.get(name, []))

        node = MemoryQueryNode(mock_mcp)
        result = await node.process(state, MagicMock())

        # Should have added a system message with memory context
        system_msgs = [m for m in result["working_buffer"] if m.get("role") == "system"]
        assert len(system_msgs) >= 1
        assert "DDP" in system_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_no_context_when_empty(self, state):
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(return_value=[])

        node = MemoryQueryNode(mock_mcp)
        result = await node.process(state, MagicMock())

        # Should not add empty context
        system_msgs = [m for m in result["working_buffer"] if m.get("role") == "system"]
        assert len(system_msgs) == 0
```

- [ ] **Step 2: Write failing tests for MemoryWriterNode**

`tests/unit/test_memory_writer_node.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.memory_writer_node import MemoryWriterNode
from harness.state import HarnessState


class TestMemoryWriterNode:
    @pytest.mark.asyncio
    async def test_writes_new_checkpoint(self):
        state = HarnessState(
            checkpoints=["Checkpoint A: original", "Checkpoint B': derived"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=1,
            max_iterations=5,
            metadata={},
        )

        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(return_value={"id": "new-id", "title": "Test"})

        node = MemoryWriterNode(mock_mcp)
        result = await node.process(state, MagicMock())

        # Should have called write_note for the new checkpoint
        mock_mcp.call_tool.assert_called()
        call_args = mock_mcp.call_tool.call_args_list
        write_calls = [c for c in call_args if c[0][0] == "write_note"]
        assert len(write_calls) == 1

    @pytest.mark.asyncio
    async def test_skips_when_no_new_checkpoint(self):
        state = HarnessState(
            checkpoints=["Checkpoint A: existing"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=0,
            max_iterations=5,
            metadata={},
        )

        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock()

        node = MemoryWriterNode(mock_mcp)
        result = await node.process(state, MagicMock())

        # No new checkpoint, should not write
        mock_mcp.call_tool.assert_not_called()
```

- [ ] **Step 3: Implement MemoryQueryNode**

`src/harness/plugins/memory_query.py`:
```python
"""Memory query plugin — retrieves relevant vault context before reasoning."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient
from harness.memory.retriever import Retriever

logger = logging.getLogger(__name__)


@register_node("memory_query")
class MemoryQueryNode(BaseNode):
    """Queries the vault for relevant context and injects it into the prompt."""

    name = "memory_query"

    def __init__(self, mcp_client, top_k: int = 5, keyword_weight: float = 0.4, embedding_weight: float = 0.6):
        self._retriever = Retriever(mcp_client, top_k, keyword_weight, embedding_weight)

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Query vault and inject context into working buffer."""
        # Get the user's original prompt
        user_messages = [m for m in state["working_buffer"] if m.get("role") == "user"]
        if not user_messages:
            return state

        query = user_messages[0]["content"]

        # Retrieve relevant context
        results = await self._retriever.retrieve(query)

        if not results:
            return state

        # Format context
        context_parts = []
        for r in results:
            rtype = r.get("type", "unknown")
            text = r.get("text", "")
            context_parts.append(f"[{rtype}] {text}")

        context_text = "\n".join(context_parts)

        # Inject as system message at the beginning of working buffer
        memory_msg = {
            "role": "system",
            "content": f"Relevant memory context:\n{context_text}",
        }

        # Insert after any existing system messages
        insert_idx = 0
        for i, msg in enumerate(state["working_buffer"]):
            if msg.get("role") == "system":
                insert_idx = i + 1
            else:
                break

        state["working_buffer"].insert(insert_idx, memory_msg)
        return state
```

- [ ] **Step 4: Implement MemoryWriterNode**

`src/harness/plugins/memory_writer_node.py`:
```python
"""Memory writer plugin — writes new checkpoints to the vault."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient
from harness.memory.writer import MemoryWriter

logger = logging.getLogger(__name__)


@register_node("memory_writer")
class MemoryWriterNode(BaseNode):
    """Writes newly created checkpoints to the vault."""

    name = "memory_writer"

    def __init__(self, mcp_client):
        self._writer = MemoryWriter(mcp_client)
        self._last_checkpoint_count = 0

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Write any new checkpoints to the vault."""
        current_count = len(state["checkpoints"])

        if current_count > self._last_checkpoint_count:
            # New checkpoint(s) were added
            for i in range(self._last_checkpoint_count, current_count):
                checkpoint = state["checkpoints"][i]
                checkpoint_label = chr(65 + i)  # A, B, C, ...

                try:
                    await self._writer.write_checkpoint(
                        checkpoint_text=checkpoint,
                        source_checkpoint=checkpoint_label,
                        tags=["auto-generated"],
                    )
                    logger.info(f"Wrote checkpoint {checkpoint_label} to vault")
                except Exception as e:
                    logger.warning(f"Failed to write checkpoint to vault: {e}")

            self._last_checkpoint_count = current_count

        return state
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_memory_query.py tests/unit/test_memory_writer_node.py -v`
Expected: All 4 tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add src/harness/plugins/memory_query.py src/harness/plugins/memory_writer_node.py tests/unit/test_memory_query.py tests/unit/test_memory_writer_node.py
git commit -m "feat(v2): MemoryQueryNode and MemoryWriterNode plugins"
```

---

## Task 9: Orchestrator Integration

**Files:**
- Modify: `src/harness/orchestrator.py`
- Modify: `src/harness/__init__.py`
- Modify: `src/harness/config.py`
- Create: `tests/integration/test_memory_flow.py`

- [ ] **Step 1: Update orchestrator to import and wire memory plugins**

In `orchestrator.py`, add to `build_graph()`:
```python
        # Import memory plugins (v2)
        try:
            import harness.plugins.memory_query  # noqa: F401
            import harness.plugins.memory_writer_node  # noqa: F401
            has_memory = True
        except ImportError:
            has_memory = False
```

Add memory nodes to graph if available:
```python
        if has_memory and self._mcp_client:
            memory_query = self._make_memory_node("memory_query")
            memory_writer = self._make_memory_node("memory_writer")
            graph.add_node("memory_query", memory_query)
            graph.add_node("memory_writer", memory_writer)

            # Wire: START → memory_query → thinker
            graph.set_entry_point("memory_query")
            graph.add_edge("memory_query", "thinker")

            # Wire: compactor → memory_writer → context_manager
            graph.add_edge("compactor", "memory_writer")
            graph.add_edge("memory_writer", "context_manager")
        else:
            # Original flow without memory
            graph.set_entry_point("thinker")
            graph.add_edge("compactor", "context_manager")
```

- [ ] **Step 2: Update CognitiveHarness to start MCP client**

In `__init__.py`:
```python
class CognitiveHarness:
    def __init__(self, config: HarnessConfig):
        self._orchestrator = Orchestrator(config)
        self._config = config

    async def invoke(self, prompt: str) -> str:
        return await self._orchestrator.invoke(prompt)

    async def startup(self):
        """Start the MCP server if memory is configured."""
        if self._config.vault_path:
            await self._orchestrator.start_mcp_client()

    async def shutdown(self):
        """Shut down the MCP server."""
        await self._orchestrator.shutdown_mcp_client()
```

- [ ] **Step 3: Write integration test**

`tests/integration/test_memory_flow.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from harness import CognitiveHarness
from harness.config import HarnessConfig
from harness.llm.client import LLMResponse


def make_response(content: str):
    return LLMResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        model="openai/gpt-4o",
        finish_reason="stop",
    )


def _make_litellm_response(resp):
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = resp.content
    mock.choices[0].finish_reason = resp.finish_reason
    mock.usage.prompt_tokens = resp.input_tokens
    mock.usage.completion_tokens = resp.output_tokens
    mock.model = resp.model
    return mock


@pytest.mark.asyncio
async def test_harness_with_memory(tmp_path):
    """Test harness works with memory system (mocked MCP)."""
    config = HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        max_iterations=2,
        vault_path=str(tmp_path / "vault"),
    )

    responses = [
        make_response("The fix is to set find_unused_parameters=False."),
    ]

    with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
        mock.side_effect = [_make_litellm_response(r) for r in responses]

        harness = CognitiveHarness(config)
        # Don't start MCP client (mock it)
        harness._orchestrator._mcp_client = MagicMock()
        harness._orchestrator._mcp_client.call_tool = AsyncMock(return_value=[])

        result = await harness.invoke("Fix the memory leak")

    assert isinstance(result, str)
    assert len(result) > 0
```

- [ ] **Step 4: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/orchestrator.py src/harness/__init__.py tests/integration/test_memory_flow.py
git commit -m "feat(v2): orchestrator integration with memory plugins"
```

---

## Task 10: End-to-End Memory Test

**Files:**
- Create: `tests/integration/test_e2e_memory.py`

- [ ] **Step 1: Write end-to-end test with real MCP server**

`tests/integration/test_e2e_memory.py`:
```python
"""End-to-end test: real MCP server, real vault, real LLM."""

import pytest
import asyncio
import os
from harness import CognitiveHarness, load_config


@pytest.mark.integration
@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)
async def test_e2e_memory(tmp_path):
    """Full test: harness with memory writes checkpoint to vault."""
    config = load_config("config/default.yaml")
    config.max_iterations = 2
    config.vault_path = str(tmp_path / "vault")

    harness = CognitiveHarness(config)
    await harness.startup()

    try:
        result = await harness.invoke("What is 2 + 2?")
        assert isinstance(result, str)
        assert len(result) > 0

        # Verify vault has content (from memory_writer)
        vault_path = tmp_path / "vault"
        assert vault_path.exists()
    finally:
        await harness.shutdown()
```

- [ ] **Step 2: Run test**

Run: `pytest tests/integration/test_e2e_memory.py -v -m integration`
Expected: PASS (if OPENAI_API_KEY set).

- [ ] **Step 3: Commit**

```powershell
git add tests/integration/test_e2e_memory.py
git commit -m "test(v2): end-to-end memory integration test"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 0 | Dependencies & Config | existing tests pass |
| 1 | Vault Operations | 5 unit tests |
| 2 | Knowledge Graph | 5 unit tests |
| 3 | Embeddings (ChromaDB) | 3 unit tests |
| 4 | MCP Server | 1 integration test |
| 5 | MCP Client | 2 unit tests |
| 6 | Hybrid Retriever | 2 unit tests |
| 7 | Memory Writer | 2 unit tests |
| 8 | Memory Plugins | 4 unit tests |
| 9 | Orchestrator Integration | 1 integration test |
| 10 | E2E Memory Test | 1 integration test |

**Total: 24 unit tests + 3 integration tests**
