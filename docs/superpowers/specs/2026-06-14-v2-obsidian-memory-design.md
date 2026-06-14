# v2: Obsidian MCP Memory System — Design Specification

## 1. Overview

Adds a persistent knowledge graph memory system to the Cognitive Harness. An MCP server manages an Obsidian-style vault with markdown notes, wikilinks, and YAML frontmatter. The harness queries the vault for relevant context before each reasoning cycle and writes verified checkpoints back after compaction.

**Key capabilities:**
- Full knowledge graph with arbitrary relations (X implies Y, D derived from A,B,C)
- Hybrid retrieval: keyword extraction + local embedding search (Qwen3 0.6B int8)
- Write-behind sync: checkpoints written to vault on creation
- MCP protocol: standard tool interface, independently testable

## 2. Architecture

### 2.1 Component Overview

```
┌─────────────────────────────────────────────────┐
│                  Cognitive Harness               │
│                                                  │
│  ┌──────────┐  ┌─────────┐  ┌──────────────────┐│
│  │MemoryQuery│→│Thinker  │→│...→Compactor      ││
│  │  Node     │  │ Node    │  │                  ││
│  └────┬─────┘  └─────────┘  └────────┬─────────┘│
│       │                              │          │
│       │         ┌────────────────────▼─────────┐│
│       │         │     MemoryWriter Node        ││
│       │         └────────────────────┬─────────┘│
│       │                              │          │
└───────┼──────────────────────────────┼──────────┘
        │                              │
        ▼                              ▼
┌───────────────────────────────────────────────┐
│            MCP Server (stdio)                  │
│                                                │
│  Tools: query_graph, search_vault, write_note, │
│         add_relation, get_derivation_tree      │
│                                                │
│  ┌─────────────┐  ┌──────────────────────┐    │
│  │ Markdown    │  │ ChromaDB             │    │
│  │ Vault       │  │ (embeddings+metadata)│    │
│  └─────────────┘  └──────────────────────┘    │
└───────────────────────────────────────────────┘
```

### 2.2 New Files

```
src/harness/
├── memory/
│   ├── __init__.py
│   ├── mcp_client.py       # MCP client: start server, call tools
│   ├── retriever.py         # Hybrid retrieval: keyword + embedding
│   └── writer.py            # Write checkpoints and relations to vault
├── plugins/
│   ├── memory_query.py      # MemoryQueryNode plugin
│   └── memory_writer.py     # MemoryWriterNode plugin
mcp_server/
├── __init__.py
├── server.py                # MCP server entry point
├── vault.py                 # Vault read/write operations
├── graph.py                 # Knowledge graph (parse wikilinks, frontmatter)
└── embeddings.py            # ChromaDB + Qwen3 embedding management
```

### 2.3 Config Additions

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

## 3. MCP Server

### 3.1 Tools

| Tool | Input | Output | Description |
|------|-------|--------|-------------|
| `query_graph` | `subject?, relation?, object?` | List of triples | Query knowledge graph edges |
| `get_derivation_tree` | `concept: str` | Tree structure | How a concept was derived |
| `write_note` | `title, content, tags, links` | Success/fail | Create/update vault note |
| `add_relation` | `subject, relation, object` | Success/fail | Add graph edge |
| `search_vault` | `query, top_k` | Ranked snippets | Hybrid search |

### 3.2 Vault Structure

```
vault/
├── checkpoints/          # Verified reasoning checkpoints
│   └── {uuid}.md
├── derivations/          # Logical derivation chains
│   └── {uuid}.md
├── concepts/             # Knowledge graph nodes
│   └── {concept-slug}.md
└── .chromadb/            # Embedding index (auto-managed)
```

### 3.3 Note Format

```markdown
---
id: uuid-123
type: checkpoint | concept | derivation
created: 2026-06-14T10:30:00Z
tags: [memory-leak, ddp, pytorch]
links:
  - "[[concept-ddp]]"
  - "[[concept-memory-management]]"
relations:
  - subject: "DDP"
    relation: "implies"
    object: "GPU_Memory_Fragmentation"
---

# Checkpoint: DDP Memory Leak Fix

Premise: DDP with unused parameters causes memory retention.
Step: Set find_unused_parameters=False.
Conclusion: Use static_graph=True for fixed computation graphs.
```

