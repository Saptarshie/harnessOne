"""Conversation engine with multi-turn tool execution."""

import json
import logging
from typing import Any

from harness.session.session import Session
from harness.tools.registry import ToolRegistry
from harness.skills.loader import SkillLoader

logger = logging.getLogger(__name__)


class ChatEngine:
    """Manages a conversation with tool execution loop."""

    def __init__(
        self,
        llm: Any,
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

    async def chat(self, message: str) -> str:
        """Process a user message with tool execution loop."""
        self._session.add_user_message(message)

        while True:
            system = self._build_system_prompt()
            messages = self._session.get_messages_for_llm()
            tools = self._tools.get_tools_as_openai()

            response = await self._llm.call_with_tools(
                system=system,
                messages=messages,
                tools=tools,
            )

            if response.tool_calls:
                tool_calls_data = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in response.tool_calls
                ]
                self._session.add_assistant_message(
                    response.content or "", tool_calls=tool_calls_data
                )

                for tc in response.tool_calls:
                    try:
                        result = await self._tools.execute_async(tc.name, tc.arguments)
                    except Exception as e:
                        result = f"Error: {e}"
                    self._session.add_tool_result(tc.id, result, name=tc.name)

                continue
            else:
                self._session.add_assistant_message(response.content)
                return response.content

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
