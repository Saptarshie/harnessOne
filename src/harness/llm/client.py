"""LiteLLM wrapper with retry, token counting, and logging."""

import asyncio
import json
import logging
from dataclasses import dataclass, field

import tiktoken
from litellm import acompletion

from harness.config import HarnessConfig

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    """A tool call from the LLM."""

    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    """Structured response from an LLM call."""

    content: str
    input_tokens: int
    output_tokens: int
    model: str
    finish_reason: str
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMClient:
    """Async LLM client wrapping LiteLLM with retry and token counting."""

    def __init__(self, config: HarnessConfig):
        self.config = config
        self._encoder = self._get_encoder(config.model)

    def _get_encoder(self, model: str) -> tiktoken.Encoding:
        """Get tiktoken encoder for the model."""
        try:
            return tiktoken.encoding_for_model(model.split("/")[-1])
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, messages: list[dict]) -> int:
        """Count tokens in a list of messages.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Total token count.
        """
        total = 0
        for msg in messages:
            total += 4  # role + separators
            content = msg.get("content", "")
            total += len(self._encoder.encode(content))
        total += 2  # priming tokens
        return total

    async def call(
        self,
        messages: list[dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM with retry logic.

        Args:
            messages: List of message dicts.
            max_retries: Maximum retry attempts.
            base_delay: Base delay for exponential backoff.
            **kwargs: Additional arguments passed to acompletion.

        Returns:
            LLMResponse with content and usage info.

        Raises:
            Exception: If all retries fail.
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                response = await acompletion(
                    model=self.config.model,
                    api_base=self.config.api_base,
                    api_key=self.config.api_key,
                    messages=messages,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                )

                choice = response.choices[0]
                return LLMResponse(
                    content=choice.message.content or "",
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens,
                    model=response.model,
                    finish_reason=choice.finish_reason or "unknown",
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_exception

    async def call_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM with tools for function calling.

        Args:
            system: System prompt.
            messages: Conversation messages.
            tools: OpenAI-format tool definitions.
            max_retries: Maximum retry attempts.
            base_delay: Base delay for exponential backoff.
            **kwargs: Additional arguments.

        Returns:
            LLMResponse with content and optional tool_calls.
        """
        last_exception = None

        # Build messages with system prompt
        full_messages = [{"role": "system", "content": system}] + messages

        for attempt in range(max_retries):
            try:
                response = await acompletion(
                    model=self.config.model,
                    api_base=self.config.api_base,
                    api_key=self.config.api_key,
                    messages=full_messages,
                    tools=tools if tools else None,
                    max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                    temperature=kwargs.get("temperature", self.config.temperature),
                )

                choice = response.choices[0]
                message = choice.message

                # Parse tool calls
                tool_calls = []
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except (json.JSONDecodeError, AttributeError):
                            args = {}
                        tool_calls.append(
                            ToolCall(
                                id=tc.id or f"call_{tc.function.name}",
                                name=tc.function.name,
                                arguments=args,
                            )
                        )

                return LLMResponse(
                    content=message.content or "",
                    input_tokens=response.usage.prompt_tokens if response.usage else 0,
                    output_tokens=response.usage.completion_tokens if response.usage else 0,
                    model=response.model,
                    finish_reason=choice.finish_reason or "unknown",
                    tool_calls=tool_calls,
                )
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)

        raise last_exception
