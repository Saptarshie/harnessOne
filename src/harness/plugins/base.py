"""Base class for all harness plugins."""

from abc import ABC, abstractmethod

from harness.state import HarnessState
from harness.llm.client import LLMClient


class BaseNode(ABC):
    """Abstract base class for harness plugin nodes.

    Each plugin implements a single step of the reasoning loop.
    Plugins receive state and an LLM client, and return modified state.
    """

    name: str

    @abstractmethod
    async def process(self, state: HarnessState, llm: LLMClient) -> HarnessState:
        """Process state and return modified state.

        Args:
            state: Current harness state.
            llm: LLM client for making model calls.

        Returns:
            Modified harness state.
        """
        ...
