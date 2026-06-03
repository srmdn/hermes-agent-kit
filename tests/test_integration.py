import os
import subprocess
import sys
import time

import pytest

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
API_KEY = os.environ.get("OPENCODE_GO_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

if not TOKEN:
    pytest.skip("TELEGRAM_BOT_TOKEN required", allow_module_level=True)
if not API_KEY:
    pytest.skip("OPENCODE_GO_API_KEY or OPENROUTER_API_KEY required", allow_module_level=True)


class TestGatewayIntegration:
    def test_gateway_starts_and_loads_hooks(self):
        hermes_home = os.path.join(os.path.dirname(__file__), "..", ".hermes-local")
        env = os.environ.copy()
        env["HERMES_HOME"] = hermes_home
        env["GATEWAY_ALLOW_ALL_USERS"] = "true"

        config_path = os.path.join(hermes_home, "config.yaml")
        if not os.path.exists(config_path):
            os.makedirs(hermes_home, exist_ok=True)
            with open(config_path, "w") as f:
                f.write("""model:
  default: opencode-go/gpt-4o-mini
  provider: opencode-go

gateway:
  polling: true

platforms:
  telegram:
    enabled: true
""")

        hermes_bin = os.path.join(os.path.dirname(sys.executable), "hermes")
        log_path = os.path.join(env["HERMES_HOME"], "gateway.log")
        log_file = open(log_path, "w")
        gateway = subprocess.Popen(
            [hermes_bin, "gateway", "run", "--accept-hooks"],
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
        )

        try:
            time.sleep(8)
            assert gateway.poll() is None, (
                f"Gateway exited early with code {gateway.returncode}"
            )

            log_file.close()
            with open(log_path) as f:
                output = f.read()

            assert "Loaded hook 'router'" in output, (
                f"Hook not loaded. Output:\n{output}"
            )

        finally:
            gateway.terminate()
            gateway.wait(timeout=10)
            log_file.close()
