"""Global cross-session memory store.

Persists knowledge across sessions — coding patterns, project decisions,
learned preferences, and reusable solutions.
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""

    key: str
    content: str
    category: str = "general"
    source_session: str = ""
    timestamp: str = ""
    access_count: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GlobalMemory:
    """Cross-session knowledge persistence."""

    def __init__(self, storage_path: str = ".harness/global_memory"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, MemoryEntry] = {}
        self._categories: dict[str, set[str]] = {}  # category -> set of keys

    def store(
        self,
        key: str,
        content: str,
        category: str = "general",
        source_session: str = "",
        metadata: dict | None = None,
    ):
        """Store or update a memory entry."""
        if key in self._entries:
            # Update existing
            entry = self._entries[key]
            entry.content = content
            entry.category = category
            entry.timestamp = datetime.now(timezone.utc).isoformat()
            if metadata:
                entry.metadata.update(metadata)
        else:
            entry = MemoryEntry(
                key=key,
                content=content,
                category=category,
                source_session=source_session,
                metadata=metadata or {},
            )
            self._entries[key] = entry

        # Update category index
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(key)

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Retrieve entries matching query.

        Uses keyword matching with scoring:
        - Exact key match: +10 points
        - Query in key: +5 points
        - Query words in content: +1 point per word
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        candidates = []
        for key, entry in self._entries.items():
            # Filter by category
            if category and entry.category != category:
                continue

            score = 0
            key_lower = key.lower()

            # Score based on key match
            if query_lower == key_lower:
                score += 10
            elif query_lower in key_lower:
                score += 5

            # Score based on content match
            content_lower = entry.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1

            if score > 0:
                candidates.append((score, entry))

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        results = [entry for _, entry in candidates[:limit]]

        # Increment access count
        for entry in results:
            entry.access_count += 1

        return results

    def delete(self, key: str):
        """Delete a memory entry."""
        if key in self._entries:
            entry = self._entries[key]
            if entry.category in self._categories:
                self._categories[entry.category].discard(key)
            del self._entries[key]

    def list_entries(self, category: str | None = None) -> list[MemoryEntry]:
        """List all entries, optionally filtered by category."""
        if category:
            keys = self._categories.get(category, set())
            return [self._entries[k] for k in keys if k in self._entries]
        return list(self._entries.values())

    def get_stats(self) -> dict:
        """Get memory statistics."""
        categories = {}
        for cat, keys in self._categories.items():
            categories[cat] = len(keys)

        return {
            "total_entries": len(self._entries),
            "categories": categories,
            "total_accesses": sum(e.access_count for e in self._entries.values()),
        }

    def persist(self):
        """Save to disk."""
        file_path = self._path / "memory.json"
        data = {
            "entries": {k: v.to_dict() for k, v in self._entries.items()},
            "categories": {k: list(v) for k, v in self._categories.items()},
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Persisted {len(self._entries)} memory entries")

    def load(self):
        """Load from disk."""
        file_path = self._path / "memory.json"
        if not file_path.exists():
            return

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self._entries = {
                k: MemoryEntry.from_dict(v) for k, v in data.get("entries", {}).items()
            }
            self._categories = {
                k: set(v) for k, v in data.get("categories", {}).items()
            }
            logger.info(f"Loaded {len(self._entries)} memory entries")
        except Exception as e:
            logger.error(f"Failed to load global memory: {e}")
