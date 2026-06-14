"""Memory query plugin - retrieves relevant vault context before reasoning."""

import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient
from harness.memory.retriever import Retriever

logger = logging.getLogger(__name__)


@register_node("memory_query")
class MemoryQueryNode(BaseNode):
    """Queries the vault for relevant context and injects it into the prompt."""

    name = "memory_query"

    def __init__(self, mcp_client=None, top_k: int = 5, keyword_weight: float = 0.4, embedding_weight: float = 0.6):
        self._retriever = Retriever(mcp_client, top_k, keyword_weight, embedding_weight) if mcp_client else None

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Query vault and inject context into working buffer."""
        if not self._retriever:
            return state

        user_messages = [m for m in state["working_buffer"] if m.get("role") == "user"]
        if not user_messages:
            return state

        query = user_messages[0]["content"]

        try:
            results = await self._retriever.retrieve(query)
        except Exception as e:
            logger.warning(f"Memory retrieval failed: {e}")
            return state

        if not results:
            return state

        context_parts = []
        for r in results:
            rtype = r.get("type", "unknown")
            text = r.get("text", "")
            context_parts.append(f"[{rtype}] {text}")

        context_text = "\n".join(context_parts)

        memory_msg = {
            "role": "system",
            "content": f"Relevant memory context:\n{context_text}",
        }

        insert_idx = 0
        for i, msg in enumerate(state["working_buffer"]):
            if msg.get("role") == "system":
                insert_idx = i + 1
            else:
                break

        state["working_buffer"].insert(insert_idx, memory_msg)
        return state
