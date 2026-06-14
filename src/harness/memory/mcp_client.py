"""MCP client for communicating with the vault server."""

import json
import logging
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)


class MCPClient:
    """Client for calling MCP tools on the vault server."""

    def __init__(self, server_path: str, vault_path: str, embedding_model: str | None = None):
        self._server_path = server_path
        self._vault_path = vault_path
        self._embedding_model = embedding_model
        self._session: ClientSession | None = None
        self._context = None

    async def start(self):
        """Start the MCP server subprocess and connect."""
        import sys
        args = [sys.executable, self._server_path, "--vault", self._vault_path]
        if self._embedding_model:
            args.extend(["--embedding-model", self._embedding_model])

        server_params = StdioServerParameters(
            command=args[0],
            args=args[1:],
        )

        self._context = stdio_client(server_params)
        read_stream, write_stream = await self._context.__aenter__()
        self._session = ClientSession(read_stream, write_stream)
        await self._session.__aenter__()
        await self._session.initialize()
        logger.info("MCP server started and connected")

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call an MCP tool and return the parsed result."""
        if not self._session:
            raise RuntimeError("MCP client not started. Call start() first.")

        result = await self._session.call_tool(name, arguments)
        if result.content:
            text = result.content[0].text
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return text
        return None

    async def shutdown(self):
        """Shut down the MCP server and clean up."""
        if self._session:
            await self._session.__aexit__(None, None, None)
        if self._context:
            await self._context.__aexit__(None, None, None)
        logger.info("MCP server shut down")
