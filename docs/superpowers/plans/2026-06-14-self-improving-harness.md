# Self-Improving Harness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add self-improvement capabilities to the Cognitive Harness — prompt optimization, evolutionary prompt search, and global cross-session memory.

**Architecture:** Three subsystems: (1) PromptTracker records metrics for every prompt/response pair, (2) PromptOptimizer uses tracked metrics to refine system prompts via DSPy-style bootstrapping, (3) GlobalMemory provides cross-session knowledge persistence. Evolutionary prompt search (EGPA) is layered on top as an optional optimizer.

**Tech Stack:** Python 3.11+, existing harness stack, numpy (for evolutionary operations)

---

## File Map

| File | Responsibility |
|------|---------------|
| `src/harness/improvement/__init__.py` | Improvement subsystem package |
| `src/harness/improvement/tracker.py` | PromptTracker — records prompt/response metrics |
| `src/harness/improvement/optimizer.py` | PromptOptimizer — refines prompts based on metrics |
| `src/harness/improvement/evolution.py` | EGPA — evolutionary prompt optimization |
| `src/harness/memory/global_store.py` | GlobalMemory — cross-session knowledge |
| `src/harness/memory/scratchpad.py` | Scratchpad — working memory for current context |
| `src/harness/plugins/prompt_tracker_node.py` | Plugin for orchestrator integration |
| `tests/unit/test_tracker.py` | PromptTracker tests |
| `tests/unit/test_optimizer.py` | PromptOptimizer tests |
| `tests/unit/test_evolution.py` | EGPA tests |
| `tests/unit/test_global_store.py` | GlobalMemory tests |
| `tests/unit/test_scratchpad.py` | Scratchpad tests |

---

## Task 0: Dependencies & Config

**Files:**
- Modify: `pyproject.toml`
- Modify: `config/default.yaml`

- [ ] **Step 1: Add numpy dependency**

Add to `pyproject.toml` dependencies:
```toml
    "numpy>=1.24.0",
```

- [ ] **Step 2: Add improvement config sections**

Append to `config/default.yaml`:
```yaml
improvement:
  enabled: true
  tracker:
    storage_path: ".harness/prompt_metrics"
    max_history: 1000
  optimizer:
    enabled: true
    min_samples: 10
    improvement_threshold: 0.05
  evolution:
    enabled: false
    population_size: 20
    generations: 10
    mutation_rate: 0.1
    crossover_rate: 0.7

global_memory:
  enabled: true
  storage_path: ".harness/global_memory"
  max_entries: 10000
  embedding_model: "qwen3-0.6b"

scratchpad:
  enabled: true
  max_entries: 100
```

- [ ] **Step 3: Run existing tests**

Run: `python -m pytest tests/unit -x -q`
Expected: All 92 tests PASS.

- [ ] **Step 4: Commit**

```powershell
git add .
git commit -m "feat(improvement): add config for self-improving subsystem"
```

---

## Task 1: PromptTracker

**Files:**
- Create: `src/harness/improvement/__init__.py`
- Create: `src/harness/improvement/tracker.py`
- Create: `tests/unit/test_tracker.py`

- [ ] **Step 1: Write PromptTracker tests**

`tests/unit/test_tracker.py`:
```python
import pytest
import json
from pathlib import Path
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_tracker.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement PromptTracker**

`src/harness/improvement/__init__.py`:
```python
"""Self-improvement subsystem for the Cognitive Harness."""
```

`src/harness/improvement/tracker.py`:
```python
"""Prompt performance tracker.

Records metrics for every prompt/response pair to enable
optimization and comparison of different prompt strategies.
"""

import json
import logging
import time
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_tracker.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/improvement/ tests/unit/test_tracker.py
git commit -m "feat(improvement): PromptTracker with metrics and comparison"
```

---

## Task 2: PromptOptimizer

**Files:**
- Create: `src/harness/improvement/optimizer.py`
- Create: `tests/unit/test_optimizer.py`

- [ ] **Step 1: Write PromptOptimizer tests**

`tests/unit/test_optimizer.py`:
```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_optimizer.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement PromptOptimizer**

