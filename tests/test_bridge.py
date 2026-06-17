import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from hermes_kit import bridge
from hermes_kit.bridge import RateLimitExceeded


class TestOverrideFunctions:
    def test_set_and_get_override(self):
        bridge._model_overrides.clear()
        bridge.set_override("s1", "gpt-4o", provider="openai")
        assert bridge.get_override("s1") == {"model": "gpt-4o", "provider": "openai"}

    def test_get_override_missing_returns_none(self):
        assert bridge.get_override("nonexistent") is None

    def test_clear_override_removes_entry(self):
        bridge.set_override("s2", model="claude")
        bridge.clear_override("s2")
        assert bridge.get_override("s2") is None

    def test_clear_override_missing_no_error(self):
        bridge.clear_override("nonexistent")


class TestFallbackFunctions:
    def setup_method(self):
        bridge._fallback_chains.clear()
        bridge._fallback_index.clear()
        bridge._model_overrides.clear()

    def test_set_and_get_fallback_chain(self):
        chain = ["gpt-4o", "claude-sonnet-4"]
        bridge.set_fallback_chain("s1", chain)
        assert bridge.get_fallback_chain("s1") == chain
        assert bridge._fallback_index["s1"] == 0

    def test_get_fallback_chain_missing(self):
        assert bridge.get_fallback_chain("nonexistent") is None

    def test_advance_fallback_increments_index(self):
        bridge.set_fallback_chain("s1", ["a", "b", "c"])
        bridge.advance_fallback("s1")
        assert bridge._fallback_index["s1"] == 1
        bridge.advance_fallback("s1")
        assert bridge._fallback_index["s1"] == 2

    def test_advance_fallback_missing_key_no_error(self):
        bridge.advance_fallback("nonexistent")

    def test_get_current_fallback_returns_correct_model(self):
        bridge.set_fallback_chain("s1", ["a", "b", "c"])
        assert bridge.get_current_fallback("s1") == "a"
        bridge.advance_fallback("s1")
        assert bridge.get_current_fallback("s1") == "b"

    def test_get_current_fallback_empty_chain(self):
        assert bridge.get_current_fallback("nonexistent") is None

    def test_get_current_fallback_past_end(self):
        bridge.set_fallback_chain("s1", ["a"])
        bridge.advance_fallback("s1")
        assert bridge.get_current_fallback("s1") is None

    def test_retry_with_fallback_advances_and_sets_override(self):
        bridge.set_fallback_chain("s1", ["a", "b"])
        result = bridge.retry_with_fallback("s1")
        assert result == "b"
        override = bridge.get_override("s1")
        assert override["model"] == "b"

    def test_retry_with_fallback_past_end_returns_none(self):
        bridge.set_fallback_chain("s1", ["a"])
        bridge.retry_with_fallback("s1")  # advances to index 1, past end
        result = bridge.retry_with_fallback("s1")  # advances to index 2, past end
        assert result is None

    def test_retry_with_fallback_missing_key(self):
        assert bridge.retry_with_fallback("nonexistent") is None


class TestRateCounterFunctions:
    def setup_method(self):
        bridge._rate_counters.clear()
        bridge._rate_windows.clear()
        bridge._rate_limited.clear()

    def test_reset_sets_count_and_window(self):
        bridge.increment_rate_counter("s1")
        bridge.reset_rate_counter("s1")
        assert bridge._rate_counters["s1"] == 0
        assert bridge._rate_windows["s1"] > 0

    def test_increment_starts_from_zero(self):
        count = bridge.increment_rate_counter("s1")
        assert count == 1
        assert "s1" in bridge._rate_windows

    def test_increment_accumulates(self):
        bridge.increment_rate_counter("s1")
        bridge.increment_rate_counter("s1")
        assert bridge.increment_rate_counter("s1") == 3

    def test_get_rate_window_start_default(self):
        assert bridge.get_rate_window_start("nonexistent") == 0.0

    def test_get_rate_window_start_after_reset(self):
        before = time.time()
        bridge.reset_rate_counter("s1")
        window = bridge.get_rate_window_start("s1")
        assert window >= before


class TestRateLimitFunctions:
    def setup_method(self):
        bridge._rate_limited.clear()

    def test_set_and_is_rate_limited(self):
        assert not bridge.is_rate_limited("s1")
        bridge.set_rate_limited("s1")
        assert bridge.is_rate_limited("s1")

    def test_reset_removes_rate_limited(self):
        bridge.set_rate_limited("s1")
        bridge.reset_rate_counter("s1")
        assert not bridge.is_rate_limited("s1")

    def test_rate_limited_across_sessions(self):
        bridge.set_rate_limited("s1")
        assert not bridge.is_rate_limited("s2")


