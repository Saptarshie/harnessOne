# Harness Upgrade: Sessions, Skills, Tools & MCP — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the Cognitive Harness to support multi-turn conversation, persistent sessions, skills system, built-in tools, external MCP servers, and CLI/API interfaces.

**Architecture:** Chat engine wraps the existing LLM client with a tool execution loop. Sessions are JSON files. Skills are SKILL.md files (hermes-agent compatible). Tools are registered in a central registry. MCP servers are config-managed.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, existing harness stack

**Spec:** `docs/superpowers/specs/2026-06-14-harness-upgrade-design.md`

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/harness/session/session.py` | Session & Message data models |
| `src/harness/session/manager.py` | Session CRUD, save/load |
| `src/harness/skills/loader.py` | Skill discovery & parsing |
| `src/harness/tools/registry.py` | Tool registration & execution |
| `src/harness/tools/schemas.py` | Tool parameter schemas |
| `src/harness/tools/builtin/file_ops.py` | read_file, write_file, edit_file |
| `src/harness/tools/builtin/shell.py` | run_command |
| `src/harness/tools/builtin/git_ops.py` | git status, diff, commit |
| `src/harness/tools/builtin/search.py` | glob, grep |
| `src/harness/tools/builtin/web.py` | fetch_url |
| `src/harness/mcp/manager.py` | Multiple MCP server management |
| `src/harness/chat/engine.py` | Conversation loop with tool execution |
| `src/harness/cli/repl.py` | Interactive CLI REPL |
| `src/harness/api/server.py` | REST API (FastAPI) |
| `skills/*/SKILL.md` | Built-in skills |

---

## Task 0: Dependencies & Config

**Files:**
- Modify: `pyproject.toml`
- Modify: `config/default.yaml`
- Modify: `src/harness/config.py`

- [ ] **Step 1: Add dependencies**

Add to `pyproject.toml` dependencies:
```toml
    "fastapi>=0.110.0",
    "uvicorn>=0.27.0",
```

- [ ] **Step 2: Add new config sections**

Append to `config/default.yaml`:
```yaml
session:
  storage_path: "sessions"
  auto_save: true
  max_history_tokens: 100000

skills:
  paths: ["skills/"]
  auto_load: true

mcp_servers: []

tools:
  enabled: [file_ops, shell, git, search, web]
  shell:
    allowed_commands: []
    blocked_commands: ["rm -rf /", "format"]
  file_ops:
    allowed_paths: ["."]
    blocked_paths: ["~/.ssh", "~/.env"]

api:
  enabled: false
  host: "0.0.0.0"
  port: 8000
```

- [ ] **Step 3: Update HarnessConfig**

Add to `HarnessConfig` in `config.py`:
```python
    # Session settings
    session_storage_path: str = "sessions"
    session_auto_save: bool = True
    session_max_history_tokens: int = 100000

    # Skills settings
    skills_paths: list[str] = field(default_factory=lambda: ["skills/"])
    skills_auto_load: bool = True

    # MCP servers
    mcp_servers: list[dict] = field(default_factory=list)

    # Tools settings
    tools_enabled: list[str] = field(default_factory=lambda: ["file_ops", "shell", "git", "search", "web"])

    # API settings
    api_enabled: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
```

- [ ] **Step 4: Install dependencies**

Run: `pip install -e ".[dev]"`

- [ ] **Step 5: Run existing tests**

Run: `pytest tests/ -q`
Expected: All 77 tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add .
git commit -m "feat(upgrade): add session/skills/tools config and dependencies"
```

---

## Task 1: Session System

**Files:**
- Create: `src/harness/session/__init__.py`
- Create: `src/harness/session/session.py`
- Create: `src/harness/session/manager.py`
- Create: `tests/unit/test_session.py`
- Create: `tests/unit/test_session_manager.py`

- [ ] **Step 1: Write session data model tests**

`tests/unit/test_session.py`:
```python
import pytest
from harness.session.session import Session, Message


class TestMessage:
    def test_create_user_message(self):
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.timestamp is not None

    def test_create_tool_message(self):
        msg = Message(role="tool", content="file contents", tool_call_id="tc-123")
        assert msg.tool_call_id == "tc-123"

    def test_to_dict(self):
        msg = Message(role="user", content="Hello")
        d = msg.to_dict()
        assert d["role"] == "user"
        assert d["content"] == "Hello"

    def test_from_dict(self):
        d = {"role": "user", "content": "Hello", "timestamp": "2026-01-01T00:00:00Z"}
        msg = Message.from_dict(d)
        assert msg.content == "Hello"


class TestSession:
    def test_create_session(self):
        session = Session()
        assert session.id is not None
        assert len(session.messages) == 0

    def test_add_messages(self):
        session = Session()
        session.add_user_message("Hello")
        session.add_assistant_message("Hi there!")
        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[1].role == "assistant"

    def test_add_tool_call_and_result(self):
        session = Session()
        session.add_user_message("Read file")
        session.add_assistant_message("", tool_calls=[{"id": "tc-1", "name": "read_file", "arguments": {"path": "test.py"}}])
        session.add_tool_result("tc-1", "file contents")
        assert len(session.messages) == 3
        assert session.messages[2].role == "tool"

    def test_to_dict_roundtrip(self):
        session = Session()
        session.add_user_message("Hello")
        session.add_assistant_message("Hi!")
        d = session.to_dict()
        restored = Session.from_dict(d)
        assert len(restored.messages) == 2
        assert restored.messages[0].content == "Hello"

    def test_auto_title(self):
        session = Session()
        session.add_user_message("Fix the DDP memory leak in training script")
        assert "DDP" in session.title or "memory" in session.title
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_session.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement session data model**

`src/harness/session/__init__.py`:
```python
"""Session management for multi-turn conversation."""
```

`src/harness/session/session.py`:
```python
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
        return [m.to_dict() for m in self.messages if m.role != "tool" or m.tool_call_id]

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_session.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Write session manager tests**

`tests/unit/test_session_manager.py`:
```python
import pytest
from harness.session.manager import SessionManager
from harness.session.session import Session


class TestSessionManager:
    def test_create_session(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        sid = mgr.create_session()
        assert sid is not None
        assert mgr.load_session(sid) is not None

    def test_save_and_load(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        session = Session()
        session.add_user_message("Hello")
        mgr.save_session(session)
        loaded = mgr.load_session(session.id)
        assert loaded.messages[0].content == "Hello"

    def test_list_sessions(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        mgr.create_session()
        mgr.create_session()
        sessions = mgr.list_sessions()
        assert len(sessions) == 2

    def test_delete_session(self, tmp_path):
        mgr = SessionManager(str(tmp_path))
        sid = mgr.create_session()
        mgr.delete_session(sid)
        assert mgr.load_session(sid) is None

    def test_auto_save(self, tmp_path):
        mgr = SessionManager(str(tmp_path), auto_save=True)
        session = Session()
        session.add_user_message("Test")
        mgr.save_session(session)
        loaded = mgr.load_session(session.id)
        assert loaded is not None
```

- [ ] **Step 6: Run tests to verify they fail**

Run: `pytest tests/unit/test_session_manager.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 7: Implement session manager**

`src/harness/session/manager.py`:
```python
"""Session persistence manager."""

import json
import logging
from pathlib import Path

from harness.session.session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages session CRUD operations and persistence."""

    def __init__(self, storage_path: str = "sessions", auto_save: bool = True):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._auto_save = auto_save

    def create_session(self) -> str:
        session = Session()
        self.save_session(session)
        return session.id

    def load_session(self, session_id: str) -> Session | None:
        file_path = self._path / f"{session_id}.json"
        if not file_path.exists():
            return None
        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            return Session.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def save_session(self, session: Session):
        file_path = self._path / f"{session.id}.json"
        file_path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")

    def list_sessions(self) -> list[dict]:
        sessions = []
        for file_path in self._path.glob("*.json"):
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                sessions.append({
                    "id": data["id"],
                    "title": data.get("title", ""),
                    "last_active": data.get("last_active", ""),
                    "message_count": len(data.get("messages", [])),
                })
            except Exception:
                continue
        sessions.sort(key=lambda s: s["last_active"], reverse=True)
        return sessions

    def delete_session(self, session_id: str):
        file_path = self._path / f"{session_id}.json"
        if file_path.exists():
            file_path.unlink()
```

- [ ] **Step 8: Run tests to verify they pass**

Run: `pytest tests/unit/test_session.py tests/unit/test_session_manager.py -v`
Expected: All 10 tests PASS.

- [ ] **Step 9: Commit**

```powershell
git add src/harness/session/ tests/unit/test_session.py tests/unit/test_session_manager.py
git commit -m "feat(upgrade): session system with persistence"
```

---

## Task 2: Skill Loader

**Files:**
- Create: `src/harness/skills/__init__.py`
- Create: `src/harness/skills/loader.py`
- Create: `tests/unit/test_skill_loader.py`
- Create: `skills/file-operations/SKILL.md`

- [ ] **Step 1: Write skill loader tests**

`tests/unit/test_skill_loader.py`:
```python
import pytest
from pathlib import Path
from harness.skills.loader import SkillLoader


class TestSkillLoader:
    def test_discover_skills(self, tmp_path):
        skill_dir = tmp_path / "file-operations"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: file-operations\ndescription: Read and write files\n---\n\n# File Operations\n\nUse read_file and write_file tools.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert len(skills) == 1
        assert skills[0]["name"] == "file-operations"

    def test_parse_frontmatter(self, tmp_path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test\ndescription: Test skill\nversion: 1.0.0\nmetadata:\n  tags: [test, demo]\n---\n\n# Test\n\nContent here.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert skills[0]["name"] == "test"
        assert "test" in skills[0]["tags"]

    def test_get_skill_content(self, tmp_path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: my-skill\ndescription: My skill\n---\n\n# My Skill\n\nDo this and that.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        loader.discover()
        content = loader.get_skill_content("my-skill")
        assert "Do this and that" in content

    def test_nested_skills(self, tmp_path):
        category = tmp_path / "software-development"
        category.mkdir()
        skill_dir = category / "tdd"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: tdd\ndescription: Test driven development\n---\n\n# TDD\n\nWrite tests first.",
            encoding="utf-8",
        )
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert len(skills) == 1
        assert skills[0]["name"] == "tdd"

    def test_empty_skills_dir(self, tmp_path):
        loader = SkillLoader([str(tmp_path)])
        skills = loader.discover()
        assert skills == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_skill_loader.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement skill loader**

`src/harness/skills/__init__.py`:
```python
"""Skills system for loading SKILL.md files."""
```

`src/harness/skills/loader.py`:
```python
"""Skill discovery and loading from SKILL.md files."""

import re
import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class SkillLoader:
    """Discovers and loads skills from SKILL.md files."""

    def __init__(self, skill_paths: list[str]):
        self._paths = [Path(p) for p in skill_paths]
        self._skills: dict[str, dict] = {}

    def discover(self) -> list[dict]:
        """Scan skill paths for SKILL.md files."""
        self._skills = {}
        for base_path in self._paths:
            if not base_path.exists():
                continue
            for skill_file in base_path.rglob("SKILL.md"):
                skill = self._parse_skill(skill_file)
                if skill:
                    self._skills[skill["name"]] = skill
        return list(self._skills.values())

    def _parse_skill(self, file_path: Path) -> dict | None:
        """Parse a SKILL.md file with YAML frontmatter."""
        try:
            text = file_path.read_text(encoding="utf-8")
            match = re.match(r"^---\n(.*?)\n---\n\n(.*)", text, re.DOTALL)
            if not match:
                return None

            frontmatter = yaml.safe_load(match.group(1))
            content = match.group(2)

            return {
                "name": frontmatter.get("name", file_path.parent.name),
                "description": frontmatter.get("description", ""),
                "version": frontmatter.get("version", "1.0.0"),
                "tags": frontmatter.get("metadata", {}).get("tags", []),
                "related_skills": frontmatter.get("metadata", {}).get("related_skills", []),
                "content": content,
                "path": str(file_path),
            }
        except Exception as e:
            logger.warning(f"Failed to parse skill {file_path}: {e}")
            return None

    def get_skill_content(self, name: str) -> str:
        """Get the markdown content of a skill by name."""
        skill = self._skills.get(name)
        return skill["content"] if skill else ""

    def get_skill(self, name: str) -> dict | None:
        """Get full skill info by name."""
        return self._skills.get(name)

    def get_all_skills(self) -> list[dict]:
        """Get all discovered skills (without content, for listing)."""
        return [
            {"name": s["name"], "description": s["description"], "tags": s["tags"]}
            for s in self._skills.values()
        ]

    def find_skills_for_task(self, task_description: str) -> list[dict]:
        """Find skills that might be relevant to a task."""
        task_lower = task_description.lower()
        matches = []
        for skill in self._skills.values():
            score = 0
            if any(tag in task_lower for tag in skill["tags"]):
                score += 2
            if any(word in skill["description"].lower() for word in task_lower.split()):
                score += 1
            if score > 0:
                matches.append((score, skill))
        matches.sort(key=lambda x: x[0], reverse=True)
        return [s for _, s in matches[:3]]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_skill_loader.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Create a built-in skill**

`skills/file-operations/SKILL.md`:
```markdown
---
name: file-operations
description: Read, write, and edit files in the workspace
version: 1.0.0
metadata:
  tags: [files, io, editing, read, write]
---

# File Operations

## When to Use
When the user asks to read, create, modify, or delete files.

## Available Tools
- `read_file(path)` — Read file contents
- `write_file(path, content)` — Write content to file
- `edit_file(path, old_string, new_string)` — Edit file using string replacement

## Instructions
- Always read a file before editing it
- Use absolute paths when possible
- When editing, include enough context in old_string to make the match unique
- After writing or editing, verify the change was applied
```

- [ ] **Step 6: Commit**

```powershell
git add src/harness/skills/ tests/unit/test_skill_loader.py skills/
git commit -m "feat(upgrade): skill loader with SKILL.md support"
```

---

## Task 3: Tool Registry & Built-in Tools

**Files:**
- Create: `src/harness/tools/__init__.py`
- Create: `src/harness/tools/registry.py`
- Create: `src/harness/tools/schemas.py`
- Create: `src/harness/tools/builtin/__init__.py`
- Create: `src/harness/tools/builtin/file_ops.py`
- Create: `src/harness/tools/builtin/shell.py`
- Create: `src/harness/tools/builtin/git_ops.py`
- Create: `src/harness/tools/builtin/search.py`
- Create: `src/harness/tools/builtin/web.py`
- Create: `tests/unit/test_tool_registry.py`
- Create: `tests/unit/test_file_ops.py`

- [ ] **Step 1: Write tool registry tests**

`tests/unit/test_tool_registry.py`:
```python
import pytest
from harness.tools.registry import ToolRegistry


class TestToolRegistry:
    def test_register_and_list(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"input": {"type": "string", "description": "Input text"}},
            handler=lambda params: f"Result: {params['input']}",
        )
        tools = registry.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_execute_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="add",
            description="Add two numbers",
            parameters={"a": {"type": "number"}, "b": {"type": "number"}},
            handler=lambda params: str(float(params["a"]) + float(params["b"])),
        )
        result = registry.execute("add", {"a": "2", "b": "3"})
        assert result == "5.0"

    def test_execute_unknown_tool(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Unknown tool"):
            registry.execute("nonexistent", {})

    def test_get_tools_for_prompt(self):
        registry = ToolRegistry()
        registry.register(
            name="read_file",
            description="Read a file",
            parameters={"path": {"type": "string"}},
            handler=lambda params: "content",
        )
        prompt = registry.get_tools_for_prompt()
        assert "read_file" in prompt
        assert "Read a file" in prompt

    def test_get_tools_as_openai_format(self):
        registry = ToolRegistry()
        registry.register(
            name="read_file",
            description="Read a file",
            parameters={"path": {"type": "string", "description": "File path"}},
            handler=lambda params: "content",
        )
        tools = registry.get_tools_as_openai()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "read_file"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement tool registry**

`src/harness/tools/__init__.py`:
```python
"""Tool system for built-in and MCP tools."""
```

`src/harness/tools/schemas.py`:
```python
"""Tool parameter schemas."""


def parameters_to_json_schema(parameters: dict) -> dict:
    """Convert simple parameter dict to JSON Schema format."""
    properties = {}
    required = []
    for name, spec in parameters.items():
        prop = {"type": spec.get("type", "string")}
        if "description" in spec:
            prop["description"] = spec["description"]
        if "enum" in spec:
            prop["enum"] = spec["enum"]
        properties[name] = prop
        if spec.get("required", False):
            required.append(name)
    return {
        "type": "object",
        "properties": properties,
        "required": required,
    }
```

`src/harness/tools/registry.py`:
```python
"""Central tool registry for built-in and MCP tools."""

import logging
from typing import Any, Callable
from dataclasses import dataclass, field

from harness.tools.schemas import parameters_to_json_schema

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable
    source: str = "builtin"  # "builtin" or "mcp"


class ToolRegistry:
    """Registers and executes tools from built-in sources and MCP servers."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, parameters: dict, handler: Callable, source: str = "builtin"):
        self._tools[name] = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
            source=source,
        )

    def get_all_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def get_tools_as_openai(self) -> list[dict]:
        """Get tools in OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": parameters_to_json_schema(t.parameters),
                },
            }
            for t in self._tools.values()
        ]

    def get_tools_for_prompt(self) -> str:
        """Get tool descriptions for system prompt injection."""
        lines = ["Available tools:"]
        for t in self._tools.values():
            params_desc = ", ".join(f"{k}: {v.get('type', 'string')}" for k, v in t.parameters.items())
            lines.append(f"- `{t.name}({params_desc})` — {t.description}")
        return "\n".join(lines)

    def execute(self, name: str, parameters: dict) -> str:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = tool.handler(parameters)
            return str(result) if result is not None else "Success"
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return f"Error: {e}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_tool_registry.py -v`
Expected: All 5 tests PASS.

- [ ] **Step 5: Implement built-in tools**

`src/harness/tools/builtin/__init__.py`:
```python
"""Built-in tools for file operations, shell, git, search, and web."""
```

`src/harness/tools/builtin/file_ops.py`:
```python
"""File operation tools: read_file, write_file, edit_file."""

import os
from pathlib import Path


def register_file_tools(registry, allowed_paths=None, blocked_paths=None):
    """Register file operation tools."""

    def read_file(params: dict) -> str:
        path = params["path"]
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        return p.read_text(encoding="utf-8")

    def write_file(params: dict) -> str:
        path = params["path"]
        content = params["content"]
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"File written: {path} ({len(content)} chars)"

    def edit_file(params: dict) -> str:
        path = params["path"]
        old_string = params["old_string"]
        new_string = params["new_string"]
        p = Path(path)
        if not p.exists():
            return f"Error: File not found: {path}"
        content = p.read_text(encoding="utf-8")
        if old_string not in content:
            return f"Error: old_string not found in {path}"
        count = content.count(old_string)
        if count > 1:
            return f"Error: old_string found {count} times in {path}. Provide more context."
        new_content = content.replace(old_string, new_string, 1)
        p.write_text(new_content, encoding="utf-8")
        return f"File edited: {path}"

    registry.register(
        name="read_file",
        description="Read the contents of a file",
        parameters={"path": {"type": "string", "description": "Absolute path to the file", "required": True}},
        handler=read_file,
    )
    registry.register(
        name="write_file",
        description="Write content to a file (creates parent directories)",
        parameters={
            "path": {"type": "string", "description": "Absolute path to the file", "required": True},
            "content": {"type": "string", "description": "Content to write", "required": True},
        },
        handler=write_file,
    )
    registry.register(
        name="edit_file",
        description="Edit a file by replacing old_string with new_string",
        parameters={
            "path": {"type": "string", "description": "Absolute path to the file", "required": True},
            "old_string": {"type": "string", "description": "String to replace (must be unique in file)", "required": True},
            "new_string": {"type": "string", "description": "Replacement string", "required": True},
        },
        handler=edit_file,
    )
```

`src/harness/tools/builtin/shell.py`:
```python
"""Shell command execution tool."""

import subprocess
import sys


def register_shell_tool(registry, blocked_commands=None):
    blocked = blocked_commands or []

    def run_command(params: dict) -> str:
        command = params["command"]
        workdir = params.get("workdir")
        timeout = int(params.get("timeout", 60))

        for blocked_cmd in blocked:
            if blocked_cmd in command:
                return f"Error: Command blocked: {blocked_cmd}"

        try:
            if sys.platform == "win32":
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=timeout, cwd=workdir,
                )
            else:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True,
                    timeout=timeout, cwd=workdir,
                )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output[:10000]  # Truncate large output
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {timeout}s"
        except Exception as e:
            return f"Error: {e}"

    registry.register(
        name="run_command",
        description="Run a shell command",
        parameters={
            "command": {"type": "string", "description": "Command to execute", "required": True},
            "workdir": {"type": "string", "description": "Working directory (optional)"},
            "timeout": {"type": "string", "description": "Timeout in seconds (default: 60)"},
        },
        handler=run_command,
    )
```

`src/harness/tools/builtin/git_ops.py`:
```python
"""Git operation tools."""

import subprocess


def _run_git(args: list[str], workdir: str = None) -> str:
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True,
            timeout=30, cwd=workdir,
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {e}"


def register_git_tools(registry):
    registry.register(
        name="git_status",
        description="Show git working tree status",
        parameters={"path": {"type": "string", "description": "Repository path (optional)"}},
        handler=lambda params: _run_git(["status", "--short"], params.get("path")),
    )
    registry.register(
        name="git_diff",
        description="Show git diff",
        parameters={
            "path": {"type": "string", "description": "File path (optional)"},
            "staged": {"type": "boolean", "description": "Show staged changes"},
        },
        handler=lambda params: _run_git(
            ["diff", "--staged" if params.get("staged") == "true" else "", params.get("path", "")],
            workdir=None,
        ),
    )
    registry.register(
        name="git_log",
        description="Show recent git log",
        parameters={"count": {"type": "string", "description": "Number of entries (default: 10)"}},
        handler=lambda params: _run_git(["log", f"--oneline", f"-{params.get('count', '10')}"]),
    )
```

`src/harness/tools/builtin/search.py`:
```python
"""File search tools: glob and grep."""

import os
import re
from pathlib import Path


def register_search_tools(registry):
    def glob_search(params: dict) -> str:
        pattern = params["pattern"]
        path = params.get("path", ".")
        base = Path(path)
        if not base.exists():
            return f"Error: Path not found: {path}"
        matches = list(base.glob(pattern))
        if not matches:
            return "No files found."
        return "\n".join(str(m) for m in matches[:100])

    def grep_search(params: dict) -> str:
        pattern = params["pattern"]
        path = params.get("path", ".")
        include = params.get("include")
        base = Path(path)
        if not base.exists():
            return f"Error: Path not found: {path}"

        results = []
        try:
            regex = re.compile(pattern)
        except re.error:
            return f"Error: Invalid regex pattern: {pattern}"

        glob_pattern = include if include else "**/*"
        for file_path in base.glob(glob_pattern):
            if not file_path.is_file():
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(content.split("\n"), 1):
                    if regex.search(line):
                        results.append(f"{file_path}:{i}: {line.strip()}")
                        if len(results) >= 50:
                            return "\n".join(results) + "\n...(truncated)"
            except Exception:
                continue

        return "\n".join(results) if results else "No matches found."

    registry.register(
        name="glob",
        description="Find files matching a glob pattern",
        parameters={
            "pattern": {"type": "string", "description": "Glob pattern (e.g., '**/*.py')", "required": True},
            "path": {"type": "string", "description": "Directory to search in (default: current)"},
        },
        handler=glob_search,
    )
    registry.register(
        name="grep",
        description="Search file contents using regex",
        parameters={
            "pattern": {"type": "string", "description": "Regex pattern to search for", "required": True},
            "path": {"type": "string", "description": "Directory to search in"},
            "include": {"type": "string", "description": "File pattern to include (e.g., '*.py')"},
        },
        handler=grep_search,
    )
