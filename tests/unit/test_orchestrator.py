import pytest
from harness.orchestrator import Orchestrator
from harness.config import HarnessConfig
from harness.plugins import clear_registry, register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        max_iterations=3,
    )


class TestOrchestrator:
    def setup_method(self):
        clear_registry()

    def teardown_method(self):
        clear_registry()

    def test_discovers_registered_plugins(self, config):
        @register_node("test_node")
        class TestNode(BaseNode):
            name = "test_node"

            async def process(self, state, llm):
                return state

        orch = Orchestrator(config)
        assert "test_node" in orch.available_nodes

    def test_builds_graph(self, config):
        @register_node("thinker")
        class ThinkerNode(BaseNode):
            name = "thinker"

            async def process(self, state, llm):
                return state

        @register_node("stuck_detector")
        class StuckDetectorNode(BaseNode):
            name = "stuck_detector"

            async def process(self, state, llm):
                return state

        @register_node("sub_agent_spawner")
        class SubAgentSpawnerNode(BaseNode):
            name = "sub_agent_spawner"

            async def process(self, state, llm):
                return state

        @register_node("compactor")
        class CompactorNode(BaseNode):
            name = "compactor"

            async def process(self, state, llm):
                return state

        @register_node("context_manager")
        class ContextManagerNode(BaseNode):
            name = "context_manager"

            async def process(self, state, llm):
                return state

        orch = Orchestrator(config)
        graph = orch.build_graph()
        assert graph is not None
