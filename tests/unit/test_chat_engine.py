import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.chat.engine import ChatEngine
from harness.session.session import Session
from harness.tools.registry import ToolRegistry


@pytest.fixture
def engine():
    mock_llm = MagicMock()
    mock_llm.call_with_tools = AsyncMock()
    registry = ToolRegistry()
    registry.register(
        name="read_file",
        description="Read a file",
        parameters={"path": {"type": "string"}},
        handler=lambda params: f"Contents of {params['path']}",
    )
    return ChatEngine(llm=mock_llm, tool_registry=registry, session=Session())


class TestChatEngine:
    @pytest.mark.asyncio
    async def test_simple_text_response(self, engine):
        mock_response = MagicMock()
        mock_response.content = "Hello! How can I help?"
        mock_response.tool_calls = None
        engine._llm.call_with_tools = AsyncMock(return_value=mock_response)

        result = await engine.chat("Hello")
        assert result == "Hello! How can I help?"
        assert len(engine._session.messages) == 2

    @pytest.mark.asyncio
    async def test_tool_call_then_response(self, engine):
        tool_call = MagicMock()
        tool_call.id = "tc-1"
        tool_call.name = "read_file"
        tool_call.arguments = {"path": "test.py"}

        tool_response = MagicMock()
        tool_response.content = "Contents of test.py"
        tool_response.tool_calls = [tool_call]

        text_response = MagicMock()
        text_response.content = "I read the file."
        text_response.tool_calls = None

        engine._llm.call_with_tools = AsyncMock(side_effect=[tool_response, text_response])

        result = await engine.chat("Read test.py")
        assert result == "I read the file."
        assert len(engine._session.messages) == 4

    @pytest.mark.asyncio
    async def test_multiple_tool_calls(self, engine):
        tc1 = MagicMock()
        tc1.id = "tc-1"
        tc1.name = "read_file"
        tc1.arguments = {"path": "a.py"}

        tc2 = MagicMock()
        tc2.id = "tc-2"
        tc2.name = "read_file"
        tc2.arguments = {"path": "b.py"}

        tool_resp = MagicMock()
        tool_resp.content = ""
        tool_resp.tool_calls = [tc1, tc2]

        text_resp = MagicMock()
        text_resp.content = "Read both files."
        text_resp.tool_calls = None

        engine._llm.call_with_tools = AsyncMock(side_effect=[tool_resp, text_resp])

        result = await engine.chat("Read a.py and b.py")
        assert result == "Read both files."
