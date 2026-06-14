"""Metacognitive stuck detection plugin."""

import re
from collections import Counter

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient


HEDGING_PATTERNS = [
    r"i'?m not sure",
    r"maybe",
    r"let me try (again|something else|another approach)",
    r"i don'?t (know|understand)",
    r"this isn'?t working",
    r"i'?m stuck",
    r"going in circles",
]


@register_node("stuck_detector")
class StuckDetectorNode(BaseNode):
    """Detects whether the model is stuck in a reasoning loop."""

    name = "stuck_detector"

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Analyze recent messages for signs of being stuck."""
        assistant_messages = [
            msg["content"]
            for msg in state["working_buffer"]
            if msg.get("role") == "assistant"
        ]

        if len(assistant_messages) < 2:
            state["is_stuck"] = False
            return state

        is_stuck = False

        if self._has_repeated_phrases(assistant_messages):
            is_stuck = True

        if self._has_excessive_hedging(assistant_messages):
            is_stuck = True

        state["is_stuck"] = is_stuck
        return state

    def _has_repeated_phrases(self, messages: list[str]) -> bool:
        """Check if the same phrases appear across multiple messages."""
        all_phrases: list[str] = []
        for msg in messages[-5:]:
            words = msg.lower().split()
            for i in range(len(words) - 3):
                phrase = " ".join(words[i : i + 4])
                all_phrases.append(phrase)

        if not all_phrases:
            return False

        counter = Counter(all_phrases)
        most_common_count = counter.most_common(1)[0][1] if counter else 0
        return most_common_count >= 3

    def _has_excessive_hedging(self, messages: list[str]) -> bool:
        """Check if recent messages have high density of hedging language."""
        recent = " ".join(messages[-3:]).lower()
        hedging_count = sum(
            1 for pattern in HEDGING_PATTERNS if re.search(pattern, recent)
        )
        return hedging_count >= 3