class TestCostFunctions:
    def setup_method(self):
        bridge._session_costs.clear()
        bridge._last_usage_totals.clear()

    def test_track_cost_adds_entry(self):
        bridge.track_cost("s1", "qwen3.6-plus", 1000, 500)
        assert "s1" in bridge._session_costs
        assert "qwen3.6-plus" in bridge._session_costs["s1"]
        assert bridge._session_costs["s1"]["qwen3.6-plus"] > 0

    def test_track_cost_unknown_model_zero_cost(self):
        bridge.track_cost("s1", "unknown-model", 1000, 500)
        assert bridge._session_costs["s1"]["unknown-model"] == 0.0

    def test_get_session_cost_sums_all_models(self):
        bridge.track_cost("s1", "qwen3.6-plus", 1_000_000, 500_000)
        cost = bridge.get_session_cost("s1")
        assert cost > 0

    def test_get_session_cost_empty(self):
        assert bridge.get_session_cost("nonexistent") == 0.0

    def test_get_session_cost_breakdown(self):
        bridge.track_cost("s1", "qwen3.6-plus", 1000, 500)
        breakdown = bridge.get_session_cost_breakdown("s1")
        assert "qwen3.6-plus" in breakdown

    def test_reset_session_cost(self):
        bridge.track_cost("s1", "qwen3.6-plus", 1000, 500)
        bridge.reset_session_cost("s1")
        assert bridge.get_session_cost("s1") == 0.0

    def test_reset_session_cost_missing_no_error(self):
        bridge.reset_session_cost("nonexistent")

    def test_track_cost_from_totals_tracks_only_delta(self):
        bridge.track_cost_from_totals("s1", "qwen3.6-plus", 1000, 500)
        first = bridge.get_session_cost("s1")
        bridge.track_cost_from_totals("s1", "qwen3.6-plus", 1500, 700)
        second = bridge.get_session_cost("s1")
        assert second > first
        bridge.track_cost_from_totals("s1", "qwen3.6-plus", 1500, 700)
        assert bridge.get_session_cost("s1") == second

    def test_alert_cost_exceeded_prints(self, capsys):
        bridge.alert_cost_exceeded("s1", 5.5, 1.0)
        captured = capsys.readouterr()
        assert "COST ALERT" in captured.out
        assert "5.5000" in captured.out
        assert "1.00" in captured.out


class TestApplyOverride:
    def test_applies_model_from_override(self):
        override = {"model": "gpt-4o"}
        model, kwargs = bridge._apply_override(override, "default-model", {})
        assert model == "gpt-4o"

    def test_applies_provider_to_kwargs(self):
        override = {"model": "gpt-4o", "provider": "openai"}
        _, kwargs = bridge._apply_override(override, "gpt-4o", {})
        assert kwargs["provider"] == "openai"

    def test_applies_all_runtime_keys(self):
        override = {"model": "gpt-4o", "api_key": "sk-123", "base_url": "https://x.com", "api_mode": "chat"}
        _, kwargs = bridge._apply_override(override, "gpt-4o", {})
        assert kwargs["api_key"] == "sk-123"
        assert kwargs["base_url"] == "https://x.com"
        assert kwargs["api_mode"] == "chat"

    def test_does_not_override_none_values(self):
        override = {"model": "gpt-4o", "provider": None}
        _, kwargs = bridge._apply_override(override, "gpt-4o", {"provider": "existing"})
        assert kwargs["provider"] == "existing"

    def test_keeps_original_model_when_not_in_override(self):
        override = {"provider": "openai"}
        model, _ = bridge._apply_override(override, "original-model", {})
        assert model == "original-model"


class TestPatchGatewayResolver:
    def setup_method(self):
        self._original = None
        self._original_run_agent = None

    def teardown_method(self):
        if self._original is not None:
            from gateway.run import GatewayRunner
            GatewayRunner._resolve_session_agent_runtime = self._original
        if self._original_run_agent is not None:
            from gateway.run import GatewayRunner
            GatewayRunner._run_agent = self._original_run_agent

    def test_patch_replaces_resolver(self):
        from gateway.run import GatewayRunner

        self._original = GatewayRunner._resolve_session_agent_runtime
        self._original_run_agent = GatewayRunner._run_agent
        bridge.patch_gateway_resolver()
        assert getattr(GatewayRunner._resolve_session_agent_runtime, "__hermes_kit_patched__", False) is True
        assert getattr(GatewayRunner._run_agent, "__hermes_kit_patched__", False) is True

    def test_rate_limited_session_raises(self):
        import inspect
        from gateway.run import GatewayRunner

        self._original = GatewayRunner._resolve_session_agent_runtime
        self._original_run_agent = GatewayRunner._run_agent
        session_key = "agent:main:telegram:dm:test-user"

        bridge.set_rate_limited(session_key)

        bridge.patch_gateway_resolver()
        resolver = GatewayRunner._resolve_session_agent_runtime

        mock_runner = MagicMock()
        mock_runner._session_model_overrides = {}

        if inspect.iscoroutinefunction(resolver):
            async def run():
                with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
                    await resolver(mock_runner, session_key=session_key)

            asyncio.run(run())
        else:
            with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
                resolver(mock_runner, session_key=session_key)

        bridge._rate_limited.clear()

    def test_non_rate_limited_session_applies_override(self):
        import inspect
        from gateway.run import GatewayRunner

        self._original = GatewayRunner._resolve_session_agent_runtime
        self._original_run_agent = GatewayRunner._run_agent
        session_key = "agent:main:telegram:dm:test-user"

        bridge.set_override(session_key, model="gpt-4o-mini")

        bridge.patch_gateway_resolver()
        resolver = GatewayRunner._resolve_session_agent_runtime

        mock_runner = MagicMock()
        mock_runner._session_model_overrides = {}

        if inspect.iscoroutinefunction(resolver):
            async def run():
                model, kwargs = await resolver(mock_runner, session_key=session_key)
                assert model == "gpt-4o-mini"

            asyncio.run(run())
        else:
            model, kwargs = resolver(mock_runner, session_key=session_key)
            assert model == "gpt-4o-mini"

        bridge._model_overrides.clear()

    def test_remember_agent_run_stores_latest_result(self):
        bridge._latest_agent_run.clear()
        bridge._session_keys_by_session_id.clear()
        bridge.remember_agent_run(
            "session-1",
            "agent:main:telegram:dm:123",
            {
                "session_id": "session-1",
                "model": "qwen3.6-plus",
                "input_tokens": 1000,
                "output_tokens": 500,
            },
        )
        snapshot = bridge.get_latest_agent_run("session-1")
        assert snapshot["model"] == "qwen3.6-plus"
        assert snapshot["input_tokens"] == 1000
        assert bridge.get_session_key_for_session_id("session-1") == "agent:main:telegram:dm:123"
