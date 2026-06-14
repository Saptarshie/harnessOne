import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from harness.llm.client import LLMClient, LLMResponse
from harness.config import HarnessConfig


@pytest.fixture
def config():
    return HarnessConfig(
        model="openai/gpt-4o",
        api_base="https://api.openai.com/v1",
        api_key="sk-test-123",
        max_tokens=4096,
        temperature=0.7,
    )


@pytest.fixture
def client(config):
    return LLMClient(config)


class TestLLMResponse:
    def test_response_attributes(self):
        resp = LLMResponse(
            content="Hello",
            input_tokens=10,
            output_tokens=5,
            model="openai/gpt-4o",
            finish_reason="stop",
        )
        assert resp.content == "Hello"
        assert resp.input_tokens == 10
        assert resp.output_tokens == 5


class TestCountTokens:
    def test_count_tokens_returns_int(self, client):
        messages = [{"role": "user", "content": "Hello world"}]
        count = client.count_tokens(messages)
        assert isinstance(count, int)
        assert count > 0

    def test_count_tokens_multiple_messages(self, client):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2?"},
        ]
        count = client.count_tokens(messages)
        assert count > 5


class TestLLMCall:
    @pytest.mark.asyncio
    async def test_call_returns_response(self, client):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "4"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.model = "openai/gpt-4o"

        with patch("harness.llm.client.acompletion", new_callable=AsyncMock, return_value=mock_response):
            response = await client.call([{"role": "user", "content": "What is 2+2?"}])

        assert isinstance(response, LLMResponse)
        assert response.content == "4"
        assert response.input_tokens == 10
        assert response.output_tokens == 5

    @pytest.mark.asyncio
    async def test_call_retries_on_failure(self, client):
        mock_success = MagicMock()
        mock_success.choices = [MagicMock()]
        mock_success.choices[0].message.content = "ok"
        mock_success.choices[0].finish_reason = "stop"
        mock_success.usage.prompt_tokens = 5
        mock_success.usage.completion_tokens = 3
        mock_success.model = "openai/gpt-4o"

        with patch(
            "harness.llm.client.acompletion",
            new_callable=AsyncMock,
            side_effect=[Exception("timeout"), mock_success],
        ):
            response = await client.call([{"role": "user", "content": "test"}])
        assert response.content == "ok"

    @pytest.mark.asyncio
    async def test_call_raises_after_max_retries(self, client):
        with patch(
            "harness.llm.client.acompletion",
            new_callable=AsyncMock,
            side_effect=Exception("persistent failure"),
        ):
            with pytest.raises(Exception, match="persistent failure"):
                await client.call([{"role": "user", "content": "test"}])
