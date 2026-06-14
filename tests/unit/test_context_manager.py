import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.context_manager import ContextManagerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


def make_state(
    checkpoints: list[str] | None = None,
    working_buffer: list[dict] | None = None,
) -> HarnessState:
    return HarnessState(
        checkpoints=checkpoints or [],
        working_buffer=working_buffer or [{"role": "user", "content": "test"}],
        is_stuck=False,
        sub_agent_results=[],
        current_response="",
        trace_id="test-123",
        iteration=0,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(token_count: int = 100, compacted_text: str = "compacted checkpoint"):
    mock_llm = MagicMock()
    mock_llm.count_tokens = MagicMock(return_value=token_count)
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=compacted_text,
            input_tokens=200,
            output_tokens=100,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    return mock_llm


class TestContextManagerNode:
    @pytest.mark.asyncio
    async def test_no_compaction_when_under_threshold(self):
        state = make_state(
            checkpoints=["short checkpoint"],
            working_buffer=[{"role": "user", "content": "hello"}],
        )
        mock_llm = make_mock_llm(token_count=100)

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert len(result["checkpoints"]) == 1
        assert result["metadata"]["compaction_type"] is None
        mock_llm.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_working_buffer_compaction_performed(self):
        large_buffer = [{"role": "assistant", "content": "x" * 5000}]
        state = make_state(
            checkpoints=["checkpoint A"],
            working_buffer=large_buffer,
        )
        mock_llm = make_mock_llm(
            token_count=5000,
            compacted_text="Compacted: key finding from buffer"
        )

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["metadata"]["compaction_type"] == "working_buffer"
        assert len(result["checkpoints"]) == 2
        assert result["checkpoints"][1] == "Compacted: key finding from buffer"
        mock_llm.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_full_compaction_performed(self):
        checkpoints = [f"checkpoint_{i}" for i in range(20)]
        large_buffer = [{"role": "assistant", "content": "x" * 3000}]
        state = make_state(
            checkpoints=checkpoints,
            working_buffer=large_buffer,
        )
        mock_llm = make_mock_llm(
            token_count=15000,
            compacted_text="Full derivation: all findings combined"
        )

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["metadata"]["compaction_type"] == "full"
        assert len(result["checkpoints"]) == 1
        assert result["checkpoints"][0] == "Full derivation: all findings combined"

    @pytest.mark.asyncio
    async def test_iteration_increment(self):
        state = make_state()
        state["iteration"] = 2
        mock_llm = make_mock_llm(token_count=100)

        node = ContextManagerNode(
            working_buffer_threshold=4000,
            full_compaction_threshold=12000,
        )
        result = await node.process(state, mock_llm)

        assert result["iteration"] == 3
