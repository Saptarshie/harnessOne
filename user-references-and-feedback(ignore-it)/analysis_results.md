# Cognitive Harness — Blueprint vs Implementation Audit

Audit of [soft-reference1.md](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/references/soft-reference1.md) against the actual codebase.

---

## Scorecard

| Blueprint Area | Status | Notes |
|:---|:---:|:---|
| **Pillar 1** — Dynamic Thinking Engine | ✅ Implemented | All core nodes present & wired |
| **Pillar 2** — Obsidian MCP & Relational Memory | ✅ Implemented | MCP server, graph, vault, hybrid retrieval |
| **Pillar 3** — Rigorous Telemetry | ⚠️ Partial | `TraceLogger` exists but is **not wired** into the live graph |
| **Pillar 4** — Self-Improvement Engine (DSPy/EGPA) | ❌ Not Implemented | Explicitly deferred; only reference material exists |

---

## Pillar 1: The Dynamic Thinking Engine (The Reasoning Loop)

> *Blueprint: Fork-Join State Graph with checkpoints, stuck detection, parallel sub-agents, Lean compaction, and context surgery.*

### ✅ State Machine / LangGraph Orchestration

- [orchestrator.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/orchestrator.py) builds the LangGraph `StateGraph` exactly as described:

```
START → [memory_query] → thinker → stuck_detector → {stuck/not_stuck}
  stuck:     sub_agent_spawner → compactor → [memory_writer] → context_manager → loop
  not_stuck: context_manager → {continue/finish}
```

- The graph uses `add_conditional_edges` for both the stuck-router and the continue-router — correct fork-join topology.

### ✅ The "Stuck" Detector

| Blueprint Requirement | Implementation | Verdict |
|:---|:---|:---:|
| Detect looping/repetition | [stuck_detector.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/stuck_detector.py) — `_has_repeated_phrases()`: 4-gram counter across last 5 messages, triggers at count ≥ 3 | ✅ |
| Detect hedging / low confidence | `_has_excessive_hedging()`: regex patterns like "I'm not sure", "going in circles", etc. Triggers at 2+ matches | ✅ |
| Lightweight heuristic (not full LLM call) | Pure heuristic — no LLM call, just regex + counting | ✅ |

> [!NOTE]
> The blueprint also mentions using "logit-confidence" for detection. The implementation uses a simpler heuristic approach, which is a reasonable pragmatic choice, but doesn't inspect raw logits.

### ✅ Parallel Sub-Agents (The Fork)

[sub_agent_spawner.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/sub_agent_spawner.py):

- Spawns **3 isolated sub-agents** via `asyncio.gather` (configurable via `sub_agent_count`)
- Each sub-agent gets the checkpoint context + blocker description
- Each is assigned a **distinct approach** (cache clearing / unused params / circular refs)
- Failures are caught per-agent without blocking others

### ✅ The "Lean" Compactor (The Join)

[compactor.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/compactor.py):

- Receives sub-agent outputs, filters for successes only
- Uses a **dedicated LLM call** with the "proof compactor" persona
- Prompt explicitly asks for: `Premise → Step → Conclusion` format
- Instructs to "discard conversational filler, failed attempts, hallucinations"
- Result is appended as a new checkpoint

> [!TIP]
> This closely matches the blueprint's "Chain-of-Verification / Entailment Checking" concept, though it relies on prompt instruction rather than a formal entailment model.

### ✅ Context Surgery (Context Rewriting)

[context_manager.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/context_manager.py):

- **Two-tier compaction** as described:
  - **Tier 1**: Working buffer → checkpoint (threshold: 4000 tokens)
  - **Tier 2**: Full compaction — all checkpoints + buffer → single derivation (threshold: 12000 tokens)
- After compaction, the working buffer is **physically truncated** and replaced with a clean continuation prompt
- Checkpoints accumulate: A + B' + C' pattern exactly as the blueprint describes

### ✅ Checkpoint A → B Cycle

[thinker.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/thinker.py):

- Assembles context from `checkpoints` (system messages) + `working_buffer` (conversation)
- Extracts `<thought>` blocks for metacognition tracking
- Clean separation between checkpoint context and working conversation

### ✅ Shared State

[state.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/state.py):

- `HarnessState` TypedDict with: `checkpoints`, `working_buffer`, `is_stuck`, `sub_agent_results`, `current_response`, `trace_id`, `iteration`, `max_iterations`, `metadata`
- Clean, well-structured state that flows through the entire graph