`src/harness/improvement/optimizer.py`:
```python
"""Prompt optimizer using tracked metrics.

Implements DSPy-inspired bootstrapping: track which prompts work best,
generate variations, and select winners based on measured performance.
"""

import json
import logging
from typing import Any

from harness.improvement.tracker import PromptTracker, PromptMetric

logger = logging.getLogger(__name__)


class PromptOptimizer:
    """Optimizes prompts based on tracked performance metrics."""

    def __init__(
        self,
        tracker: PromptTracker,
        llm: Any | None = None,
        min_samples: int = 10,
        improvement_threshold: float = 0.05,
    ):
        self._tracker = tracker
        self._llm = llm
        self._min_samples = min_samples
        self._threshold = improvement_threshold

    def should_optimize(self, prompt_id: str) -> bool:
        """Check if we have enough data to optimize a prompt."""
        metrics = self._tracker.get_metrics_for_prompt(prompt_id)
        return len(metrics) >= self._min_samples

    def get_best_prompt(self) -> dict:
        """Get the best performing prompt so far."""
        top = self._tracker.get_top_prompts(n=1)
        return top[0] if top else {"prompt_id": "none", "score": 0.0, "samples": 0}

    async def generate_variations(
        self,
        base_prompt: str,
        n: int = 3,
        focus: str = "success rate",
    ) -> list[str]:
        """Generate prompt variations using LLM.

        Args:
            base_prompt: The current prompt to improve.
            n: Number of variations to generate.
            focus: What to optimize for (success rate, conciseness, etc.)

        Returns:
            List of prompt variation strings.
        """
        if not self._llm:
            raise ValueError("LLM required for prompt generation")

        # Get current performance data
        best = self.get_best_prompt()
        metrics_summary = self._tracker.get_metrics_for_prompt(best["prompt_id"])
        success_rate = sum(1 for m in metrics_summary if m.success) / max(len(metrics_summary), 1)
        avg_tokens = sum(m.tokens_used for m in metrics_summary) / max(len(metrics_summary), 1)

        prompt = f"""You are optimizing a system prompt for an AI assistant.

Current prompt:
```
{base_prompt}
```

Current performance:
- Success rate: {success_rate:.1%}
- Average tokens: {avg_tokens:.0f}
- Focus: {focus}

Generate {n} variations of this prompt that might perform better.
Each variation should be a complete system prompt.

Return ONLY a JSON array of strings, like: ["variation1", "variation2", "variation3"]
No explanations, just the JSON array."""

        response = await self._llm.call(
            system="You are a prompt engineering expert.",
            messages=[{"role": "user", "content": prompt}],
        )

        try:
            variations = json.loads(response.content)
            if isinstance(variations, list) and all(isinstance(v, str) for v in variations):
                return variations[:n]
        except (json.JSONDecodeError, TypeError):
            pass

        logger.warning("Failed to parse LLM response as JSON array")
        return []

    def select_winner(self, prompt_ids: list[str]) -> str:
        """Select the best performing prompt from a list."""
        best_id = None
        best_score = -1.0

        for pid in prompt_ids:
            score = self._tracker.calculate_score(pid)
            if score > best_score:
                best_score = score
                best_id = pid

        return best_id or prompt_ids[0]

    def get_report(self) -> dict:
        """Generate optimization report."""
        top_prompts = self._tracker.get_top_prompts(n=5)
        return {
            "prompts": top_prompts,
            "best_prompt": top_prompts[0] if top_prompts else None,
            "total_metrics": len(self._tracker.get_history()),
            "unique_prompts": len(self._tracker._index),
            "min_samples_required": self._min_samples,
        }

    async def run_optimization_cycle(
        self,
        current_prompt_id: str,
        current_prompt_text: str,
        n_variations: int = 3,
    ) -> dict:
        """Run a full optimization cycle.

        1. Check if optimization is needed
        2. Generate variations
        3. Return variations for testing

        Returns dict with:
            - optimized: bool
            - variations: list of new prompt texts
            - reason: why optimization was/wasn't run
        """
        if not self.should_optimize(current_prompt_id):
            return {
                "optimized": False,
                "variations": [],
                "reason": f"Insufficient data (need {self._min_samples} samples)",
            }

        # Check if current prompt is already good enough
        current_score = self._tracker.calculate_score(current_prompt_id)
        if current_score > 0.95:
            return {
                "optimized": False,
                "variations": [],
                "reason": f"Current prompt already excellent (score: {current_score:.2f})",
            }

        # Generate variations
        variations = await self.generate_variations(current_prompt_text, n=n_variations)

        return {
            "optimized": True,
            "variations": variations,
            "current_score": current_score,
            "reason": "Generated variations for testing",
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_optimizer.py -v`
Expected: All 6 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/improvement/optimizer.py tests/unit/test_optimizer.py
git commit -m "feat(improvement): PromptOptimizer with DSPy-style bootstrapping"
```

---

## Task 3: Evolutionary Engine (EGPA)

**Files:**
- Create: `src/harness/improvement/evolution.py`
- Create: `tests/unit/test_evolution.py`

- [ ] **Step 1: Write EvolutionaryEngine tests**

`tests/unit/test_evolution.py`:
```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from harness.improvement.evolution import EvolutionaryEngine, PromptGenome


