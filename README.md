# Cognitive Harness

**Cognitive Harness** is a plugin-based LLM reasoning engine designed to solve complex multi-step problems autonomously without getting stuck in unproductive reasoning loops. It introduces metacognitive loop recovery, evolutionary prompt optimization, and a hybrid persistent memory system to maintain productive reasoning over extended interactions.

## 🌟 Key Features

*   **Metacognitive Stuck Detector**: Identifies when the LLM is stalled (e.g., using hedging language or going in circles) using a zero-cost heuristic n-gram and regex pattern analyzer, preventing wasted tokens.
*   **Parallel Sub-Agent Recovery**: When the main agent gets stuck, it concurrently spawns multiple sub-agents, each with a distinct exploration strategy, to break out of the loop and find a viable path forward.
*   **Two-Tier Context Compaction**: Inspired by Lean-style proof compaction, it manages context window limits by summarizing the working buffer and condensing the entire reasoning history into structured, dense derivations.
*   **Evolutionary Prompt Optimization (EGPA)**: Self-improves its own system prompts using genetic algorithms. It tracks success rates, latency, and token efficiency, then applies LLM-driven mutation and crossover to discover higher-performing prompts.
*   **Hybrid Memory System**: Combines ChromaDB vector embeddings with a knowledge graph, fused via Reciprocal Rank Fusion (RRF), and exposed via the Model Context Protocol (MCP). It features cross-session global memory and an Obsidian-style vault.
*   **Modular Architecture**: Built on LangGraph, every component (Thinker, Stuck Detector, Compactor, etc.) is a plugin that can be easily replaced or extended.

## 🏗️ Architecture Overview

```text
User → Chat Engine ↔ LLM Client (LiteLLM)
         ↓ tool calls
   Tool Registry → Built-in Tools | MCP Tools
         ↓ reasoning loop
   LangGraph Orchestrator:
     Thinker → Stuck Detector → {Sub-Agent Spawner → Compactor} → Context Manager → [loop]
         ↓ memory
   Memory: Vault + KnowledgeGraph + ChromaDB
         ↓ optimization
   EGPA: Tracker → Optimizer → Evolution Engine
```

## 🚀 Quick Start

### Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Saptarshie/harnessOne.git
cd harnessOne
pip install -e .
```

### Starting the TUI (Terminal UI)

Cognitive Harness comes with a rich Terminal User Interface. Run the following command in any directory to start a new session (it will create a `.harness/` workspace in your current directory):

```bash
harness
```

**TUI Commands:**
*   `/sessions` - List all sessions
*   `/resume <id>` - Resume a specific session
*   `/skills` - List available skills
*   `/tools` - List available tools
*   `/history` - Show conversation history
*   `/clear` - Clear the current session
*   `/save` - Save the current session
*   `/exit` - Save and exit

### CLI Options

```bash
harness --resume abc-123         # Resume a previous session
harness --sessions               # List all sessions
harness --skills                 # List available skills
harness --tools                  # List available tools
harness --api                    # Start REST API server
harness --init                   # Initialize .harness/ workspace
```

## ⚙️ Configuration

When you run `harness`, a default `.harness/config.yaml` is generated. You can customize the LLM model, memory weights, and sub-agent counts here:

```yaml
llm:
  model: "openai/deepseek-v4-flash"
  max_tokens: 4096
  temperature: 0.7

harness:
  max_iterations: 5
  sub_agent_count: 3
  working_buffer_compact_threshold: 4000
  full_compaction_threshold: 12000

memory:
  vault_path: ".harness/vault"
  embedding_model: "Qwen/Qwen3-Embedding-0.6B"
  top_k: 5
  keyword_weight: 0.4
  embedding_weight: 0.6
```

Set your API key in the `.harness/.env` file:
```env
OPENAI_API_KEY=your-api-key
```

## 📂 Project Structure

*   `src/harness/` - Core reasoning engine and LangGraph orchestrator.
    *   `plugins/` - Modular nodes (`thinker.py`, `stuck_detector.py`, `sub_agent_spawner.py`, etc.).
    *   `memory/` - Global store, scratchpad, hybrid retriever, and writer.
    *   `improvement/` - EGPA framework (`tracker.py`, `optimizer.py`, `evolution.py`).
    *   `chat/` - Chat engine and streaming loop.
    *   `llm/` - LiteLLM abstraction layer.
*   `mcp_server/` - Standalone MCP server managing the Vault, Knowledge Graph, and ChromaDB.
*   `harness_tui.py` - Rich Terminal User Interface application.
*   `tests/` - Comprehensive test suite for end-to-end verification.

## 🧠 Example Use Cases

Cognitive Harness has been verified on complex multi-step reasoning problems, including:
1.  Solving complex mathematical and logical derivations.
2.  Code understanding and autonomous debugging of large repositories.
3.  Generating a complete, functional Flappy Bird game from scratch.

## 📄 License

This project is open-source. Please see the LICENSE file for details.
