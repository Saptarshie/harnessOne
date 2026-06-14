"""Main LLM reasoning plugin."""

import re

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


@register_node("thinker")
class ThinkerNode(BaseNode):
    """Main reasoning node. Calls the LLM with assembled context."""

    name = "thinker"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Run the main LLM reasoning step.

        Assembles context from checkpoints + working buffer, calls the LLM,
        and appends the response to the working buffer.
        """
        messages = self._assemble_context(state)
        response = await llm.call(messages)

        # Extract thought blocks for tracking
        thought = self._extract_thought(response.content)
        if thought:
            state.setdefault("metadata", {})["last_thought"] = thought

        # Append response to working buffer
        state["working_buffer"].append({
            "role": "assistant",
            "content": response.content,
        })
        state["current_response"] = response.content

        return state

    def _assemble_context(self, state: HarnessState) -> list[dict]:
        """Build the message list for the LLM call.

        Combines checkpoints into a system message, then includes the working buffer.
        """
        messages = []

        if state["checkpoints"]:
            checkpoint_text = "\n\n".join(
                f"[Checkpoint {chr(65 + i)}]: {cp}"
                for i, cp in enumerate(state["checkpoints"])
            )
            messages.append({
                "role": "system",
                "content": (
                    "You are a reasoning engine. Here are your verified reasoning checkpoints:\n\n"
                    f"{checkpoint_text}\n\n"
                    "Continue reasoning from where the last checkpoint left off."
                ),
            })
        else:
            messages.append({
                "role": "system",
                "content": "You are a reasoning engine. Think step by step.",
            })

        messages.extend(state["working_buffer"])
        return messages

    def _extract_thought(self, content: str) -> str | None:
        """Extract content from <thought> tags."""
        match = re.search(r"<thought>(.*?)</thought>", content, re.DOTALL)
        return match.group(1).strip() if match else None
