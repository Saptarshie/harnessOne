import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.plugins.sub_agent_spawner import SubAgentSpawnerNode
from harness.llm.client import LLMResponse
from harness.state import HarnessState


@pytest.fixture
def stuck_state():
    return HarnessState(
        checkpoints=["Checkpoint A: debugging memory leak"],
        working_buffer=[
            {"role": "user", "content": "Fix the memory leak"},
            {"role": "assistant", "content": "I tried reducing batch size but it didn't work."},
        ],
        is_stuck=True,
        sub_agent_results=[],
        current_response="I tried reducing batch size but it didn't work.",
        trace_id="test-123",
        iteration=1,
        max_iterations=5,
        metadata={},
    )


def make_mock_llm(response_text: str):
    mock_llm = MagicMock()
    mock_llm.call = AsyncMock(
        return_value=LLMResponse(
            content=response_text,
            input_tokens=100,
            output_tokens=50,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
    )
    mock_llm.count_tokens = MagicMock(return_value=150)
    return mock_llm


class TestSubAgentSpawnerNode:
    @pytest.mark.asyncio
    async def test_spawns_sub_agents(self, stuck_state):
        mock_llm = make_mock_llm("Try using gradient checkpointing.")

        node = SubAgentSpawnerNode(sub_agent_count=3)
        result = await node.process(stuck_state, mock_llm)

        assert len(result["sub_agent_results"]) == 3
        assert result["is_stuck"] is True

    @pytest.mark.asyncio
    async def test_each_sub_agent_gets_checkpoint_context(self, stuck_state):
        captured_messages = []

        async def capture_call(messages, **kwargs):
            captured_messages.append(messages)
            return LLMResponse(
                content="suggestion",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = capture_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = SubAgentSpawnerNode(sub_agent_count=2)
        await node.process(stuck_state, mock_llm)

        assert len(captured_messages) == 2
        for messages in captured_messages:
            system_msg = messages[0]
            assert "Checkpoint A" in system_msg["content"]

    @pytest.mark.asyncio
    async def test_handles_sub_agent_failure(self, stuck_state):
        call_count = 0

        async def flaky_call(messages, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("API error")
            return LLMResponse(
                content="suggestion",
                input_tokens=100,
                output_tokens=50,
                model="openai/gpt-4o",
                finish_reason="stop",
            )

        mock_llm = MagicMock()
        mock_llm.call = flaky_call
        mock_llm.count_tokens = MagicMock(return_value=150)

        node = SubAgentSpawnerNode(sub_agent_count=3)
        result = await node.process(stuck_state, mock_llm)

        assert len(result["sub_agent_results"]) == 3
        successes = [r for r in result["sub_agent_results"] if r["success"]]
        failures = [r for r in result["sub_agent_results"] if not r["success"]]
        assert len(successes) == 2
        assert len(failures) == 1
