import pytest
from unittest.mock import patch
from hermes_kit.hooks.router.handler import handle


@pytest.fixture(autouse=True)
def reset_bridge():
    from hermes_kit import bridge

    bridge._model_overrides.clear()
    bridge._session_keys_by_session_id.clear()
    yield
    bridge._model_overrides.clear()
    bridge._session_keys_by_session_id.clear()


def make_context(chat_id="123456789", thread_id=None, platform="telegram"):
    parts = ["agent", "main", platform, "dm", chat_id]
    if thread_id:
        parts.append(thread_id)
    return {
        "session_key": ":".join(parts),
        "session_id": f"session-{chat_id}{('-' + thread_id) if thread_id else ''}",
        "chat_id": chat_id,
        "user_id": chat_id,
        "platform": platform,
    }


SET_OVERRIDE = "hermes_kit.hooks.router.handler.bridge.set_override"
READ_ROUTING = "hermes_kit.hooks.router.handler._read_routing"


class TestSessionKeyParsing:
    def test_sets_override_when_default_exists(self):
        ctx = make_context(chat_id="111")
        with patch(READ_ROUTING, return_value=({}, {"model": "openai/gpt-4o-mini"})):
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
        with patch(READ_ROUTING, return_value=({"42": {"model": "qwen/qwen-3.6-plus"}}, None)):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()
                assert mock_set.call_args[1]["model"] == "qwen/qwen-3.6-plus"

    def test_default_fallback_when_topic_not_mapped(self):
        ctx = make_context(chat_id="999")
        with patch(READ_ROUTING, return_value=({"42": {"model": "deepseek/deepseek-chat"}}, {"model": "openai/gpt-4o-mini"})):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()
                assert mock_set.call_args[1]["model"] == "openai/gpt-4o-mini"

    def test_no_override_when_nothing_matches(self):
        ctx = make_context(chat_id="999")
        with patch(READ_ROUTING, return_value=({"42": {"model": "deepseek/deepseek-chat"}}, None)):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("session:start", ctx))
                mock_set.assert_not_called()

    def test_passes_provider_when_specified(self):
        ctx = make_context(chat_id="42")
        with patch(READ_ROUTING, return_value=({"42": {"model": "qwen/qwen-3.6-plus", "provider": "openrouter"}}, None)):
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
        with patch(READ_ROUTING, return_value=({"default": {"model": "gpt-4"}}, None)):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("agent:step", ctx))
                mock_set.assert_not_called()

    def test_ignores_agent_end(self):
        ctx = make_context()
        with patch(READ_ROUTING, return_value=({}, None)):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio
                asyncio.run(handle("agent:end", ctx))
                mock_set.assert_not_called()


TRACK_USER_TOPIC = "hermes_kit.hooks.router.handler.bridge.track_user_topic"


class TestBridgeTracking:
    def test_tracks_user_topic_on_session_start(self):
        ctx = make_context(chat_id="111")
        with patch(READ_ROUTING, return_value=({}, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE):
                with patch(TRACK_USER_TOPIC) as mock_track:
                    import asyncio

                    asyncio.run(handle("session:start", ctx))
                    mock_track.assert_called_once_with("111", "111")

    def test_tracks_user_topic_with_thread_id(self):
        ctx = make_context(chat_id="111", thread_id="222")
        with patch(READ_ROUTING, return_value=({}, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE):
                with patch(TRACK_USER_TOPIC) as mock_track:
                    import asyncio

                    asyncio.run(handle("session:start", ctx))
                    mock_track.assert_called_once_with("111", "222")

    def test_no_tracking_when_missing_user_id(self):
        ctx = {
            "session_key": "agent:main:telegram:dm:111",
            "session_id": "session-111",
            "chat_id": "111",
            "platform": "telegram",
        }
        with patch(READ_ROUTING, return_value=({}, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE):
                with patch(TRACK_USER_TOPIC) as mock_track:
                    import asyncio

                    asyncio.run(handle("session:start", ctx))
                    mock_track.assert_not_called()


class TestGroupSessionKeyParsing:
    def test_group_with_topic_uses_thread_id(self):
        ctx = {
            "session_key": "agent:main:telegram:group:-1003701036521:17585",
            "session_id": "session-group-topic",
            "chat_id": "-1003701036521",
            "user_id": "12345",
            "platform": "telegram",
        }
        with patch(READ_ROUTING, return_value=({}, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio

                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()
                assert mock_set.call_args[0][0] == ctx["session_key"]
                assert mock_set.call_args[1]["model"] == "gpt-4o"

    def test_group_per_user_uses_user_id(self):
        ctx = {
            "session_key": "agent:main:telegram:group:-1003701036521:12345",
            "session_id": "session-group-user",
            "chat_id": "-1003701036521",
            "user_id": "12345",
            "platform": "telegram",
        }
        with patch(READ_ROUTING, return_value=({}, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio

                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()

    def test_group_with_topic_routes_correct_routing_id(self):
        ctx = {
            "session_key": "agent:main:telegram:group:-100:17585",
            "session_id": "session-group-topic-2",
            "chat_id": "-100",
            "user_id": "12345",
            "platform": "telegram",
        }
        ROUTING_WITH_TOPIC = {"17585": {"model": "claude-sonnet-4"}}
        with patch(READ_ROUTING, return_value=(ROUTING_WITH_TOPIC, {"model": "gpt-4o"})):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio

                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()
                assert mock_set.call_args[1]["model"] == "claude-sonnet-4"

    def test_dm_session_still_works(self):
        ctx = {
            "session_key": "agent:main:telegram:dm:12345",
            "session_id": "session-dm-12345",
            "chat_id": "12345",
            "user_id": "12345",
            "platform": "telegram",
        }
        with patch(READ_ROUTING, return_value=({"12345": {"model": "gpt-4o"}}, None)):
            with patch(SET_OVERRIDE) as mock_set:
                import asyncio

                asyncio.run(handle("session:start", ctx))
                mock_set.assert_called_once()
                assert mock_set.call_args[1]["model"] == "gpt-4o"

    def test_rereads_routing_file_after_update(self, tmp_path):
        import asyncio
        import hermes_kit.hooks.router.handler as handler

        original_path = handler._routing_path
        handler._routing_path = tmp_path / "topic_router.yaml"
        try:
            handler._routing_path.write_text("topics:\n  \"123456789\":\n    model: gpt-4o\n")
            ctx = make_context()
            asyncio.run(handle("session:start", ctx))
            from hermes_kit import bridge
            assert bridge.get_override(ctx["session_key"])["model"] == "gpt-4o"

            bridge.clear_override(ctx["session_key"])
            handler._routing_path.write_text("topics:\n  \"123456789\":\n    model: claude-sonnet-4\n")
            asyncio.run(handle("session:start", ctx))
            assert bridge.get_override(ctx["session_key"])["model"] == "claude-sonnet-4"
        finally:
            handler._routing_path = original_path
