"""Cognitive LLM Harness — plugin-based reasoning engine."""

from harness.config import HarnessConfig, load_config
from harness.orchestrator import Orchestrator


class CognitiveHarness:
    """Main entry point for the cognitive harness.

    Usage:
        config = load_config("config/default.yaml")
        harness = CognitiveHarness(config)
        await harness.startup()  # Start MCP server if configured
        result = await harness.invoke("Your prompt here")
        await harness.shutdown()  # Clean up
    """

    def __init__(self, config: HarnessConfig):
        self._orchestrator = Orchestrator(config)
        self._config = config

    async def startup(self):
        """Start the MCP server if memory is configured."""
        if self._config.vault_path:
            await self._orchestrator.start_mcp_client()

    async def invoke(self, prompt: str) -> str:
        """Run the reasoning harness on a prompt."""
        return await self._orchestrator.invoke(prompt)

    async def shutdown(self):
        """Shut down the MCP server."""
        await self._orchestrator.shutdown_mcp_client()


__all__ = ["CognitiveHarness", "HarnessConfig", "load_config", "Orchestrator"]