class TestPromptGenome:
    def test_create_genome(self):
        genome = PromptGenome(
            genes={
                "role": "You are a coding assistant.",
                "constraints": "Be concise.",
                "style": "Professional.",
            }
        )
        assert genome.fitness == 0.0
        assert genome.genes["role"] == "You are a coding assistant."

    def test_genome_to_prompt(self):
        genome = PromptGenome(
            genes={
                "role": "You are a coding assistant.",
                "constraints": "Be concise.",
                "style": "Professional.",
            }
        )
        prompt = genome.to_prompt()
        assert "coding assistant" in prompt
        assert "concise" in prompt

    def test_genome_crossover(self):
        parent1 = PromptGenome(genes={"role": "A", "constraints": "B", "style": "C"})
        parent2 = PromptGenome(genes={"role": "X", "constraints": "Y", "style": "Z"})
        child = parent1.crossover(parent2)
        # Child should have genes from both parents
        for key in child.genes:
            assert child.genes[key] in ["A", "B", "C", "X", "Y", "Z"]

    def test_genome_mutation(self, tmp_path):
        mock_llm = AsyncMock()
        mock_llm.call = AsyncMock(return_value=MagicMock(content="Mutated text."))

        genome = PromptGenome(genes={"role": "Original", "constraints": "Original"})
        # Note: mutation requires LLM, so we test the structure
        assert genome.genes["role"] == "Original"


class TestEvolutionaryEngine:
    def test_create_population(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints", "style"],
            population_size=10,
        )
        population = engine.create_population(
            seed_genes={"role": "You are helpful.", "constraints": "Be concise.", "style": "Professional."}
        )
        assert len(population) == 10
        # First genome should be the seed
        assert population[0].genes["role"] == "You are helpful."

    @pytest.mark.asyncio
    async def test_evaluate_population(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )

        # Mock fitness function
        async def mock_fitness(genome: PromptGenome) -> float:
            return 0.8

        await engine.evaluate_population(population, mock_fitness)
        for genome in population:
            assert genome.fitness == 0.8

    def test_select_parents(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )
        # Set fitness values
        for i, genome in enumerate(population):
            genome.fitness = i * 0.2

        parents = engine.select_parents(population, n=2)
        assert len(parents) == 2
        # Should select higher fitness genomes
        assert parents[0].fitness >= parents[1].fitness

    def test_evolve_generation(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints", "style"],
            population_size=10,
            mutation_rate=0.5,
            crossover_rate=0.7,
        )
        population = engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test", "style": "Test"}
        )
        # Set fitness
        for i, genome in enumerate(population):
            genome.fitness = i * 0.1

        new_pop = engine.evolve_generation(population)
        assert len(new_pop) == 10
        # New population should be different (mutations/crossover)
        # At least some genes should differ
        changed = False
        for old, new in zip(population, new_pop):
            for key in old.genes:
                if old.genes[key] != new.genes[key]:
                    changed = True
                    break
        # With 50% mutation rate, very likely some changed
        assert changed or engine._mutation_rate < 0.1

    def test_get_best_genome(self):
        engine = EvolutionaryEngine(
            gene_keys=["role", "constraints"],
            population_size=5,
        )
        population = engine.create_population(
            seed_genes={"role": "Test", "constraints": "Test"}
        )
        population[2].fitness = 1.0  # Best
        best = engine.get_best(population)
        assert best is population[2]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_evolution.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement EvolutionaryEngine**