---

## Pillar 2: Obsidian MCP & Relational Memory System

> *Blueprint: Graph database via MCP, semantic search, write-behind memory sync.*

### ✅ MCP Server

[server.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/mcp_server/server.py) exposes all 5 tools described in the blueprint:

| Blueprint Tool | MCP Tool | Status |
|:---|:---|:---:|
| `query_graph(subject, relation, object)` | `query_graph` | ✅ |
| `get_derivation_tree(concept)` | `get_derivation_tree` | ✅ |
| `write_obsidian_note(title, content, tags, links)` | `write_note` | ✅ |
| `add_relation(subject, relation, object)` | `add_relation` | ✅ |
| Semantic search | `search_vault` | ✅ |

### ✅ Vault as Graph Database

[vault.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/mcp_server/vault.py):

- Obsidian-style markdown files with **YAML frontmatter** (id, type, created, tags, links, relations)
- Organized into subdirectories: `checkpoints/`, `derivations/`, `concepts/`
- `[[wiki-links]]` in frontmatter for inter-note linking

[graph.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/mcp_server/graph.py):

- In-memory **triple store** (`subject → relation → object`)
- Rebuilds index from vault on startup
- `query()` supports filtering by any combination of subject/relation/object
- `get_derivation_tree()` with recursive depth traversal — exactly as the blueprint specifies

### ✅ Semantic GraphRAG (Hybrid Retrieval)

[retriever.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/memory/retriever.py):

- **Hybrid retrieval**: keyword extraction + embedding search
- **RRF (Reciprocal Rank Fusion)** to merge results with configurable weights (keyword: 0.4, embedding: 0.6)
- Keywords extracted → graph queries; embeddings → ChromaDB vector search
- Parallel execution via `asyncio.create_task`

[embeddings.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/mcp_server/embeddings.py):

- **ChromaDB** persistent client with cosine similarity
- Supports local embedding model via `sentence-transformers` (default: `Qwen/Qwen3-Embedding-0.6B`)
- Falls back to ChromaDB's built-in embeddings if model unavailable

### ✅ Write-Behind Memory Sync

[memory_writer_node.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/memory_writer_node.py):

- Integrated as a graph node: fires **after compaction**, before context management
- Writes new checkpoints to the vault via MCP (`write_note`)
- Tracks `_last_checkpoint_count` to only write genuinely new checkpoints

[memory_query.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/memory_query.py):

- Runs at graph entry point: queries vault **before** the thinker node
- Injects relevant memory context as a system message in the working buffer

### ✅ MCP Client

[memory/__init__.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/memory/__init__.py):

- Connects to the MCP server via stdio
- Proper lifecycle management (start/shutdown)
- JSON result parsing with fallback

---

## Pillar 3: Rigorous Telemetry & The "Glass Box" Logger

> *Blueprint: Structured JSONL logging, execution traces, "Why" tracker.*

### ⚠️ TraceLogger — Exists But Not Wired

[trace_logger.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/logging/trace_logger.py):

| Feature | Implementation | Status |
|:---|:---|:---:|
| Structured JSONL | ✅ Appends JSON objects with `trace_id`, `node`, `timestamp`, `iteration`, `input_tokens`, `output_tokens`, `success`, `duration_ms` | ✅ Built |
| Arbitrary metadata (`**metadata`) | ✅ Supports `sub_agent_paths`, `human_feedback`, `success_metric`, etc. | ✅ Built |
| Timer for duration tracking | ✅ `start_timer()` + auto-duration calculation | ✅ Built |
| Flush to disk | ✅ Buffered writes with `flush()` | ✅ Built |

> [!WARNING]
> **Critical Gap**: The `TraceLogger` is defined and tested (77 tests pass), but it is **not imported or used** anywhere in the live orchestrator, plugins, or chat engine. The JSONL schema exactly matches the blueprint, but no actual traces are being written during execution.

### ⚠️ "Why" Tracker

