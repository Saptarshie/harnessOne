"""Prompt performance tracker.

Records metrics for every prompt/response pair to enable
optimization and comparison of different prompt strategies.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class PromptMetric:
    """A single prompt/response measurement."""

    prompt_id: str
    prompt_text: str
    response_text: str
    user_message: str
    tokens_used: int
    latency_ms: float
    tool_calls: int
    success: bool
    timestamp: str = ""
    feedback_score: float | None = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PromptMetric":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class PromptTracker:
    """Tracks prompt performance metrics over time."""

    def __init__(self, storage_path: str = ".harness/prompt_metrics", max_history: int = 1000):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._max_history = max_history
        self._metrics: list[PromptMetric] = []
        self._index: dict[str, list[int]] = {}  # prompt_id -> indices

    def record(self, metric: PromptMetric):
        """Record a prompt/response metric."""
        self._metrics.append(metric)
        idx = len(self._metrics) - 1
        if metric.prompt_id not in self._index:
            self._index[metric.prompt_id] = []
        self._index[metric.prompt_id].append(idx)

        # Trim if over limit
        if len(self._metrics) > self._max_history:
            self._metrics = self._metrics[-self._max_history:]
            self._rebuild_index()

    def _rebuild_index(self):
        """Rebuild the prompt_id index after trimming."""
        self._index = {}
        for i, m in enumerate(self._metrics):
            if m.prompt_id not in self._index:
                self._index[m.prompt_id] = []
            self._index[m.prompt_id].append(i)

    def get_history(self) -> list[PromptMetric]:
        """Get all recorded metrics."""
        return list(self._metrics)

    def get_metrics_for_prompt(self, prompt_id: str) -> list[PromptMetric]:
        """Get all metrics for a specific prompt version."""
        indices = self._index.get(prompt_id, [])
        return [self._metrics[i] for i in indices]

    def calculate_score(self, prompt_id: str) -> float:
        """Calculate composite score for a prompt.

        Score = 0.6 * success_rate + 0.2 * (1 - normalized_latency) + 0.2 * (1 - normalized_tokens)
        """
        metrics = self.get_metrics_for_prompt(prompt_id)
        if not metrics:
            return 0.0

        success_rate = sum(1 for m in metrics if m.success) / len(metrics)
        avg_latency = sum(m.latency_ms for m in metrics) / len(metrics)
        avg_tokens = sum(m.tokens_used for m in metrics) / len(metrics)

        # Normalize latency (lower is better, cap at 10s)
        normalized_latency = min(avg_latency / 10000.0, 1.0)
        # Normalize tokens (lower is better, cap at 4000)
        normalized_tokens = min(avg_tokens / 4000.0, 1.0)

        score = (
            0.6 * success_rate
            + 0.2 * (1.0 - normalized_latency)
            + 0.2 * (1.0 - normalized_tokens)
        )
        return round(score, 4)

    def compare_prompts(self, prompt_a_id: str, prompt_b_id: str) -> dict:
        """Compare two prompt versions."""
        score_a = self.calculate_score(prompt_a_id)
        score_b = self.calculate_score(prompt_b_id)

        metrics_a = self.get_metrics_for_prompt(prompt_a_id)
        metrics_b = self.get_metrics_for_prompt(prompt_b_id)

        return {
            "prompt_a_id": prompt_a_id,
            "prompt_b_id": prompt_b_id,
            "prompt_a_score": score_a,
            "prompt_b_score": score_b,
            "improvement": round(score_b - score_a, 4),
            "prompt_a_samples": len(metrics_a),
            "prompt_b_samples": len(metrics_b),
            "prompt_a_success_rate": sum(1 for m in metrics_a if m.success) / max(len(metrics_a), 1),
            "prompt_b_success_rate": sum(1 for m in metrics_b if m.success) / max(len(metrics_b), 1),
        }

    def persist(self):
        """Save metrics to disk."""
        file_path = self._path / "metrics.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for metric in self._metrics:
                f.write(json.dumps(metric.to_dict()) + "\n")
        logger.info(f"Persisted {len(self._metrics)} metrics to {file_path}")

    def load(self):
        """Load metrics from disk."""
        file_path = self._path / "metrics.jsonl"
        if not file_path.exists():
            return
        self._metrics = []
        self._index = {}
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data = json.loads(line)
                        metric = PromptMetric.from_dict(data)
                        self.record(metric)
                    except Exception as e:
                        logger.warning(f"Failed to parse metric: {e}")
        logger.info(f"Loaded {len(self._metrics)} metrics from {file_path}")

    def get_top_prompts(self, n: int = 5) -> list[dict]:
        """Get the top N performing prompt IDs."""
        prompt_scores = []
        for prompt_id in self._index:
            score = self.calculate_score(prompt_id)
            samples = len(self.get_metrics_for_prompt(prompt_id))
            prompt_scores.append({
                "prompt_id": prompt_id,
                "score": score,
                "samples": samples,
            })
        prompt_scores.sort(key=lambda x: x["score"], reverse=True)
        return prompt_scores[:n]
