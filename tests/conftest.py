import os
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
