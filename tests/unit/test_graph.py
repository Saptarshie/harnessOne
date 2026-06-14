import pytest
from mcp_server.graph import KnowledgeGraph
from mcp_server.vault import Vault


class TestKnowledgeGraph:
    def test_add_relation(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("DDP", "implies", "GPU_Memory_Fragmentation")
        triples = graph.query(subject="DDP")
        assert len(triples) == 1
        assert triples[0]["relation"] == "implies"

    def test_query_by_relation(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("C", "fixes", "D")
        triples = graph.query(relation="implies")
        assert len(triples) == 1
        assert triples[0]["subject"] == "A"

    def test_query_all(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("C", "fixes", "D")
        triples = graph.query()
        assert len(triples) == 2

    def test_derivation_tree(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        graph.add_relation("A", "implies", "B")
        graph.add_relation("B", "implies", "C")
        graph.add_relation("C", "implies", "D")
        tree = graph.get_derivation_tree("D")
        assert "C" in str(tree)
        assert "B" in str(tree)

    def test_empty_graph(self, tmp_path):
        vault = Vault(str(tmp_path))
        graph = KnowledgeGraph(vault)
        assert graph.query() == []
