from unittest.mock import MagicMock

import pytest

from hermes_kit import bridge
from hermes_kit.bridge import RateLimitExceeded


def _save_original():
    from gateway.run import GatewayRunner
    return GatewayRunner._resolve_session_agent_runtime


def _restore_original(original):
    from gateway.run import GatewayRunner
    GatewayRunner._resolve_session_agent_runtime = original


def _clear_bridge_state():
    bridge._model_overrides.clear()
    bridge._fallback_chains.clear()
    bridge._fallback_index.clear()
    bridge._rate_counters.clear()
    bridge._rate_windows.clear()
    bridge._rate_limited.clear()
    bridge._session_costs.clear()


def _make_mock_runner(session_model_overrides=None):
    runner = MagicMock()
    runner._session_model_overrides = session_model_overrides or {}
    return runner


class TestBridgePatchAgainstRealHermes:
    def setup_method(self):
        _clear_bridge_state()
        self._original = _save_original()

    def teardown_method(self):
        _restore_original(self._original)
        _clear_bridge_state()

    def test_patch_replaces_real_resolver(self):
        bridge.patch_gateway_resolver()

        from gateway.run import GatewayRunner
        assert GatewayRunner._resolve_session_agent_runtime is not self._original

    def test_patch_idempotent(self):
        bridge.patch_gateway_resolver()
        bridge.patch_gateway_resolver()

    def test_original_resolver_restored(self):
        bridge.patch_gateway_resolver()

        _restore_original(self._original)

        from gateway.run import GatewayRunner
        assert GatewayRunner._resolve_session_agent_runtime is self._original


class TestModelOverrideEndToEnd:
    def setup_method(self):
        _clear_bridge_state()
        self._original = _save_original()
        bridge.patch_gateway_resolver()

        from gateway.run import GatewayRunner
        self._resolver = GatewayRunner._resolve_session_agent_runtime

    def teardown_method(self):
        _restore_original(self._original)
        _clear_bridge_state()

    def test_override_changes_model(self):
        bridge.set_override("test-session", model="custom-model-v2")

        runner = _make_mock_runner()
        model, _runtime = self._resolver(runner, session_key="test-session")

        assert model == "custom-model-v2"

    def test_no_override_passes_through(self):
        runner = _make_mock_runner()
        model, runtime = self._resolver(runner, session_key="unknown")

        assert isinstance(model, str)
        assert isinstance(runtime, dict)

    def test_override_cleared_after_remove(self):
        bridge.set_override("test-session", model="custom-model-v2")
        bridge.clear_override("test-session")

        runner = _make_mock_runner()
        model, _runtime = self._resolver(runner, session_key="test-session")

        assert model != "custom-model-v2"


class TestRateLimitEndToEnd:
    def setup_method(self):
        _clear_bridge_state()
        self._original = _save_original()
        bridge.patch_gateway_resolver()

        from gateway.run import GatewayRunner
        self._resolver = GatewayRunner._resolve_session_agent_runtime

    def teardown_method(self):
        _restore_original(self._original)
        _clear_bridge_state()

    def test_rate_limited_session_raises_rate_limit_exceeded(self):
        bridge.set_rate_limited("blocked-session")

        runner = _make_mock_runner()
        with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
            self._resolver(runner, session_key="blocked-session")

    def test_rate_limit_specific_to_session(self):
        bridge.set_rate_limited("session-a")

        runner = _make_mock_runner()

        model_b, _runtime = self._resolver(runner, session_key="session-b")
        assert isinstance(model_b, str)

        with pytest.raises(RateLimitExceeded, match="Rate limit exceeded"):
            self._resolver(runner, session_key="session-a")


class TestPatchPreservesOriginalBehavior:
    def setup_method(self):
        _clear_bridge_state()
        self._original = _save_original()
        bridge.patch_gateway_resolver()

        from gateway.run import GatewayRunner
        self._resolver = GatewayRunner._resolve_session_agent_runtime

    def teardown_method(self):
        _restore_original(self._original)
        _clear_bridge_state()

    def test_unpatched_sessions_still_work(self):
        runner = _make_mock_runner()
        model, runtime = self._resolver(runner, session_key="clean-session")

        assert isinstance(model, str)
        assert isinstance(runtime, dict)

    def test_multiple_overrides_different_sessions(self):
        overrides = {
            "s1": "gpt-4o",
            "s2": "claude-sonnet-4",
            "s3": "deepseek-chat",
        }
        for key, model in overrides.items():
            bridge.set_override(key, model=model)

        runner = _make_mock_runner()
        for session_key, expected_model in overrides.items():
            model, _runtime = self._resolver(runner, session_key=session_key)
            assert model == expected_model, (
                f"Expected {expected_model} for {session_key}, got {model}"
            )
