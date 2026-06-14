import pytest
from harness.tools.registry import ToolRegistry


class TestToolRegistry:
    def test_register_and_list(self):
        registry = ToolRegistry()
        registry.register(
            name="test_tool",
            description="A test tool",
            parameters={"input": {"type": "string", "description": "Input text"}},
            handler=lambda params: f"Result: {params['input']}",
        )
        tools = registry.get_all_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"

    def test_execute_tool(self):
        registry = ToolRegistry()
        registry.register(
            name="add",
            description="Add two numbers",
            parameters={"a": {"type": "number"}, "b": {"type": "number"}},
            handler=lambda params: str(float(params["a"]) + float(params["b"])),
        )
        result = registry.execute("add", {"a": "2", "b": "3"})
        assert result == "5.0"

    def test_execute_unknown_tool(self):
        registry = ToolRegistry()
        with pytest.raises(ValueError, match="Unknown tool"):
            registry.execute("nonexistent", {})

    def test_get_tools_for_prompt(self):
        registry = ToolRegistry()
        registry.register(
            name="read_file",
            description="Read a file",
            parameters={"path": {"type": "string"}},
            handler=lambda params: "content",
        )
        prompt = registry.get_tools_for_prompt()
        assert "read_file" in prompt
        assert "Read a file" in prompt

    def test_get_tools_as_openai_format(self):
        registry = ToolRegistry()
        registry.register(
            name="read_file",
            description="Read a file",
            parameters={"path": {"type": "string", "description": "File path"}},
            handler=lambda params: "content",
        )
        tools = registry.get_tools_as_openai()
        assert len(tools) == 1
        assert tools[0]["type"] == "function"
        assert tools[0]["function"]["name"] == "read_file"
