v1 Core Engine (92 tests passing)

- Config, LLMClient (LiteLLM), HarnessState
- Plugin system (@register_node, BaseNode)
- TraceLogger (JSONL)
- 5 core plugins: Thinker, StuckDetector, SubAgentSpawner, Compactor, ContextManager
- Orchestrator with LangGraph graph
  v2 Obsidian Memory (25 tests)
- Vault (markdown + YAML frontmatter)
- KnowledgeGraph (triples, derivation trees)
- EmbeddingStore (ChromaDB + Qwen3-0.6B)
- MCP server (5 tools)
- HybridRetriever (keyword + embedding RRF)
- MemoryWriter, MemoryQueryNode plugins
  v3 Harness Upgrade (32 tests + live tested)
- Session system (JSON persistence)
- SkillLoader (SKILL.md discovery)
- ToolRegistry (OpenAI function calling)
- 10 built-in tools (file_ops, shell, git, search, web)
- ChatEngine with streaming + tool execution loop
- MCPManager (local stdio + remote SSE/streamable_http)
- CLI TUI with rich markdown rendering
- Context window size display
- CWD-based workspace (.harness/)
  File Structure
  harnssOne-1/
  ├── harness.py # Main CLI entry point
  ├── runner.py # Legacy runner
  ├── harness_cli.py # pip install entry point
  ├── pyproject.toml # Package config
  ├── config/
  │ ├── default.yaml # Default config
  │ └── global-mcp.yaml # Global MCP servers
  ├── src/harness/
  │ ├── **init**.py # CognitiveHarness
  │ ├── config.py # Config loading + global/local merge
  │ ├── orchestrator.py # LangGraph orchestrator
  │ ├── state.py # HarnessState TypedDict
  │ ├── llm/client.py # LLMClient (streaming + tools)
  │ ├── chat/engine.py # ChatEngine (streaming callback)
  │ ├── session/
  │ │ ├── session.py # Session + Message models
  │ │ └── manager.py # SessionManager (JSON)
  │ ├── skills/loader.py # SkillLoader
  │ ├── tools/
  │ │ ├── registry.py # ToolRegistry (sync+async)
  │ │ ├── schemas.py # JSON Schema converter
  │ │ └── builtin/ # 5 tool modules
  │ ├── mcp/
  │ │ ├── client.py # GenericMCPClient (stdio/SSE/HTTP)
  │ │ └── manager.py # MCPManager
  │ ├── plugins/ # 7 plugin modules
  │ ├── memory/ # MCP client, retriever, writer
  │ └── logging/ # TraceLogger
  ├── mcp_server/ # Vault MCP server
  ├── skills/ # Global skills
  ├── tests/ # 92 unit + 12 E2E + 2 real LLM
  └── sessions/ # Session storage
  Current Config

# Model

model: openai/deepseek-v4-flash
api_base: https://opencode.ai/zen/go/v1

# Workspace

.harness/ # Per-project workspace
├── sessions/ # Session JSON files
├── vault/ # Memory vault
├── skills/ # Project-specific skills
├── logs/ # Trace logs
└── config.yaml # Project config

# Global (repo)

config/global-mcp.yaml # Global MCP servers
skills/ # Global skills
MCP Support
Transport Status
stdio (local) Working
SSE Working
streamable_http Working
What's Left for v3

1. DSPy self-improvement — Prompt optimization
2. EGPA evolutionary prompts — Genetic algorithm for prompts
3. Global memory & scratchpad — Cross-session knowledge
4. Session branching — Fork sessions
5. Plugin hot-reload — Dynamic plugin loading
   Known Issues

- MCP shutdown throws asyncio cleanup warnings (cosmetic)
- PDF MCP server args need fixing in user's config
- Remote SSE endpoints may timeout on slow networks
  Test Commands

# Unit tests

python -m pytest tests/unit -x -q

# Integration

python -m pytest tests/integration -x -q

# Real LLM

python -m pytest tests/integration/test_real_llm.py -x -q

# Run harness

harness # Interactive
harness --sessions # List sessions
harness --tools # List tools
harness --mcp # List MCP
