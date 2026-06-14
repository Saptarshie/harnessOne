"""Memory writer plugin - writes new checkpoints to the vault."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient
from harness.memory.writer import MemoryWriter

logger = logging.getLogger(__name__)


@register_node("memory_writer")
class MemoryWriterNode(BaseNode):
    """Writes newly created checkpoints to the vault."""

    name = "memory_writer"

    def __init__(self, mcp_client=None):
        self._writer = MemoryWriter(mcp_client) if mcp_client else None
        self._last_checkpoint_count = 0

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Write any new checkpoints to the vault."""
        if not self._writer:
            return state

        current_count = len(state["checkpoints"])

        if current_count > self._last_checkpoint_count:
            for i in range(self._last_checkpoint_count, current_count):
                checkpoint = state["checkpoints"][i]
                checkpoint_label = chr(65 + i)

                try:
                    await self._writer.write_checkpoint(
                        checkpoint_text=checkpoint,
                        source_checkpoint=checkpoint_label,
                        tags=["auto-generated"],
                    )
                    logger.info(f"Wrote checkpoint {checkpoint_label} to vault")
                except Exception as e:
                    logger.warning(f"Failed to write checkpoint to vault: {e}")

            self._last_checkpoint_count = current_count

        return state