```

`src/harness/tools/builtin/web.py`:
```python
"""Web fetch tool."""


def register_web_tool(registry):
    def fetch_url(params: dict) -> str:
        url = params["url"]
        format_type = params.get("format", "text")

        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(url, headers={"User-Agent": "CognitiveHarness/1.0"})
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8", errors="replace")

            if format_type == "text":
                # Simple HTML to text
                import re
                content = re.sub(r"<[^>]+>", " ", content)
                content = re.sub(r"\s+", " ", content).strip()

            return content[:20000]  # Truncate
        except Exception as e:
            return f"Error fetching {url}: {e}"

    registry.register(
        name="fetch_url",
        description="Fetch content from a URL",
        parameters={
            "url": {"type": "string", "description": "URL to fetch", "required": True},
            "format": {"type": "string", "description": "Output format: 'text' or 'html'", "enum": ["text", "html"]},
        },
        handler=fetch_url,
    )
```

- [ ] **Step 6: Write file_ops tests**

`tests/unit/test_file_ops.py`:
```python
import pytest
from harness.tools.registry import ToolRegistry
from harness.tools.builtin.file_ops import register_file_tools


class TestFileOps:
    @pytest.fixture
    def registry(self):
        reg = ToolRegistry()
        register_file_tools(reg)
        return reg

    def test_write_and_read_file(self, registry, tmp_path):
        path = str(tmp_path / "test.txt")
        registry.execute("write_file", {"path": path, "content": "Hello World"})
        result = registry.execute("read_file", {"path": path})
        assert result == "Hello World"

    def test_edit_file(self, registry, tmp_path):
        path = str(tmp_path / "test.py")
        registry.execute("write_file", {"path": path, "content": "def foo():\n    return 1"})
        registry.execute("edit_file", {"path": path, "old_string": "return 1", "new_string": "return 42"})
        result = registry.execute("read_file", {"path": path})
        assert "return 42" in result

    def test_read_nonexistent(self, registry):
        result = registry.execute("read_file", {"path": "/nonexistent/file.txt"})
        assert "Error" in result
