"""Session and Message data models."""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str
    content: str
    timestamp: str = ""
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        d = {"role": self.role, "content": self.content, "timestamp": self.timestamp}
        if self.tool_calls:
            d["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        if self.name:
            d["name"] = self.name
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            role=data["role"],
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
            tool_calls=data.get("tool_calls"),
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
        )


@dataclass
class Session:
    id: str = ""
    created: str = ""
    last_active: str = ""
    title: str = ""
    messages: list[Message] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        if not self.created:
            self.created = now
        if not self.last_active:
            self.last_active = now

    def add_user_message(self, content: str):
        self.messages.append(Message(role="user", content=content))
        self.last_active = datetime.now(timezone.utc).isoformat()
        if not self.title and len(content) > 5:
            self.title = content[:60] + ("..." if len(content) > 60 else "")

    def add_assistant_message(self, content: str, tool_calls: list[dict] | None = None):
        self.messages.append(Message(role="assistant", content=content, tool_calls=tool_calls))
        self.last_active = datetime.now(timezone.utc).isoformat()

    def add_tool_result(self, tool_call_id: str, content: str, name: str = ""):
        self.messages.append(Message(role="tool", content=content, tool_call_id=tool_call_id, name=name))
        self.last_active = datetime.now(timezone.utc).isoformat()

    def add_system_message(self, content: str):
        self.messages.insert(0, Message(role="system", content=content))

    def get_messages_for_llm(self) -> list[dict]:
        return [m.to_dict() for m in self.messages]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created": self.created,
            "last_active": self.last_active,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Session":
        return cls(
            id=data["id"],
            created=data.get("created", ""),
            last_active=data.get("last_active", ""),
            title=data.get("title", ""),
            messages=[Message.from_dict(m) for m in data.get("messages", [])],
            metadata=data.get("metadata", {}),
        )
