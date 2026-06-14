import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.mcp.manager import MCPManager


class TestMCPManager:
    def test_register_server(self):
        mgr = MCPManager()
        mgr.register_server("vault", "python", ["mcp_server/server.py"])
        assert "vault" in mgr.get_server_names()

    def test_get_tools_from_servers(self):
        mgr = MCPManager()
        mock_client = MagicMock()
        mock_client.call_tool = AsyncMock(return_value="result")
        mgr._clients["vault"] = mock_client
        mgr._server_tools["vault"] = [
            {"name": "vault_query", "description": "Query vault", "parameters": {}}
        ]
        tools = mgr.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "vault_query"
