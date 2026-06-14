# Harness Upgrade: Sessions, Skills, Tools & MCP — Design Specification

## 1. Overview

Upgrades the Cognitive Harness from a single-turn reasoning engine to a full-featured AI coding assistant with multi-turn conversation, persistent sessions, skills system, built-in tools, and external MCP server support.

**Key capabilities:**
- Multi-turn conversation with tool execution loop
- Session persistence (save/resume across disconnections)
- Skills system (hermes-agent compatible SKILL.md files)
- 6 built-in tools (file ops, shell, git, glob, grep, web fetch)
- External MCP server registration (config-based)
- LLM-driven tool selection (tool_use/function calling)
- CLI REPL + REST API interfaces

## 2. Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  CLI REPL    │  │  REST API    │  │  Programmatic    │  │
│  │  (terminal)  │  │  (FastAPI)   │  │  (Python SDK)    │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
└─────────┼─────────────────┼────────────────────┼────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Conversation Engine                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │  Session Mgr │  │  Chat Loop   │  │  Tool Executor   │  │
│  │  (save/load) │  │  (multi-turn)│  │  (tool_use loop) │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  Skills Mgr  │  │  Tool Reg    │  │  MCP Manager │
│  (SKILL.md)  │  │  (built-in)  │  │  (external)  │
└──────────────┘  └──────────────┘  └──────────────┘
```

### 2.2 New Files

```
src/harness/
├── session/
│   ├── __init__.py
│   ├── manager.py         # Session CRUD, save/load
│   └── session.py         # Session data model
├── skills/
│   ├── __init__.py
│   └── loader.py          # Skill discovery, parsing
├── tools/
│   ├── __init__.py
│   ├── registry.py        # Tool registry (built-in + MCP)
│   ├── builtin/
│   │   ├── __init__.py
│   │   ├── file_ops.py    # read_file, write_file, edit_file
│   │   ├── shell.py       # run_command
│   │   ├── git_ops.py     # git status, diff, commit, etc.
│   │   ├── search.py      # glob, grep
│   │   └── web.py         # fetch_url
│   └── schemas.py         # Tool parameter schemas
├── mcp/
│   ├── __init__.py
│   └── manager.py         # Multiple MCP server management
├── chat/
│   ├── __init__.py
│   └── engine.py          # Conversation loop with tool execution
├── api/
│   ├── __init__.py
│   └── server.py          # REST API (FastAPI)
├── cli/
│   ├── __init__.py
│   └── repl.py            # Interactive CLI REPL
skills/                     # Built-in skills (hermes-agent format)
├── file-operations/
│   └── SKILL.md
├── shell/
│   └── SKILL.md
├── git/
│   └── SKILL.md
├── software-development/
│   ├── test-driven-development/
│   │   └── SKILL.md
│   ├── writing-plans/
│   │   └── SKILL.md
│   └── systematic-debugging/
│       └── SKILL.md
├── research/
│   └── SKILL.md
└── creative/
    └── SKILL.md
sessions/                   # Session storage (auto-created)
├── {uuid}.json
└── ...
```

### 2.3 Config Additions

```yaml
# Session settings
session:
  storage_path: "sessions"
  auto_save: true
  max_history_tokens: 100000

# Skills settings
skills:
  paths: ["skills/", "~/.harness/skills/"]
  auto_load: true

# External MCP servers
mcp_servers:
  - name: vault
    command: python
    args: ["mcp_server/server.py", "--vault", "vault"]
    auto_start: true
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
    auto_start: false

# Built-in tools
tools:
  enabled:
    - file_ops
    - shell
    - git
    - search
    - web
  shell:
    allowed_commands: []  # Empty = all allowed
    blocked_commands: ["rm -rf /", "format"]
  file_ops:
    allowed_paths: ["."]
    blocked_paths: ["~/.ssh", "~/.env"]

# API settings
api:
  enabled: true
  host: "0.0.0.0"
  port: 8000
```

## 3. Session System

### 3.1 Session Data Model

```python
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: str
    tool_calls: list[ToolCall] | None
    tool_call_id: str | None

class Session:
    id: str
    created: str
    last_active: str
    title: str
    messages: list[Message]
    metadata: dict  # model, tokens, checkpoints, etc.
