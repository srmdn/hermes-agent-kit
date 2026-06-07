import asyncio

import pytest
import yaml

from hermes_kit import bridge
import hermes_kit.hooks.model_switch.handler as handler


# ═══════════════════════════════════════════════════════════════════════
#  Model Switch Hook E2E
# ═══════════════════════════════════════════════════════════════════════

class TestModelSwitchE2E:
    @pytest.fixture(autouse=True)
    def _setup(self, tmp_path):
        self.yaml_path = tmp_path / "topic_router.yaml"
        handler._ROUTING_PATH = None
        handler._ROUTING_PATH = self.yaml_path
        bridge._model_overrides.clear()

    # ── helpers ──────────────────────────────────────────────────────

    def _make_context(self, **kwargs):
        ctx = {"platform": "telegram", "user_id": "123", "args": "", **kwargs}
        ctx.pop(None, None)
        return ctx

    def _call(self, context=None, **kw):
        if context is None:
            context = self._make_context(**kw)
        return asyncio.run(handler.handle("command:route", context))

    def _read_yaml(self):
        return yaml.safe_load(self.yaml_path.read_text()) or {}

    def _write_yaml(self, config):
        self.yaml_path.write_text(
            yaml.dump(config, default_flow_style=False, sort_keys=False)
        )

    # ── route set model ──────────────────────────────────────────────

    def test_route_set_model(self):
        result = self._call(args="gpt-4o")

        data = self._read_yaml()
        assert data["topics"]["123"]["model"] == "gpt-4o"
        assert result["decision"] == "handled"
        assert "gpt-4o" in result["message"]

    # ── route show ───────────────────────────────────────────────────

    def test_route_show_with_routing(self):
        self._write_yaml({"topics": {"123": {"model": "gpt-4o"}}})

        result = self._call(args="show")

        assert "gpt-4o" in result["message"]

    def test_route_show_no_routing(self):
        result = self._call(args="show")

        assert "No routing configured" in result["message"]

    # ── route reset ──────────────────────────────────────────────────

    def test_route_reset(self):
        self._write_yaml({"topics": {"123": {"model": "gpt-4o"}}})

        self._call(args="reset")

        data = self._read_yaml()
        topics = data.get("topics") or {}
        assert "123" not in topics

    # ── route default ────────────────────────────────────────────────

    def test_route_default(self):
        self._call(args="default claude-sonnet-4")

        data = self._read_yaml()
        assert data["default"]["model"] == "claude-sonnet-4"

    # ── usage ────────────────────────────────────────────────────────

    def test_route_no_args_shows_usage(self):
        result = self._call(args="")

        for word in ("/route", "show", "default", "reset"):
            assert word in result["message"], f"'{word}' not in usage message"

    # ── unknown command treated as model ─────────────────────────────

    def test_route_unknown_cmd_treated_as_model(self):
        self._call(args="nonexistent-model")

        data = self._read_yaml()
        assert data["topics"]["123"]["model"] == "nonexistent-model"

    # ── missing user_id ──────────────────────────────────────────────

    def test_route_missing_user_id(self):
        ctx = {"platform": "telegram"}
        result = self._call(context=ctx)

        assert "Cannot identify" in result["message"]

    # ── preserves other topics ───────────────────────────────────────

    def test_preserves_other_topics(self):
        self._write_yaml({"topics": {"456": {"model": "deepseek"}}})

        self._call(args="gpt-4o")

        data = self._read_yaml()
        assert data["topics"]["456"]["model"] == "deepseek"
        assert data["topics"]["123"]["model"] == "gpt-4o"

    def test_uses_bridge_topic_when_available(self):
        bridge._user_topics["123"] = "topic-456"
        try:
            self._call(args="gpt-4o")

            data = self._read_yaml()
            assert "topic-456" in data["topics"], (
                f"Expected routing key 'topic-456' from bridge, got: {list(data.get('topics', {}).keys())}"
            )
            assert data["topics"]["topic-456"]["model"] == "gpt-4o"
            assert "123" not in data["topics"]
        finally:
            bridge._user_topics.clear()
