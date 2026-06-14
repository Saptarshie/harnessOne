"""Parallel sub-agent spawning plugin."""

import asyncio
import logging

from harness.plugins import register_node
from harness.plugins.base import BaseNode
from harness.state import HarnessState
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)


@register_node("sub_agent_spawner")
class SubAgentSpawnerNode(BaseNode):
    """Spawns parallel sub-agents to explore solutions when stuck."""

    name = "sub_agent_spawner"

    def __init__(self, sub_agent_count: int = 3):
        self._count = sub_agent_count

    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Spawn N sub-agents in parallel, each exploring a different approach."""
        blocker = state["current_response"]
        checkpoints = state["checkpoints"]

        tasks = [
            self._run_sub_agent(i, checkpoints, blocker, llm)
            for i in range(self._count)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        sub_agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Sub-agent {i} failed: {result}")
                sub_agent_results.append({
                    "agent_id": i,
                    "success": False,
                    "content": str(result),
                    "approach": f"approach_{i}",
                })
            else:
                sub_agent_results.append(result)

        state["sub_agent_results"] = sub_agent_results
        return state

    async def _run_sub_agent(
        self,
        agent_id: int,
        checkpoints: list[str],
        blocker: str,
        llm: LLMClient,
    ) -> dict:
        """Run a single sub-agent."""
        checkpoint_text = "\n".join(
            f"[Checkpoint {chr(65 + i)}]: {cp}"
            for i, cp in enumerate(checkpoints)
        )

        approach_prompts = [
            "Investigate clearing GPU/CUDA caches and memory pools.",
            "Check for unused parameters, dangling tensors, or detached variables.",
            "Look for circular references, event hooks, or logging that retains objects.",
        ]
        approach = approach_prompts[agent_id % len(approach_prompts)]

        messages = [
            {
                "role": "system",
                "content": (
                    f"You are sub-agent #{agent_id} exploring a specific approach.\n\n"
                    f"Reasoning context:\n{checkpoint_text}\n\n"
                    f"Your assigned approach: {approach}\n\n"
                    "Propose a concrete solution. Be specific and actionable."
                ),
            },
            {
                "role": "user",
                "content": f"The main agent is stuck on this: {blocker}\n\nWhat is your proposed solution?",
            },
        ]

        response = await llm.call(messages)

        return {
            "agent_id": agent_id,
            "success": True,
            "content": response.content,
            "approach": approach,
        }
