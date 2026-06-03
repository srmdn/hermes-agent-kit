import pytest
from unittest.mock import patch
from hermes_kit.hooks.router.handler import handle


@pytest.fixture(autouse=True)
def reset_bridge():
    from hermes_kit import bridge

    bridge._model_overrides.clear()
    yield
    bridge._model_overrides.clear()


def make_context(chat_id="123456789", thread_id=None, platform="telegram"):
    parts = ["agent", "main", platform, "dm", chat_id]
    if thread_id:
        parts.append(thread_id)
    return {
        "session_key": ":".join(parts),
        "chat_id": chat_id,
        "platform": platform,
    }


SET_OVERRIDE = "hermes_kit.hooks.router.handler.bridge.set_override"
ROUTING = "hermes_kit.hooks.router.handler._ROUTING"
DEFAULT = "hermes_kit.hooks.router.handler._DEFAULT"


class TestSessionKeyParsing:
    def test_sets_override_when_default_exists(self):
        ctx = make_context(chat_id="111")
        with patch(ROUTING, {}):
            with patch(DEFAULT, {"model": "openai/gpt-4o-mini"}):
                with patch(SET_OVERRIDE) as mock_set:
                    import asyncio
                    asyncio.run(handle("session:start", ctx))
                    mock_set.assert_called_once()
                    assert mock_set.call_args[0][0] == ctx["session_key"]

    def test_handles_missing_session_key(self):
        ctx = {"platform": "telegram"}
        with patch(SET_OVERRIDE) as mock_set:
            import asyncio
            asyncio.run(handle("session:start", ctx))
            mock_set.assert_not_called()


class TestRouterLookup:
    def test_matching_topic_overrides_model(self):
        ctx = make_context(chat_id="42")
        with patch(ROUTING, {"42": {"model": "qwen/qwen-3.6-plus"}}):
            with patch(DEFAULT, None):
                with patch(SET_OVERRIDE) as mock_set:
                    import asyncio
                    asyncio.run(handle("session:start", ctx))
                    mock_set.assert_called_once()
                    assert mock_set.call_args[1]["model"] == "qwen/qwen-3.6-plus"

    def test_default_fallback_when_topic_not_mapped(self):
        ctx = make_context(chat_id="999")
        with patch(ROUTING, {"42": {"model": "deepseek/deepseek-chat"}}):
            with patch(DEFAULT, {"model": "openai/gpt-4o-mini"}):
                with patch(SET_OVERRIDE) as mock_set:
                    import asyncio
                    asyncio.run(handle("session:start", ctx))
                    mock_set.assert_called_once()
                    assert mock_set.call_args[1]["model"] == "openai/gpt-4o-mini"

    def test_no_override_when_nothing_matches(self):
        ctx = make_context(chat_id="999")
        with patch(ROUTING, {"42": {"model": "deepseek/deepseek-chat"}}):
            with patch(DEFAULT, None):
                with patch(SET_OVERRIDE) as mock_set:
                    import asyncio
                    asyncio.run(handle("session:start", ctx))
                    mock_set.assert_not_called()

    def test_passes_provider_when_specified(self):
        ctx = make_context(chat_id="42")
        with patch(ROUTING, {"42": {"model": "qwen/qwen-3.6-plus", "provider": "openrouter"}}):
            with patch(DEFAULT, None):
                with patch(SET_OVERRIDE) as mock_set:
                    import asyncio
                    asyncio.run(handle("session:start", ctx))
                    assert mock_set.call_args[1]["provider"] == "openrouter"


class TestSessionReset:
    def test_clears_override_on_reset(self):
        from hermes_kit.bridge import set_override, get_override

        session_key = "agent:main:telegram:dm:111"
        set_override(session_key, model="test-model")
        ctx = {"session_key": session_key}

        import asyncio
        asyncio.run(handle("session:reset", ctx))

        assert get_override(session_key) is None

    def test_reset_missing_key_no_error(self):
        ctx = {"session_key": "nonexistent"}
        import asyncio
        asyncio.run(handle("session:reset", ctx))


class TestIrrelevantEvents:
    def test_ignores_agent_step(self):
        ctx = make_context()
        with patch(ROUTING, {"default": {"model": "gpt-4"}}):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("agent:step", ctx))
                mock_set.assert_not_called()

    def test_ignores_agent_end(self):
        ctx = make_context()
        with patch(ROUTING, {}):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("agent:end", ctx))
                mock_set.assert_not_called()
