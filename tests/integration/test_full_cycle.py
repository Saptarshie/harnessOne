import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from harness import CognitiveHarness
from harness.config import HarnessConfig
from harness.llm.client import LLMResponse


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test-123",
        max_tokens=4096,
        temperature=0.7,
        max_iterations=3,
        sub_agent_count=2,
        sub_agent_max_iterations=2,
        working_buffer_compact_threshold=4000,
        full_compaction_threshold=12000,
        stuck_detector="heuristic",
        log_level="INFO",
        jsonl_path="logs/test_traces.jsonl",
        enable_thought_tracking=True,
    )


def make_response(content: str, input_tokens: int = 100, output_tokens: int = 50):
    return LLMResponse(
        content=content,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model="openai/gpt-4o",
        finish_reason="stop",
    )


def _make_litellm_response(resp: LLMResponse):
    """Create a mock LiteLLM response object."""
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = resp.content
    mock.choices[0].finish_reason = resp.finish_reason
    mock.usage.prompt_tokens = resp.input_tokens
    mock.usage.completion_tokens = resp.output_tokens
    mock.model = resp.model
    return mock


class TestCognitiveHarness:
    @pytest.mark.asyncio
    async def test_simple_non_stuck_completion(self, config):
        """Test: LLM responds without getting stuck -> completes in one iteration."""
        responses = [
            make_response("The bug is on line 42. Fix: change < to <=."),
        ]

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _make_litellm_response(r) for r in responses
            ]
            harness = CognitiveHarness(config)
            result = await harness.invoke("Fix the off-by-one error")

        assert "line 42" in result
        assert "Fix" in result

    @pytest.mark.asyncio
    async def test_stuck_then_recover(self, config):
        """Test: LLM gets stuck and sub-agents are spawned to explore solutions."""
        config.max_iterations = 2
        config.sub_agent_count = 2

        # Track which calls are made
        call_log = []

        async def tracking_acompletion(*args, **kwargs):
            messages = kwargs.get("messages", args[0] if args else [])
            system_content = messages[0]["content"] if messages else ""

            if "sub-agent" in system_content.lower():
                call_log.append("sub_agent")
                return _make_litellm_response(make_response(
                    "Try find_unused_parameters=False in DDP."
                ))
            elif "compactor" in system_content.lower() or "proof compactor" in system_content.lower():
                call_log.append("compactor")
                return _make_litellm_response(make_response(
                    "Premise: DDP issue. Step: Set find_unused_parameters=False. Conclusion: Fixed."
                ))
            else:
                call_log.append("thinker")
                return _make_litellm_response(make_response(
                    "I'm not sure about this. Maybe it's wrong. This isn't working."
                ))

        with patch("harness.llm.client.acompletion", side_effect=tracking_acompletion):
            harness = CognitiveHarness(config)
            result = await harness.invoke("Fix the DDP memory leak")

        # Verify: sub-agents were spawned (stuck detection worked)
        assert "sub_agent" in call_log
        # Verify: compactor was called (lean compaction happened)
        assert "compactor" in call_log
        # Verify: multiple thinker calls (loop ran)
        assert call_log.count("thinker") >= 2
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_max_iterations_safety(self, config):
        """Test: Harness stops at max_iterations even if stuck."""
        config.max_iterations = 2

        stuck_response = make_response("I'm not sure. Let me try again.")

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = [
                _make_litellm_response(stuck_response) for _ in range(20)
            ]
            harness = CognitiveHarness(config)
            result = await harness.invoke("Solve an impossible problem")

        assert isinstance(result, str)
        assert len(result) > 0
