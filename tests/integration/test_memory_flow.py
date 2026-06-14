"""Integration test: harness with memory (mocked MCP)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from harness import CognitiveHarness
from harness.config import HarnessConfig
from harness.llm.client import LLMResponse


def make_response(content: str):
    return LLMResponse(
        content=content,
        input_tokens=100,
        output_tokens=50,
        model="openai/gpt-4o",
        finish_reason="stop",
    )


def _make_litellm_response(resp):
    mock = MagicMock()
    mock.choices = [MagicMock()]
    mock.choices[0].message.content = resp.content
    mock.choices[0].finish_reason = resp.finish_reason
    mock.usage.prompt_tokens = resp.input_tokens
    mock.usage.completion_tokens = resp.output_tokens
    mock.model = resp.model
    return mock


@pytest.mark.asyncio
async def test_harness_with_memory(tmp_path):
    """Test harness works with memory system (mocked MCP)."""
    config = HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        max_iterations=2,
        vault_path=str(tmp_path / "vault"),
    )

    responses = [
        make_response("The fix is to set find_unused_parameters=False."),
    ]

    with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
        mock.side_effect = [_make_litellm_response(r) for r in responses]

        harness = CognitiveHarness(config)
        # Mock MCP client instead of starting real server
        harness._orchestrator._mcp_client = MagicMock()
        harness._orchestrator._mcp_client.call_tool = AsyncMock(return_value=[])

        result = await harness.invoke("Fix the memory leak")

    assert isinstance(result, str)
    assert len(result) > 0


@pytest.mark.asyncio
async def test_harness_without_memory():
    """Test harness works without memory (no vault_path)."""
    config = HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test",
        max_iterations=2,
        vault_path="",
    )

    responses = [
        make_response("The answer is 42."),
    ]

    with patch("harness.llm.client.acompletion", new_callable=AsyncMock) as mock:
        mock.side_effect = [_make_litellm_response(r) for r in responses]

        harness = CognitiveHarness(config)
        result = await harness.invoke("What is the answer?")

    assert "42" in result
