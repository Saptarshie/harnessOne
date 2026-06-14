# Cognitive LLM Harness — Design Specification

## 1. Overview

A plugin-based LLM reasoning harness that implements dynamic intelligent thinking: the LLM reasons until stuck, spawns parallel sub-agents to explore solutions, compacts their findings into verified logical checkpoints, and resumes — all while maintaining context discipline and structured logging for future self-improvement.

**Primary goal (v1):** Dynamic Thinking Engine + Config + Logging.
**Deferred:** Obsidian MCP memory (v2), DSPy/EGPA self-improvement (v3).

## 2. Architecture

### 2.1 Approach: Plugin Architecture with LangGraph Orchestration

Each reasoning step is a **plugin node** that registers with a central **Orchestrator** via a `@register_node("name")` decorator. The Orchestrator builds a LangGraph state graph from a YAML-defined topology and executes it.

### 2.2 Project Structure

```
harness/
├── pyproject.toml
├── config/
│   └── default.yaml
├── src/
│   └── harness/
│       ├── __init__.py
│       ├── config.py              # YAML config loader with validation
│       ├── orchestrator.py        # Plugin registry + LangGraph graph builder
│       ├── state.py               # Shared HarnessState TypedDict
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── base.py            # BaseNode ABC: process(state, llm) -> state
│       │   ├── thinker.py         # Main LLM reasoning node
│       │   ├── stuck_detector.py  # Metacognition: is the model stuck?
│       │   ├── sub_agent_spawner.py  # Fork parallel sub-agents
│       │   ├── compactor.py       # Lean-style compaction into checkpoints
│       │   └── context_manager.py # Context window management & surgery
│       ├── llm/
│       │   ├── __init__.py
│       │   └── client.py          # LiteLLM wrapper with retry/logging
│       └── logging/
│           ├── __init__.py
│           └── trace_logger.py    # Structured JSONL execution traces
├── tests/
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_thinker.py
│   │   ├── test_stuck_detector.py
│   │   ├── test_sub_agent_spawner.py
│   │   ├── test_compactor.py
│   │   ├── test_context_manager.py
│   │   └── test_llm_client.py
│   └── integration/
│       └── test_full_cycle.py
└── docs/
    └── superpowers/specs/
```

## 3. Core Data Flow

### 3.1 The Checkpoint Accumulation Model

Context is composed of **immutable checkpoints** + an **active working buffer**:

```
[Checkpoint A] + [Checkpoint B'] + [Checkpoint C'] + ... + [Working Buffer]
     locked          derived            derived              active
```

- **Checkpoint A**: Initial grounding (solid reasoning foundation). Never re-compacted.
- **Checkpoint B', C', ...**: Derived from sub-agent exploration. Each is a self-contained logical derivation that encodes its dependencies (e.g., "given A, we derived X, Y, Z"). Never re-compacted.
- **Working Buffer**: Active conversation — new observations, tool outputs, LLM responses. This is what gets compacted into checkpoints.

### 3.2 Two-Tier Compaction

**Tier 1 — Working buffer compaction:**
When `len(working_buffer) > working_buffer_compact_threshold`:
- Compact the working buffer into a new checkpoint
- Append checkpoint to the checkpoints list
- Clear working buffer (keep only the new checkpoint reference)

**Tier 2 — Full compaction:**
When `total_context_tokens > full_compaction_threshold`:
- Compact ALL checkpoints + working buffer into a single dense derivation
- Reset: `checkpoints = [dense_derivation]`, `working_buffer = []`
- Obsidian MCP (v2) preserves the full checkpoint history

### 3.3 State Machine Flow

```
                    ┌─────────────┐
                    │   START     │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
              ┌─────│   THINKER   │◄──────────────┐
              │     └──────┬──────┘               │
              │            │                      │
              │     ┌──────▼──────┐               │
              │     │STUCK_DETECT │               │
              │     └──────┬──────┘               │
              │            │                      │
              │     ┌──────┴──────┐               │
              │  [stuck]      [not stuck]         │
              │     │              │               │
              │  ┌──▼──────────┐  │               │
              │  │SUB_AGENT    │  │               │
              │  │SPAWN (N)    │  │               │
              │  └──┬──────────┘  │               │
              │     │              │               │
              │  ┌──▼──────────┐  │               │
              │  │COMPACTOR    │  │               │
              │  │(lean compact│  │               │
              │  └──┬──────────┘  │               │
              │     │              │               │
              │  ┌──▼──────────┐  │               │
              │  │CTX_MANAGE   │  │               │
              │  │(inject CP)  │  │               │
              │  └──┬──────────┘  │               │
              │     │              │               │
              │     │         ┌────▼─────┐        │
              │     │         │CTX_MANAGE│        │
              │     │         │(compact  │        │
              │     │         │ if needed│        │
              │     │         └────┬─────┘        │
              │     │              │               │
              │     │         ┌────▼─────┐        │
              │     │         │ITER_CHECK│        │
              │     │         └────┬─────┘        │
              │     │              │               │
              │     │         [under limit]        │
              │     │              │               │
              └─────┴──────────────┘               │
                                                  │
                                         [over limit or done]
                                                  │
                                           ┌──────▼──────┐
                                           │   FINISH    │
                                           └─────────────┘
```

