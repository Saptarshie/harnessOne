"""Rigorous tests for PromptOptimizer."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from harness.improvement.optimizer import PromptOptimizer
from harness.improvement.tracker import PromptTracker, PromptMetric


@pytest.fixture
def tracker_with_varied_data(tmp_path):
    """Tracker with multiple prompt versions and varied metrics."""
    tracker = PromptTracker(str(tmp_path))

    # Version 1: mediocre (60% success, high latency)
    for i in range(20):
        tracker.record(PromptMetric(
            prompt_id="sys-v1",
            prompt_text="You are a helpful assistant. Please help the user with their request.",
            response_text=f"response {i}",
            user_message=f"msg {i}",
            tokens_used=150,
            latency_ms=3000,
            tool_calls=2,
            success=i < 12,
        ))

    # Version 2: good (85% success, medium latency)
    for i in range(20):
        tracker.record(PromptMetric(
            prompt_id="sys-v2",
            prompt_text="You are a precise coding assistant. Be concise and accurate.",
            response_text=f"response {i}",
            user_message=f"msg {i}",
            tokens_used=100,
            latency_ms=1500,
            tool_calls=1,
            success=i < 17,
        ))

    # Version 3: excellent (95% success, low latency)
    for i in range(20):
        tracker.record(PromptMetric(
            prompt_id="sys-v3",
            prompt_text="Expert coder. Fix bugs. Be direct.",
            response_text=f"response {i}",
            user_message=f"msg {i}",
            tokens_used=60,
            latency_ms=800,
            tool_calls=0,
            success=i < 19,
        ))

    return tracker


class TestPromptOptimizerRigorous:
    """Rigorous tests for PromptOptimizer."""

    def test_should_optimize_with_exact_threshold(self, tmp_path):
        """Test optimization threshold boundary."""
        tracker = PromptTracker(str(tmp_path))
        optimizer = PromptOptimizer(tracker, min_samples=10)

        # Add 9 metrics (below threshold)
        for i in range(9):
            tracker.record(PromptMetric(
                prompt_id="test",
                prompt_text="test",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=1000,
                tool_calls=0,
                success=True,
            ))
        assert optimizer.should_optimize("test") is False

        # Add 1 more (at threshold)
        tracker.record(PromptMetric(
            prompt_id="test",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))
        assert optimizer.should_optimize("test") is True

    def test_get_best_prompt_ordering(self, tracker_with_varied_data):
        """Test that best prompt is correctly identified."""
        optimizer = PromptOptimizer(tracker_with_varied_data, min_samples=10)
        best = optimizer.get_best_prompt()
        assert best["prompt_id"] == "sys-v3"
        assert best["score"] > 0.9

    def test_get_best_prompt_empty_tracker(self, tmp_path):
        """Test best prompt with no data."""
        tracker = PromptTracker(str(tmp_path))
        optimizer = PromptOptimizer(tracker, min_samples=10)
        best = optimizer.get_best_prompt()
        assert best["prompt_id"] == "none"
        assert best["score"] == 0.0

    def test_select_winner_multiple_prompts(self, tracker_with_varied_data):
        """Test winner selection from multiple prompts."""
        optimizer = PromptOptimizer(tracker_with_varied_data, min_samples=10)
        winner = optimizer.select_winner(["sys-v1", "sys-v2", "sys-v3"])
        assert winner == "sys-v3"

    def test_select_winner_single_prompt(self, tmp_path):
        """Test winner selection with single prompt."""
        tracker = PromptTracker(str(tmp_path))
        tracker.record(PromptMetric(
            prompt_id="only",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))
        optimizer = PromptOptimizer(tracker, min_samples=1)
        winner = optimizer.select_winner(["only"])
        assert winner == "only"

    def test_report_structure(self, tracker_with_varied_data):
        """Test report contains all expected fields."""
        optimizer = PromptOptimizer(tracker_with_varied_data, min_samples=10)
        report = optimizer.get_report()

        assert "prompts" in report
        assert "best_prompt" in report
        assert "total_metrics" in report
        assert "unique_prompts" in report
        assert "min_samples_required" in report

        assert report["total_metrics"] == 60
        assert report["unique_prompts"] == 3
        assert report["min_samples_required"] == 10

    def test_report_top_prompts_limit(self, tracker_with_varied_data):
        """Test report limits top prompts correctly."""
        optimizer = PromptOptimizer(tracker_with_varied_data, min_samples=10)
        report = optimizer.get_report()
        assert len(report["prompts"]) <= 5

    @pytest.mark.asyncio
    async def test_generate_variations_with_mock_llm(self, tracker_with_varied_data):
        """Test variation generation with mocked LLM."""
        mock_llm = AsyncMock()
        variations = [
            "You are an expert programmer. Fix bugs efficiently.",
            "Coding assistant. Be precise and direct.",
            "Expert developer. Solve problems quickly.",
        ]
        mock_llm.call = AsyncMock(return_value=MagicMock(
            content=json.dumps(variations)
        ))

        optimizer = PromptOptimizer(tracker_with_varied_data, llm=mock_llm, min_samples=10)
        result = await optimizer.generate_variations(
            base_prompt="You are a helpful assistant.",
            n=3,
        )

        assert len(result) == 3
        assert result == variations
        mock_llm.call.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_variations_invalid_json(self, tracker_with_varied_data):
        """Test variation generation with invalid JSON response."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(
            content="This is not JSON"
        ))

        optimizer = PromptOptimizer(tracker_with_varied_data, llm=mock_llm, min_samples=10)
        result = await optimizer.generate_variations(
            base_prompt="test",
            n=3,
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_generate_variations_partial_json(self, tracker_with_varied_data):
        """Test variation generation with partial JSON."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(
            content='["variation1", "variation2"]'
        ))

        optimizer = PromptOptimizer(tracker_with_varied_data, llm=mock_llm, min_samples=10)
        result = await optimizer.generate_variations(
            base_prompt="test",
            n=5,
        )

        # Should return only 2 even though 5 requested
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_generate_variations_no_llm(self, tracker_with_varied_data):
        """Test variation generation without LLM."""
        optimizer = PromptOptimizer(tracker_with_varied_data, min_samples=10)
        with pytest.raises(ValueError, match="LLM required"):
            await optimizer.generate_variations("test", n=3)

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_insufficient_data(self, tmp_path):
        """Test optimization cycle with insufficient data."""
        tracker = PromptTracker(str(tmp_path))
        for i in range(5):
            tracker.record(PromptMetric(
                prompt_id="test",
                prompt_text="test",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=1000,
                tool_calls=0,
                success=True,
            ))

        optimizer = PromptOptimizer(tracker, min_samples=10)
        result = await optimizer.run_optimization_cycle("test", "test prompt")

        assert result["optimized"] is False
        assert "Insufficient data" in result["reason"]

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_already_excellent(self, tmp_path):
        """Test optimization cycle when prompt is already excellent."""
        tracker = PromptTracker(str(tmp_path))
        for i in range(15):
            tracker.record(PromptMetric(
                prompt_id="excellent",
                prompt_text="excellent prompt",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=500,
                tool_calls=0,
                success=True,
            ))

        optimizer = PromptOptimizer(tracker, min_samples=10)
        result = await optimizer.run_optimization_cycle("excellent", "excellent prompt")

        assert result["optimized"] is False
        assert "already excellent" in result["reason"]

    @pytest.mark.asyncio
    async def test_run_optimization_cycle_success(self, tracker_with_varied_data):
        """Test successful optimization cycle."""
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(
            content='["variation1", "variation2", "variation3"]'
        ))

        optimizer = PromptOptimizer(
            tracker_with_varied_data,
            llm=mock_llm,
            min_samples=10,
        )
        result = await optimizer.run_optimization_cycle(
            "sys-v1",
            "You are a helpful assistant.",
            n_variations=3,
        )

        assert result["optimized"] is True
        assert len(result["variations"]) == 3
        assert "current_score" in result
