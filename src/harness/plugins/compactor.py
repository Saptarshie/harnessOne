"""Lean-style compaction plugin."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("compactor")
class CompactorNode(BaseNode):
    """Compacts sub-agent results into a verified logical checkpoint."""

    name = "compactor"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Compact successful sub-agent results into a new checkpoint."""
        sub_results = state.get("sub_agent_results", [])
        if not sub_results:
            return state

        successful = [r for r in sub_results if r.get("success")]
        if not successful:
            logger.warning("All sub-agents failed, skipping compaction")
            state["sub_agent_results"] = []
            return state

        agent_outputs = "\n\n".join(
            f"--- Sub-agent #{r['agent_id']} (approach: {r['approach']}) ---\n{r['content']}"
            for r in successful
        )

        checkpoint_context = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(state["checkpoints"])
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are a logical proof compactor. Your job is to extract ONLY "
                    "verified, logically sound derivations from the following outputs.\n\n"
                    "Format your response as:\n"
                    "Premise: [what we know]\n"
                    "Step: [logical derivation]\n"
                    "Conclusion: [verified finding]\n\n"
                    "Discard all conversational filler, failed attempts, hallucinations, "
                    "and unverified claims. Output ONLY the compiled takeaway."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Existing reasoning context:\n{checkpoint_context}\n\n"
                    f"Sub-agent outputs to compact:\n{agent_outputs}\n\n"
                    "Extract the verified logical derivations and create a checkpoint."
                ),
            },
        ]

        response = await llm.call(messages)

        state["checkpoints"].append(response.content)
        state["sub_agent_results"] = []
        state["is_stuck"] = False

        return state
