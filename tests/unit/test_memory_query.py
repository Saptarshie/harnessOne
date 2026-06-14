import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.memory_query import MemoryQueryNode
from harness.state import HarnessState


@pytest.fixture
def state():
    return HarnessState(
        checkpoints=[],
        working_buffer=[{"role": "user", "content": "Fix the DDP memory leak"}],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestMemoryQueryNode:
    @pytest.mark.asyncio
    async def test_injects_context_into_system_prompt(self, state):
        mock_mcp = MagicMock()

        async def side_effect(name, args):
            if name == "search_vault":
                return [
                    {"id": "n1", "text": "DDP memory leak: use static_graph=True", "metadata": {"type": "checkpoint"}},
                ]
            elif name == "query_graph":
                return [
                    {"subject": "DDP", "relation": "implies", "object": "Memory_Leak"},
                ]
            return []

        mock_mcp.call_tool = AsyncMock(side_effect=side_effect)

        node = MemoryQueryNode(mock_mcp)
        result = await node.process(state, MagicMock())

        system_msgs = [m for m in result["working_buffer"] if m.get("role") == "system"]
        assert len(system_msgs) >= 1
        assert "DDP" in system_msgs[0]["content"]

    @pytest.mark.asyncio
    async def test_no_context_when_empty(self, state):
        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(return_value=[])

        node = MemoryQueryNode(mock_mcp)
        result = await node.process(state, MagicMock())

        system_msgs = [m for m in result["working_buffer"] if m.get("role") == "system"]
        assert len(system_msgs) == 0