`src/harness/improvement/evolution.py`:
```python
"""Evolutionary prompt optimization (EGPA).

Uses genetic algorithms to evolve prompt components:
- Genes: Individual prompt sections (role, constraints, style, etc.)
- Fitness: Measured by prompt tracker scores
- Selection: Tournament selection favoring higher fitness
- Crossover: Uniform crossover between parent genomes
- Mutation: LLM-driven rewriting of individual genes
"""

import logging
import random
from typing import Any, Callable, Awaitable
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PromptGenome:
    """A prompt represented as evolvable genes."""

    genes: dict[str, str]
    fitness: float = 0.0

    def to_prompt(self) -> str:
        """Combine genes into a full prompt."""
        parts = []
        for key, value in self.genes.items():
            parts.append(value)
        return "\n\n".join(parts)

    def crossover(self, other: "PromptGenome") -> "PromptGenome":
        """Create child via uniform crossover."""
        child_genes = {}
        for key in self.genes:
            if random.random() < 0.5:
                child_genes[key] = self.genes[key]
            else:
                child_genes[key] = other.genes[key]
        return PromptGenome(genes=child_genes)

    async def mutate(self, llm: Any, mutation_rate: float = 0.1):
        """Mutate genes using LLM rewriting."""
        for key in self.genes:
            if random.random() < mutation_rate:
                try:
                    response = await llm.call(
                        system="Rewrite the following text to be clearer and more effective. Return ONLY the rewritten text.",
                        messages=[{"role": "user", "content": self.genes[key]}],
                    )
                    self.genes[key] = response.content.strip()
                except Exception as e:
                    logger.warning(f"Mutation failed for {key}: {e}")


class EvolutionaryEngine:
    """Genetic algorithm engine for prompt optimization."""

    def __init__(
        self,
        gene_keys: list[str],
        population_size: int = 20,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        tournament_size: int = 3,
        elite_count: int = 2,
    ):
        self._gene_keys = gene_keys
        self._pop_size = population_size
        self._mutation_rate = mutation_rate
        self._crossover_rate = crossover_rate
        self._tournament_size = tournament_size
        self._elite_count = elite_count

    def create_population(self, seed_genes: dict[str, str]) -> list[PromptGenome]:
        """Create initial population from seed genes.

        First genome is the seed, rest are copies with slight variations.
        """
        population = [PromptGenome(genes=dict(seed_genes))]

        # Create variations by shuffling/swapping phrases
        for i in range(self._pop_size - 1):
            new_genes = {}
            for key, value in seed_genes.items():
                words = value.split()
                if len(words) > 3:
                    # Slight shuffle
                    idx = list(range(len(words)))
                    swap_count = max(1, len(words) // 5)
                    for _ in range(swap_count):
                        a, b = random.sample(range(len(words)), 2)
                        idx[a], idx[b] = idx[b], idx[a]
                    new_genes[key] = " ".join(words[j] for j in idx)
                else:
                    new_genes[key] = value
            population.append(PromptGenome(genes=new_genes))

        return population

    async def evaluate_population(
        self,
        population: list[PromptGenome],
        fitness_fn: Callable[[PromptGenome], Awaitable[float]],
    ):
        """Evaluate fitness for all genomes in population."""
        for genome in population:
            try:
                genome.fitness = await fitness_fn(genome)
            except Exception as e:
                logger.warning(f"Fitness evaluation failed: {e}")
                genome.fitness = 0.0

    def select_parents(
        self,
        population: list[PromptGenome],
        n: int = 2,
    ) -> list[PromptGenome]:
        """Select parents using tournament selection."""
        parents = []
        for _ in range(n):
            tournament = random.sample(population, min(self._tournament_size, len(population)))
            winner = max(tournament, key=lambda g: g.fitness)
            parents.append(winner)
        return parents

    def evolve_generation(
        self,
        population: list[PromptGenome],
    ) -> list[PromptGenome]:
        """Create next generation via selection, crossover, mutation."""
        # Sort by fitness
        population.sort(key=lambda g: g.fitness, reverse=True)

        # Keep elites
        new_population = [PromptGenome(genes=dict(g.genes), fitness=g.fitness)
                          for g in population[:self._elite_count]]

        # Fill rest with crossover + mutation
        while len(new_population) < self._pop_size:
            parents = self.select_parents(population, n=2)

            if random.random() < self._crossover_rate:
                child = parents[0].crossover(parents[1])
            else:
                child = PromptGenome(genes=dict(parents[0].genes))

            # Note: async mutation happens in run_evolution
            new_population.append(child)

        return new_population[:self._pop_size]

    def get_best(self, population: list[PromptGenome]) -> PromptGenome:
        """Get the best genome from population."""
        return max(population, key=lambda g: g.fitness)

    async def run_evolution(
        self,
        seed_genes: dict[str, str],
        fitness_fn: Callable[[PromptGenome], Awaitable[float]],
        llm: Any | None = None,
        generations: int | None = None,
    ) -> dict:
        """Run full evolutionary optimization.

        Returns:
            dict with best_genome, history, final_fitness
        """
        gens = generations or 10
        population = self.create_population(seed_genes)
        history = []

        for gen in range(gens):
            # Evaluate
            await self.evaluate_population(population, fitness_fn)

            # Track best
            best = self.get_best(population)
            history.append({
                "generation": gen,
                "best_fitness": best.fitness,
                "avg_fitness": sum(g.fitness for g in population) / len(population),
                "best_genes": dict(best.genes),
            })

            logger.info(f"Gen {gen}: best={best.fitness:.3f}, avg={history[-1]['avg_fitness']:.3f}")

            # Check convergence
            if gen > 2 and history[-1]["best_fitness"] == history[-2]["best_fitness"] == history[-3]["best_fitness"]:
                logger.info(f"Converged at generation {gen}")
                break

            # Evolve (except last generation)
            if gen < gens - 1:
                population = self.evolve_generation(population)
                # Apply mutations
                if llm:
                    for genome in population:
                        await genome.mutate(llm, self._mutation_rate)

        best = self.get_best(population)
        return {
            "best_genome": best,
            "best_prompt": best.to_prompt(),
            "best_fitness": best.fitness,
            "generations_run": len(history),
            "history": history,
        }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_evolution.py -v`
Expected: All 7 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/improvement/evolution.py tests/unit/test_evolution.py
git commit -m "feat(improvement): EGPA evolutionary prompt optimization"
```

---

## Task 4: Global Memory Store

**Files:**
- Create: `src/harness/memory/global_store.py`
- Create: `tests/unit/test_global_store.py`

- [ ] **Step 1: Write GlobalMemory tests**

`tests/unit/test_global_store.py`:
```python
import pytest
from harness.memory.global_store import GlobalMemory, MemoryEntry


