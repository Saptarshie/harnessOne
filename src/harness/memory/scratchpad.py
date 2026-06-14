"""Working memory scratchpad for current context.

Stores temporary, session-scoped information that the LLM
needs to reference during a conversation:
- Current task description
- Key findings so far
- Open questions
- Relevant constraints
"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScratchpadEntry:
    """A single scratchpad entry."""

    label: str
    content: str
    priority: int = 5  # 1=highest, 10=lowest
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScratchpadEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Scratchpad:
    """Working memory for current conversation context."""

    def __init__(self, storage_path: str | None = None, max_entries: int = 100):
        self._entries: OrderedDict[str, ScratchpadEntry] = OrderedDict()
        self._storage_path = Path(storage_path) if storage_path else None
        self._max_entries = max_entries

    def set(self, label: str, content: str, priority: int = 5):
        """Set a scratchpad entry."""
        if label in self._entries:
            # Update existing
            entry = self._entries[label]
            entry.content = content
            entry.priority = priority
            entry.timestamp = datetime.now(timezone.utc).isoformat()
            # Move to end (most recent)
            self._entries.move_to_end(label)
        else:
            # Evict if at capacity
            while len(self._entries) >= self._max_entries:
                self._entries.popitem(last=False)

            self._entries[label] = ScratchpadEntry(
                label=label,
                content=content,
                priority=priority,
            )

    def get(self, label: str, default: str | None = None) -> str | None:
        """Get a scratchpad entry by label."""
        entry = self._entries.get(label)
        return entry.content if entry else default

    def delete(self, label: str):
        """Delete a scratchpad entry."""
        self._entries.pop(label, None)

    def list_entries(self) -> list[ScratchpadEntry]:
        """List all entries, sorted by priority."""
        entries = list(self._entries.values())
        entries.sort(key=lambda e: (e.priority, e.timestamp))
        return entries

    def clear(self):
        """Clear all entries."""
        self._entries.clear()

    def to_context_string(self) -> str:
        """Format scratchpad as context string for LLM."""
        entries = self.list_entries()
        if not entries:
            return ""

        lines = ["## Scratchpad"]
        for entry in entries:
            lines.append(f"- **{entry.label}**: {entry.content}")
        return "\n".join(lines)

    def persist(self):
        """Save to disk."""
        if not self._storage_path:
            return
        self._storage_path.mkdir(parents=True, exist_ok=True)
        file_path = self._storage_path / "scratchpad.json"
        data = [entry.to_dict() for entry in self._entries.values()]
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self):
        """Load from disk."""
        if not self._storage_path:
            return
        file_path = self._storage_path / "scratchpad.json"
        if not file_path.exists():
            return

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self._entries.clear()
            for item in data:
                entry = ScratchpadEntry.from_dict(item)
                self._entries[entry.label] = entry
        except Exception as e:
            logger.error(f"Failed to load scratchpad: {e}")
