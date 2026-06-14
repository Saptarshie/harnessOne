"""Cognitive LLM Harness — plugin-based reasoning engine."""

from harness.config import HarnessConfig, load_config
from harness.orchestrator import Orchestrator


class CognitiveHarness:
    """Main entry point for the cognitive harness.

    Usage:
        config = load_config("config/default.yaml")
        harness = CognitiveHarness(config)
        result = await harness.invoke("Your prompt here")
    """

    def __init__(self, config: HarnessConfig):
        self._orchestrator = Orchestrator(config)

    async def invoke(self, prompt: str) -> str:
        """Run the reasoning harness on a prompt.

        Args:
            prompt: The user's input prompt.

        Returns:
            The final response after reasoning, stuck detection,
            sub-agent exploration, and compaction.
        """
        return await self._orchestrator.invoke(prompt)


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
