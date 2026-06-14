"""Central tool registry for built-in and MCP tools."""

import logging
from typing import Callable
from dataclasses import dataclass

from harness.tools.schemas import parameters_to_json_schema

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    handler: Callable
    source: str = "builtin"


class ToolRegistry:
    """Registers and executes tools from built-in sources and MCP servers."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, name: str, description: str, parameters: dict, handler: Callable, source: str = "builtin"):
        self._tools[name] = Tool(
            name=name, description=description, parameters=parameters,
            handler=handler, source=source,
        )

    def get_all_tools(self) -> list[dict]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def get_tools_as_openai(self) -> list[dict]:
        """Get tools in OpenAI function calling format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": parameters_to_json_schema(t.parameters),
                },
            }
            for t in self._tools.values()
        ]

    def get_tools_for_prompt(self) -> str:
        """Get tool descriptions for system prompt injection."""
        lines = ["Available tools:"]
        for t in self._tools.values():
            params_desc = ", ".join(f"{k}: {v.get('type', 'string')}" for k, v in t.parameters.items())
            lines.append(f"- `{t.name}({params_desc})` - {t.description}")
        return "\n".join(lines)

    def execute(self, name: str, parameters: dict) -> str:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = tool.handler(parameters)
            return str(result) if result is not None else "Success"
        except Exception as e:
            logger.error(f"Tool {name} failed: {e}")
            return f"Error: {e}"

    def has_tool(self, name: str) -> bool:
        return name in self._tools

    def get_tool_names(self) -> list[str]:
        return list(self._tools.keys())
