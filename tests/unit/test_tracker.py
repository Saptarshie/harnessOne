import sys
from pathlib import Path

# Add src to path for imports
src_path = str(Path(__file__).parent.parent.parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import pytest
import json
from harness.improvement.tracker import PromptTracker, PromptMetric


class TestPromptMetric:
    def test_create_metric(self):
        metric = PromptMetric(
            prompt_id="sys-v1",
            prompt_text="You are a helpful assistant.",
            response_text="Hello!",
            user_message="Hi",
            tokens_used=50,
            latency_ms=1200,
            tool_calls=0,
            success=True,
        )
        assert metric.prompt_id == "sys-v1"
        assert metric.success is True
        assert metric.tokens_used == 50

    def test_metric_to_dict(self):
        metric = PromptMetric(
            prompt_id="sys-v1",
            prompt_text="You are a helpful assistant.",
            response_text="Hello!",
            user_message="Hi",
            tokens_used=50,
            latency_ms=1200,
            tool_calls=0,
            success=True,
        )
        d = metric.to_dict()
        assert d["prompt_id"] == "sys-v1"
        assert "timestamp" in d

    def test_metric_from_dict(self):
        d = {
            "prompt_id": "sys-v1",
            "prompt_text": "test",
            "response_text": "response",
            "user_message": "user",
            "tokens_used": 50,
            "latency_ms": 1200,
            "tool_calls": 0,
            "success": True,
            "timestamp": "2026-01-01T00:00:00Z",
            "feedback_score": None,
        }
        metric = PromptMetric.from_dict(d)
        assert metric.prompt_id == "sys-v1"


class TestPromptTracker:
    def test_record_metric(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        metric = PromptMetric(
            prompt_id="sys-v1",
            prompt_text="test prompt",
            response_text="test response",
            user_message="hello",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        )
        tracker.record(metric)
        assert len(tracker.get_history()) == 1

    def test_get_metrics_for_prompt(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(5):
            tracker.record(PromptMetric(
                prompt_id="sys-v1",
                prompt_text="test",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50 + i,
                latency_ms=1000,
                tool_calls=0,
                success=i % 2 == 0,
            ))
        tracker.record(PromptMetric(
            prompt_id="sys-v2",
            prompt_text="test2",
            response_text="response",
            user_message="msg",
            tokens_used=60,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))

        v1_metrics = tracker.get_metrics_for_prompt("sys-v1")
        assert len(v1_metrics) == 5
        v2_metrics = tracker.get_metrics_for_prompt("sys-v2")
        assert len(v2_metrics) == 1

    def test_calculate_score(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="sys-v1",
                prompt_text="test",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=50,
                latency_ms=1000,
                tool_calls=0,
                success=i < 8,  # 80% success rate
            ))

        score = tracker.calculate_score("sys-v1")
        assert 0.7 <= score <= 0.9  # ~80% success

    def test_compare_prompts(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        for i in range(10):
            tracker.record(PromptMetric(
                prompt_id="sys-v1",
                prompt_text="old prompt",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=100,
                latency_ms=2000,
                tool_calls=2,
                success=i < 6,  # 60% success
            ))
            tracker.record(PromptMetric(
                prompt_id="sys-v2",
                prompt_text="new prompt",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=80,
                latency_ms=1500,
                tool_calls=1,
                success=i < 9,  # 90% success
            ))

        comparison = tracker.compare_prompts("sys-v1", "sys-v2")
        assert comparison["prompt_b_score"] > comparison["prompt_a_score"]
        assert comparison["improvement"] > 0

    def test_persist_metrics(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        tracker.record(PromptMetric(
            prompt_id="sys-v1",
            prompt_text="test",
            response_text="response",
            user_message="msg",
            tokens_used=50,
            latency_ms=1000,
            tool_calls=0,
            success=True,
        ))
        tracker.persist()

        # Load from disk
        tracker2 = PromptTracker(str(tmp_path))
        tracker2.load()
        assert len(tracker2.get_history()) == 1

    def test_max_history_limit(self, tmp_path):
        tracker = PromptTracker(str(tmp_path), max_history=5)
        for i in range(10):
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
        assert len(tracker.get_history()) == 5  # Only last 5 kept