```

- [ ] **Step 7: Run all tests**

Run: `pytest tests/unit/test_tool_registry.py tests/unit/test_file_ops.py -v`
Expected: All 8 tests PASS.

- [ ] **Step 8: Commit**

```powershell
git add src/harness/tools/ tests/unit/test_tool_registry.py tests/unit/test_file_ops.py
git commit -m "feat(upgrade): tool registry and built-in tools (file, shell, git, search, web)"
```

---

## Task 4: MCP Manager

**Files:**
- Create: `src/harness/mcp/__init__.py`
- Create: `src/harness/mcp/manager.py`
- Create: `tests/unit/test_mcp_manager.py`

- [ ] **Step 1: Write MCP manager tests**

`tests/unit/test_mcp_manager.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.mcp.manager import MCPManager


class TestMCPManager:
    def test_register_server(self):
        mgr = MCPManager()
        mgr.register_server("vault", "python", ["mcp_server/server.py"])
        assert "vault" in mgr.get_server_names()

    def test_get_tools_from_servers(self):
        mgr = MCPManager()
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value="result")
        mgr._clients["vault"] = mock_client
        mgr._server_tools["vault"] = [
            {"name": "vault_query", "description": "Query vault", "parameters": {}}
        ]
        tools = mgr.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "vault_query"
