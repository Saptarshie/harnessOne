import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.mcp.manager import MCPManager


class TestMCPManager:
    def test_register_server(self):
        mgr = MCPManager()
        mgr.register_server("vault", "stdio", command="python", args=["mcp_server/server.py"])
        assert "vault" in mgr.get_server_names()

    def test_get_tools_from_servers(self):
        mgr = MCPManager()
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value="result")
        mock_client.tools = [
            {"name": "vault_query", "description": "Query vault", "parameters": {}}
        ]
        mgr._clients["vault"] = mock_client
        tools = mgr.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "vault_query"
