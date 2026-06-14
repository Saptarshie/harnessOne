import pytest
from unittest.mock import MagicMock
from harness.plugins.stuck_detector import StuckDetectorNode
from harness.state import HarnessState


def make_state(assistant_messages: list[str]) -> HarnessState:
    buffer = [{"role": "user", "content": "Fix the bug"}]
    for msg in assistant_messages:
        buffer.append({"role": "assistant", "content": msg})
    return HarnessState(
        checkpoints=[],
        working_buffer=buffer,
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


class TestStuckDetectorNode:
    @pytest.mark.asyncio
    async def test_not_stuck_on_first_response(self):
        state = make_state(["Let me look at the code."])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is False

    @pytest.mark.asyncio
    async def test_stuck_on_repeated_phrases(self):
        state = make_state([
            "I think the issue is in the loop.",
            "Let me try again. I think the issue is in the loop.",
            "Hmm, I think the issue is in the loop.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is True

    @pytest.mark.asyncio
    async def test_stuck_on_hedging_language(self):
        state = make_state([
            "I'm not sure about this. Let me try something else.",
            "Maybe the issue is somewhere else. I'm not sure.",
            "Let me try again. I'm not sure what's happening.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is True

    @pytest.mark.asyncio
    async def test_not_stuck_on_progress(self):
        state = make_state([
            "I found the issue in line 10.",
            "The fix is to add a null check.",
            "I've applied the fix and the tests pass.",
        ])
        mock_llm = MagicMock()

        node = StuckDetectorNode()
        result = await node.process(state, mock_llm)

        assert result["is_stuck"] is False