```

- [ ] **Step 2: Implement MCP manager**

`src/harness/mcp/__init__.py`:
```python
"""MCP server management."""
```

`src/harness/mcp/manager.py`:
```python
"""Multiple MCP server management."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list[str]
    env: dict | None = None
    auto_start: bool = True


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self):
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict = {}
        self._server_tools: dict[str, list[dict]] = {}

    def register_server(self, name: str, command: str, args: list[str], auto_start: bool = True, env: dict = None):
        self._configs[name] = MCPServerConfig(
            name=name, command=command, args=args, auto_start=auto_start, env=env,
        )

    def get_server_names(self) -> list[str]:
        return list(self._configs.keys())

    def get_all_tools(self) -> list[dict]:
        tools = []
        for server_name, server_tools in self._server_tools.items():
            for tool in server_tools:
                tools.append({**tool, "source": f"mcp:{server_name}"})
        return tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        for server_name, tools in self._server_tools.items():
            for tool in tools:
                if tool["name"] == name:
                    client = self._clients.get(server_name)
                    if client:
                        return await client.call_tool(name, arguments)
        raise ValueError(f"MCP tool not found: {name}")

    async def start_all(self):
        for name, config in self._configs.items():
            if config.auto_start:
                await self.start_server(name)

    async def start_server(self, name: str):
        # Uses existing MCPClient from harness.memory.mcp_client
        from harness.memory.mcp_client import MCPClient
        config = self._configs[name]
        client = MCPClient(
            server_path=config.command,
            vault_path="",
        )
        # Override with actual command
        client._server_path = config.command
        client._args = config.args
        try:
            await client.start()
            self._clients[name] = client
            # Discover tools from server
            tools = await client.call_tool("list_tools", {})
            self._server_tools[name] = tools if isinstance(tools, list) else []
            logger.info(f"Started MCP server: {name}")
        except Exception as e:
            logger.warning(f"Failed to start MCP server {name}: {e}")

    async def stop_all(self):
        for name, client in self._clients.items():
            try:
                await client.shutdown()
            except Exception:
                pass
        self._clients.clear()
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/unit/test_mcp_manager.py -v`
Expected: All 2 tests PASS.

- [ ] **Step 4: Commit**

```powershell
git add src/harness/mcp/ tests/unit/test_mcp_manager.py
git commit -m "feat(upgrade): MCP manager for multiple servers"
```

---

## Task 5: Chat Engine (Conversation Loop)

**Files:**
- Create: `src/harness/chat/__init__.py`
- Create: `src/harness/chat/engine.py`
- Create: `tests/unit/test_chat_engine.py`

- [ ] **Step 1: Write chat engine tests**

`tests/unit/test_chat_engine.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.chat.engine import ChatEngine
from harness.session.session import Session
from harness.tools.registry import ToolRegistry


@pytest.fixture
def engine():
    mock_llm = MagicMock()
    mock_llm.call_with_tools = AsyncMock()
    registry = ToolRegistry()
    registry.register(
        name="read_file",
        description="Read a file",
        parameters={"path": {"type": "string"}},
        handler=lambda params: f"Contents of {params['path']}",
    )
    return ChatEngine(llm=mock_llm, tool_registry=registry, session=Session())


class TestChatEngine:
    @pytest.mark.asyncio
    async def test_simple_text_response(self, engine):
        # LLM returns text (no tool calls)
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help?"
        mock_response.tool_calls = None
        engine._llm.call_with_tools = AsyncMock(return_value=mock_response)

        result = await engine.chat("Hello")
        assert result == "Hello! How can I help?"
        assert len(engine._session.messages) == 2  # user + assistant

    @pytest.mark.asyncio
    async def test_tool_call_then_response(self, engine):
        # First LLM call returns tool call
        tool_call = MagicMock()
        tool_call.id = "tc-1"
        tool_call.name = "read_file"
        tool_call.arguments = {"path": "test.py"}

        tool_response = MagicMock()
        tool_response.content = "Contents of test.py"
        tool_response.tool_calls = [tool_call]

        # Second LLM call returns text
        text_response = MagicMock()
        text_response.content = "I read the file."
        text_response.tool_calls = None

        engine._llm.call_with_tools = AsyncMock(side_effect=[tool_response, text_response])

        result = await engine.chat("Read test.py")
        assert result == "I read the file."
        # user, assistant(tool_call), tool, assistant(text)
        assert len(engine._session.messages) == 4

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, engine):
        tc1 = MagicMock()
        tc1.id = "tc-1"
        tc1.name = "read_file"
        tc1.arguments = {"path": "a.py"}

        tc2 = MagicMock()
        tc2.id = "tc-2"
        tc2.name = "read_file"
        tc2.arguments = {"path": "b.py"}

        tool_resp = MagicMock()
        tool_resp.content = ""
        tool_resp.tool_calls = [tc1, tc2]

        text_resp = MagicMock()
        text_resp.content = "Read both files."
        text_resp.tool_calls = None

        engine._llm.call_with_tools = AsyncMock(side_effect=[tool_resp, text_resp])

        result = await engine.chat("Read a.py and b.py")
        assert result == "Read both files."
```

- [ ] **Step 2: Implement chat engine**

`src/harness/chat/__init__.py`:
```python
"""Conversation engine with tool execution loop."""
```

`src/harness/chat/engine.py`:
```python
"""Conversation engine with multi-turn tool execution."""

import logging
from typing import Any

from harness.session.session import Session
from harness.tools.registry import ToolRegistry
from harness.skills.loader import SkillLoader

logger = logging.getLogger(__name__)


class ChatEngine:
    """Manages a conversation with tool execution loop."""

    def __init__(
        self,
        llm: Any,
        tool_registry: ToolRegistry,
        session: Session,
        skill_loader: SkillLoader | None = None,
        memory_context: str = "",
    ):
        self._llm = llm
        self._tools = tool_registry
        self._session = session
        self._skills = skill_loader
        self._memory_context = memory_context

    @property
    def session(self) -> Session:
        return self._session

    async def chat(self, message: str) -> str:
        """Process a user message with tool execution loop.

        Returns the assistant's final text response.
        """
        self._session.add_user_message(message)

        while True:
            # Build system prompt
            system = self._build_system_prompt()

            # Get messages for LLM
            messages = self._session.get_messages_for_llm()

            # Get tools in OpenAI format
            tools = self._tools.get_tools_as_openai()

            # Call LLM
            response = await self._llm.call_with_tools(
                system=system,
                messages=messages,
                tools=tools,
            )

            if response.tool_calls:
                # Add assistant message with tool calls
                tool_calls_data = [
                    {"id": tc.id, "name": tc.name, "arguments": tc.arguments}
                    for tc in response.tool_calls
                ]
                self._session.add_assistant_message(
                    response.content or "", tool_calls=tool_calls_data
                )

                # Execute each tool
                for tc in response.tool_calls:
                    try:
                        result = self._tools.execute(tc.name, tc.arguments)
                    except Exception as e:
                        result = f"Error: {e}"
                    self._session.add_tool_result(tc.id, result, name=tc.name)

                # Loop — LLM will see tool results
                continue
            else:
                # Text response — done
                self._session.add_assistant_message(response.content)
                return response.content

    def _build_system_prompt(self) -> str:
        """Build system prompt with skills and memory context."""
        parts = ["You are a helpful AI assistant with access to tools."]

        # Add skills context
        if self._skills:
            skill_list = self._skills.get_all_skills()
            if skill_list:
                parts.append("\n## Available Skills")
                for s in skill_list[:10]:
                    parts.append(f"- {s['name']}: {s['description']}")

                # Inject relevant skill content
                if self._session.messages:
                    last_user = [m for m in self._session.messages if m.role == "user"]
                    if last_user:
                        relevant = self._skills.find_skills_for_task(last_user[-1].content)
                        for skill in relevant[:1]:
                            content = self._skills.get_skill_content(skill["name"])
                            if content:
                                parts.append(f"\n## Skill: {skill['name']}\n{content[:2000]}")

        # Add memory context
        if self._memory_context:
            parts.append(f"\n## Memory Context\n{self._memory_context}")

        # Add tool descriptions
        parts.append(f"\n{self._tools.get_tools_for_prompt()}")

        return "\n".join(parts)
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/unit/test_chat_engine.py -v`
Expected: All 3 tests PASS.

- [ ] **Step 4: Commit**

```powershell
git add src/harness/chat/ tests/unit/test_chat_engine.py
git commit -m "feat(upgrade): chat engine with tool execution loop"
```

---

## Task 6: CLI REPL

**Files:**
- Create: `src/harness/cli/__init__.py`
- Create: `src/harness/cli/repl.py`

- [ ] **Step 1: Implement CLI REPL**

`src/harness/cli/__init__.py`:
```python
"""CLI interface."""
```

`src/harness/cli/repl.py`:
```python
"""Interactive CLI REPL for the harness."""

import asyncio
import sys


class HarnessREPL:
    """Interactive command-line interface."""

    def __init__(self, harness):
        self._harness = harness
        self._running = False

    async def run(self):
        """Start the REPL loop."""
        self._running = True
        print("Cognitive Harness v3 — Type '/help' for commands, '/exit' to quit.\n")

        while self._running:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                await self._handle_command(user_input)
            else:
                await self._handle_message(user_input)

    async def _handle_message(self, message: str):
        """Process a user message."""
        try:
            response = await self._harness.chat(message)
            print(f"\n{response}\n")
        except Exception as e:
            print(f"\nError: {e}\n")

    async def _handle_command(self, command: str):
        """Handle slash commands."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd == "/help":
            print("""
Commands:
  /sessions         List all sessions
  /resume <id>      Resume a session
  /new              Start a new session
  /skills           List available skills
  /tools            List available tools
  /clear            Clear current session
  /exit             Save and exit
""")
        elif cmd == "/sessions":
            sessions = await self._harness.list_sessions()
            if not sessions:
                print("No sessions found.")
            else:
                for s in sessions:
                    print(f"  {s['id']} | {s['title'][:40]} | {s['message_count']} msgs | {s['last_active'][:16]}")
        elif cmd == "/resume":
            if arg:
                await self._harness.resume_session(arg.strip())
                print(f"Resumed session {arg.strip()}")
            else:
                print("Usage: /resume <session-id>")
        elif cmd == "/new":
            sid = await self._harness.start_session()
            print(f"New session: {sid}")
        elif cmd == "/skills":
            skills = await self._harness.list_skills()
            for s in skills:
                print(f"  {s['name']}: {s['description']}")
        elif cmd == "/tools":
            tools = self._harness._tool_registry.get_all_tools()
            for t in tools:
                print(f"  {t['name']}: {t['description']}")
        elif cmd == "/clear":
            self._harness._session = Session()
            print("Session cleared.")
        elif cmd == "/exit":
            self._running = False
            print("Session saved. Goodbye!")
        else:
            print(f"Unknown command: {cmd}. Type /help for commands.")
