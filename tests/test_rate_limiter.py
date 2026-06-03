from unittest.mock import patch
import time
from hermes_kit.hooks.rate_limiter.handler import handle

INC = "hermes_kit.hooks.rate_limiter.handler.bridge.increment_rate_counter"
RESET = "hermes_kit.hooks.rate_limiter.handler.bridge.reset_rate_counter"
WINDOW = "hermes_kit.hooks.rate_limiter.handler.bridge.get_rate_window_start"
LIMITED = "hermes_kit.hooks.rate_limiter.handler.bridge.set_rate_limited"
LIMITS = "hermes_kit.hooks.rate_limiter.handler._LIMITS"

NOW = time.time()


def make_context(user_id="123", platform="telegram"):
    return {
        "session_key": f"agent:main:{platform}:dm:{user_id}",
        "user_id": user_id,
        "platform": platform,
    }


class TestRateLimiter:
    def test_resets_counter_on_session_start(self):
        ctx = make_context()
        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            with patch(RESET) as mock_reset:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_reset.assert_called_once_with(ctx["session_key"])

    def test_increments_on_agent_step(self):
        ctx = make_context()
        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 3600}}):
            with patch(WINDOW, return_value=NOW):
                with patch(INC, return_value=5) as mock_inc:
                    import asyncio
                    asyncio.run(handle("agent:step", ctx))
                    mock_inc.assert_called_once_with(ctx["session_key"])

    def test_sets_rate_limited_when_exceeded(self):
        ctx = make_context()
        with patch(LIMITS, {"global": {"max_messages_per_window": 5, "window_seconds": 3600}}):
            with patch(WINDOW, return_value=NOW):
                with patch(INC, return_value=6):
                    with patch(LIMITED) as mock_limited:
                        import asyncio
                        asyncio.run(handle("agent:step", ctx))
                        mock_limited.assert_called_once_with(ctx["session_key"])

    def test_resets_window_when_expired(self):
        ctx = make_context()
        with patch(LIMITS, {"global": {"max_messages_per_window": 100, "window_seconds": 60}}):
            with patch(WINDOW, return_value=0):
                with patch(INC, return_value=50):
                    with patch(RESET) as mock_reset:
                        import asyncio
                        asyncio.run(handle("agent:step", ctx))
                        mock_reset.assert_called_once()

    def test_no_limit_configured_no_action(self):
        ctx = make_context()
        with patch(LIMITS, {}):
            with patch(INC) as mock_inc:
                import asyncio
                asyncio.run(handle("agent:step", ctx))
                mock_inc.assert_not_called()