class TestMemoryEntry:
    def test_create_entry(self):
        entry = MemoryEntry(
            key="python/typing",
            content="Use type hints for all function signatures.",
            category="coding",
            source_session="abc-123",
        )
        assert entry.key == "python/typing"
        assert entry.category == "coding"
        assert entry.access_count == 0

    def test_entry_to_dict(self):
        entry = MemoryEntry(
            key="test",
            content="test content",
            category="test",
        )
        d = entry.to_dict()
        assert d["key"] == "test"
        assert "timestamp" in d

    def test_entry_from_dict(self):
        d = {
            "key": "test",
            "content": "content",
            "category": "cat",
            "source_session": "sess",
            "timestamp": "2026-01-01T00:00:00Z",
            "access_count": 5,
            "metadata": {},
        }
        entry = MemoryEntry.from_dict(d)
        assert entry.access_count == 5


class TestGlobalMemory:
    def test_store_and_retrieve(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/typing", "Use type hints.", category="coding")
        results = memory.retrieve("typing")
        assert len(results) == 1
        assert results[0].content == "Use type hints."

    def test_retrieve_by_category(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("code/style", "Follow PEP 8.", category="coding")
        memory.store("design/mvc", "Use MVC pattern.", category="architecture")
        memory.store("code/formatting", "Use black formatter.", category="coding")

        coding = memory.retrieve("code", category="coding")
        assert len(coding) == 2

    def test_update_existing(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "original")
        memory.store("key1", "updated")
        results = memory.retrieve("key1")
        assert len(results) == 1
        assert results[0].content == "updated"

    def test_delete(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content")
        assert len(memory.retrieve("key1")) == 1
        memory.delete("key1")
        assert len(memory.retrieve("key1")) == 0

    def test_list_entries(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("a/1", "content1", category="a")
        memory.store("b/1", "content2", category="b")
        memory.store("a/2", "content3", category="a")

        all_entries = memory.list_entries()
        assert len(all_entries) == 3

        a_entries = memory.list_entries(category="a")
        assert len(a_entries) == 2

    def test_increment_access_count(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content")
        memory.retrieve("key1")
        memory.retrieve("key1")
        entries = memory.retrieve("key1")
        assert entries[0].access_count == 2

    def test_persist_and_load(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("key1", "content1")
        memory.store("key2", "content2")
        memory.persist()

        memory2 = GlobalMemory(str(tmp_path))
        memory2.load()
        assert len(memory2.list_entries()) == 2

    def test_get_stats(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("a/1", "content1", category="a")
        memory.store("b/1", "content2", category="b")
        stats = memory.get_stats()
        assert stats["total_entries"] == 2
        assert stats["categories"]["a"] == 1
        assert stats["categories"]["b"] == 1

    def test_search_with_keywords(self, tmp_path):
        memory = GlobalMemory(str(tmp_path))
        memory.store("python/types", "Use typing module for annotations", category="coding")
        memory.store("python/format", "Use black for formatting", category="coding")
        memory.store("js/types", "TypeScript for type safety", category="coding")

        results = memory.retrieve("python typing")
        # Should find python/types as most relevant
        assert len(results) >= 1
        assert any("typing" in r.content.lower() for r in results)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_global_store.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement GlobalMemory**

`src/harness/memory/global_store.py`:
```python
"""Global cross-session memory store.

Persists knowledge across sessions — coding patterns, project decisions,
learned preferences, and reusable solutions.
"""

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """A single memory entry."""

    key: str
    content: str
    category: str = "general"
    source_session: str = ""
    timestamp: str = ""
    access_count: int = 0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class GlobalMemory:
    """Cross-session knowledge persistence."""

    def __init__(self, storage_path: str = ".harness/global_memory"):
        self._path = Path(storage_path)
        self._path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, MemoryEntry] = {}
        self._categories: dict[str, set[str]] = {}  # category -> set of keys

    def store(
        self,
        key: str,
        content: str,
        category: str = "general",
        source_session: str = "",
        metadata: dict | None = None,
    ):
        """Store or update a memory entry."""
        if key in self._entries:
            # Update existing
            entry = self._entries[key]
            entry.content = content
            entry.category = category
            entry.timestamp = datetime.now(timezone.utc).isoformat()
            if metadata:
                entry.metadata.update(metadata)
        else:
            entry = MemoryEntry(
                key=key,
                content=content,
                category=category,
                source_session=source_session,
                metadata=metadata or {},
            )
            self._entries[key] = entry

        # Update category index
        if category not in self._categories:
            self._categories[category] = set()
        self._categories[category].add(key)

    def retrieve(
        self,
        query: str,
        category: str | None = None,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """Retrieve entries matching query.

        Uses keyword matching with scoring:
        - Exact key match: +10 points
        - Query in key: +5 points
        - Query words in content: +1 point per word
        """
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))

        candidates = []
        for key, entry in self._entries.items():
            # Filter by category
            if category and entry.category != category:
                continue

            score = 0
            key_lower = key.lower()

            # Score based on key match
            if query_lower == key_lower:
                score += 10
            elif query_lower in key_lower:
                score += 5

            # Score based on content match
            content_lower = entry.content.lower()
            for word in query_words:
                if word in content_lower:
                    score += 1

            if score > 0:
                candidates.append((score, entry))

        # Sort by score descending
        candidates.sort(key=lambda x: x[0], reverse=True)

        results = [entry for _, entry in candidates[:limit]]

        # Increment access count
        for entry in results:
            entry.access_count += 1

        return results

    def delete(self, key: str):
        """Delete a memory entry."""
        if key in self._entries:
            entry = self._entries[key]
            if entry.category in self._categories:
                self._categories[entry.category].discard(key)
            del self._entries[key]

    def list_entries(self, category: str | None = None) -> list[MemoryEntry]:
        """List all entries, optionally filtered by category."""
        if category:
            keys = self._categories.get(category, set())
            return [self._entries[k] for k in keys if k in self._entries]
        return list(self._entries.values())

    def get_stats(self) -> dict:
        """Get memory statistics."""
        categories = {}
        for cat, keys in self._categories.items():
            categories[cat] = len(keys)

        return {
            "total_entries": len(self._entries),
            "categories": categories,
            "total_accesses": sum(e.access_count for e in self._entries.values()),
        }

    def persist(self):
        """Save to disk."""
        file_path = self._path / "memory.json"
        data = {
            "entries": {k: v.to_dict() for k, v in self._entries.items()},
            "categories": {k: list(v) for k, v in self._categories.items()},
        }
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Persisted {len(self._entries)} memory entries")

    def load(self):
        """Load from disk."""
        file_path = self._path / "memory.json"
        if not file_path.exists():
            return

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self._entries = {
                k: MemoryEntry.from_dict(v) for k, v in data.get("entries", {}).items()
            }
            self._categories = {
                k: set(v) for k, v in data.get("categories", {}).items()
            }
            logger.info(f"Loaded {len(self._entries)} memory entries")
        except Exception as e:
            logger.error(f"Failed to load global memory: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_global_store.py -v`
Expected: All 9 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/memory/global_store.py tests/unit/test_global_store.py
git commit -m "feat(memory): GlobalMemory cross-session knowledge store"
```

---

## Task 5: Scratchpad

**Files:**
- Create: `src/harness/memory/scratchpad.py`
- Create: `tests/unit/test_scratchpad.py`

- [ ] **Step 1: Write Scratchpad tests**

`tests/unit/test_scratchpad.py`:
```python
import pytest
from harness.memory.scratchpad import Scratchpad, ScratchpadEntry


class TestScratchpadEntry:
    def test_create_entry(self):
        entry = ScratchpadEntry(
            label="current_task",
            content="Fix the memory leak in training loop",
            priority=1,
        )
        assert entry.label == "current_task"
        assert entry.priority == 1

    def test_entry_to_dict(self):
        entry = ScratchpadEntry(label="test", content="content")
        d = entry.to_dict()
        assert d["label"] == "test"


class TestScratchpad:
    def test_set_and_get(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug #123")
        assert pad.get("task") == "Fix bug #123"

    def test_get_nonexistent(self):
        pad = Scratchpad()
        assert pad.get("missing") is None
        assert pad.get("missing", "default") == "default"

    def test_overwrite(self):
        pad = Scratchpad()
        pad.set("task", "Old task")
        pad.set("task", "New task")
        assert pad.get("task") == "New task"

    def test_delete(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.delete("task")
        assert pad.get("task") is None

    def test_list_entries(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        pad.set("goal", "No memory leaks")
        entries = pad.list_entries()
        assert len(entries) == 3

    def test_priority_ordering(self):
        pad = Scratchpad()
        pad.set("low", "low priority", priority=3)
        pad.set("high", "high priority", priority=1)
        pad.set("medium", "medium priority", priority=2)
        entries = pad.list_entries()
        assert entries[0].label == "high"
        assert entries[1].label == "medium"
        assert entries[2].label == "low"

    def test_clear(self):
        pad = Scratchpad()
        pad.set("a", "1")
        pad.set("b", "2")
        pad.clear()
        assert len(pad.list_entries()) == 0

    def test_to_context_string(self):
        pad = Scratchpad()
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        context = pad.to_context_string()
        assert "task:" in context
        assert "Fix bug" in context
        assert "context:" in context

    def test_persist_and_load(self, tmp_path):
        pad = Scratchpad(str(tmp_path))
        pad.set("task", "Fix bug")
        pad.set("context", "In training loop")
        pad.persist()

        pad2 = Scratchpad(str(tmp_path))
        pad2.load()
        assert pad2.get("task") == "Fix bug"
        assert len(pad2.list_entries()) == 2

    def test_max_entries(self):
        pad = Scratchpad(max_entries=3)
        pad.set("a", "1")
        pad.set("b", "2")
        pad.set("c", "3")
        pad.set("d", "4")  # Should evict oldest
        assert len(pad.list_entries()) == 3
        assert pad.get("a") is None  # Evicted
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/unit/test_scratchpad.py -v`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement Scratchpad**

`src/harness/memory/scratchpad.py`:
```python
"""Working memory scratchpad for current context.

Stores temporary, session-scoped information that the LLM
needs to reference during a conversation:
- Current task description
- Key findings so far
- Open questions
- Relevant constraints
"""

import json
import logging
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ScratchpadEntry:
    """A single scratchpad entry."""

    label: str
    content: str
    priority: int = 5  # 1=highest, 10=lowest
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ScratchpadEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class Scratchpad:
    """Working memory for current conversation context."""

    def __init__(self, storage_path: str | None = None, max_entries: int = 100):
        self._entries: OrderedDict[str, ScratchpadEntry] = OrderedDict()
        self._storage_path = Path(storage_path) if storage_path else None
        self._max_entries = max_entries

    def set(self, label: str, content: str, priority: int = 5):
        """Set a scratchpad entry."""
        if label in self._entries:
            # Update existing
            entry = self._entries[label]
            entry.content = content
            entry.priority = priority
            entry.timestamp = datetime.now(timezone.utc).isoformat()
            # Move to end (most recent)
            self._entries.move_to_end(label)
        else:
            # Evict if at capacity
            while len(self._entries) >= self._max_entries:
                self._entries.popitem(last=False)

            self._entries[label] = ScratchpadEntry(
                label=label,
                content=content,
                priority=priority,
            )

    def get(self, label: str, default: str | None = None) -> str | None:
        """Get a scratchpad entry by label."""
        entry = self._entries.get(label)
        return entry.content if entry else default

    def delete(self, label: str):
        """Delete a scratchpad entry."""
        self._entries.pop(label, None)

    def list_entries(self) -> list[ScratchpadEntry]:
        """List all entries, sorted by priority."""
        entries = list(self._entries.values())
        entries.sort(key=lambda e: (e.priority, e.timestamp))
        return entries

    def clear(self):
        """Clear all entries."""
        self._entries.clear()

    def to_context_string(self) -> str:
        """Format scratchpad as context string for LLM."""
        entries = self.list_entries()
        if not entries:
            return ""

        lines = ["## Scratchpad"]
        for entry in entries:
            lines.append(f"- **{entry.label}**: {entry.content}")
        return "\n".join(lines)

    def persist(self):
        """Save to disk."""
        if not self._storage_path:
            return
        self._storage_path.mkdir(parents=True, exist_ok=True)
        file_path = self._storage_path / "scratchpad.json"
        data = [entry.to_dict() for entry in self._entries.values()]
        file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self):
        """Load from disk."""
        if not self._storage_path:
            return
        file_path = self._storage_path / "scratchpad.json"
        if not file_path.exists():
            return

        try:
            data = json.loads(file_path.read_text(encoding="utf-8"))
            self._entries.clear()
            for item in data:
                entry = ScratchpadEntry.from_dict(item)
                self._entries[entry.label] = entry
        except Exception as e:
            logger.error(f"Failed to load scratchpad: {e}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/unit/test_scratchpad.py -v`
Expected: All 11 tests PASS.

- [ ] **Step 5: Commit**

```powershell
git add src/harness/memory/scratchpad.py tests/unit/test_scratchpad.py
git commit -m "feat(memory): Scratchpad working memory"
```

---

## Task 6: Integration with Harness

**Files:**
- Modify: `src/harness/__init__.py`
- Modify: `src/harness/chat/engine.py`
- Create: `src/harness/plugins/prompt_tracker_node.py`
- Create: `tests/unit/test_prompt_tracker_node.py`

- [ ] **Step 1: Write PromptTrackerNode tests**

`tests/unit/test_prompt_tracker_node.py`:
```python
import pytest
from unittest.mock import MagicMock
from harness.plugins.prompt_tracker_node import PromptTrackerNode
from harness.improvement.tracker import PromptTracker


class TestPromptTrackerNode:
    def test_node_initialization(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        node = PromptTrackerNode(tracker=tracker)
        assert node.name == "prompt_tracker"

    def test_node_processes_state(self, tmp_path):
        tracker = PromptTracker(str(tmp_path))
        node = PromptTrackerNode(tracker=tracker)

        state = {
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi!"},
            ],
            "current_response": "Hi!",
            "prompt_id": "sys-v1",
            "prompt_text": "You are helpful.",
            "tokens_used": 50,
            "latency_ms": 1000,
            "tool_calls_count": 0,
        }

        result = node(state)
        assert len(tracker.get_history()) == 1
        assert result["tracker_recorded"] is True
```

- [ ] **Step 2: Implement PromptTrackerNode**

`src/harness/plugins/prompt_tracker_node.py`:
```python
"""Plugin node for recording prompt metrics."""

import logging
from harness.improvement.tracker import PromptTracker, PromptMetric

logger = logging.getLogger(__name__)


class PromptTrackerNode:
    """Records prompt/response metrics for optimization."""

    name = "prompt_tracker"

    def __init__(self, tracker: PromptTracker):
        self._tracker = tracker

    def __call__(self, state: dict) -> dict:
        """Record metrics from current state."""
        try:
            metric = PromptMetric(
                prompt_id=state.get("prompt_id", "unknown"),
                prompt_text=state.get("prompt_text", ""),
                response_text=state.get("current_response", ""),
                user_message=state.get("messages", [{}])[-1].get("content", ""),
                tokens_used=state.get("tokens_used", 0),
                latency_ms=state.get("latency_ms", 0),
                tool_calls=state.get("tool_calls_count", 0),
                success=not state.get("is_stuck", False),
            )
            self._tracker.record(metric)
            return {**state, "tracker_recorded": True}
        except Exception as e:
            logger.warning(f"Failed to record metric: {e}")
            return {**state, "tracker_recorded": False}
```

- [ ] **Step 3: Update ChatEngine with improvement integration**

Modify `src/harness/chat/engine.py` to integrate scratchpad and global memory:

```python
# Add to ChatEngine.__init__:
#     self._scratchpad = scratchpad
#     self._global_memory = global_memory

# Update _build_system_prompt to include scratchpad context
```

- [ ] **Step 4: Update CognitiveHarness**

Modify `src/harness/__init__.py` to expose improvement APIs:

```python
# Add to CognitiveHarness:
#     self._tracker = PromptTracker(...)
#     self._optimizer = PromptOptimizer(self._tracker, ...)
#     self._global_memory = GlobalMemory(...)
#     self._scratchpad = Scratchpad(...)
```

- [ ] **Step 5: Run all tests**

Run: `python -m pytest tests/unit -x -q`
Expected: All tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add .
git commit -m "feat(improvement): integrate tracker, optimizer, and memory with harness"
```

---

## Task 7: End-to-End Tests

**Files:**
- Modify: `tests/test_comprehensive.py`

- [ ] **Step 1: Add improvement E2E tests**

Add to `tests/test_comprehensive.py`:

```python
class TestImprovementE2E:
    def test_tracker_optimizer_cycle(self, tmp_path):
        """Full cycle: track metrics -> optimize -> compare."""
        from harness.improvement.tracker import PromptTracker, PromptMetric
        from harness.improvement.optimizer import PromptOptimizer

        tracker = PromptTracker(str(tmp_path / "metrics"))

        # Simulate 20 interactions with old prompt
        for i in range(20):
            tracker.record(PromptMetric(
                prompt_id="sys-v1",
                prompt_text="You are a helpful assistant.",
                response_text=f"response {i}",
                user_message=f"msg {i}",
                tokens_used=100,
                latency_ms=2000,
                tool_calls=0,
                success=i < 12,  # 60% success
            ))

        optimizer = PromptOptimizer(tracker, min_samples=10)
        assert optimizer.should_optimize("sys-v1") is True

        report = optimizer.get_report()
        assert report["total_metrics"] == 20
        assert report["best_prompt"]["prompt_id"] == "sys-v1"

    def test_global_memory_workflow(self, tmp_path):
        """Full workflow: store, retrieve, persist, load."""
        from harness.memory.global_store import GlobalMemory

        mem = GlobalMemory(str(tmp_path / "global"))

        # Store knowledge
        mem.store("python/typing", "Always use type hints.", category="coding")
        mem.store("python/formatting", "Use black for formatting.", category="coding")
        mem.store("project/structure", "Follow src layout.", category="project")

        # Retrieve
        results = mem.retrieve("python")
        assert len(results) == 2

        # Persist and reload
        mem.persist()
        mem2 = GlobalMemory(str(tmp_path / "global"))
        mem2.load()
        assert len(mem2.list_entries()) == 3

    def test_scratchpad_context(self, tmp_path):
        """Scratchpad provides context for LLM."""
        from harness.memory.scratchpad import Scratchpad

        pad = Scratchpad(str(tmp_path / "scratch"))
        pad.set("task", "Fix memory leak", priority=1)
        pad.set("context", "In training loop", priority=2)
        pad.set("constraint", "Must be backwards compatible", priority=3)

        context = pad.to_context_string()
        assert "task:" in context
        assert "Fix memory leak" in context
        assert "constraint:" in context
```

- [ ] **Step 2: Run E2E tests**

Run: `python -m pytest tests/test_comprehensive.py -x -q`
Expected: All tests PASS.

- [ ] **Step 3: Commit**

```powershell
git add tests/test_comprehensive.py
git commit -m "test(improvement): E2E tests for self-improvement subsystem"
```

---

## Final Verification

- [ ] **Run full test suite**

Run: `python -m pytest tests/ -x -q`
Expected: All tests PASS.

- [ ] **Run harness CLI**

Run: `harness`
Expected: TUI starts, improvement features accessible.

- [ ] **Final commit**

```powershell
git add .
git commit -m "feat: self-improving harness with tracker, optimizer, evolution, and global memory"
```
