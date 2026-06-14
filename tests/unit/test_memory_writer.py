import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.memory.writer import MemoryWriter


@pytest.fixture
def mock_mcp():
    mcp = MagicMock()
    mcp.call_tool = AsyncMock(return_value={"id": "test-id", "path": "/test/path", "title": "Test"})
    return mcp


class TestMemoryWriter:
    @pytest.mark.asyncio
    async def test_write_checkpoint(self, mock_mcp):
        writer = MemoryWriter(mock_mcp)
        result = await writer.write_checkpoint(
            checkpoint_text="Premise: DDP issue. Conclusion: Use static_graph=True.",
            source_checkpoint="A",
            tags=["ddp", "memory"],
        )
        assert result["id"] == "test-id"
        mock_mcp.call_tool.assert_called_once()
        call_args = mock_mcp.call_tool.call_args
        assert call_args[0][0] == "write_note"
        assert call_args[0][1]["note_type"] == "checkpoint"

    @pytest.mark.asyncio
    async def test_write_relation(self, mock_mcp):
        writer = MemoryWriter(mock_mcp)
        await writer.write_relation("DDP", "implies", "Memory_Leak")
        call_args = mock_mcp.call_tool.call_args
        assert call_args[0][0] == "add_relation"
        assert call_args[0][1]["subject"] == "DDP"
