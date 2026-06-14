import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.compactor import CompactorNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def state_with_sub_agent_results():
    return HarnessState(
        checkpoints=["Checkpoint A: debugging memory leak"],
        working_buffer=[
            {"role": "user", "content": "Fix the memory leak"},
            {"role": "assistant", "content": "I'm stuck."},
        ],
        is_stuck=True,
        sub_agent_results=[
            {
                "agent_id": 0,
                "success": True,
                "content": "Try clearing CUDA cache with torch.cuda.empty_cache() after each batch.",
                "approach": "Investigate clearing GPU/CUDA caches",
            },
            {
                "agent_id": 1,
                "success": True,
                "content": "Set find_unused_parameters=False in DDP and use static_graph=True.",
                "approach": "Check for unused parameters",
            },
            {
                "agent_id": 2,
                "success": False,
                "content": "API error",
                "approach": "Check circular references",
            },
        ],
        current_response="I'm stuck.",
        trace_id="test-123",
        iteration=1,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(compacted_text: str):
    mock_llm = MagicMock()
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=compacted_text,
            input_tokens=200,
            output_tokens=100,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    mock_llm.count_tokens = MagicMock(return_value=300)
    return mock_llm


class TestCompactorNode:
    @pytest.mark.asyncio
    async def test_creates_checkpoint_from_sub_agent_results(self, state_with_sub_agent_results):
        compacted = (
            "Derivation: DDP with unused parameters causes memory retention.\n"
            "Fix: Set find_unused_parameters=False and use static_graph=True.\n"
            "Also clear CUDA cache after each batch with torch.cuda.empty_cache()."
        )
        mock_llm = make_mock_llm(compacted)

        node = CompactorNode()
        result = await node.process(state_with_sub_agent_results, mock_llm)

        assert len(result["checkpoints"]) == 2
        assert result["checkpoints"][1] == compacted
        assert result["sub_agent_results"] == []

    @pytest.mark.asyncio
    async def test_skips_when_no_results(self):
        state = HarnessState(
            checkpoints=["Checkpoint A"],
            working_buffer=[{"role": "user", "content": "test"}],
            is_stuck=False,
            sub_agent_results=[],
            current_response="",
            trace_id="test-123",
            iteration=0,
            max_iterations=5,
            metadata={},
        )
        mock_llm = MagicMock()

        node = CompactorNode()
        result = await node.process(state, mock_llm)

        assert len(result["checkpoints"]) == 1

    @pytest.mark.asyncio
    async def test_filters_failed_sub_agents(self, state_with_sub_agent_results):
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.append(messages)
            return LLMResponse(
                content="compacted",
                input_tokens=200,
                output_tokens=100,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=300)

        node = CompactorNode()
        await node.process(state_with_sub_agent_results, mock_llm)

        prompt = captured_messages[0][1]["content"]  # user message, not system
        assert "API error" not in prompt
        assert "CUDA cache" in prompt or "find_unused_parameters" in prompt
