import asyncio
import time
from unittest.mock import patch

from hermes_kit import bridge
from hermes_kit.hooks.cost_tracker.handler import handle as cost_tracker_handle
from hermes_kit.hooks.fallback.handler import handle as fallback_handle
from hermes_kit.hooks.rate_limiter.handler import handle as rate_limiter_handle
from hermes_kit.hooks.router.handler import handle as router_handle


def make_context(session_key="agent:main:telegram:dm:123", **kwargs):
    return {"session_key": session_key, "user_id": "123", "platform": "telegram", **kwargs}


# ── Patch targets for YAML config (module-level constants) ─────────────

ROUTING = "hermes_kit.hooks.router.handler._ROUTING"
DEFAULT = "hermes_kit.hooks.router.handler._DEFAULT"
LIMITS = "hermes_kit.hooks.rate_limiter.handler._LIMITS"
CHAINS = "hermes_kit.hooks.fallback.handler._CHAINS"
THRESHOLD = "hermes_kit.hooks.cost_tracker.handler._ALERT_THRESHOLD"


# ═══════════════════════════════════════════════════════════════════════
#  Router Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestRouterHookE2E:
    def setup_method(self):
        bridge._model_overrides.clear()

    def test_session_start_sets_override(self):
        ctx = make_context()
        with patch(ROUTING, {"123": {"model": "gpt-4o"}}):
            with patch(DEFAULT, None):
                asyncio.run(router_handle("session:start", ctx))

        override = bridge.get_override(ctx["session_key"])
        assert override is not None
        assert override["model"] == "gpt-4o"

    def test_session_reset_clears_override(self):
        session_key = "agent:main:telegram:dm:111"
        bridge.set_override(session_key, model="test-model")

        ctx = {"session_key": session_key}
        asyncio.run(router_handle("session:reset", ctx))

        assert bridge.get_override(session_key) is None

    def test_irrelevant_event_noop(self):
        ctx = make_context()
        with patch(ROUTING, {"123": {"model": "gpt-4o"}}):
            with patch(DEFAULT, {"model": "gpt-4o-mini"}):
                asyncio.run(router_handle("agent:step", ctx))

        # No override should have been set for non-start/reset events
        assert bridge.get_override(ctx["session_key"]) is None


# ═══════════════════════════════════════════════════════════════════════
#  Rate Limiter Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestRateLimiterHookE2E:
    def setup_method(self):
        bridge._rate_counters.clear()
        bridge._rate_windows.clear()
        bridge._rate_limited.clear()

    def test_session_start_resets_counter(self):
        ctx = make_context()
        session_key = ctx["session_key"]

        bridge._rate_counters[session_key] = 99

        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("session:start", ctx))

        assert bridge._rate_counters[session_key] == 0
        assert not bridge.is_rate_limited(session_key)

    def test_agent_step_increments_counter(self):
        ctx = make_context()

        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("agent:step", ctx))

        assert bridge._rate_counters[ctx["session_key"]] == 1
        assert not bridge.is_rate_limited(ctx["session_key"])

    def test_exceeding_limit_sets_rate_limited(self):
        ctx = make_context()
        session_key = ctx["session_key"]

        # Pre-seed counter at 2 so next increment returns 3 (> limit of 2)
        bridge._rate_windows[session_key] = time.time()
        bridge._rate_counters[session_key] = 2

        with patch(LIMITS, {"global": {"max_messages_per_window": 2, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("agent:step", ctx))

        assert bridge.is_rate_limited(session_key) is True


# ═══════════════════════════════════════════════════════════════════════
#  Fallback Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestFallbackHookE2E:
    def setup_method(self):
        bridge._fallback_chains.clear()
        bridge._fallback_index.clear()

    def test_agent_start_sets_chain(self):
        ctx = make_context()
        chain = ["claude-sonnet-4", "deepseek/deepseek-chat"]

        with patch(CHAINS, {"global": chain}):
            asyncio.run(fallback_handle("agent:start", ctx))

        assert bridge.get_fallback_chain(ctx["session_key"]) == chain

    def test_no_chain_noop(self):
        ctx = make_context()

        with patch(CHAINS, {}):
            asyncio.run(fallback_handle("agent:start", ctx))

        assert bridge.get_fallback_chain(ctx["session_key"]) is None


# ═══════════════════════════════════════════════════════════════════════
#  Cost Tracker Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestCostTrackerHookE2E:
    def setup_method(self):
        bridge._session_costs.clear()

    def test_agent_step_tracks_cost(self):
        ctx = make_context(
            usage={"prompt_tokens": 1000, "completion_tokens": 500},
            model="qwen-3.6-plus",
        )

        asyncio.run(cost_tracker_handle("agent:step", ctx))

        cost = bridge.get_session_cost(ctx["session_key"])
        assert cost > 0

    def test_agent_end_resets_cost(self):
        ctx = make_context()
        session_key = ctx["session_key"]

        bridge.track_cost(session_key, "qwen-3.6-plus", 1000, 500)

        with patch(THRESHOLD, 0.0):
            asyncio.run(cost_tracker_handle("agent:end", ctx))

        assert bridge.get_session_cost(session_key) == 0.0
