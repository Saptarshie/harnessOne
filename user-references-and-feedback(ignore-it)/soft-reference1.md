This is a blueprint for a **Cognitive LLM Harness**—an architecture that moves beyond simple "prompt-and-response" and acts as a true reasoning engine. You are essentially describing a hybrid of **System 1 (Fast Intuition)**, **System 2 (Deliberate/Parallel Search)**, and a **Self-Optimizing Metacognitive Loop**.

Here is the complete, production-grade architecture for your harness, broken down into its core pillars, data flows, and technology stack.

---

### 🏛️ The High-Level Architecture: "The Cognitive Engine"

The harness operates on a **State Machine** paradigm (best implemented via LangGraph or a custom asynchronous DAG). It maintains a strict separation between the **Working Memory** (Context Window), the **Episodic Memory** (Scratchpad/Logs), and the **Semantic Memory** (Obsidian Vault).

#### The Core Data Flow (The "Checkpoint A $\rightarrow$ B" Cycle)

1. **Ingest & Plan:** Read prompt + Obsidian context $\rightarrow$ Generate Checkpoint A (Solid Foundation).
2. **Metacognition Check:** "Am I stuck?" (Confidence scoring / Entailment check).
3. **Exploration (Parallel):** Fork sub-agents to explore dead ends or parallel hypotheses.
4. **Compilation (The "Lean" Compactor):** Sub-agents return. A specialized Critic LLM extracts verified logical steps (Proof Compaction), discarding noise to create Checkpoint B.
5. **Context Surgery:** Replace raw exploration tokens with Checkpoint B. Context is now $A + B$.
6. **Memory Sync & Log:** Write new derivations to Obsidian; append trace to DSPy logs.

---

### 🏗️ Pillar 1: The Dynamic Thinking Engine (The Reasoning Loop)

This is the core loop that handles your "Checkpoint A to B" requirement. It uses a **Fork-Join State Graph**.

- **The "Stuck" Detector:** Instead of waiting for the model to output `<stuck>`, the harness uses a lightweight classifier (or a cheap LLM call) that evaluates the last $N$ tokens for looping behavior, contradiction, or low logit-confidence.
- **Parallel Sub-Agents (The Fork):** When stuck, the main thread pauses. The harness spawns 3 isolated sub-agents (using lightweight models or high-temp sampling). They are given the prompt: _"Here is Checkpoint A. Propose 3 distinct ways to overcome the current blocker."_
- **The "Lean" Compactor (The Join):** This is the most critical node. You cannot just summarize; you must _compile_.
  - _Mechanism:_ Use an LLM prompted with **Chain-of-Verification** or **Entailment Checking**.
  - _Prompt Logic:_ "Review the outputs of the 3 sub-agents. Extract ONLY the logical derivations that are mathematically/logically sound. Format them like a Lean/Mathlib proof: Premise $\rightarrow$ Step $\rightarrow$ Conclusion. Discard all conversational filler, failed attempts, and hallucinations. Output the 'Compiled Takeaway'."
  - _Result:_ The massive exploration tree is compressed into 4-5 dense, verified logical steps (Checkpoint B).
- **Context Rewriting:** The harness physically truncates the context window, appends Checkpoint B, and prompts the main LLM to resume.

### 🧠 Pillar 2: Obsidian MCP & Relational Memory System

Standard vector databases fail at logic ("X implies Y"). Your Obsidian Vault acts as a **Graph Database** powered by the **Model Context Protocol (MCP)**.

- **The Obsidian MCP Server:** You build a local MCP server that exposes your Vault to the LLM as a set of tools.
  - `query_graph(subject, relation, object)`: e.g., `(User_Preferences, implies, Python_Strict_Typing)`.
  - `get_derivation_tree(concept)`: Returns how concept D was derived from A, B, and C.
- **Write-Behind Memory Sync:** When the LLM compiles a brilliant "Checkpoint B" that represents a _universal truth_ or a _reusable heuristic_ (e.g., "When debugging CUDA out-of-memory, always check batch size before model weights"), the harness automatically triggers a tool: `write_obsidian_note(title, content, tags, links)`.
- **Semantic GraphRAG:** Before starting a prompt, the harness extracts keywords from the user prompt, queries the Obsidian MCP for relevant Markdown files, reads the YAML frontmatter, and injects the most relevant relational context into the system prompt.

### 🛠️ Pillar 3: Rigorous Telemetry & The "Glass Box" Logger

To enable self-improvement (DSPy/EGPA), the harness must generate **Execution Traces**, not just text logs.

- **Structured JSONL Logging:** Every node in the state graph logs a JSON object:
  ```json
  {
    "trace_id": "uuid-123",
    "node": "compactor",
    "input_tokens": 4500,
    "output_tokens": 120,
    "sub_agent_paths": ["path_1_failed", "path_2_success"],
    "human_feedback": null,
    "success_metric": 1
  }
  ```
- **The "Why" Tracker:** Whenever the LLM uses a tool (reads a file, runs a bash command), it must output a `<thought>` block explaining _why_ it is doing it. The harness parses this and links it to the tool execution in the logs.

### 🧬 Pillar 4: The Self-Improvement Engine (DSPy & EGPA)

This runs **asynchronously** in the background. It doesn't slow down the main harness; it analyzes the logs and optimizes the prompts for future runs.

