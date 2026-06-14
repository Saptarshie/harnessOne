"""Multiple MCP server management."""

import logging
from dataclasses import dataclass

from harness.mcp.client import GenericMCPClient

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
        self._clients: dict[str, GenericMCPClient] = {}

    def register_server(self, name: str, command: str, args: list[str] = None,
                        auto_start: bool = True, env: dict = None):
        """Register an MCP server configuration."""
        self._configs[name] = MCPServerConfig(
            name=name, command=command, args=args or [], auto_start=auto_start, env=env,
        )

    def register_from_config(self, servers_config: list[dict]):
        """Register servers from config YAML list.

        Each entry should have:
          name: str
          command: str (e.g. "npx", "uvx", "python")
          args: list[str] (e.g. ["-y", "@modelcontextprotocol/server-filesystem", "."])
          env: dict (optional, env vars to set)
          auto_start: bool (optional, default true)
        """
        for srv in servers_config:
            name = srv.get("name")
            command = srv.get("command")
            if not name or not command:
                logger.warning(f"Skipping MCP server with missing name/command: {srv}")
                continue
            self.register_server(
                name=name,
                command=command,
                args=srv.get("args", []),
                auto_start=srv.get("auto_start", True),
                env=srv.get("env"),
            )

    def get_server_names(self) -> list[str]:
        return list(self._configs.keys())

    def get_all_tools(self) -> list[dict]:
        """Get tools from all connected servers."""
        tools = []
        for name, client in self._clients.items():
            for tool in client.tools:
                tools.append({
                    **tool,
                    "source": f"mcp:{name}",
                })
        return tools

    def get_tools_for_prompt(self) -> str:
        """Get a formatted string of MCP tools for the system prompt."""
        tools = self.get_all_tools()
        if not tools:
            return ""
        lines = ["\n## MCP Tools"]
        for t in tools:
            params = ", ".join(
                f"{k}: {v.get('type', 'any')}"
                for k, v in t.get("parameters", {}).get("properties", {}).items()
            )
            source = t.get("source", "")
            lines.append(f"- `{t['name']}({params})` [{source}] - {t['description']}")
        return "\n".join(lines)

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Call a tool on any connected server."""
        for server_name, client in self._clients.items():
            for tool in client.tools:
                if tool["name"] == name:
                    return await client.call_tool(name, arguments)
        raise ValueError(f"MCP tool not found: {name}")

    async def start_all(self):
        """Start all registered servers with auto_start=True."""
        for name, config in self._configs.items():
            if config.auto_start:
                await self.start_server(name)

    async def start_server(self, name: str):
        """Start a specific MCP server."""
        config = self._configs[name]
        client = GenericMCPClient(
            name=name,
            command=config.command,
            args=config.args,
            env=config.env,
        )
        try:
            await client.start()
            self._clients[name] = client
            logger.info(f"Started MCP server: {name} ({len(client.tools)} tools)")
        except Exception as e:
            logger.warning(f"Failed to start MCP server {name}: {e}")

    async def stop_all(self):
        """Stop all connected servers."""
        for name, client in self._clients.items():
            try:
                await client.shutdown()
            except Exception:
                pass
        self._clients.clear()
