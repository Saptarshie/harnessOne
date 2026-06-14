"""Multiple MCP server management."""

import logging
from dataclasses import dataclass

from harness.mcp.client import GenericMCPClient

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    name: str
    transport: str  # "stdio", "sse", "streamable_http"
    command: str = None
    args: list[str] = None
    env: dict = None
    url: str = None
    headers: dict = None
    auto_start: bool = True


class MCPManager:
    """Manages multiple MCP server connections."""

    def __init__(self):
        self._configs: dict[str, MCPServerConfig] = {}
        self._clients: dict[str, GenericMCPClient] = {}

    def register_server(self, name: str, transport: str = "stdio",
                        command: str = None, args: list[str] = None,
                        env: dict = None, url: str = None,
                        headers: dict = None, auto_start: bool = True):
        """Register an MCP server configuration."""
        self._configs[name] = MCPServerConfig(
            name=name, transport=transport,
            command=command, args=args or [], env=env,
            url=url, headers=headers, auto_start=auto_start,
        )

    def register_from_config(self, servers_config: list[dict]):
        """Register servers from config YAML/JSON list.

        Format (opencode-compatible):
          - name: server-name
            type: local|remote           # maps to transport
            command: npx                 # for local (stdio)
            args: ["-y", "package"]      # for local (stdio)
            url: https://...             # for remote (sse/streamable_http)
            headers: {Authorization: ..} # for remote
            env: {KEY: value}            # environment variables
            enabled: true|false          # auto_start

        Legacy format (also supported):
          - name: server-name
            command: npx
            args: ["-y", "package"]
        """
        for srv in servers_config:
            name = srv.get("name")
            if not name:
                logger.warning(f"Skipping MCP server with missing name: {srv}")
                continue

            # Determine transport from 'type' or infer
            srv_type = srv.get("type", "local")
            if srv_type in ("local", "stdio"):
                transport = "stdio"
                command = srv.get("command")
                if not command:
                    logger.warning(f"Skipping local MCP '{name}': missing command")
                    continue
            elif srv_type in ("remote", "sse"):
                transport = "sse"
                url = srv.get("url")
                if not url:
                    logger.warning(f"Skipping remote MCP '{name}': missing url")
                    continue
            elif srv_type == "streamable_http":
                transport = "streamable_http"
                url = srv.get("url")
                if not url:
                    logger.warning(f"Skipping streamable_http MCP '{name}': missing url")
                    continue
            else:
                # Infer transport
                if srv.get("url"):
                    transport = "sse"
                    url = srv["url"]
                elif srv.get("command"):
                    transport = "stdio"
                    command = srv["command"]
                else:
                    logger.warning(f"Skipping MCP '{name}': can't determine transport")
                    continue

            self.register_server(
                name=name,
                transport=transport,
                command=srv.get("command"),
                args=srv.get("args", []),
                env=srv.get("env"),
                url=srv.get("url"),
                headers=srv.get("headers"),
                auto_start=srv.get("enabled", srv.get("auto_start", True)),
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
            transport=config.transport,
            command=config.command,
            args=config.args,
            env=config.env,
            url=config.url,
            headers=config.headers,
        )
        try:
            await client.start()
            self._clients[name] = client
            logger.info(f"Started MCP: {name} ({len(client.tools)} tools)")
        except Exception as e:
            logger.warning(f"Failed to start MCP '{name}': {e}")

    async def stop_all(self):
        """Stop all connected servers."""
        for name, client in self._clients.items():
            try:
                await client.shutdown()
            except Exception:
                pass
        self._clients.clear()
