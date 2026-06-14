"""Conversation engine with multi-turn tool execution and streaming."""

import json
import logging
from typing import Any, Callable, Awaitable

from harness.session.session import Session
from harness.tools.registry import ToolRegistry
from harness.skills.loader import SkillLoader
from harness.llm.client import LLMClient

logger = logging.getLogger(__name__)

# Type for streaming callback: receives (delta_text, is_done, token_usage)
StreamCallback = Callable[[str, bool, dict | None], Awaitable[None]]


class ChatEngine:
    """Manages a conversation with tool execution loop and streaming."""

    def __init__(
        self,
        llm: LLMClient,
        tool_registry: ToolRegistry,
        session: Session,
        skill_loader: SkillLoader | None = None,
        memory_context: str = "",
    ):
        self._llm = llm
        self._tools = tool_registry
        self._session = session
        self._skills = skill_loader
        self._memory_context = memory_context

    @property
    def session(self) -> Session:
        return self._session

    @property
    def context_tokens(self) -> int:
        """Get current context token count."""
        messages = self._session.get_messages_for_llm()
        return self._llm.count_tokens(messages)

    async def chat(self, message: str, on_stream: StreamCallback | None = None) -> str:
        """Process a user message with tool execution loop.

        Args:
            message: User message.
            on_stream: Optional callback for streaming: (delta, is_done, usage) -> None

        Returns:
            Final assistant response text.
        """
        self._session.add_user_message(message)

        while True:
            system = self._build_system_prompt()
            messages = self._session.get_messages_for_llm()
            tools = self._tools.get_tools_as_openai()

            if on_stream:
                # Streaming mode
                response_text, tool_calls, usage = await self._stream_response(
                    system, messages, tools, on_stream
                )
            else:
                # Non-streaming mode
                response = await self._llm.call_with_tools(
                    system=system,
                    messages=messages,
                    tools=tools,
                )
                response_text = response.content
                tool_calls = response.tool_calls if response.tool_calls else None
                usage = {
                    "input_tokens": response.input_tokens,
                    "output_tokens": response.output_tokens,
                }

            # Handle tool calls
            if tool_calls:
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in tool_calls
                ]
                self._session.add_assistant_message(
                    response_text or "", tool_calls=tool_calls_data
                )

                for tc in tool_calls:
                    try:
                        result = await self._tools.execute_async(tc.name, tc.arguments)
                    except Exception as e:
                        result = f"Error: {e}"
                    self._session.add_tool_result(tc.id, result, name=tc.name)

                # Notify stream that we're continuing with tool calls
                if on_stream:
                    await on_stream("", True, usage)

                continue
            else:
                self._session.add_assistant_message(response_text)

                # Final stream notification
                if on_stream:
                    await on_stream("", True, usage)

                return response_text

    async def _stream_response(
        self,
        system: str,
        messages: list[dict],
        tools: list[dict],
        on_stream: StreamCallback,
    ) -> tuple[str, list | None, dict]:
        """Stream a response from the LLM.

        Returns:
            Tuple of (full_text, tool_calls_or_none, usage_dict)
        """
        full_text = ""
        tool_calls = None
        usage = {"input_tokens": 0, "output_tokens": 0}

        async for chunk in self._llm.stream_with_tools(
            system=system,
            messages=messages,
            tools=tools,
        ):
            if chunk.delta:
                full_text += chunk.delta
                await on_stream(chunk.delta, False, None)

            if chunk.tool_calls:
                # Store partial tool calls for final assembly
                tool_calls = chunk.tool_calls

            if chunk.finish_reason:
                if chunk.usage:
                    usage = chunk.usage

        # If we got tool calls, convert to ToolCall objects
        parsed_tool_calls = None
        if tool_calls:
            from harness.llm.client import ToolCall
            parsed_tool_calls = []
            for tc in tool_calls:
                if isinstance(tc, dict):
                    args = tc.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except (json.JSONDecodeError, AttributeError):
                            args = {}
                    parsed_tool_calls.append(
                        ToolCall(
                            id=tc.get("id", f"call_{tc.get('name', 'unknown')}"),
                            name=tc.get("name", ""),
                            arguments=args,
                        )
                    )

        return full_text, parsed_tool_calls, usage

    def _build_system_prompt(self) -> str:
        """Build system prompt with skills and memory context."""
        parts = ["You are a helpful AI assistant with access to tools."]

        if self._skills:
            skill_list = self._skills.get_all_skills()
            if skill_list:
                parts.append("\n## Available Skills")
                for s in skill_list[:10]:
                    parts.append(f"- {s['name']}: {s['description']}")

                if self._session.messages:
                    last_user = [m for m in self._session.messages if m.role == "user"]
                    if last_user:
                        relevant = self._skills.find_skills_for_task(last_user[-1].content)
                        for skill in relevant[:1]:
                            content = self._skills.get_skill_content(skill["name"])
                            if content:
                                parts.append(f"\n## Skill: {skill['name']}\n{content[:2000]}")

        if self._memory_context:
            parts.append(f"\n## Memory Context\n{self._memory_context}")

        parts.append(f"\n{self._tools.get_tools_for_prompt()}")

        return "\n".join(parts)
