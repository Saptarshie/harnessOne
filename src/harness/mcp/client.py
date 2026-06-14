"""Generic MCP client for connecting to any MCP server."""

import json
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class GenericMCPClient:
    """Client for calling tools on any MCP server."""

    def __init__(self, name: str, command: str, args: list[str] = None, env: dict = None):
        self.name = name
        self._command = command
        self._args = args or []
        self._env = env
        self._session: ClientSession | None = None
        self._context = None
        self._tools: list[dict] = []

    async def start(self):
        """Start the MCP server subprocess and connect."""
        import os
        
        # Merge env with current process env
        merged_env = {**os.environ}
        if self._env:
            merged_env.update(self._env)

        server_params = StdioServerParameters(
            command=self._command,
            args=self._args,
            env=merged_env,
        )

        self._context = stdio_client(server_params)
        read_stream, write_stream = await self._context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

        # Discover available tools
        tools_result = await self._session.list_tools()
        self._tools = []
        for tool in tools_result.tools:
            self._tools.append({
                "name": tool.name,
                "description": tool.description or "",
                "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
            })

        logger.info(f"MCP server '{self.name}' started: {len(self._tools)} tools")

    @property
    def tools(self) -> list[dict]:
        """Get discovered tools."""
        return self._tools

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call an MCP tool and return the parsed result."""
        if not self._session:
            raise RuntimeError(f"MCP client '{self.name}' not started.")

        result = await self._session.call_tool(name, arguments)
        if result.content:
            # Handle multiple content items
            parts = []
            for item in result.content:
                if hasattr(item, 'text'):
                    parts.append(item.text)
                elif hasattr(item, 'data'):
                    parts.append(f"[binary data: {item.mimeType}]")
            text = "\n".join(parts)
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    async def shutdown(self):
        """Shut down the MCP server and clean up."""
        if self._session:
            try:
                await self._session.__aexit__(None, None, None)
            except Exception:
                pass
        if self._context:
            try:
                await self._context.__aexit__(None, None, None)
            except Exception:
                pass
        logger.info(f"MCP server '{self.name}' shut down")
