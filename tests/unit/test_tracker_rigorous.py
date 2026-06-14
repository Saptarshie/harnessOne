"""Rigorous tests for PromptTracker."""

import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import json
from harness.improvement.tracker import PromptTracker, PromptMetric


class TestPromptMetricEdgeCases:
    """Edge cases for PromptMetric."""

    def test_metric_with_zero_values(self):
        metric = PromptMetric(
            prompt_id="test",
            prompt_text="",
            response_text="",
            user_message="",
            tokens_used=0,
            latency_ms=0.0,
            tool_calls=0,
            success=True,
        )
        assert metric.tokens_used == 0
        assert metric.latency_ms == 0.0

    def test_metric_with_large_values(self):
        metric = PromptMetric(
            prompt_id="test",
            prompt_text="x" * 10000,
            response_text="y" * 50000,
            user_message="z" * 1000,
            tokens_used=100000,
            latency_ms=999999.99,
            tool_calls=100,
            success=True,
        )
        assert metric.tokens_used == 100000
        assert metric.latency_ms == 999999.99

    def test_metric_with_special_characters(self):
        metric = PromptMetric(
            prompt_id="test/special-chars_v2",
            prompt_text="Hello\nWorld\tTab",
            response_text="Response with 'quotes' and \"double quotes\"",
            user_message="User message with emoji 🎉",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        )
        d = metric.to_dict()
        restored = PromptMetric.from_dict(d)
        assert restored.prompt_id == "test/special-chars_v2"
        assert "\n" in restored.prompt_text
        assert "🎉" in restored.user_message

    def test_metric_with_feedback_score(self):
        metric = PromptMetric(
            prompt_id="test",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
            feedback_score=4.5,
        )
        assert metric.feedback_score == 4.5
        d = metric.to_dict()
        assert d["feedback_score"] == 4.5


class TestPromptTrackerEdgeCases:
    """Edge cases for PromptTracker."""

    def test_empty_tracker(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        assert len(tracker.get_history()) == 0
        assert tracker.get_metrics_for_prompt("nonexistent") == []
        assert tracker.calculate_score("nonexistent") == 0.0
        assert tracker.get_top_prompts() == []

    def test_single_metric(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
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
        assert len(tracker.get_history()) == 1
        score = tracker.calculate_score("test")
        assert 0.0 < score <= 1.0

    def test_many_metrics(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(100):
            tracker.record(PromptMetric(
                prompt_id=f"prompt-{i % 10}",
                prompt_text=f"test {i}",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50 + i,
                latency_ms=1000 + i * 10,
                tool_calls=i % 5,
                success=i % 3 != 0,
            ))
        assert len(tracker.get_history()) == 100
        # Should have 10 unique prompts
        top = tracker.get_top_prompts(n=10)
        assert len(top) == 10

    def test_persistence_roundtrip(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(20):
            tracker.record(PromptMetric(
                prompt_id=f"prompt-{i % 3}",
                prompt_text=f"test {i}",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50 + i * 10,
                latency_ms=1000 + i * 100,
                tool_calls=i % 4,
                success=i % 2 == 0,
                feedback_score=float(i % 5),
            ))
        tracker.persist()

        tracker2 = PromptTracker(str(tmp_path))
        tracker2.load()
        assert len(tracker2.get_history()) == 20

        # Verify all metrics match
        for m1, m2 in zip(tracker.get_history(), tracker2.get_history()):
            assert m1.prompt_id == m2.prompt_id
            assert m1.tokens_used == m2.tokens_used
            assert m1.success == m2.success

    def test_max_history_eviction(self, tmp_path):
        tracker = PromptTracker(str(tmp_path), max_history=10)
        for i in range(25):
            tracker.record(PromptMetric(
                prompt_id="test",
                prompt_text=f"test {i}",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=1000,
                tool_calls=0,
                success=True,
            ))
        assert len(tracker.get_history()) == 10
        # Should keep the last 10
        assert tracker.get_history()[0].prompt_text == "test 15"
        assert tracker.get_history()[-1].prompt_text == "test 24"

    def test_compare_prompts_with_no_data(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        comparison = tracker.compare_prompts("nonexistent1", "nonexistent2")
        assert comparison["prompt_a_score"] == 0.0
        assert comparison["prompt_b_score"] == 0.0
        assert comparison["improvement"] == 0.0

    def test_score_calculation_all_success(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="test",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=100,
                latency_ms=1000,
                tool_calls=0,
                success=True,
            ))
        score = tracker.calculate_score("test")
        # Score should be high (success=1.0, low latency, low tokens)
        assert score > 0.8

    def test_score_calculation_all_failure(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="test",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=100,
                latency_ms=1000,
                tool_calls=0,
                success=False,
            ))
        score = tracker.calculate_score("test")
        # Score should be low (success=0.0)
        assert score < 0.5

    def test_score_normalization(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        # High latency, high tokens
        for i in range(5):
            tracker.record(PromptMetric(
                prompt_id="slow",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=4000,
                latency_ms=10000,
                tool_calls=5,
                success=True,
            ))
        # Low latency, low tokens
        for i in range(5):
            tracker.record(PromptMetric(
                prompt_id="fast",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=50,
                latency_ms=100,
                tool_calls=0,
                success=True,
            ))

        score_slow = tracker.calculate_score("slow")
        score_fast = tracker.calculate_score("fast")
        # Fast should score higher
        assert score_fast > score_slow

    def test_top_prompts_ordering(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        # Create prompts with different scores
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="bad",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=100,
                latency_ms=2000,
                tool_calls=2,
                success=False,
            ))
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="good",
                prompt_text="test",
                response_text="response",
                user_message="msg",
                tokens_used=50,
                latency_ms=500,
                tool_calls=0,
                success=True,
            ))

        top = tracker.get_top_prompts(n=2)
        assert top[0]["prompt_id"] == "good"
        assert top[1]["prompt_id"] == "bad"
        assert top[0]["score"] > top[1]["score"]

    def test_corrupted_jsonl_handling(self, tmp_path):
        # Write corrupted JSONL
        metrics_file = tmp_path / "metrics.jsonl"
        with open(metrics_file, "w") as f:
            f.write('{"prompt_id": "test", "prompt_text": "test", "response_text": "r", "user_message": "m", "tokens_used": 50, "latency_ms": 1000, "tool_calls": 0, "success": true, "timestamp": "2026-01-01T00:00:00Z"}\n')
            f.write("not valid json\n")
            f.write('{"prompt_id": "test2", "prompt_text": "test2", "response_text": "r2", "user_message": "m2", "tokens_used": 60, "latency_ms": 1000, "tool_calls": 0, "success": true, "timestamp": "2026-01-01T00:00:00Z"}\n')

        tracker = PromptTracker(str(tmp_path))
        tracker.load()
        # Should load 2 valid metrics, skip the corrupted one
        assert len(tracker.get_history()) == 2
