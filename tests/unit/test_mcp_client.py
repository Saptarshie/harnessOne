import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.memory.mcp_client import MCPClient


class TestMCPClient:
    @pytest.mark.asyncio
    async def test_call_tool(self):
        client = MCPClient("mcp_server/server.py", "vault")
        mock_result = MagicMock()
        mock_result.content = [MagicMock(text='[{"subject":"A","relation":"implies","object":"B"}]')]
        client._session = MagicMock()
        client._session.call_tool = AsyncMock(return_value=mock_result)

        result = await client.call_tool("query_graph", {"subject": "A"})
        assert result == [{"subject": "A", "relation": "implies", "object": "B"}]

    @pytest.mark.asyncio
    async def test_call_tool_error(self):
        client = MCPClient("mcp_server/server.py", "vault")
        client._session = MagicMock()
        client._session.call_tool = AsyncMock(side_effect=Exception("connection lost"))

        with pytest.raises(Exception, match="connection lost"):
            await client.call_tool("query_graph", {})
