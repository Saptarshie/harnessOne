"""Conversation engine with multi-turn tool execution and streaming."""

import json
import logging
import time
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
        tracker: Any | None = None,
        scratchpad: Any | None = None,
        global_memory: Any | None = None,
        trace_logger: Any | None = None,
        optimizer: Any | None = None,
    ):
        self._llm = llm
        self._tools = tool_registry
        self._session = session
        self._skills = skill_loader
        self._memory_context = memory_context
        self._tracker = tracker
        self._scratchpad = scratchpad
        self._global_memory = global_memory
        self._trace_logger = trace_logger
        self._optimizer = optimizer

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
        start_time = time.time()
        tool_calls_count = 0

        while True:
            system = self._build_system_prompt(message)
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
                tool_calls_count += len(tool_calls)
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

                # Record metric in tracker
                self._record_metric(
                    message, response_text, usage, tool_calls_count, start_time
                )

                # Log trace
                self._log_trace(message, response_text, usage, tool_calls_count)

                return response_text

    def _record_metric(
        self,
        user_message: str,
        response_text: str,
        usage: dict,
        tool_calls_count: int,
        start_time: float,
    ):
        """Record a prompt/response metric in the tracker."""
        if not self._tracker:
            return

        from harness.improvement.tracker import PromptMetric

        latency_ms = (time.time() - start_time) * 1000
        tokens_used = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)

        metric = PromptMetric(
            prompt_id="default",
            prompt_text="system",
            response_text=response_text or "",
            user_message=user_message,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            tool_calls=tool_calls_count,
            success=True,
        )
        self._tracker.record(metric)

    def _log_trace(
        self,
        user_message: str,
        response_text: str,
        usage: dict,
        tool_calls_count: int,
    ):
        """Log a trace entry for the conversation turn."""
        if not self._trace_logger:
            return

        self._trace_logger.log(
            trace_id=self._session.id,
            node="chat_engine",
            iteration=1,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            success=True,
            user_message=user_message[:100],
            response_preview=(response_text or "")[:100],
            tool_calls=tool_calls_count,
        )

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

    def _build_system_prompt(self, user_message: str = "") -> str:
        """Build system prompt with skills, memory, scratchpad, and global memory context."""
        base_prompt = (
            "You are a helpful AI assistant with access to tools.\n"
            "You have the ability to metalearn: when you discover a reusable workflow, tool sequence, or solution pattern, "
            "you MUST use the create_skill tool to document it as a skill. This allows you to learn and evolve over time."
        )

        if getattr(self, "_optimizer", None) and getattr(self, "_tracker", None):
            best = self._optimizer.get_best_prompt()
            if best and best.get("prompt_id") != "none":
                metrics = self._tracker.get_metrics_for_prompt(best["prompt_id"])
                if metrics and metrics[0].prompt_text:
                    base_prompt = metrics[0].prompt_text

        parts = [base_prompt]

        # Add skills context
        if self._skills:
            skill_list = self._skills.get_all_skills()
            if skill_list:
                parts.append("\n## Available Skills")
                for s in skill_list:
                    parts.append(f"- {s['name']} (Category: {s.get('category', 'general')}): {s['description']}")

                if self._session.messages:
                    last_user = [m for m in self._session.messages if m.role == "user"]
                    if last_user:
                        relevant = self._skills.find_skills_for_task(last_user[-1].content)
                        for skill in relevant[:1]:
                            content = self._skills.get_skill_content(skill["name"])
                            if content:
                                parts.append(f"\n## Skill: {skill['name']}\n{content[:2000]}")

        # Add scratchpad context
        if self._scratchpad:
            scratchpad_context = self._scratchpad.to_context_string()
            if scratchpad_context:
                parts.append(f"\n{scratchpad_context}")

        # Query global memory for relevant context
        if self._global_memory and user_message:
            memory_results = self._global_memory.retrieve(user_message, limit=3)
            if memory_results:
                parts.append("\n## Relevant Knowledge")
                for entry in memory_results:
                    parts.append(f"- [{entry.category}] {entry.key}: {entry.content}")

        # Add MCP memory context
        if self._memory_context:
            parts.append(f"\n## Memory Context\n{self._memory_context}")

        parts.append(f"\n{self._tools.get_tools_for_prompt()}")

        return "\n".join(parts)
