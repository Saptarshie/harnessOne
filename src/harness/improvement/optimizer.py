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
