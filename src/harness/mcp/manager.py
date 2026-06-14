"""Multiple MCP server management."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    command: str
    args: list[str]
    env: dict | None = None
    auto_start: bool = True


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self):
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict = {}
        self._server_tools: dict[str, list[dict]] = {}

    def register_server(self, name: str, command: str, args: list[str], auto_start: bool = True, env: dict = None):
        self._configs[name] = MCPServerConfig(
            name=name, command=command, args=args, auto_start=auto_start, env=env,
        )

    def get_server_names(self) -> list[str]:
        return list(self._configs.keys())

    def get_all_tools(self) -> list[dict]:
        tools = []
        for server_name, server_tools in self._server_tools.items():
            for tool in server_tools:
                tools.append({**tool, "source": f"mcp:{server_name}"})
        return tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        for server_name, tools in self._server_tools.items():
            for tool in tools:
                if tool["name"] == name:
                    client = self._clients.get(server_name)
                    if client:
                        return await client.call_tool(name, arguments)
        raise ValueError(f"MCP tool not found: {name}")

    async def start_all(self):
        for name, config in self._configs.items():
            if config.auto_start:
                await self.start_server(name)

    async def start_server(self, name: str):
        from harness.memory.mcp_client import MCPClient
        config = self._configs[name]
        client = MCPClient(
            server_path=config.command,
            vault_path="",
        )
        try:
            await client.start()
            self._clients[name] = client
            logger.info(f"Started MCP server: {name}")
        except Exception as e:
            logger.warning(f"Failed to start MCP server {name}: {e}")

    async def stop_all(self):
        for name, client in self._clients.items():
            try:
                await client.shutdown()
            except Exception:
                pass
        self._clients.clear()
