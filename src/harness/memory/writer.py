"""Write checkpoints and relations to the vault via MCP."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class MemoryWriter:
    """Writes verified knowledge to the vault."""

    def __init__(self, mcp_client: Any):
        self._mcp = mcp_client

    async def write_checkpoint(
        self,
        checkpoint_text: str,
        source_checkpoint: str | None = None,
        tags: list[str] | None = None,
    ) -> dict:
        """Write a checkpoint to the vault."""
        title = f"Checkpoint: {checkpoint_text[:50]}..."
        links = []
        if source_checkpoint:
            links.append(f"checkpoint-{source_checkpoint}")

        result = await self._mcp.call_tool("write_note", {
            "title": title,
            "content": checkpoint_text,
            "tags": tags or [],
            "links": links,
            "note_type": "checkpoint",
        })
        logger.info(f"Wrote checkpoint to vault: {result.get('id', 'unknown')}")
        return result

    async def write_relation(self, subject: str, relation: str, obj: str):
        """Write a relation triple to the vault."""
        await self._mcp.call_tool("add_relation", {
            "subject": subject,
            "relation": relation,
            "object": obj,
        })
        logger.info(f"Wrote relation: {subject} --{relation}--> {obj}")