**Edges (LangGraph):**
- `START → THINKER`
- `THINKER → STUCK_DETECT`
- `STUCK_DETECT → SUB_AGENT_SPAWN` (when stuck)
- `STUCK_DETECT → CTX_MANAGE_NOT_STUCK` (when not stuck)
- `SUB_AGENT_SPAWN → COMPACTOR`
- `COMPACTOR → CTX_MANAGE_STUCK` (inject new checkpoint)
- `CTX_MANAGE_STUCK → THINKER` (loop)
- `CTX_MANAGE_NOT_STUCK → ITER_CHECK`
- `ITER_CHECK → THINKER` (under max_iterations)
- `ITER_CHECK → FINISH` (over max_iterations or task complete)

**Termination conditions:**
- `is_stuck == False` and no pending work → finish (task complete)
- `iteration >= max_iterations` → finish (safety limit)
- All sub-agents fail → finish with error state

### 3.4 Abstraction: Single Entry Point

The entire harness is exposed as a single call:

```python
result = await harness.invoke("Fix the memory leak in the distributed training script")
```

The caller sees none of the internal machinery (checkpoints, sub-agents, compaction). The harness returns a clean final response.

## 4. Shared State

```python
class HarnessState(TypedDict):
    # Core conversation
    checkpoints: list[str]         # [A, B', C', ...] — immutable derived facts
    working_buffer: list[dict]     # Active messages (compacted into checkpoints)
    
    # Reasoning control
    is_stuck: bool                 # Stuck detector output
    sub_agent_results: list[dict]  # Raw sub-agent outputs
    current_response: str          # Latest LLM response
    
    # Execution metadata
    trace_id: str                  # UUID for this execution
    iteration: int                 # Current loop iteration
    max_iterations: int            # From config: recursion depth
    metadata: dict                 # Extensible plugin data
```

## 5. Plugin Interface

### 5.1 Base Node

```python
from abc import ABC, abstractmethod

class BaseNode(ABC):
    name: str
    
    @abstractmethod
    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Process state and return modified state."""
        ...
```

### 5.2 Plugin Registration

```python
@register_node("thinker")
class ThinkerNode(BaseNode):
    name = "thinker"
    
    async def process(self, state, llm):
        ...
```

The `Orchestrator` discovers all registered nodes and builds the LangGraph graph.

## 6. Core Plugins (v1)

### 6.1 ThinkerNode

**Purpose:** Main LLM reasoning call.

- Assembles context: all checkpoints + working buffer
- Calls LLM via `LLMClient`
- Appends response to working buffer
- Extracts `<thought>` blocks for trace logging

### 6.2 StuckDetectorNode

**Purpose:** Metacognitive check — is the model stuck?

**Heuristic approach (v1):**
- Check for repeated phrases/patterns in last N tokens
- Check for contradiction markers ("however", "but wait", "actually")
- Check for low-confidence hedging ("I'm not sure", "maybe", "let me try again")

**LLM approach (v2):**
- Lightweight LLM call: "Given this reasoning trace, is the model making progress or stuck?"

Returns `state.is_stuck = True/False`.

### 6.3 SubAgentSpawnerNode

**Purpose:** Fork N parallel sub-agents to explore solutions.

- Spawns N asyncio tasks (not processes — lightweight)
- Each sub-agent gets: Checkpoint A + current blocker description
- Sub-agents use the same `LLMClient` (same model for v1)
- Collects results into `state.sub_agent_results`
- Sub-agents have their own iteration limit (from config)

### 6.4 CompactorNode

**Purpose:** Lean-style compaction of sub-agent results into a verified checkpoint.

- Receives `state.sub_agent_results` (raw sub-agent outputs)
- LLM prompt (Chain-of-Verification style):
  ```
  Review the outputs of N sub-agents.
  Extract ONLY the logical derivations that are mathematically/logically sound.
  Format: Premise → Step → Conclusion.
  Discard all conversational filler, failed attempts, and hallucinations.
  Output the "Compiled Takeaway".
  ```
- Creates a new checkpoint string
- Appends to `state.checkpoints`
- Clears `state.sub_agent_results`

### 6.5 ContextManagerNode

**Purpose:** Context window management — compaction thresholds, token counting, context surgery.

- Checks working buffer size vs threshold → triggers Tier 1 compaction
- Checks total context size vs threshold → triggers Tier 2 compaction
- After compactor creates a checkpoint: trims working buffer, preserves checkpoint
- Token counting via `LLMClient.count_tokens()`

## 7. Configuration

### 7.1 `config/default.yaml`

