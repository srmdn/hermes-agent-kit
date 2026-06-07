import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hermes_kit.cli import main


def _run_cli(argv: list[str], capsys) -> str:
    with patch.object(sys, "argv", argv):
        try:
            main()
        except SystemExit as e:
            if e.code is not None and e.code != 0:
                pass
    return capsys.readouterr().out


class TestNoArgs:
    def test_no_args_shows_usage(self, capsys):
        out = _run_cli(["hermes-kit"], capsys)
        assert "Usage:" in out

    def test_list_shows_all_hooks(self, capsys):
        out = _run_cli(["hermes-kit", "list"], capsys)
        assert "router" in out
        assert "fallback" in out
        assert "rate-limiter" in out
        assert "cost-tracker" in out


class TestHelp:
    def test_help_flag(self, capsys):
        out = _run_cli(["hermes-kit", "--help"], capsys)
        assert "install <hooks>" in out
        assert "reinstall <hooks>" in out
        assert "doctor" in out
        assert "status" in out
        assert "gateway run" in out
        assert "router <subcommand>" in out
        assert "version" in out

    def test_h_flag(self, capsys):
        out = _run_cli(["hermes-kit", "-h"], capsys)
        assert "Commands:" in out

    def test_help_command(self, capsys):
        out = _run_cli(["hermes-kit", "help"], capsys)
        assert "Commands:" in out


class TestVersion:
    def test_version_command(self, capsys):
        out = _run_cli(["hermes-kit", "version"], capsys)
        assert "hermes-agent-kit v" in out
        assert "CLI: hermes-kit" in out

    def test_double_dash_version(self, capsys):
        out = _run_cli(["hermes-kit", "--version"], capsys)
        assert "hermes-agent-kit" in out

    def test_v_flag(self, capsys):
        out = _run_cli(["hermes-kit", "-v"], capsys)
        assert "hermes-agent-kit" in out


class TestInstall:
    def test_install_valid_hook(self, capsys):
        with patch("hermes_kit.cli.shutil.copytree") as mock_copy:
            out = _run_cli(["hermes-kit", "install", "router"], capsys)
            assert mock_copy.called
            assert "Installed" in out
            assert "router" in out

    def test_install_multiple_hooks(self, capsys):
        with patch("hermes_kit.cli.shutil.copytree") as mock_copy:
            out = _run_cli(["hermes-kit", "install", "router", "fallback"], capsys)
            assert mock_copy.call_count == 2
            assert "router" in out
            assert "fallback" in out

    def test_install_unknown_hook(self, capsys):
        out = _run_cli(["hermes-kit", "install", "nonexistent"], capsys)
        assert "Unknown hook" in out

    def test_install_no_args(self, capsys):
        out = _run_cli(["hermes-kit", "install"], capsys)
        assert "Usage:" in out

    def test_install_already_installed(self, capsys):
        with patch("hermes_kit.cli.Path.exists", return_value=True):
            out = _run_cli(["hermes-kit", "install", "router"], capsys)
            assert "already installed" in out
            assert "reinstall" in out


class TestReinstall:
    def test_reinstall_valid_hook(self, capsys):
        with patch("hermes_kit.cli.Path.exists", return_value=True):
            with patch("hermes_kit.cli.shutil.rmtree") as mock_rm:
                with patch("hermes_kit.cli.shutil.copytree") as mock_copy:
                    out = _run_cli(["hermes-kit", "reinstall", "router"], capsys)
                    assert mock_rm.called
                    assert mock_copy.called
                    assert "Reinstalled" in out

    def test_reinstall_new_hook(self, capsys):
        with patch("hermes_kit.cli.Path.exists", return_value=False):
            with patch("hermes_kit.cli.shutil.copytree") as mock_copy:
                out = _run_cli(["hermes-kit", "reinstall", "router"], capsys)
                assert mock_copy.called
                assert "Reinstalled" in out

    def test_reinstall_unknown_hook(self, capsys):
        out = _run_cli(["hermes-kit", "reinstall", "nonexistent"], capsys)
        assert "Unknown hook" in out

    def test_reinstall_no_args(self, capsys):
        out = _run_cli(["hermes-kit", "reinstall"], capsys)
        assert "Usage:" in out

    def test_reinstall_multiple(self, capsys):
        with patch("hermes_kit.cli.Path.exists", return_value=False):
            with patch("hermes_kit.cli.shutil.copytree") as mock_copy:
                _run_cli(["hermes-kit", "reinstall", "router", "fallback"], capsys)
                assert mock_copy.call_count == 2


class TestDoctor:
    def test_doctor_no_hooks(self, capsys):
        with patch("hermes_kit.cli.Path.exists", return_value=False):
            out = _run_cli(["hermes-kit", "doctor"], capsys)
            assert "No hooks" in out or "OK" in out


