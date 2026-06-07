import asyncio
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from hermes_kit.hooks.model_switch.handler import (
    handle,
    _routing_id,
    _handle_set_model,
    _handle_show,
    _handle_reset,
    _handle_default,
    _show_usage,
)

# ── helpers ──────────────────────────────────────────────────────────────────

def make_context(args="", user_id="123456789", platform="telegram"):
    return {
        "platform": platform,
        "user_id": user_id,
        "command": "route",
        "raw_command": "route",
        "args": args,
        "raw_args": args,
    }


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def reset_routing_global():
    import hermes_kit.hooks.model_switch.handler as mod

    mod._ROUTING_PATH = None
    yield
    mod._ROUTING_PATH = None


# ══════════════════════════════════════════════════════════════════════════════
# TestCommandParsing
# ══════════════════════════════════════════════════════════════════════════════

class TestCommandParsing:
    """Test that different args route to the correct internal handlers."""

    READ = "hermes_kit.hooks.model_switch.handler._read_routing"
    WRITE = "hermes_kit.hooks.model_switch.handler._write_routing"

    # ── set ──────────────────────────────────────────────────────────────

    def test_set_model(self):
        ctx = make_context(args="gpt-4o")
        expected = {"topics": {"123456789": {"model": "gpt-4o"}}}

        with patch(self.READ, return_value={}) as mock_read:
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "123456789" in result["message"]
        assert "gpt-4o" in result["message"]
        mock_write.assert_called_once()
        written = mock_write.call_args[0][0]
        assert written == expected

    def test_set_model_with_provider(self):
        """Model name only for now — provider handled by CLI separately."""
        ctx = make_context(args="gpt-4o")
        expected = {"topics": {"123456789": {"model": "gpt-4o"}}}

        with patch(self.READ, return_value={}) as mock_read:
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        written = mock_write.call_args[0][0]
        assert written["topics"]["123456789"] == {"model": "gpt-4o"}
        assert "provider" not in written["topics"]["123456789"]

    # ── show ─────────────────────────────────────────────────────────────

    def test_show(self):
        ctx = make_context(args="show")
        config = {"topics": {"123456789": {"model": "gpt-4o"}}}

        with patch(self.READ, return_value=config):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "gpt-4o" in result["message"]
        mock_write.assert_not_called()

    def test_show_default_only(self):
        ctx = make_context(args="show")
        config = {"default": {"model": "claude-sonnet-4"}}

        with patch(self.READ, return_value=config):
            result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "claude-sonnet-4" in result["message"]
        assert "default" in result["message"].lower()

    def test_show_nothing_configured(self):
        ctx = make_context(args="show")

        with patch(self.READ, return_value={}):
            result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "No routing configured" in result["message"]

    # ── reset ────────────────────────────────────────────────────────────

    def test_reset(self):
        ctx = make_context(args="reset")
        config = {"topics": {"123456789": {"model": "gpt-4o"}}}

        with patch(self.READ, return_value=config) as mock_read:
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "Removed routing" in result["message"]
        mock_write.assert_called_once()
        written = mock_write.call_args[0][0]
        assert "123456789" not in written.get("topics", {})

    def test_reset_not_configured(self):
        ctx = make_context(args="reset")
        config = {"topics": {"999": {"model": "deepseek-chat"}}}

        with patch(self.READ, return_value=config):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "No routing set" in result["message"]
        mock_write.assert_not_called()

    def test_reset_with_default_fallback_message(self):
        ctx = make_context(args="reset")
        config = {
            "topics": {"123456789": {"model": "gpt-4o"}},
            "default": {"model": "claude-sonnet-4"},
        }

        with patch(self.READ, return_value=config):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert "claude-sonnet-4" in result["message"]

    # ── default ──────────────────────────────────────────────────────────

    def test_default(self):
        ctx = make_context(args="default gpt-4o-mini")
        expected = {"default": {"model": "gpt-4o-mini"}}

        with patch(self.READ, return_value={}) as mock_read:
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "gpt-4o-mini" in result["message"]
        mock_write.assert_called_once()
        written = mock_write.call_args[0][0]
        assert written == expected

    def test_default_no_args(self):
        ctx = make_context(args="default")

        with patch(self.READ, return_value={}):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "Usage" in result["message"]
        mock_write.assert_not_called()

    # ── usage / edge cases ───────────────────────────────────────────────

    def test_no_args(self):
        ctx = make_context(args="")

        with patch(self.READ, return_value={}):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "/route <model>" in result["message"]
        mock_write.assert_not_called()

    def test_unknown_subcommand(self):
        """Unknown subcommand is treated as a model name (set_model path)."""
        ctx = make_context(args="nonexistent")
        expected = {"topics": {"123456789": {"model": "nonexistent"}}}

        with patch(self.READ, return_value={}) as mock_read:
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        written = mock_write.call_args[0][0]
        assert written == expected

    # ── whitespace / arg edge cases ──────────────────────────────────────

    def test_args_with_extra_whitespace(self):
        ctx = make_context(args="  gpt-4o  ")

        with patch(self.READ, return_value={}):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        written = mock_write.call_args[0][0]
        assert written["topics"]["123456789"]["model"] == "gpt-4o"

    def test_default_with_extra_spaces(self):
        ctx = make_context(args="default   deepseek-chat")

        with patch(self.READ, return_value={}):
            with patch(self.WRITE) as mock_write:
                result = asyncio.run(handle("command:route", ctx))

        written = mock_write.call_args[0][0]
        assert written["default"]["model"] == "deepseek-chat"


