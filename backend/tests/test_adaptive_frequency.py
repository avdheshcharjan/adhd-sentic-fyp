"""
Unit tests for the Thompson Sampling Bandit.

Covers:
  - Initial weak prior (Beta(2, 2))
  - should_deliver returns bool
  - update shifts alpha on success
  - update shifts beta on failure
  - Context key discretisation
  - Stats computation
"""

from services.adaptive_frequency import ThompsonSamplingBandit


def _bandit() -> ThompsonSamplingBandit:
    return ThompsonSamplingBandit()


class TestInitialState:
    def test_initial_prior_is_weak(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        params = bandit.get_arm_params(ctx)
        assert params["alpha"] == 2.0
        assert params["beta"] == 2.0

    def test_should_deliver_returns_bool(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        result = bandit.should_deliver(ctx)
        assert isinstance(result, bool)


class TestUpdates:
    def test_success_increases_alpha(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        before = bandit.get_arm_params(ctx)["alpha"]
        bandit.update(ctx, success=True)
        after = bandit.get_arm_params(ctx)["alpha"]
        assert after == before + 1

    def test_failure_increases_beta(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        before = bandit.get_arm_params(ctx)["beta"]
        bandit.update(ctx, success=False)
        after = bandit.get_arm_params(ctx)["beta"]
        assert after == before + 1

    def test_success_does_not_change_beta(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        before = bandit.get_arm_params(ctx)["beta"]
        bandit.update(ctx, success=True)
        after = bandit.get_arm_params(ctx)["beta"]
        assert after == before


class TestContextKey:
    def test_different_hours_different_keys(self):
        bandit = _bandit()
        ctx1 = {"hour": 2, "whoop_recovery": 50, "minutes_since_last": 60}
        ctx2 = {"hour": 14, "whoop_recovery": 50, "minutes_since_last": 60}
        key1 = bandit._context_key(ctx1)
        key2 = bandit._context_key(ctx2)
        assert key1 != key2

    def test_different_recovery_different_keys(self):
        bandit = _bandit()
        ctx1 = {"hour": 10, "whoop_recovery": 20, "minutes_since_last": 60}
        ctx2 = {"hour": 10, "whoop_recovery": 80, "minutes_since_last": 60}
        key1 = bandit._context_key(ctx1)
        key2 = bandit._context_key(ctx2)
        assert key1 != key2

    def test_same_context_same_key(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        assert bandit._context_key(ctx) == bandit._context_key(ctx)


class TestStats:
    def test_initial_stats_empty(self):
        bandit = _bandit()
        assert bandit.get_stats() == {}

    def test_stats_after_observations(self):
        bandit = _bandit()
        ctx = {"hour": 10, "whoop_recovery": 50, "minutes_since_last": 60}
        bandit.update(ctx, success=True)
        bandit.update(ctx, success=False)
        stats = bandit.get_stats()
        assert len(stats) == 1
        key = list(stats.keys())[0]
        assert stats[key]["n_observations"] == 2
        assert 0 < stats[key]["expected_reward"] < 1
