"""Generic MCP client for connecting to any MCP server (local or remote)."""

import json
import logging
import warnings
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class GenericMCPClient:
    """Client for calling tools on any MCP server.

    Supports:
    - Local (stdio): subprocess-based MCP servers
    - Remote (SSE): Server-Sent Events at a URL
    - Remote (streamable_http): HTTP streaming at a URL
    """

    def __init__(self, name: str, transport: str = "stdio",
                 command: str = None, args: list[str] = None, env: dict = None,
                 url: str = None, headers: dict = None):
        self.name = name
        self.transport = transport
        self._command = command
        self._args = args or []
        self._env = env
        self._url = url
        self._headers = headers
        self._session: ClientSession | None = None
        self._context = None
        self._tools: list[dict] = []
        self._started = False

    async def start(self):
        """Start the MCP server and connect."""
        if self.transport == "stdio":
            await self._start_stdio()
        elif self.transport == "sse":
            await self._start_sse()
        elif self.transport == "streamable_http":
            await self._start_streamable_http()
        else:
            raise ValueError(f"Unknown transport: {self.transport}")

        # Discover available tools
        try:
            tools_result = await self._session.list_tools()
            self._tools = []
            for tool in tools_result.tools:
                self._tools.append({
                    "name": tool.name,
                    "description": tool.description or "",
                    "parameters": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
            })
            self._started = True
            logger.info(f"MCP '{self.name}' started ({self.transport}): {len(self._tools)} tools")
        except Exception as e:
            logger.warning(f"MCP '{self.name}' connected but failed to list tools: {e}")
            self._tools = []
            self._started = True

    async def _start_stdio(self):
        """Start a local MCP server via stdio."""
        import os

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

    async def _start_sse(self):
        """Connect to a remote MCP server via SSE."""
        from mcp.client.sse import sse_client

        self._context = sse_client(
            url=self._url,
            headers=self._headers,
        )
        read_stream, write_stream = await self._context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

    async def _start_streamable_http(self):
        """Connect to a remote MCP server via streamable HTTP."""
        from mcp.client.streamable_http import streamablehttp_client

        self._context = streamablehttp_client(
            url=self._url,
            headers=self._headers,
        )
        result = await self._context.__aenter__()
        read_stream, write_stream = result[0], result[1]
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()

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
        if not self._started:
            return

        # Suppress asyncio cleanup errors
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            if self._session:
                try:
                    await self._session.__aexit__(None, None, None)
                except Exception:
                    pass
                self._session = None

            if self._context:
                try:
                    await self._context.__aexit__(None, None, None)
                except Exception:
                    pass
                self._context = None

        self._started = False
        logger.info(f"MCP '{self.name}' shut down")
