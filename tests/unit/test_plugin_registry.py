import pytest
from harness.plugins import get_registered_nodes, clear_registry
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


class TestPluginRegistry:
    def setup_method(self):
        clear_registry()

    def teardown_method(self):
        clear_registry()

    def test_register_and_retrieve(self):
        from harness.plugins import register_node

        @register_node("test_node")
        class TestNode(BaseNode):
            name = "test_node"

            async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
                return state

        nodes = get_registered_nodes()
        assert "test_node" in nodes
        assert nodes["test_node"] is TestNode

    def test_multiple_registrations(self):
        from harness.plugins import register_node

        @register_node("node_a")
        class NodeA(BaseNode):
            name = "node_a"

            async def process(self, state, llm):
                return state

        @register_node("node_b")
        class NodeB(BaseNode):
            name = "node_b"

            async def process(self, state, llm):
                return state

        nodes = get_registered_nodes()
        assert len(nodes) == 2
        assert "node_a" in nodes
        assert "node_b" in nodes

    def test_clear_registry(self):
        from harness.plugins import register_node

        @register_node("temp_node")
        class TempNode(BaseNode):
            name = "temp_node"

            async def process(self, state, llm):
                return state

        assert len(get_registered_nodes()) == 1
        clear_registry()
        assert len(get_registered_nodes()) == 0
