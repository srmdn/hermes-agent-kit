from unittest.mock import patch
from hermes_kit.hooks.cost_tracker.handler import handle

TRACK = "hermes_kit.hooks.cost_tracker.handler.bridge.track_cost"
TRACK_TOTALS = "hermes_kit.hooks.cost_tracker.handler.bridge.track_cost_from_totals"
GET_COST = "hermes_kit.hooks.cost_tracker.handler.bridge.get_session_cost"
RESET = "hermes_kit.hooks.cost_tracker.handler.bridge.reset_session_cost"
RESET_BASELINE = "hermes_kit.hooks.cost_tracker.handler.bridge.reset_usage_baseline"
ALERT = "hermes_kit.hooks.cost_tracker.handler.bridge.alert_cost_exceeded"
THRESHOLD = "hermes_kit.hooks.cost_tracker.handler._ALERT_THRESHOLD"
LATEST_RUN = "hermes_kit.hooks.cost_tracker.handler.bridge.get_latest_agent_run"


def make_context(**kwargs):
    return {
        "session_key": "agent:main:telegram:dm:123",
        "user_id": "123",
        "platform": "telegram",
        **kwargs,
    }


class TestCostTracker:
    def test_session_start_resets_cost_and_baseline(self):
        ctx = make_context(session_id="sess-1")
        with patch(RESET) as mock_reset:
            with patch(RESET_BASELINE) as mock_baseline:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_reset.assert_called_once_with(ctx["session_key"])
                mock_baseline.assert_called_once_with(ctx["session_key"])

    def test_tracks_tokens_on_step(self):
        ctx = make_context(usage={"prompt_tokens": 1000, "completion_tokens": 500}, model="gpt-4o-mini")
        with patch(TRACK) as mock_track:
            import asyncio
            asyncio.run(handle("agent:step", ctx))
            mock_track.assert_called_once_with(
                ctx["session_key"], "gpt-4o-mini", 1000, 500
            )

    def test_no_usage_no_tracking(self):
        ctx = make_context()
        with patch(TRACK) as mock_track:
            import asyncio
            asyncio.run(handle("agent:step", ctx))
            mock_track.assert_not_called()

    def test_resets_cost_on_agent_end(self):
        ctx = make_context(session_id="sess-2")
        with patch(GET_COST, return_value=0.5):
            with patch(LATEST_RUN, return_value=None):
                with patch(THRESHOLD, 0.0):
                    with patch(RESET) as mock_reset:
                        import asyncio
                        asyncio.run(handle("session:start", ctx))
                        mock_reset.reset_mock()
                        asyncio.run(handle("agent:end", {"session_id": "sess-2", "user_id": "123", "platform": "telegram"}))
                        mock_reset.assert_called_once_with(ctx["session_key"])

    def test_alerts_when_cost_exceeds_threshold(self):
        ctx = make_context(session_id="sess-3")
        with patch(GET_COST, return_value=5.0):
            with patch(LATEST_RUN, return_value=None):
                with patch(THRESHOLD, 1.0):
                    with patch(ALERT) as mock_alert:
                        import asyncio
                        asyncio.run(handle("session:start", ctx))
                        asyncio.run(handle("agent:end", {"session_id": "sess-3", "user_id": "123", "platform": "telegram"}))
                        mock_alert.assert_called_once()

    def test_no_alert_when_below_threshold(self):
        ctx = make_context(session_id="sess-4")
        with patch(GET_COST, return_value=0.5):
            with patch(LATEST_RUN, return_value=None):
                with patch(THRESHOLD, 1.0):
                    with patch(ALERT) as mock_alert:
                        import asyncio
                        asyncio.run(handle("session:start", ctx))
                        asyncio.run(handle("agent:end", {"session_id": "sess-4", "user_id": "123", "platform": "telegram"}))
                        mock_alert.assert_not_called()

    def test_agent_end_tracks_from_latest_agent_run(self):
        ctx = make_context(session_id="sess-5")
        with patch(LATEST_RUN, return_value={"model": "qwen3.6-plus", "input_tokens": 1000, "output_tokens": 500}):
            with patch(TRACK_TOTALS) as mock_track:
                with patch(GET_COST, return_value=0.5):
                    with patch(THRESHOLD, 0.0):
                        with patch(RESET):
                            import asyncio
                            asyncio.run(handle("session:start", ctx))
                            asyncio.run(handle("agent:end", {"session_id": "sess-5", "user_id": "123", "platform": "telegram"}))
                            mock_track.assert_called_once_with(ctx["session_key"], "qwen3.6-plus", 1000, 500)
