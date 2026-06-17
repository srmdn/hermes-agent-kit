from unittest.mock import patch
from hermes_kit.hooks.fallback.handler import handle

SET_CHAIN = "hermes_kit.hooks.fallback.handler.bridge.set_fallback_chain"
CHAINS = "hermes_kit.hooks.fallback.handler._CHAINS"


def make_context(chat_id="123", platform="telegram"):
    return {
        "session_key": f"agent:main:{platform}:dm:{chat_id}",
        "session_id": f"session-{chat_id}",
        "chat_id": chat_id,
        "platform": platform,
    }


class TestFallbackHandler:
    def test_registers_global_chain(self):
        ctx = make_context()
        chain = ["claude-sonnet-4", "deepseek/deepseek-chat"]
        with patch(CHAINS, {"global": chain}):
            with patch(SET_CHAIN) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once_with(ctx["session_key"], chain)

    def test_no_chain_configured_no_override(self):
        ctx = make_context()
        with patch(CHAINS, {}):
            with patch(SET_CHAIN) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.assert_not_called()

    def test_agent_start_uses_session_mapping(self):
        ctx = make_context()
        chain = ["claude-sonnet-4"]
        with patch(CHAINS, {"global": chain}):
            with patch(SET_CHAIN) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.reset_mock()
                asyncio.run(handle("agent:start", {"session_id": ctx["session_id"], "platform": "telegram"}))
                mock_set.assert_called_once_with(ctx["session_key"], chain)

    def test_handles_missing_session_key(self):
        ctx = {"platform": "telegram"}
        chain = ["claude-sonnet-4"]
        with patch(CHAINS, {"global": chain}):
            with patch(SET_CHAIN) as mock_set:
                import asyncio
                asyncio.run(handle("agent:start", ctx))
                mock_set.assert_not_called()
