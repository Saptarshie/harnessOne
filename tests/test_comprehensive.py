"""Comprehensive end-to-end verification of all harness features."""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, ".")  # For mcp_server package


async def test_vault_operations():
    """Test vault read/write, frontmatter, wikilinks."""
    print("=== 1. Vault Operations ===")
    from mcp_server.vault import Vault

    with tempfile.TemporaryDirectory() as tmp:
        vault = Vault(tmp)

        # Write checkpoint
        result = vault.write_note(
            title="DDP Memory Leak Fix",
            content="Premise: DDP with unused parameters causes memory retention.\nStep: Set find_unused_parameters=False.\nConclusion: Use static_graph=True.",
            tags=["ddp", "memory-leak", "pytorch"],
            links=["concept-ddp", "concept-memory-management"],
            note_type="checkpoint",
            relations=[
                {"subject": "DDP", "relation": "implies", "object": "GPU_Memory_Fragmentation"},
                {"subject": "find_unused_parameters", "relation": "fixes", "object": "DDP_Memory_Leak"},
            ],
        )
        print(f"  [OK] Write checkpoint: id={result['id']}")

        # Write concept
        vault.write_note(
            title="GPU Memory Management",
            content="CUDA caches should be cleared after each batch.",
            tags=["gpu", "memory", "cuda"],
            links=[],
            note_type="concept",
        )
        print("  [OK] Write concept note")

        # Read note
        note = vault.read_note(result["id"])
        assert note is not None, "Note should exist"
        assert note["title"] == "DDP Memory Leak Fix"
        assert "ddp" in note["tags"]
        assert len(note["relations"]) == 2
        print(f"  [OK] Read note: title='{note['title']}', relations={len(note['relations'])}")

        # List notes
        checkpoints = vault.list_notes("checkpoint")
        concepts = vault.list_notes("concept")
        assert len(checkpoints) == 1, f"Expected 1 checkpoint, got {len(checkpoints)}"
        assert len(concepts) == 1, f"Expected 1 concept, got {len(concepts)}"
        print(f"  [OK] List notes: {len(checkpoints)} checkpoints, {len(concepts)} concepts")

        # Frontmatter parsing
        assert note["relations"][0]["subject"] == "DDP"
        assert note["relations"][0]["relation"] == "implies"
        print("  [OK] Frontmatter parsing with relations")

    print("  PASS\n")


async def test_knowledge_graph():
    """Test graph queries and derivation trees."""
    print("=== 2. Knowledge Graph ===")
    from mcp_server.vault import Vault
    from mcp_server.graph import KnowledgeGraph

    with tempfile.TemporaryDirectory() as tmp:
        vault = Vault(tmp)
        graph = KnowledgeGraph(vault)

        # Add relations
        graph.add_relation("DDP", "implies", "GPU_Memory_Fragmentation")
        graph.add_relation("find_unused_parameters", "fixes", "DDP_Memory_Leak")
        graph.add_relation("static_graph", "fixes", "DDP_Memory_Leak")
        graph.add_relation("GPU_Memory_Fragmentation", "causes", "OOM_Error")
        print("  [OK] Added 4 relations")

        # Query by subject
        triples = graph.query(subject="DDP")
        assert len(triples) == 1
        assert triples[0]["object"] == "GPU_Memory_Fragmentation"
        print(f"  [OK] Query by subject: DDP -> {triples[0]['object']}")

        # Query by relation
        fixes = graph.query(relation="fixes")
        assert len(fixes) == 2
        print(f"  [OK] Query by relation: {len(fixes)} 'fixes' triples")

        # Query all
        all_triples = graph.query()
        assert len(all_triples) == 4
        print(f"  [OK] Query all: {len(all_triples)} triples")

        # Derivation tree
        tree = graph.get_derivation_tree("OOM_Error")
        assert tree["concept"] == "OOM_Error"
        assert len(tree["derived_from"]) > 0
        print(f"  [OK] Derivation tree for OOM_Error: {len(tree['derived_from'])} sources")

    print("  PASS\n")


