import os
import subprocess
import sys
from pathlib import Path

import pytest


def _kit_bin():
    return os.path.join(os.path.dirname(sys.executable), "hermes-kit")


def _run_kit(*args, timeout=15):
    return subprocess.run(
        [_kit_bin(), *args],
        capture_output=True, text=True, timeout=timeout,
    )


class TestGatewayStartup:
    def test_gateway_starts_and_stays_alive(self, gateway_process):
        assert gateway_process.poll() is None

    def test_hooks_are_loaded(self, hermes_local, gateway_process):
        log_path = hermes_local / "gateway.log"
        output = log_path.read_text()

        for name in ("router", "fallback", "rate-limiter", "cost-tracker"):
            assert f"Loaded hook '{name}'" in output, (
                f"hook '{name}' not loaded. log:\n{output}"
            )

    def test_bridge_is_patched(self, hermes_local, gateway_process):
        result = _run_kit("status")
        assert result.returncode == 0, f"status failed: {result.stderr}"
        assert "Bridge state:" in result.stdout, (
            f"bridge state not found — patch may not be active. stdout:\n{result.stdout}"
        )


class TestHermesKitCLI:
    def test_install_puts_hooks_in_place(self, hermes_local, hermes_kit_installed):
        hooks_dir = hermes_local / "hooks"
        for name in ("router", "fallback", "rate-limiter", "cost-tracker"):
            hook_dir = hooks_dir / name
            assert hook_dir.is_dir(), f"{name} not installed at {hook_dir}"
            assert (hook_dir / "handler.py").exists(), f"handler.py missing from {name}"
            assert (hook_dir / "HOOK.yaml").exists(), f"HOOK.yaml missing from {name}"

    def test_doctor_reports_healthy(self, hermes_kit_installed):
        result = _run_kit("doctor")
        assert result.returncode == 0, result.stderr
        assert "✓" in result.stdout

    def test_status_shows_bridge_state(self, hermes_kit_installed):
        result = _run_kit("status")
        assert result.returncode == 0, result.stderr
        assert "Bridge state:" in result.stdout

    def test_version_shows_version(self, hermes_kit_installed):
        result = _run_kit("version")
        assert "hermes-agent-kit" in result.stdout

    def test_list_shows_all_hooks(self, hermes_kit_installed):
        result = _run_kit("list")
        for name in ("router", "fallback", "rate-limiter", "cost-tracker"):
            assert name in result.stdout, f"{name} missing from list output"


class TestGatewayWithHooks:
    def test_hermes_kit_status_detects_gateway(self, gateway_process):
        result = _run_kit("status")
        output = result.stdout.lower()
        assert "running" in output or "hooks:" in output or "installed" in output

    def test_gateway_log_contains_no_errors(self, hermes_local, gateway_process):
        log_path = hermes_local / "gateway.log"
        output = log_path.read_text()
        error_lines = [line for line in output.splitlines() if "error" in line.lower()]
        assert not error_lines, f"found error lines in gateway log:\n{chr(10).join(error_lines)}"