```yaml
llm:
  model: "openai/gpt-4o"           # LiteLLM model string
  api_base: "https://api.openai.com/v1"
  api_key_env: "OPENAI_API_KEY"    # Env var name (never store key in file)
  max_tokens: 4096
  temperature: 0.7

harness:
  max_iterations: 5                # Max think→stuck→compact loops
  sub_agent_count: 3               # Parallel sub-agents to spawn
  sub_agent_max_iterations: 3      # Max iterations per sub-agent
  working_buffer_compact_threshold: 4000   # tokens
  full_compaction_threshold: 12000         # tokens
  stuck_detector: "heuristic"      # "heuristic" or "llm"

logging:
  level: "INFO"
  jsonl_path: "logs/traces.jsonl"
  enable_thought_tracking: true
```

### 7.2 Config Loader (`config.py`)

- Loads YAML with `pyyaml`
- Validates required fields
- Resolves API key from environment variable
- Supports config overrides via environment variables (e.g., `HARNESS_LLM_MODEL`)

## 8. LLM Client

### 8.1 `LLMClient` (`llm/client.py`)

```python
class LLMClient:
    def __init__(self, config: HarnessConfig): ...
    async def call(self, messages: list[dict], **kwargs) -> LLMResponse: ...
    def count_tokens(self, messages: list[dict]) -> int: ...
```

**Implementation:**
- Uses `litellm.acompletion()` for async calls
- Automatic retry with exponential backoff (3 retries, base delay 1s)
- Token counting via `litellm.token_counter()` or tiktoken fallback
- Every call logged to trace logger with token counts
- Returns `LLMResponse(content, usage, model, finish_reason)`

## 9. Logging & Telemetry

### 9.1 Structured JSONL Traces

Every plugin logs a trace entry after processing:

```json
{
  "trace_id": "uuid-123",
  "node": "compactor",
  "timestamp": "2026-06-13T10:30:00Z",
  "iteration": 2,
  "input_tokens": 4500,
  "output_tokens": 120,
  "checkpoint_created": "C'",
  "sub_agents_used": ["path_1_failed", "path_2_success"],
  "success": true,
  "duration_ms": 3200,
  "metadata": {}
}
```

### 9.2 Thought Tracking

When `enable_thought_tracking` is true, the ThinkerNode extracts `<thought>` blocks from LLM output and logs them separately. This enables future DSPy optimization of reasoning traces.

### 9.3 Log File Structure

```
logs/
├── traces.jsonl           # All execution traces (append-only)
└── runs/
    └── {trace_id}/
        ├── state_snapshot.json   # Final state
        └── checkpoints.json      # All checkpoints created
```

## 10. Error Handling

- **LLM call failures**: Retry 3x with exponential backoff. If all fail, log error and terminate with partial result.
- **Sub-agent failures**: If a sub-agent fails, log failure and continue with remaining sub-agents. If ALL sub-agents fail, return error state.
- **Config errors**: Fail fast on startup with clear error message.
- **Token limit exceeded**: Trigger emergency full compaction. If still over limit, truncate oldest checkpoints (with warning in logs).
- **Max iterations reached**: Return best-effort response with warning.

## 11. Testing Strategy

### 11.1 Build Order (test-as-you-go)

1. `config.py` → `test_config.py`
2. `llm/client.py` → `test_llm_client.py`
3. `state.py` (no tests needed — just a TypedDict)
4. `plugins/thinker.py` → `test_thinker.py`
5. `plugins/stuck_detector.py` → `test_stuck_detector.py`
6. `plugins/sub_agent_spawner.py` → `test_sub_agent_spawner.py`
7. `plugins/compactor.py` → `test_compactor.py`
8. `plugins/context_manager.py` → `test_context_manager.py`
9. `orchestrator.py` → integration tests
10. `logging/trace_logger.py` → tested as part of integration

### 11.2 Unit Tests

- Each plugin tested with mocked `LLMClient` that returns deterministic responses
- Test edge cases: empty state, max iterations, all sub-agents fail
- Use `pytest` with `pytest-asyncio` for async tests

### 11.3 Integration Tests

- Full `harness.invoke()` with real LLM calls
- Marked `@pytest.mark.integration` (skip in CI, run manually)
- Test the complete think→stuck→explore→compact→resume cycle

## 12. Dependencies

```toml
[project]
name = "cognitive-harness"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "litellm>=1.40.0",
    "langgraph>=0.2.0",
    "pyyaml>=6.0",
    "tiktoken>=0.7.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-mock>=3.12",
]
```

## 13. Deferred to v2

- **Obsidian MCP Server**: Graph queries, derivation trees, write-behind sync
- **Semantic GraphRAG**: Pre-prompt context injection from vault
- **Context surgery refinement**: Intelligent working buffer summarization

## 14. Deferred to v3

- **DSPy integration**: Module-based prompt optimization with metrics
- **EGPA**: Evolutionary prompt adaptation for stuck detector and compactor
- **Global memory & scratchpad**: Persistent cross-session memory