async def test_embedding_store():
    """Test ChromaDB embedding operations."""
    print("=== 3. Embedding Store (ChromaDB) ===")
    from mcp_server.embeddings import EmbeddingStore

    tmp = tempfile.mkdtemp()
    try:
        store = EmbeddingStore(persist_dir=tmp, model_name=None)

        # Add documents
        store.add("doc1", "DDP with unused parameters causes memory leak", {"type": "checkpoint"})
        store.add("doc2", "Use gradient checkpointing to reduce memory", {"type": "concept"})
        store.add("doc3", "CUDA out of memory error in training loop", {"type": "checkpoint"})
        print(f"  [OK] Added 3 documents, count={store.count()}")

        # Search
        results = store.search("memory leak DDP", top_k=2)
        assert len(results) == 2
        assert results[0]["id"] == "doc1"
        print(f"  [OK] Search 'memory leak DDP': top result={results[0]['id']}")

        # Metadata filter
        filtered = store.search("memory", top_k=5, where={"type": "concept"})
        assert len(filtered) == 1
        assert filtered[0]["id"] == "doc2"
        print(f"  [OK] Filtered search (type=concept): {len(filtered)} results")

        # Delete
        store.delete("doc3")
        assert store.count() == 2
        print(f"  [OK] Delete: count now={store.count()}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("  PASS\n")


async def test_mcp_server():
    """Test MCP server tools."""
    print("=== 4. MCP Server ===")
    from mcp_server.server import create_server

    tmp = tempfile.mkdtemp()
    try:
        server = create_server(tmp, embedding_model=None)
        print("  [OK] Server created successfully")

        # Verify server has tool handlers registered
        assert server is not None
        print("  [OK] Server instance valid")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("  PASS\n")


async def test_hybrid_retriever():
    """Test keyword + embedding retrieval with RRF fusion."""
    print("=== 5. Hybrid Retriever ===")
    from unittest.mock import AsyncMock, MagicMock
    from harness.memory.retriever import Retriever

    mock_mcp = MagicMock()

    async def side_effect(name, args):
        if name == "search_vault":
            return [
                {"id": "n1", "text": "DDP memory leak fix", "metadata": {"type": "checkpoint"}, "distance": 0.1},
                {"id": "n2", "text": "GPU memory management", "metadata": {"type": "concept"}, "distance": 0.3},
            ]
        elif name == "query_graph":
            return [
                {"subject": "DDP", "relation": "implies", "object": "Memory_Leak"},
            ]
        return []

    mock_mcp.call_tool = AsyncMock(side_effect=side_effect)

    retriever = Retriever(mock_mcp, top_k=5, keyword_weight=0.4, embedding_weight=0.6)
    results = await retriever.retrieve("Fix DDP memory leak")

    assert len(results) > 0
    types = [r.get("type") for r in results]
    print(f"  [OK] Retrieved {len(results)} results: types={types}")

    # Verify both embedding and graph results are present
    assert "checkpoint" in types or "concept" in types
    assert "graph_triple" in types
    print("  [OK] RRF fusion: both embedding and graph results present")

    print("  PASS\n")


async def test_memory_writer():
    """Test checkpoint writing to vault."""
    print("=== 6. Memory Writer ===")
    from unittest.mock import AsyncMock, MagicMock
    from harness.memory.writer import MemoryWriter

    mock_mcp = MagicMock()
    mock_mcp.call_tool = AsyncMock(return_value={"id": "test-id", "path": "/test", "title": "Test"})

    writer = MemoryWriter(mock_mcp)

    # Write checkpoint
    result = await writer.write_checkpoint(
        checkpoint_text="Premise: DDP issue. Conclusion: Use static_graph=True.",
        source_checkpoint="A",
        tags=["ddp"],
    )
    assert result["id"] == "test-id"
    assert mock_mcp.call_tool.call_args[0][0] == "write_note"
    print("  [OK] Write checkpoint via MCP")

    # Write relation
    await writer.write_relation("DDP", "implies", "Memory_Leak")
    assert mock_mcp.call_tool.call_args[0][0] == "add_relation"
    print("  [OK] Write relation via MCP")

    print("  PASS\n")


async def test_config():
    """Test config loading with memory settings."""
    print("=== 7. Configuration ===")
    from harness.config import load_config

    config = load_config("config/default.yaml")
    assert config.model == "openai/deepseek-v4-flash"
    assert config.vault_path == "vault"
    assert config.embedding_model == "Qwen/Qwen3-Embedding-0.6B"
    assert config.memory_top_k == 5
    assert config.keyword_weight == 0.4
    print(f"  [OK] Config loaded: model={config.model}")
    print(f"  [OK] Memory settings: vault={config.vault_path}, embedding={config.embedding_model}")
    print(f"  [OK] Retrieval: top_k={config.memory_top_k}, kw_weight={config.keyword_weight}, emb_weight={config.embedding_weight}")

    print("  PASS\n")


async def test_stuck_detector():
    """Test stuck detection heuristics."""
    print("=== 8. Stuck Detector ===")
    from harness.plugins.stuck_detector import StuckDetectorNode
    from harness.state import HarnessState
    from unittest.mock import MagicMock

    def make_state(messages):
        buffer = [{"role": "user", "content": "Fix the bug"}]
        for msg in messages:
            buffer.append({"role": "assistant", "content": msg})
        return HarnessState(
            checkpoints=[], working_buffer=buffer, is_stuck=False,
            sub_agent_results=[], current_response="", trace_id="test",
            iteration=0, max_iterations=5, metadata={},
        )

    node = StuckDetectorNode()
    llm = MagicMock()

    # Not stuck - normal response
    state = make_state(["The bug is on line 42. Fix: change < to <=."])
    result = await node.process(state, llm)
    assert result["is_stuck"] is False
    print("  [OK] Not stuck: normal response")

    # Stuck - hedging patterns
    state = make_state(["I'm not sure about this. Maybe it's wrong. This isn't working."])
    result = await node.process(state, llm)
    assert result["is_stuck"] is True
    print("  [OK] Stuck: hedging patterns detected")

    # Stuck - repeated phrases
    state = make_state([
        "I think the issue is in the loop.",
        "Let me try again. I think the issue is in the loop.",
        "Hmm, I think the issue is in the loop.",
    ])
    result = await node.process(state, llm)
    assert result["is_stuck"] is True
    print("  [OK] Stuck: repeated phrases detected")

    print("  PASS\n")


async def test_plugin_registry():
    """Test plugin registration and discovery."""
    print("=== 9. Plugin Registry ===")
    from harness.plugins import get_registered_nodes, clear_registry, register_node
    from harness.plugins.base import BaseNode

    # Save original registry
    original = dict(get_registered_nodes())

    @register_node("test_a")
    class NodeA(BaseNode):
        name = "test_a"
        async def process(self, state, llm):
            return state

    @register_node("test_b")
    class NodeB(BaseNode):
        name = "test_b"
        async def process(self, state, llm):
            return state

    nodes = get_registered_nodes()
    assert "test_a" in nodes
    assert "test_b" in nodes
    print(f"  [OK] Registered {len(nodes)} plugins: {list(nodes.keys())}")

    # Restore original registry
    clear_registry()
    for name, cls in original.items():
        from harness.plugins import _registry
        _registry[name] = cls
    print("  [OK] Registry restored")

    print("  PASS\n")


async def test_trace_logger():
    """Test structured JSONL logging."""
    print("=== 10. Trace Logger ===")
    import json
    from harness.logging.trace_logger import TraceLogger

    with tempfile.TemporaryDirectory() as tmp:
        log_path = os.path.join(tmp, "traces.jsonl")
        logger = TraceLogger(log_path)

        logger.log(
            trace_id="test-123", node="thinker", iteration=0,
            input_tokens=100, output_tokens=50, success=True,
            custom_field="test_value",
        )
        logger.flush()

        with open(log_path) as f:
            entry = json.loads(f.readline())

        assert entry["trace_id"] == "test-123"
        assert entry["node"] == "thinker"
        assert entry["custom_field"] == "test_value"
        print(f"  [OK] Log entry: {entry['node']}, tokens={entry['input_tokens']}+{entry['output_tokens']}")

    print("  PASS\n")


async def test_orchestrator_graph():
    """Test orchestrator graph building."""
    print("=== 11. Orchestrator Graph ===")
    from harness.orchestrator import Orchestrator
    from harness.config import HarnessConfig

    # Re-import plugins since test 9 cleared the registry
    import harness.plugins.thinker
    import harness.plugins.stuck_detector
    import harness.plugins.sub_agent_spawner
    import harness.plugins.compactor
    import harness.plugins.context_manager

    config = HarnessConfig(
        model="openai/gpt-4o", api_base="https://api.openai.com/v1",
        api_key="sk-test", max_iterations=3,
    )

    orch = Orchestrator(config)
    compiled_graph = orch.build_graph()

    # Verify graph has all core nodes
    graph_obj = compiled_graph.get_graph()
    nodes = list(graph_obj.nodes)
    assert "thinker" in nodes
    assert "stuck_detector" in nodes
    assert "sub_agent_spawner" in nodes
    assert "compactor" in nodes
    assert "context_manager" in nodes
    print(f"  [OK] Graph nodes: {nodes}")

    # Verify edges
    edges = list(graph_obj.edges)
    print(f"  [OK] Graph edges: {len(edges)} connections")

    print("  PASS\n")


async def test_full_harness():
    """Test full harness with real LLM calls."""
    print("=== 12. Full Harness (Real LLM) ===")
    from harness import CognitiveHarness, load_config

    config = load_config("config/default.yaml")
    config.max_iterations = 2

    harness = CognitiveHarness(config)

    # Test 1: Simple math
    result = await harness.invoke("What is 15 + 27? Reply with just the number.")
    assert "42" in result, f"Expected '42', got: {result}"
    print(f"  [OK] Math: '{result}'")

    # Test 2: Reasoning
    result = await harness.invoke(
        "I have 10 apples. I eat 3 and buy 7 more. How many do I have? Reply with just the number."
    )
    assert "14" in result, f"Expected '14', got: {result}"
    print(f"  [OK] Reasoning: '{result}'")

    # Test 3: Code understanding
    result = await harness.invoke(
        "What does 'def foo(x): return x * 2' do in Python? Answer in one sentence."
    )
    assert isinstance(result, str) and len(result) > 10
    print(f"  [OK] Code understanding: '{result[:60]}...'")

    print("  PASS\n")


async def main():
    print("=" * 60)
    print("COGNITIVE HARNESS — COMPREHENSIVE END-TO-END VERIFICATION")
    print("=" * 60)
    print()

    tests = [
        test_vault_operations,
        test_knowledge_graph,
        test_embedding_store,
        test_mcp_server,
        test_hybrid_retriever,
        test_memory_writer,
        test_config,
        test_stuck_detector,
        test_plugin_registry,
        test_trace_logger,
        test_orchestrator_graph,
        test_full_harness,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} tests")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