```

### 3.2 Session Storage

**File: `sessions/{uuid}.json`**

```json
{
  "id": "uuid-123",
  "created": "2026-06-14T10:00:00Z",
  "last_active": "2026-06-14T10:30:00Z",
  "title": "Fix DDP memory leak",
  "messages": [
    {"role": "user", "content": "Fix the DDP memory leak", "timestamp": "..."},
    {"role": "assistant", "content": "I'll analyze...", "timestamp": "...", "tool_calls": [...]},
    {"role": "tool", "name": "read_file", "content": "file contents...", "tool_call_id": "..."}
  ],
  "metadata": {
    "model": "openai/deepseek-v4-flash",
    "total_tokens": 1500
  }
}
```

### 3.3 Session Operations

- `create_session() -> session_id` — New session
- `load_session(id) -> Session` — Load existing
- `save_session(session)` — Persist to disk
- `list_sessions() -> list[dict]` — All sessions (id, title, last_active)
- `delete_session(id)` — Remove session
- `auto_save(session)` — Save after each turn

## 4. Skills System

### 4.1 Skill Format (hermes-agent compatible)

**File: `skills/{category}/{skill-name}/SKILL.md`**

```markdown
---
name: test-driven-development
description: "TDD: enforce RED-GREEN-REFACTOR, tests before code."
version: 1.1.0
metadata:
  tags: [testing, tdd, development]
  related_skills: [systematic-debugging]
---

# Test-Driven Development

## When to Use
- New features
- Bug fixes

## The Iron Law
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST

## Red-Green-Refactor Cycle
...
```

### 4.2 Skill Discovery

1. Scan `skills/` directories (configurable)
2. Find all `SKILL.md` files
3. Parse YAML frontmatter (name, description, tags)
4. Index by name and tags
5. Make available for LLM context injection

### 4.3 Skill Injection

When the LLM needs a skill:
1. Find skill by name or match description to task
2. Inject SKILL.md content into system prompt
3. LLM follows the skill instructions
4. LLM calls tools as directed by the skill

## 5. Tool System

### 5.1 Tool Registry

```python
class Tool:
    name: str
    description: str
    parameters: dict  # JSON Schema
    handler: Callable  # Async function

class ToolRegistry:
    def register(tool: Tool): ...
    def get_all() -> list[Tool]: ...        # For LLM tool_use
    def execute(name, params) -> str: ...   # Execute any tool
    def get_tools_for_prompt() -> str: ...  # Tool descriptions for system prompt
```

### 5.2 Built-in Tools

| Tool | Parameters | Description |
|------|-----------|-------------|
| `read_file` | `path: str` | Read file contents |
| `write_file` | `path: str, content: str` | Write to file |
| `edit_file` | `path: str, old_string: str, new_string: str` | Edit file |
| `run_command` | `command: str, workdir: str?` | Run shell command |
| `git_status` | `path: str?` | Git status |
| `git_diff` | `path: str?, staged: bool?` | Git diff |
| `git_commit` | `message: str, files: list?` | Git commit |
| `glob` | `pattern: str, path: str?` | Find files by pattern |
| `grep` | `pattern: str, path: str?, include: str?` | Search file contents |
| `fetch_url` | `url: str, format: str?` | Fetch web content |

### 5.3 Tool Execution Flow

```
LLM response with tool_calls
  ↓
For each tool_call:
  ├─ Is it a built-in tool? → Execute directly
  ├─ Is it an MCP tool? → Forward to MCP server
  └─ Is it unknown? → Return error
  ↓
Collect results
  ↓
Add tool results to conversation
  ↓
Call LLM again (loop until text response)
```

## 6. MCP Manager

### 6.1 Multiple MCP Server Support

```python
class MCPManager:
    def __init__(self, config): ...
    async def start_all(self): ...           # Start auto_start servers
    async def start_server(name): ...        # Start specific server
    async def stop_all(self): ...
    def get_tools() -> list[Tool]: ...       # All tools from all servers
    async def call_tool(name, params): ...   # Route to correct server
```

### 6.2 MCP Server Config

```yaml
mcp_servers:
  - name: vault
    command: python
    args: ["mcp_server/server.py"]
    auto_start: true
  - name: filesystem
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
    auto_start: false
    env:
      TOKEN: "${ENV_VAR}"  # Resolved from environment