- **DSPy (Declarative Self-Improving Python):**
  - You define your harness steps (Planner, Explorer, Compactor) as DSPy `Modules`.
  - You define a **Metric** (e.g., "Did the final code pass the unit tests?", "Was the context window kept under 8k tokens?").
  - _The Magic:_ DSPy's `BootstrapFewShot` or `MIPRO` optimizer reads your rigorous JSONL logs. It finds the traces where the "Lean Compactor" successfully compressed thoughts and led to a correct answer. It then **automatically rewrites the system prompts** and selects the best few-shot examples to inject into the Compactor node for future runs.
- **EGPA (Evolutionary/Genetic Prompt Adaptation):**
  - For highly complex prompts (like the "Stuck Detector" or the "Obsidian Graph Query" logic), you use an evolutionary algorithm.
  - The algorithm mutates the prompt instructions (e.g., changing "Extract key steps" to "Extract logically entailed proofs").
  - It runs these mutated prompts against a historical dataset of "Stuck" scenarios from your logs, keeping the "fittest" prompts that result in the highest success rate.

---

### 🔄 The Execution Lifecycle: A Single Prompt Walkthrough

Let's trace exactly what happens when you give this harness **one** prompt: _"Fix the memory leak in the distributed training script."_

1.  **Initialization (MCP & GraphRAG):**
    - Harness queries Obsidian MCP: "What do we know about distributed training memory leaks?"
    - Obsidian returns: `[[NCCL]] implies [[GPU_Memory_Fragmentation]]`.
    - Harness builds initial context: User Prompt + Obsidian facts.
2.  **Checkpoint A (Solid Grounding):**
    - LLM reads the script, identifies the model architecture, and sets up the distributed environment. (Context is clean).
3.  **The "Stuck" Phase:**
    - LLM tries to fix the leak by reducing batch size. It fails. It tries gradient checkpointing. It fails. It starts looping.
    - _Harness Intercepts:_ The Metacognition Node detects a loop. It pauses the main LLM.
4.  **Parallel Exploration (Sub-agents):**
    - Agent 1: Investigates CUDA cache clearing.
    - Agent 2: Investigates DDP (DistributedDataParallel) unused parameter buffers.
    - Agent 3: Investigates Tensor detachment.
5.  **The "Lean" Compaction (Checkpoint B):**
    - The Compactor Node receives the 3 agent logs.
    - It uses entailment checking: _Agent 1's fix failed. Agent 3 is irrelevant to DDP. Agent 2 found that `find_unused_parameters=True` leaves dangling tensors._
    - It compiles Checkpoint B: _"Derivation: DDP with unused parameters causes memory retention. Fix: Set `find_unused_parameters=False` and ensure all forward-pass tensors are used, or use `static_graph=True`."_
6.  **Context Surgery & Resumption:**
    - The harness deletes the 3000 tokens of failed Agent 1 and Agent 3 attempts.
    - It injects Checkpoint B. Context is now perfectly clean: Checkpoint A + Checkpoint B.
    - Main LLM resumes, applies the fix, and finishes the task.
7.  **Memory Sync & Logging:**
    - Harness writes to Obsidian: `DDP_Memory_Leaks.md` with the new derivation.
    - Harness saves the JSONL trace.
8.  **Background Optimization:**
    - Tonight, DSPy reads this trace, realizes the Compactor did a great job, and slightly tweaks the Compactor's prompt to make it even faster next time.

---

### 🧰 The Recommended Tech Stack

To build this today, you should not write everything from scratch. Use this stack:

| Component                    | Recommended Technology              | Why?                                                                                                                                                                                               |
| :--------------------------- | :---------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Orchestration / State**    | **LangGraph** (Python)              | Best-in-class for cyclic graphs, checkpointing, and human-in-the-loop state manipulation. Allows you to pause, edit state, and resume.                                                             |
| **Memory / Vault**           | **Obsidian** + **Local MCP Server** | Use the official `mcp` Python SDK to build a server that reads/writes to your local Obsidian vault via standard file I/O and `dataview` queries.                                                   |
| **Vector / Semantic Search** | **LlamaIndex** or **ChromaDB**      | Run locally alongside Obsidian to allow the MCP server to do semantic search over your markdown files.                                                                                             |
| **Self-Improvement**         | **DSPy**                            | The absolute standard for programmatic prompt optimization and metric-based LLM tuning.                                                                                                            |
| **Telemetry / Logging**      | **Arize Phoenix** or **LangSmith**  | Excellent for visualizing the exact token-level traces, context window bloat, and tool calls.                                                                                                      |
| **Sub-Agent Execution**      | **Asyncio + LiteLLM**               | Use Python's `asyncio` to spin up parallel sub-agents. Use `LiteLLM` to route these cheap/fast calls to local models (like Hermes/Llama-3-8B) or fast APIs (like Groq/Claude Haiku) to save money. |

### 🚀 How to start building this right now:

1.  **Step 1:** Set up a basic **LangGraph** state machine with two nodes: `Think` and `Evaluate`.
2.  **Step 2:** Implement the **Context Surgery** logic. Write a Python function that takes the LLM output, passes it to a second LLM prompt asking for "Lean-style logical compaction", and manually overrides the `messages` array in the LangGraph state before calling the LLM again.
3.  **Step 3:** Build the **Obsidian MCP Server**. Write a simple Python script using the `mcp` library that exposes a `search_vault` and `append_note` tool.
4.  **Step 4:** Once the harness works manually, wrap the node prompts in **DSPy** modules and define a success metric to let the system optimize itself.
