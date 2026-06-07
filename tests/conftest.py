import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
env_file = project_root / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key, value)


@pytest.fixture(autouse=True)
def isolate_hermes_home(tmp_path):
    os.environ["HERMES_HOME"] = str(tmp_path / ".hermes-test")
    yield
    os.environ.pop("HERMES_HOME", None)


@pytest.fixture
def hermes_local(tmp_path):
    home = tmp_path / ".hermes-e2e"
    home.mkdir(parents=True)
    (home / "hooks").mkdir()

    config = home / "config.yaml"
    config.write_text("""model:
  default: opencode-go/gpt-4o-mini
  provider: opencode-go

gateway:
  polling: true
""")

    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        shutil.copy(env_file, home / ".env")

    old_home = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(home)
    yield home
    if old_home:
        os.environ["HERMES_HOME"] = old_home
    else:
        os.environ.pop("HERMES_HOME", None)


@pytest.fixture
def hermes_kit_installed(hermes_local):
    kit_bin = os.path.join(os.path.dirname(sys.executable), "hermes-kit")
    subprocess.run(
        [kit_bin, "install", "router", "fallback", "rate-limiter", "cost-tracker"],
        capture_output=True, text=True, timeout=30,
    )
    yield


@pytest.fixture
def gateway_process(hermes_local, hermes_kit_installed):
    try:
        import hermes_cli.main  # noqa: F401
    except ImportError:
        pytest.skip("Hermes Agent not installed — is hermes_cli available?")

    env = os.environ.copy()
    env["GATEWAY_ALLOW_ALL_USERS"] = "true"

    log_path = hermes_local / "gateway.log"
    log_file = open(log_path, "w")

    proc = subprocess.Popen(
        [sys.executable, "-m", "hermes_cli.main", "gateway", "run", "--accept-hooks"],
        env=env, stdout=log_file, stderr=subprocess.STDOUT,
    )

    time.sleep(10)

    yield proc

    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
    log_file.close()