### 3.4 Graph Storage

Relations are stored in frontmatter `relations` field:
```yaml
relations:
  - subject: "DDP"
    relation: "implies"
    object: "GPU_Memory_Fragmentation"
  - subject: "find_unused_parameters"
    relation: "fixes"
    object: "DDP_Memory_Leak"
```

The MCP server parses these fields to answer `query_graph` and `get_derivation_tree` calls.

## 4. Hybrid Retrieval System

### 4.1 Keyword Extraction

Lightweight LLM call (or regex-based for v1):
```
Extract 3-5 key technical concepts from: "{user_prompt}"
Output: comma-separated list
```

### 4.2 Embedding Search

- Model: Qwen3-Embedding-0.6B (int8 quantized)
- Runs locally via `sentence-transformers`
- ChromaDB stores embeddings + metadata
- Query: embed user prompt → search top-K similar notes

### 4.3 Result Fusion (RRF)

Reciprocal Rank Fusion merges keyword and embedding results:
```
RRF_score = sum(1 / (k + rank_i)) for each ranking
```

Where `k=60` (standard RRF constant). Results sorted by fused score.

### 4.4 Context Injection

Top-K results formatted as:
```
Relevant memory context:
- [checkpoint] DDP Memory Leak Fix: Premise: DDP with unused parameters...
- [concept] GPU Memory: CUDA caches should be cleared after each batch...
```

Injected into the system prompt before the ThinkerNode.

## 5. Plugin Integration

### 5.1 MemoryQueryNode

- Position: Before ThinkerNode in the graph
- Input: User prompt from working buffer
- Output: Enriched system prompt with vault context
- Calls: MCP `search_vault` + MCP `query_graph`

### 5.2 MemoryWriterNode

- Position: After CompactorNode in the graph
- Input: New checkpoint from compactor
- Output: Writes to vault via MCP
- Calls: MCP `write_note` + MCP `add_relation`

### 5.3 Updated Graph Flow

```
START → memory_query → thinker → stuck_detector →
  [stuck] → sub_agent_spawner → compactor → memory_writer → context_manager → loop/finish
  [not_stuck] → context_manager → loop/finish
```

## 6. MCP Client

### 6.1 Lifecycle

1. On `CognitiveHarness.__init__()`: start MCP server subprocess
2. On each tool call: send request via stdio, await response
3. On `harness.shutdown()`: send shutdown signal, wait for server exit

### 6.2 Error Handling

- Server crash: restart automatically (up to 3 retries)
- Tool call timeout: 10s default, configurable
- Connection lost: reconnect with backoff

### 6.3 Interface

```python
class MCPClient:
    async def start(self) -> None: ...
    async def call_tool(self, name: str, arguments: dict) -> Any: ...
    async def shutdown(self) -> None: ...
```

## 7. Testing Strategy

### 7.1 Unit Tests

- `test_vault.py`: Vault read/write, frontmatter parsing, wikilink extraction
- `test_graph.py`: Graph queries, derivation tree construction
- `test_retriever.py`: Keyword extraction, RRF fusion
- `test_mcp_client.py`: Mock MCP server, tool call/response
- `test_embeddings.py`: ChromaDB operations (mock embedding model)

### 7.2 Integration Tests

- `test_mcp_server.py`: Start real MCP server, call tools, verify vault files
- `test_memory_flow.py`: Full harness with memory (mock LLM, real MCP)

### 7.3 Build Order

1. Vault read/write (vault.py)
2. Graph operations (graph.py)
3. MCP server (server.py)
4. MCP client (mcp_client.py)
5. Embeddings (embeddings.py)
6. Retriever (retriever.py)
7. Writer (writer.py)
8. MemoryQueryNode plugin
9. MemoryWriterNode plugin
10. Orchestrator integration

## 8. Dependencies

```toml
# New dependencies for v2
"mcp>=1.0.0",
"sentence-transformers>=3.0.0",
"chromadb>=0.5.0",
```

## 9. Deferred to v3

- DSPy module-based prompt optimization
- EGPA evolutionary prompt adaptation
- Global memory & scratchpad (cross-session)
- Derivation tree visualization
