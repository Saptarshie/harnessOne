"""LiteLLM wrapper with retry, token counting, streaming, and logging."""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import AsyncGenerator

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


@dataclass
class StreamChunk:
    """A single chunk from a streaming response."""

    delta: str  # Text content delta
    tool_calls: list[dict] | None = None  # Partial tool calls
    finish_reason: str | None = None
    usage: dict | None = None  # Token usage (at end)


class LLMClient:
    """Async LLM client wrapping LiteLLM with retry, token counting, and streaming."""

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
        """Count tokens in a list of messages."""
        total = 0
        for msg in messages:
            total += 4
            content = msg.get("content", "")
            total += len(self._encoder.encode(content))
        total += 2
        return total

    async def call(
        self,
        messages: list[dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> LLMResponse:
        """Call the LLM with retry logic."""
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
        """Call the LLM with tools for function calling."""
        last_exception = None
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

    async def stream_with_tools(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        max_retries: int = 3,
        base_delay: float = 1.0,
        **kwargs,
    ) -> AsyncGenerator[StreamChunk, None]:
        """Stream a response with tools, yielding chunks as they arrive.

        Yields:
            StreamChunk objects with delta text, partial tool calls, and final usage.
        """
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
                    stream=True,
                )

                # Collect tool calls incrementally
                tool_call_buffers: dict[int, dict] = {}
                input_tokens = 0
                output_tokens = 0

                async for chunk in response:
                    if not chunk.choices:
                        # Usage chunk at the end
                        if hasattr(chunk, 'usage') and chunk.usage:
                            input_tokens = chunk.usage.prompt_tokens or 0
                            output_tokens = chunk.usage.completion_tokens or 0
                        continue

                    choice = chunk.choices[0]
                    delta = choice.delta

                    # Extract text content
                    text_delta = ""
                    if hasattr(delta, 'content') and delta.content:
                        text_delta = delta.content

                    # Extract tool calls
                    partial_tool_calls = None
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        partial_tool_calls = []
                        for tc in delta.tool_calls:
                            idx = tc.index
                            if idx not in tool_call_buffers:
                                tool_call_buffers[idx] = {
                                    "id": tc.id or "",
                                    "name": "",
                                    "arguments": "",
                                }
                            buf = tool_call_buffers[idx]
                            if tc.id:
                                buf["id"] = tc.id
                            if tc.function:
                                if tc.function.name:
                                    buf["name"] = tc.function.name
                                if tc.function.arguments:
                                    buf["arguments"] += tc.function.arguments
                            partial_tool_calls.append({
                                "index": idx,
                                "id": buf["id"],
                                "name": buf["name"],
                                "arguments": buf["arguments"],
                            })

                    # Check finish reason
                    finish_reason = choice.finish_reason

                    yield StreamChunk(
                        delta=text_delta,
                        tool_calls=partial_tool_calls,
                        finish_reason=finish_reason,
                        usage={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                        } if finish_reason else None,
                    )

                # Build final tool calls from buffers
                if tool_call_buffers:
                    final_tool_calls = []
                    for idx in sorted(tool_call_buffers.keys()):
                        buf = tool_call_buffers[idx]
                        try:
                            args = json.loads(buf["arguments"])
                        except (json.JSONDecodeError, AttributeError):
                            args = {}
                        final_tool_calls.append(
                            ToolCall(
                                id=buf["id"] or f"call_{buf['name']}",
                                name=buf["name"],
                                arguments=args,
                            )
                        )
                    # Yield a final chunk with parsed tool calls
                    yield StreamChunk(
                        delta="",
                        tool_calls=[{
                            "index": i,
                            "id": tc.id,
                            "name": tc.name,
                            "arguments": tc.arguments,
                        } for i, tc in enumerate(final_tool_calls)],
                        finish_reason="tool_calls",
                        usage={
                            "input_tokens": input_tokens,
                            "output_tokens": output_tokens,
                        },
                    )

                return  # Success, exit retry loop

            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    logger.warning(
                        f"LLM stream failed (attempt {attempt + 1}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    raise