```

## 7. Conversation Engine

### 7.1 Chat Loop

```python
class ChatEngine:
    async def chat(self, message: str) -> str:
        """Single conversation turn with tool execution loop."""
        self._session.add_user_message(message)
        
        while True:
            # Build prompt with skills + memory context
            system = self._build_system_prompt()
            messages = self._session.get_messages()
            tools = self._tool_registry.get_all()
            
            # Call LLM with tool definitions
            response = await self._llm.call_with_tools(
                system=system,
                messages=messages,
                tools=tools,
            )
            
            if response.tool_calls:
                # Execute tools
                self._session.add_assistant_message(
                    response.content, tool_calls=response.tool_calls
                )
                for tool_call in response.tool_calls:
                    result = await self._tool_registry.execute(
                        tool_call.name, tool_call.arguments
                    )
                    self._session.add_tool_result(tool_call.id, result)
                # Loop — LLM will see tool results and respond
            else:
                # Text response — done
                self._session.add_assistant_message(response.content)
                self._session_manager.save(self._session)
                return response.content
```

### 7.2 System Prompt Construction

```
You are a helpful AI assistant with access to tools.

## Available Skills
{skill_descriptions}

## Memory Context
{memory_context_from_vault}

## Instructions
- Use tools when needed to help the user
- Follow skill instructions when applicable
- Be concise and direct
```

## 8. CLI & API Interfaces

### 8.1 CLI REPL

```
$ harness chat
> Fix the DDP memory leak
[Harness reads files, analyzes, responds with fix]
> What files did you change?
[Harness lists changes]
> /sessions
Session: abc-123 | Fix DDP memory leak | 5 messages | 2 min ago
> /resume abc-123
Resumed session abc-123.
> /skills
Available skills: file-operations, shell, git, tdd, ...
> /exit
Session saved.
```

**Slash commands:**
- `/sessions` — List sessions
- `/resume <id>` — Resume session
- `/skills` — List skills
- `/tools` — List tools
- `/clear` — Clear current session
- `/exit` — Save and exit

### 8.2 REST API

```
POST   /chat                    — Send message, get response
GET    /sessions                — List sessions
GET    /sessions/:id            — Get session details
POST   /sessions/:id/resume     — Resume session
DELETE /sessions/:id            — Delete session
GET    /skills                  — List available skills
GET    /tools                   — List available tools
POST   /tools/:name/execute     — Execute tool directly
```

## 9. Testing Strategy

### 9.1 Unit Tests

- `test_session_manager.py` — Session CRUD, save/load, auto-save
- `test_session.py` — Session data model, message handling
- `test_skill_loader.py` — Skill discovery, frontmatter parsing
- `test_tool_registry.py` — Tool registration, execution routing
- `test_file_ops.py` — read_file, write_file, edit_file
- `test_shell.py` — run_command (mocked)
- `test_git_ops.py` — git operations (mocked)
- `test_search.py` — glob, grep
- `test_web.py` — fetch_url (mocked)
- `test_mcp_manager.py` — Multiple MCP server management
- `test_chat_engine.py` — Conversation loop with tool execution
- `test_cli_repl.py` — CLI commands
- `test_api.py` — REST API endpoints

### 9.2 Integration Tests

- `test_full_conversation.py` — Multi-turn with tools
- `test_session_resume.py` — Save and resume
- `test_skill_injection.py` — Skills loaded into prompt
- `test_mcp_integration.py` — External MCP tools

### 9.3 Build Order

1. Session system (manager + data model)
2. Skill loader
3. Tool registry
4. Built-in tools (file_ops, shell, git, search, web)
5. MCP manager
6. Chat engine (conversation loop)
7. CLI REPL
8. REST API
9. Integration tests

## 10. Dependencies

```toml
# New dependencies
"fastapi>=0.110.0",
"uvicorn>=0.27.0",
"readline; sys_platform == 'darwin'",
"pyreadline3; sys_platform == 'win32'",
```

## 11. Migration from v1/v2

The existing `CognitiveHarness.invoke()` continues to work. The new `ChatEngine` wraps it:

```python
# Old way (still works)
result = await harness.invoke("Fix the bug")

# New way (with sessions, tools, skills)
harness = await CognitiveHarness.create(config)
session_id = await harness.start_session()
result = await harness.chat("Fix the bug")
# ... later, resume
await harness.resume_session(session_id)
result = await harness.chat("What about the tests?")
```
