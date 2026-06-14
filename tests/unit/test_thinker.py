import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.thinker import ThinkerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def state():
    return HarnessState(
        checkpoints=["Checkpoint A: The user wants to fix a bug."],
        working_buffer=[
            {"role": "user", "content": "Fix the bug in main.py"},
            {"role": "assistant", "content": "Let me analyze the code..."},
        ],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestThinkerNode:
    @pytest.mark.asyncio
    async def test_appends_response_to_working_buffer(self, state):
        mock_llm = MagicMock()
        mock_llm.call = AsyncMock(
            return_value=LLMResponse(
                content="I found the bug: line 42 has an off-by-one error.",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )
        )
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        result = await node.process(state, mock_llm)

        assert len(result["working_buffer"]) == 3
        assert result["working_buffer"][-1]["role"] == "assistant"
        assert "off-by-one" in result["working_buffer"][-1]["content"]
        assert result["current_response"] == "I found the bug: line 42 has an off-by-one error."

    @pytest.mark.asyncio
    async def test_assembles_context_from_checkpoints_and_buffer(self, state):
        mock_llm = MagicMock()
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.extend(messages)
            return LLMResponse(
                content="response",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        await node.process(state, mock_llm)

        assert len(captured_messages) >= 3
        system_msg = captured_messages[0]
        assert system_msg["role"] == "system"
        assert "Checkpoint A" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_extracts_thought_blocks(self, state):
        mock_llm = MagicMock()
        mock_llm.call = AsyncMock(
            return_value=LLMResponse(
                content="<thought>I need to check the loop bounds</thought>The fix is to change < to <=.",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )
        )
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = ThinkerNode()
        result = await node.process(state, mock_llm)

        assert result["metadata"]["last_thought"] == "I need to check the loop bounds"