[thinker.py](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/src/harness/plugins/thinker.py#L69-L72):

- `_extract_thought()` parses `<thought>` tags from LLM output
- Extracted thoughts are stored in `state.metadata["last_thought"]`

> [!NOTE]
> The extraction exists but the `<thought>` block is not systematically enforced in prompts. The LLM isn't explicitly instructed to emit `<thought>` blocks explaining tool usage rationale. The tracking is passive, not active.

---

## Pillar 4: The Self-Improvement Engine (DSPy & EGPA)

> *Blueprint: DSPy modules for automatic prompt optimization, EGPA for evolutionary prompt mutation.*

### ❌ Not Implemented

This is **explicitly deferred** as documented in:
- [whats-done-till-v1.txt](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/references/whats-done-till-v1.txt#L41): *"DSPy/EGPA self-improvement"* listed under "What's deferred to v2/v3"
- [2026-06-14-cognitive-llm-harness-design.md](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/docs/superpowers/specs/2026-06-14-cognitive-llm-harness-design.md): *"Deferred: DSPy/EGPA self-improvement (v3)"*

| Blueprint Requirement | Status |
|:---|:---:|
| DSPy Modules wrapping Planner/Explorer/Compactor | ❌ |
| Success metrics ("Did code pass tests?", "Context under 8k?") | ❌ |
| `BootstrapFewShot` / `MIPRO` optimizer consuming JSONL logs | ❌ |
| Automatic prompt rewriting for future runs | ❌ |
| EGPA evolutionary prompt mutation | ❌ |

> [!IMPORTANT]
> A reference DSPy SKILL.md exists at [references/skills/mlops/research/dspy/SKILL.md](file:///d:/prac_prog/fun/hernessOne/harnssOne-1/references/skills/mlops/research/dspy/SKILL.md), but this is documentation/research material only — no integration code exists.

---

## Execution Lifecycle Verification

The blueprint provides a detailed walkthrough of a single prompt. Let me trace it against the code:

| Lifecycle Step | Blueprint | Code Path | Status |
|:---|:---|:---|:---:|
| 1. **Initialization (MCP & GraphRAG)** | Query Obsidian MCP for relevant context | `memory_query` node → `Retriever.retrieve()` → hybrid search | ✅ |
| 2. **Checkpoint A** | LLM reads context, sets up foundation | `thinker` node → `_assemble_context()` → LLM call | ✅ |
| 3. **"Stuck" Phase** | Harness detects looping | `stuck_detector` node → hedging + repetition checks | ✅ |
| 4. **Parallel Exploration** | 3 sub-agents explore distinct paths | `sub_agent_spawner` → `asyncio.gather` with 3 agents | ✅ |
| 5. **Lean Compaction → Checkpoint B** | Compile verified derivations | `compactor` → LLM with "proof compactor" prompt | ✅ |
| 6. **Context Surgery** | Truncate exploration, inject checkpoint | `context_manager` → truncate buffer, append checkpoint | ✅ |
| 7. **Memory Sync & Logging** | Write to vault + JSONL trace | `memory_writer` → vault ✅ / JSONL trace ⚠️ **not wired** | ⚠️ |
| 8. **Background Optimization** | DSPy reads traces, tweaks prompts | Not implemented | ❌ |

---

## Tech Stack Verification

| Blueprint Component | Recommended | Actual | Match? |
|:---|:---|:---|:---:|
| **Orchestration** | LangGraph | LangGraph (`StateGraph`) | ✅ |
| **Memory / Vault** | Obsidian + Local MCP Server | Markdown vault + MCP Server via `mcp` SDK | ✅ |
| **Vector Search** | LlamaIndex or ChromaDB | ChromaDB (`PersistentClient`) | ✅ |
| **Self-Improvement** | DSPy | Not implemented | ❌ |
| **Telemetry** | Arize Phoenix or LangSmith | Custom `TraceLogger` (JSONL) — simpler but functional schema | ⚠️ |
| **Sub-Agent Execution** | Asyncio + LiteLLM | Asyncio + LiteLLM | ✅ |

---

## Summary of Gaps

### High Priority
1. **TraceLogger not wired**: The logger infrastructure is ready but no plugin/orchestrator calls it. This blocks all downstream work (DSPy, telemetry dashboards, debugging).
2. **DSPy/EGPA entirely missing**: The entire self-improvement loop (Pillar 4) has no code beyond reference material.

### Medium Priority
3. **`<thought>` tracking is passive**: The thinker extracts thoughts but doesn't instruct the LLM to produce them, and doesn't log them to the JSONL trace.
4. **No external telemetry integration**: No Arize Phoenix, LangSmith, or similar. The custom logger is simpler than the blueprint envisions.

### Low Priority
5. **Stuck detector doesn't use logit confidence**: Uses heuristic regex only — reasonable but less capable than the blueprint's "lightweight classifier" suggestion.
6. **Sub-agent approaches are hardcoded**: The 3 approach prompts are static strings, not dynamically generated based on the problem domain.
