"""
Adaptive frequency learning via Thompson Sampling.

A contextual bandit that learns WHEN to deliver interventions.
Arms: [deliver, skip].  Reward: user returned to productive task within 5 min.

Cold start: weak Beta(2, 2) priors.
Personalisation kicks in after ~50-100 decision points (2-4 weeks).
"""

import random
from collections import defaultdict


class ThompsonSamplingBandit:
    """Thompson Sampling bandit for adaptive intervention frequency.

    The JITAI engine decides WHAT to suggest; this decides IF/WHEN.
    """

    def __init__(self) -> None:
        # Beta distribution parameters per context bucket
        # key: context_hash → {"alpha": successes+prior, "beta": failures+prior}
        self._arms: dict[str, dict[str, float]] = defaultdict(
            lambda: {"alpha": 2.0, "beta": 2.0},
        )

    # ── Public API ──────────────────────────────────────────────────

    def should_deliver(self, context: dict) -> bool:
        """Sample from posterior to decide whether to deliver.

        Returns True if we should deliver, False if we should skip.
        """
        key = self._context_key(context)
        arm = self._arms[key]
        sampled_reward = random.betavariate(arm["alpha"], arm["beta"])
        return sampled_reward > 0.5

    def update(self, context: dict, success: bool) -> None:
        """Update model based on outcome.

        Args:
            context: Same context dict used in should_deliver.
            success: True if user returned to productive task within 5 min.
        """
        key = self._context_key(context)
        if success:
            self._arms[key]["alpha"] += 1
        else:
            self._arms[key]["beta"] += 1

    def get_stats(self) -> dict:
        """Return learned parameters for debugging/logging."""
        return {
            key: {
                "expected_reward": arm["alpha"] / (arm["alpha"] + arm["beta"]),
                "n_observations": arm["alpha"] + arm["beta"] - 4,  # subtract prior
            }
            for key, arm in self._arms.items()
        }

    def get_arm_params(self, context: dict) -> dict:
        """Get raw alpha/beta for a context. Useful for tests."""
        key = self._context_key(context)
        arm = self._arms[key]
        return {"alpha": arm["alpha"], "beta": arm["beta"]}

    # ── Private helpers ──────────────────────────────────────────────

    def _context_key(self, context: dict) -> str:
        """Discretise context into buckets for the bandit."""
        hour_bucket = context.get("hour", 12) // 4  # 6 buckets
        recovery_score = context.get("whoop_recovery", 50)
        recovery = (
            "high" if recovery_score > 66
            else "low" if recovery_score < 34
            else "mid"
        )
        minutes = context.get("minutes_since_last", 60)
        recency = "recent" if minutes < 30 else "not_recent"
        return f"{hour_bucket}_{recovery}_{recency}"
