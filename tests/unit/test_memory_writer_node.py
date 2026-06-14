import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.memory_writer_node import MemoryWriterNode
from harness.state import HarnessState


class TestMemoryWriterNode:
    @pytest.mark.asyncio
    async def test_writes_new_checkpoint(self):
        state = HarnessState(
            checkpoints=["Checkpoint A: original", "Checkpoint B': derived"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=1,
            max_iterations=5,
            metadata={},
        )

        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock(return_value={"id": "new-id", "title": "Test"})

        node = MemoryWriterNode(mock_mcp)
        result = await node.process(state, MagicMock())

        mock_mcp.call_tool.assert_called()
        call_args = mock_mcp.call_tool.call_args_list
        write_calls = [c for c in call_args if c[0][0] == "write_note"]
        assert len(write_calls) == 2  # Both checkpoints are new

    @pytest.mark.asyncio
    async def test_skips_when_no_new_checkpoint(self):
        state = HarnessState(
            checkpoints=["Checkpoint A: existing"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=0,
            max_iterations=5,
            metadata={},
        )

        mock_mcp = MagicMock()
        mock_mcp.call_tool = AsyncMock()

        node = MemoryWriterNode(mock_mcp)
        node._last_checkpoint_count = 1  # Already written
        result = await node.process(state, MagicMock())

        mock_mcp.call_tool.assert_not_called()
