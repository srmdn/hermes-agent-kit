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


# ── Patch targets for YAML config ──────────────────────────────────────

READ_ROUTING = "hermes_kit.hooks.router.handler._read_routing"
LIMITS = "hermes_kit.hooks.rate_limiter.handler._LIMITS"
CHAINS = "hermes_kit.hooks.fallback.handler._CHAINS"
THRESHOLD = "hermes_kit.hooks.cost_tracker.handler._ALERT_THRESHOLD"


# ═══════════════════════════════════════════════════════════════════════
#  Router Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestRouterHookE2E:
    def setup_method(self):
        bridge._model_overrides.clear()
        bridge._session_keys_by_session_id.clear()

    def test_session_start_sets_override(self):
        ctx = make_context()
        with patch(READ_ROUTING, return_value=({"123": {"model": "gpt-4o"}}, None)):
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
        with patch(READ_ROUTING, return_value=({"123": {"model": "gpt-4o"}}, {"model": "gpt-4o-mini"})):
            asyncio.run(router_handle("agent:step", ctx))

        # No override should have been set for non-start/reset events
        assert bridge.get_override(ctx["session_key"]) is None

    def test_session_start_reloads_updated_routing_file(self, tmp_path):
        import hermes_kit.hooks.router.handler as handler

        original_path = handler._routing_path
        handler._routing_path = tmp_path / "topic_router.yaml"
        try:
            handler._routing_path.write_text("topics:\n  \"123\":\n    model: gpt-4o\n")
            ctx = make_context()
            asyncio.run(router_handle("session:start", ctx))
            assert bridge.get_override(ctx["session_key"])["model"] == "gpt-4o"

            bridge.clear_override(ctx["session_key"])
            handler._routing_path.write_text("topics:\n  \"123\":\n    model: claude-sonnet-4\n")
            asyncio.run(router_handle("session:start", ctx))
            assert bridge.get_override(ctx["session_key"])["model"] == "claude-sonnet-4"
        finally:
            handler._routing_path = original_path


# ═══════════════════════════════════════════════════════════════════════
#  Rate Limiter Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestRateLimiterHookE2E:
    def setup_method(self):
        bridge._rate_counters.clear()
        bridge._rate_windows.clear()
        bridge._rate_limited.clear()
        bridge._session_keys_by_session_id.clear()

    def test_session_start_resets_counter(self):
        ctx = make_context()
        session_key = ctx["session_key"]

        bridge._rate_counters[session_key] = 99

        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("session:start", ctx))

        assert bridge._rate_counters[session_key] == 0
        assert not bridge.is_rate_limited(session_key)

    def test_agent_step_increments_counter(self):
        start_ctx = make_context(session_id="sess-1")
        step_ctx = {"session_id": "sess-1", "user_id": "123", "platform": "telegram"}

        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("session:start", start_ctx))
            asyncio.run(rate_limiter_handle("agent:step", step_ctx))

        assert bridge._rate_counters[start_ctx["session_key"]] == 1
        assert not bridge.is_rate_limited(start_ctx["session_key"])

    def test_exceeding_limit_sets_rate_limited(self):
        start_ctx = make_context(session_id="sess-2")
        step_ctx = {"session_id": "sess-2", "user_id": "123", "platform": "telegram"}
        session_key = start_ctx["session_key"]

        # Pre-seed counter at 2 so next increment returns 3 (> limit of 2)
        bridge._rate_windows[session_key] = time.time()
        bridge._rate_counters[session_key] = 2

        with patch(LIMITS, {"global": {"max_messages_per_window": 2, "window_seconds": 3600}}):
            asyncio.run(rate_limiter_handle("session:start", start_ctx))
            bridge._rate_counters[session_key] = 2
            bridge._rate_windows[session_key] = time.time()
            asyncio.run(rate_limiter_handle("agent:step", step_ctx))

        assert bridge.is_rate_limited(session_key) is True


# ═══════════════════════════════════════════════════════════════════════
#  Fallback Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestFallbackHookE2E:
    def setup_method(self):
        bridge._fallback_chains.clear()
        bridge._fallback_index.clear()
        bridge._session_keys_by_session_id.clear()

    def test_session_start_sets_chain(self):
        ctx = make_context(session_id="sess-3")
        chain = ["claude-sonnet-4", "deepseek/deepseek-chat"]

        with patch(CHAINS, {"global": chain}):
            asyncio.run(fallback_handle("session:start", ctx))

        assert bridge.get_fallback_chain(ctx["session_key"]) == chain

    def test_agent_start_uses_session_mapping_when_no_session_key(self):
        bridge.register_session("sess-4", "agent:main:telegram:dm:123")
        ctx = {"session_id": "sess-4", "user_id": "123", "platform": "telegram"}
        chain = ["claude-sonnet-4", "deepseek/deepseek-chat"]

        with patch(CHAINS, {"global": chain}):
            asyncio.run(fallback_handle("agent:start", ctx))

        assert bridge.get_fallback_chain("agent:main:telegram:dm:123") == chain


# ═══════════════════════════════════════════════════════════════════════
#  Cost Tracker Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestCostTrackerHookE2E:
    def setup_method(self):
        bridge._session_costs.clear()
        bridge._session_keys_by_session_id.clear()
        bridge._latest_agent_run.clear()
        bridge._last_usage_totals.clear()

    def test_agent_end_tracks_cost_from_latest_agent_run(self):
        start_ctx = make_context(session_id="sess-5")
        end_ctx = {"session_id": "sess-5", "user_id": "123", "platform": "telegram"}

        asyncio.run(cost_tracker_handle("session:start", start_ctx))
        bridge.remember_agent_run(
            "sess-5",
            start_ctx["session_key"],
            {"session_id": "sess-5", "model": "qwen3.6-plus", "input_tokens": 1000, "output_tokens": 500},
        )
        asyncio.run(cost_tracker_handle("agent:end", end_ctx))

        assert bridge.get_session_cost(start_ctx["session_key"]) == 0.0
        assert bridge._last_usage_totals[start_ctx["session_key"]] == (1000, 500)

    def test_agent_end_resets_cost(self):
        ctx = make_context(session_id="sess-6")
        session_key = ctx["session_key"]

        asyncio.run(cost_tracker_handle("session:start", ctx))
        bridge.track_cost(session_key, "qwen3.6-plus", 1000, 500)

        with patch(THRESHOLD, 0.0):
            asyncio.run(cost_tracker_handle("agent:end", {"session_id": "sess-6", "user_id": "123", "platform": "telegram"}))

        assert bridge.get_session_cost(session_key) == 0.0