```

- [ ] **Step 2: Commit**

```powershell
git add src/harness/cli/
git commit -m "feat(upgrade): CLI REPL with slash commands"
```

---

## Task 7: REST API

**Files:**
- Create: `src/harness/api/__init__.py`
- Create: `src/harness/api/server.py`

- [ ] **Step 1: Implement REST API**

`src/harness/api/__init__.py`:
```python
"""REST API interface."""
```

`src/harness/api/server.py`:
```python
"""REST API for the harness using FastAPI."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Cognitive Harness API", version="3.0.0")

# These get set by the harness startup
_harness = None


def set_harness(harness):
    global _harness
    _harness = harness


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    if request.session_id:
        await _harness.resume_session(request.session_id)
    response = await _harness.chat(request.message)
    return ChatResponse(response=response, session_id=_harness._session.id)


@app.get("/sessions")
async def list_sessions():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return await _harness.list_sessions()


@app.get("/sessions/{session_id}")
async def get_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    session = _harness._session_manager.load_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.post("/sessions/{session_id}/resume")
async def resume_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    await _harness.resume_session(session_id)
    return {"status": "resumed", "session_id": session_id}


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    _harness._session_manager.delete_session(session_id)
    return {"status": "deleted"}


@app.get("/skills")
async def list_skills():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return await _harness.list_skills()


@app.get("/tools")
async def list_tools():
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    return _harness._tool_registry.get_all_tools()


@app.post("/tools/{tool_name}/execute")
async def execute_tool(tool_name: str, parameters: dict = {}):
    if not _harness:
        raise HTTPException(status_code=503, detail="Harness not initialized")
    try:
        result = _harness._tool_registry.execute(tool_name, parameters)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 2: Commit**

```powershell
git add src/harness/api/
git commit -m "feat(upgrade): REST API with FastAPI"
```

---

## Task 8: Unified Harness Entry Point

**Files:**
- Modify: `src/harness/__init__.py`
- Create: `tests/integration/test_upgrade.py`

- [ ] **Step 1: Update CognitiveHarness**

`src/harness/__init__.py`:
```python
"""Cognitive LLM Harness — plugin-based reasoning engine."""

from harness.config import HarnessConfig, load_config
from harness.orchestrator import Orchestrator
from harness.session.session import Session
from harness.session.manager import SessionManager
from harness.skills.loader import SkillLoader
from harness.tools.registry import ToolRegistry
from harness.tools.builtin.file_ops import register_file_tools
from harness.tools.builtin.shell import register_shell_tool
from harness.tools.builtin.git_ops import register_git_tools
from harness.tools.builtin.search import register_search_tools
from harness.tools.builtin.web import register_web_tool
from harness.chat.engine import ChatEngine


class CognitiveHarness:
    """Main entry point for the cognitive harness.

    Usage:
        config = load_config("config/default.yaml")
        harness = CognitiveHarness(config)
        await harness.startup()

        session_id = await harness.start_session()
        result = await harness.chat("Fix the bug")
        result = await harness.chat("What about tests?")

        await harness.shutdown()
    """

    def __init__(self, config: HarnessConfig):
        self._config = config
        self._orchestrator = Orchestrator(config)
        self._session_manager = SessionManager(
            storage_path=config.session_storage_path,
            auto_save=config.session_auto_save,
        )
        self._skill_loader = SkillLoader(config.skills_paths)
        self._tool_registry = ToolRegistry()
        self._session: Session | None = None
        self._chat_engine: ChatEngine | None = None

    async def startup(self):
        """Initialize all subsystems."""
        # Load skills
        if self._config.skills_auto_load:
            self._skill_loader.discover()

        # Register built-in tools
        self._register_builtin_tools()

        # Start MCP servers
        if self._config.mcp_servers:
            for server in self._config.mcp_servers:
                self._orchestrator._mcp_client = None  # TODO: register in MCP manager

        # Start MCP client for vault if configured
        if self._config.vault_path:
            await self._orchestrator.start_mcp_client()

    async def shutdown(self):
        """Clean up resources."""
        await self._orchestrator.shutdown_mcp_client()

    def _register_builtin_tools(self):
        """Register all enabled built-in tools."""
        enabled = self._config.tools_enabled
        if "file_ops" in enabled:
            register_file_tools(self._tool_registry)
        if "shell" in enabled:
            register_shell_tool(self._tool_registry)
        if "git" in enabled:
            register_git_tools(self._tool_registry)
        if "search" in enabled:
            register_search_tools(self._tool_registry)
        if "web" in enabled:
            register_web_tool(self._tool_registry)

    async def start_session(self, session_id: str = None) -> str:
        """Start a new or resume existing session."""
        if session_id:
            self._session = self._session_manager.load_session(session_id)
            if not self._session:
                raise ValueError(f"Session not found: {session_id}")
        else:
            self._session = Session()
            self._session_manager.save_session(self._session)

        self._chat_engine = ChatEngine(
            llm=self._orchestrator.llm,
            tool_registry=self._tool_registry,
            session=self._session,
            skill_loader=self._skill_loader,
        )
        return self._session.id

    async def resume_session(self, session_id: str) -> str:
        """Resume an existing session."""
        return await self.start_session(session_id)

    async def chat(self, message: str) -> str:
        """Send a message and get a response."""
        if not self._chat_engine:
            await self.start_session()
        return await self._chat_engine.chat(message)

    async def list_sessions(self) -> list[dict]:
        return self._session_manager.list_sessions()

    async def list_skills(self) -> list[dict]:
        return self._skill_loader.get_all_skills()

    # Legacy v1/v2 interface
    async def invoke(self, prompt: str) -> str:
        """Legacy single-turn interface."""
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
```

- [ ] **Step 2: Write integration test**

`tests/integration/test_upgrade.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness import CognitiveHarness, load_config
from harness.session.session import Session


def test_session_roundtrip(tmp_path):
    from harness.session.manager import SessionManager
    mgr = SessionManager(str(tmp_path))
    session = Session()
    session.add_user_message("Hello")
    session.add_assistant_message("Hi!")
    mgr.save_session(session)
    loaded = mgr.load_session(session.id)
    assert loaded.messages[0].content == "Hello"


def test_skill_discovery(tmp_path):
    from harness.skills.loader import SkillLoader
    skill_dir = tmp_path / "test-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: test\ndescription: Test\n---\n\n# Test\n\nContent.",
        encoding="utf-8",
    )
    loader = SkillLoader([str(tmp_path)])
    skills = loader.discover()
    assert len(skills) == 1


def test_tool_registry():
    from harness.tools.registry import ToolRegistry
    from harness.tools.builtin.file_ops import register_file_tools
    reg = ToolRegistry()
    register_file_tools(reg)
    assert "read_file" in reg.get_tool_names()
    assert "write_file" in reg.get_tool_names()
```

- [ ] **Step 3: Run all tests**

Run: `pytest tests/ -v --tb=short`
Expected: All tests PASS.

- [ ] **Step 4: Commit**

```powershell
git add src/harness/__init__.py tests/integration/test_upgrade.py
git commit -m "feat(upgrade): unified harness with sessions, skills, tools"
```

---

## Summary

| Task | Component | Tests |
|------|-----------|-------|
| 0 | Dependencies & Config | existing tests pass |
| 1 | Session System | 10 unit tests |
| 2 | Skill Loader | 5 unit tests |
| 3 | Tool Registry + Built-in Tools | 8 unit tests |
| 4 | MCP Manager | 2 unit tests |
| 5 | Chat Engine | 3 unit tests |
| 6 | CLI REPL | manual test |
| 7 | REST API | manual test |
| 8 | Unified Entry Point | 3 integration tests |

**Total: 31 new tests + existing 77 = 108 tests**
