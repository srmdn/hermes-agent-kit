from unittest.mock import patch
from hermes_kit.hooks.cost_tracker.handler import handle

TRACK = "hermes_kit.hooks.cost_tracker.handler.bridge.track_cost"
GET_COST = "hermes_kit.hooks.cost_tracker.handler.bridge.get_session_cost"
RESET = "hermes_kit.hooks.cost_tracker.handler.bridge.reset_session_cost"
ALERT = "hermes_kit.hooks.cost_tracker.handler.bridge.alert_cost_exceeded"
THRESHOLD = "hermes_kit.hooks.cost_tracker.handler._ALERT_THRESHOLD"


def make_context(**kwargs):
    return {
        "session_key": "agent:main:telegram:dm:123",
        "user_id": "123",
        "platform": "telegram",
        **kwargs,
    }


class TestCostTracker:
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
        ctx = make_context()
        with patch(GET_COST, return_value=0.5):
            with patch(THRESHOLD, 0.0):
                with patch(RESET) as mock_reset:
                    import asyncio
                    asyncio.run(handle("agent:end", ctx))
                    mock_reset.assert_called_once_with(ctx["session_key"])

    def test_alerts_when_cost_exceeds_threshold(self):
        ctx = make_context()
        with patch(GET_COST, return_value=5.0):
            with patch(THRESHOLD, 1.0):
                with patch(ALERT) as mock_alert:
                    import asyncio
                    asyncio.run(handle("agent:end", ctx))
                    mock_alert.assert_called_once()

    def test_no_alert_when_below_threshold(self):
        ctx = make_context()
        with patch(GET_COST, return_value=0.5):
            with patch(THRESHOLD, 1.0):
                with patch(ALERT) as mock_alert:
                    import asyncio
                    asyncio.run(handle("agent:end", ctx))
                    mock_alert.assert_not_called()
