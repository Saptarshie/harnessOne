import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.improvement.optimizer import PromptOptimizer
from harness.improvement.tracker import PromptTracker, PromptMetric


@pytest.fixture
def tracker_with_data(tmp_path):
    tracker = PromptTracker(str(tmp_path))
    # Add metrics for old prompt
    for i in range(15):
        tracker.record(PromptMetric(
            prompt_id="sys-v1",
            prompt_text="You are a helpful assistant.",
            response_text=f"response {i}",
            user_message=f"msg {i}",
            tokens_used=100,
            latency_ms=2000,
            tool_calls=0,
            success=i < 9,  # 60% success
        ))
    # Add metrics for new prompt
    for i in range(15):
        tracker.record(PromptMetric(
            prompt_id="sys-v2",
            prompt_text="You are a precise coding assistant. Be concise.",
            response_text=f"response {i}",
            user_message=f"msg {i}",
            tokens_used=80,
            latency_ms=1500,
            tool_calls=0,
            success=i < 13,  # 87% success
        ))
    return tracker


class TestPromptOptimizer:
    def test_should_optimize(self, tracker_with_data):
        optimizer = PromptOptimizer(tracker_with_data, min_samples=10)
        assert optimizer.should_optimize("sys-v1") is True

    def test_should_not_optimize_insufficient_data(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(5):
            tracker.record(PromptMetric(
                prompt_id="sys-v1",
                prompt_text="test",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=1000,
                tool_calls=0,
                success=True,
            ))
        optimizer = PromptOptimizer(tracker, min_samples=10)
        assert optimizer.should_optimize("sys-v1") is False

    def test_get_best_prompt(self, tracker_with_data):
        optimizer = PromptOptimizer(tracker_with_data, min_samples=10)
        best = optimizer.get_best_prompt()
        assert best["prompt_id"] == "sys-v2"
        assert best["score"] > 0.8

    @pytest.mark.asyncio
    async def test_generate_variations(self, tracker_with_data):
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(
            content='["You are a coding expert.", "Write clean, concise code.", "Be precise and helpful."]'
        ))

        optimizer = PromptOptimizer(tracker_with_data, llm=mock_llm, min_samples=10)
        variations = await optimizer.generate_variations(
            base_prompt="You are a helpful assistant.",
            n=3,
        )
        assert len(variations) == 3
        mock_llm.call.assert_called_once()

    def test_select_winner(self, tracker_with_data):
        optimizer = PromptOptimizer(tracker_with_data, min_samples=10)
        winner = optimizer.select_winner(["sys-v1", "sys-v2"])
        assert winner == "sys-v2"

    def test_get_optimization_report(self, tracker_with_data):
        optimizer = PromptOptimizer(tracker_with_data, min_samples=10)
        report = optimizer.get_report()
        assert "prompts" in report
        assert "best_prompt" in report
        assert "total_metrics" in report
        assert report["total_metrics"] == 30
