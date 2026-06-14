"""Context window management plugin with two-tier compaction."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("context_manager")
class ContextManagerNode(BaseNode):
    """Manages context window size with two-tier compaction.

    Tier 1: Working buffer compaction (buffer -> checkpoint)
    Tier 2: Full compaction (all checkpoints + buffer -> single derivation)

    Performs compaction directly using the LLM client.
    """

    name = "context_manager"

    def __init__(
        self,
        working_buffer_threshold: int = 4000,
        full_compaction_threshold: int = 12000,
    ):
        self._wb_threshold = working_buffer_threshold
        self._full_threshold = full_compaction_threshold

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Check context size and perform compaction if needed."""
        state["iteration"] = state.get("iteration", 0) + 1

        all_messages = self._get_all_messages(state)
        total_tokens = llm.count_tokens(all_messages)

        # Tier 2: Full compaction (highest priority)
        if total_tokens > self._full_threshold:
            logger.info(
                f"Full compaction triggered: {total_tokens} > {self._full_threshold} tokens"
            )
            state = await self._perform_full_compaction(state, llm)
            return state

        # Tier 1: Working buffer compaction
        wb_tokens = llm.count_tokens(state["working_buffer"])
        if wb_tokens > self._wb_threshold:
            logger.info(
                f"Working buffer compaction triggered: {wb_tokens} > {self._wb_threshold} tokens"
            )
            state = await self._perform_wb_compaction(state, llm)
            return state

        state["metadata"]["compaction_type"] = None
        return state

    def _get_all_messages(self, state: HarnessState) -> list[dict]:
        """Get all messages for token counting."""
        checkpoint_text = "\n".join(state["checkpoints"])
        messages = [{"role": "system", "content": checkpoint_text}]
        messages.extend(state["working_buffer"])
        return messages

    async def _perform_wb_compaction(
        self, state: HarnessState, llm: LLMClient
    ) -> HarnessState:
        """Compact working buffer into a new checkpoint."""
        checkpoint_text = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )
        buffer_text = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in state["working_buffer"]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a context compactor. Compact the following working buffer "
                    "into a dense, verified checkpoint. Preserve all key findings, "
                    "decisions, and logical steps. Discard noise and repetition.\n\n"
                    "Format: logical derivation with Premise -> Steps -> Conclusion."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Existing checkpoints:\n{checkpoint_text}\n\n"
                    f"Working buffer to compact:\n{buffer_text}\n\n"
                    "Create a compact checkpoint from the working buffer."
                ),
            },
        ]

        response = await llm.call(messages)

        state["checkpoints"].append(response.content)
        state["working_buffer"] = [{"role": "system", "content": "Context compacted. Continue reasoning."}]
        state["metadata"]["compaction_type"] = "working_buffer"

        return state

    async def _perform_full_compaction(
        self, state: HarnessState, llm: LLMClient
    ) -> HarnessState:
        """Compact everything into a single dense derivation."""
        checkpoint_text = "\n\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )
        buffer_text = "\n".join(
            f"[{m['role']}]: {m['content']}" for m in state["working_buffer"]
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a context compactor performing FULL compaction. "
                    "Combine all checkpoints and working buffer into a single, "
                    "dense, self-contained derivation. Preserve the complete "
                    "logical chain. This will become the new foundation.\n\n"
                    "Format: a single coherent derivation with all key findings."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"All checkpoints:\n{checkpoint_text}\n\n"
                    f"Working buffer:\n{buffer_text}\n\n"
                    "Create a single dense derivation from everything."
                ),
            },
        ]

        response = await llm.call(messages)

        state["checkpoints"] = [response.content]
        state["working_buffer"] = [{"role": "system", "content": "Full compaction complete. Continue reasoning."}]
        state["metadata"]["compaction_type"] = "full"

        return state