# ══════════════════════════════════════════════════════════════════════════════
# TestRoutingContext
# ══════════════════════════════════════════════════════════════════════════════

class TestRoutingContext:
    """Test _routing_id extraction from context dicts."""

    def test_user_id_from_context(self):
        ctx = {"user_id": "12345"}
        assert _routing_id(ctx) == "12345"

    def test_user_id_empty_string(self):
        ctx = {"user_id": ""}
        assert _routing_id(ctx) is None

    def test_missing_user_id(self):
        ctx = {"platform": "telegram"}
        assert _routing_id(ctx) is None

    def test_user_id_among_other_keys(self):
        ctx = {
            "platform": "telegram",
            "user_id": "42",
            "command": "route",
            "args": "show",
        }
        assert _routing_id(ctx) == "42"

    def test_handle_missing_routing_id(self):
        ctx = {"platform": "telegram"}

        with patch(
            "hermes_kit.hooks.model_switch.handler._read_routing",
            return_value={},
        ):
            result = asyncio.run(handle("command:route", ctx))

        assert result["decision"] == "handled"
        assert "Cannot identify topic" in result["message"]


# ══════════════════════════════════════════════════════════════════════════════
# TestYamlPersistence
# ══════════════════════════════════════════════════════════════════════════════

HANDLER_MOD = "hermes_kit.hooks.model_switch.handler"


class TestYamlPersistence:
    """Integration-style tests using real yaml reads/writes on tmp_path."""

    @pytest.fixture(autouse=True)
    def setup_temp_routing(self, tmp_path):
        import hermes_kit.hooks.model_switch.handler as mod

        hooks_dir = tmp_path / "hooks" / "router"
        hooks_dir.mkdir(parents=True)
        routing_file = hooks_dir / "topic_router.yaml"
        mod._ROUTING_PATH = None

        yield routing_file

        mod._ROUTING_PATH = None

    def test_writes_topics_to_yaml(self, setup_temp_routing):
        routing_file = setup_temp_routing

        with patch(HANDLER_MOD + "._read_routing", return_value={}) as mock_read:
            with patch(HANDLER_MOD + "._write_routing") as mock_write:
                result = asyncio.run(
                    handle("command:route", make_context(args="gpt-4o"))
                )

        assert result["decision"] == "handled"
        mock_write.assert_called_once()
        written = mock_write.call_args[0][0]
        assert written["topics"]["123456789"] == {"model": "gpt-4o"}

    def test_preserves_other_topics(self, setup_temp_routing):
        routing_file = setup_temp_routing
        existing = {"topics": {"topic-a": {"model": "claude-sonnet-4"}}}

        with patch(HANDLER_MOD + "._read_routing", return_value=existing):
            with patch(HANDLER_MOD + "._write_routing") as mock_write:
                asyncio.run(
                    handle("command:route", make_context(args="gpt-4o", user_id="topic-b"))
                )

        written = mock_write.call_args[0][0]
        assert written["topics"]["topic-a"] == {"model": "claude-sonnet-4"}
        assert written["topics"]["topic-b"] == {"model": "gpt-4o"}

    def test_preserves_default_on_topic_set(self, setup_temp_routing):
        routing_file = setup_temp_routing
        existing = {"default": {"model": "gpt-4o-mini"}}

        with patch(HANDLER_MOD + "._read_routing", return_value=existing):
            with patch(HANDLER_MOD + "._write_routing") as mock_write:
                asyncio.run(
                    handle("command:route", make_context(args="deepseek-chat"))
                )

        written = mock_write.call_args[0][0]
        assert written["default"] == {"model": "gpt-4o-mini"}
        assert written["topics"]["123456789"] == {"model": "deepseek-chat"}

    def test_default_overwrites(self, setup_temp_routing):
        routing_file = setup_temp_routing
        config = {"default": {"model": "gpt-4o"}}

        with patch(HANDLER_MOD + "._read_routing", return_value=config):
            with patch(HANDLER_MOD + "._write_routing") as mock_write:
                result = asyncio.run(
                    handle(
                        "command:route",
                        make_context(args="default gpt-4o-mini"),
                    )
                )

        assert "gpt-4o-mini" in result["message"]
        written = mock_write.call_args[0][0]
        assert written["default"] == {"model": "gpt-4o-mini"}

    def test_real_write_then_read(self, setup_temp_routing):
        """Use real file I/O: write via a manual call, then read back."""
        routing_file = setup_temp_routing

        import hermes_kit.hooks.model_switch.handler as mod

        # Force the handler to use our temp file
        mod._ROUTING_PATH = routing_file

        config = {"topics": {"42": {"model": "gpt-4o-mini"}}}
        yaml.safe_dump(config, open(str(routing_file), "w"), sort_keys=False)

        with patch(HANDLER_MOD + "._get_routing_path", return_value=routing_file):
            with patch(HANDLER_MOD + "._write_routing") as mock_write:
                result = asyncio.run(
                    handle(
                        "command:route",
                        make_context(args="gpt-4o", user_id="42"),
                    )
                )

        # The real _read_routing should read from our file
        # and _write_routing should get called with updated config
        assert result["decision"] == "handled"
        assert mock_write.called
        written = mock_write.call_args[0][0]
        assert written["topics"]["42"] == {"model": "gpt-4o"}