class TestStatus:
    def test_status_shows_version(self, capsys):
        out = _run_cli(["hermes-kit", "status"], capsys)
        assert "hermes-agent-kit v" in out

    def test_status_shows_bridge_state(self, capsys):
        out = _run_cli(["hermes-kit", "status"], capsys)
        assert "Bridge state:" in out
        assert "Active model overrides:" in out
        assert "Rate-limited sessions:" in out
        assert "Sessions cost-tracked:" in out
        assert "Fallback chains:" in out
        assert "Gateway:" in out


class TestRouterCLI:
    def test_router_no_args(self, capsys):
        out = _run_cli(["hermes-kit", "router"], capsys)
        assert "Usage:" in out

    def test_router_add_missing_args(self, capsys):
        out = _run_cli(["hermes-kit", "router", "add"], capsys)
        assert "Usage:" in out

    def test_router_remove_missing_args(self, capsys):
        out = _run_cli(["hermes-kit", "router", "remove"], capsys)
        assert "Usage:" in out

    def test_router_set_default_missing_model(self, capsys):
        out = _run_cli(["hermes-kit", "router", "set-default"], capsys)
        assert "Usage:" in out

    def test_router_unknown_subcommand(self, capsys):
        out = _run_cli(["hermes-kit", "router", "bogus"], capsys)
        assert "Unknown router command" in out

    def test_router_add(self, capsys):
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value={}):
                with patch("hermes_kit.cli._write_router_config") as mock_write:
                    out = _run_cli(["hermes-kit", "router", "add", "42", "--model", "gpt-4o"], capsys)
                    assert mock_write.called
                    config = mock_write.call_args[0][0]
                    assert config["topics"]["42"]["model"] == "gpt-4o"
                    assert "Added topic" in out

    def test_router_add_with_provider(self, capsys):
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value={}):
                with patch("hermes_kit.cli._write_router_config") as mock_write:
                    out = _run_cli(["hermes-kit", "router", "add", "42", "--model", "gpt-4o", "--provider", "openai"], capsys)
                    config = mock_write.call_args[0][0]
                    assert config["topics"]["42"]["provider"] == "openai"
                    assert "provider: openai" in out

    def test_router_remove(self, capsys):
        existing = {"topics": {"42": {"model": "gpt-4o"}}}
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value=existing):
                with patch("hermes_kit.cli._write_router_config") as mock_write:
                    out = _run_cli(["hermes-kit", "router", "remove", "42"], capsys)
                    assert mock_write.called
                    assert "42" not in mock_write.call_args[0][0]["topics"]
                    assert "Removed topic" in out

    def test_router_remove_not_found(self, capsys):
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value={}):
                out = _run_cli(["hermes-kit", "router", "remove", "99"], capsys)
                assert "not found" in out

    def test_router_show_empty(self, capsys):
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value={}):
                out = _run_cli(["hermes-kit", "router", "show"], capsys)
                assert "No routing configured" in out

    def test_router_show_with_routes(self, capsys):
        config = {
            "default": {"model": "gpt-4o-mini", "provider": "openai"},
            "topics": {"42": {"model": "deepseek-chat"}},
        }
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value=config):
                out = _run_cli(["hermes-kit", "router", "show"], capsys)
                assert "gpt-4o-mini" in out
                assert "openai" in out
                assert "42" in out
                assert "deepseek-chat" in out

    def test_router_set_default(self, capsys):
        with patch("hermes_kit.cli._router_config_path", return_value=Path("/tmp/test_router.yaml")):
            with patch("hermes_kit.cli._read_router_config", return_value={}):
                with patch("hermes_kit.cli._write_router_config") as mock_write:
                    out = _run_cli(
                        ["hermes-kit", "router", "set-default", "--model", "gpt-4o-mini", "--provider", "openai"],
                        capsys,
                    )
                    config = mock_write.call_args[0][0]
                    assert config["default"]["model"] == "gpt-4o-mini"
                    assert config["default"]["provider"] == "openai"
                    assert "Default model:" in out


class TestGatewayRun:
    def test_gateway_run_no_subcommand(self, capsys):
        out = _run_cli(["hermes-kit", "gateway"], capsys)
        assert "Usage:" in out

    def test_gateway_run_wrong_subcommand(self, capsys):
        out = _run_cli(["hermes-kit", "gateway", "bogus"], capsys)
        assert "Usage:" in out


class TestUnknownCommand:
    def test_unknown_command(self, capsys):
        out = _run_cli(["hermes-kit", "bogus"], capsys)
        assert "Unknown command" in out
