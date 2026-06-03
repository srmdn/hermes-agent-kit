import shutil
import sys
from pathlib import Path

import yaml

from hermes_kit.lib.hermes_api import get_hooks_dir


HOOKS_SRC = Path(__file__).parent / "hooks"

_hook_dir_names = [d.name for d in HOOKS_SRC.iterdir() if d.is_dir()]

_hook_names: dict[str, str] = {}
_hook_dirs: dict[str, str] = {}
for _dir in _hook_dir_names:
    _hook_yaml = HOOKS_SRC / _dir / "HOOK.yaml"
    if _hook_yaml.exists():
        _name = yaml.safe_load(_hook_yaml.read_text()).get("name", _dir)
    else:
        _name = _dir
    _hook_names[_dir] = _name
    _hook_dirs[_name] = _dir

AVAILABLE_HOOKS = sorted(_hook_dirs.keys())


def install(hook_name: str) -> None:
    dir_name = _hook_dirs.get(hook_name)
    if not dir_name:
        print(f"Unknown hook: {hook_name}. Available: {', '.join(AVAILABLE_HOOKS)}")
        sys.exit(1)

    src = HOOKS_SRC / dir_name
    dest = Path(get_hooks_dir()) / hook_name
    if dest.exists():
        print(f"Hook '{hook_name}' already installed. Use 'hermes-kit reinstall {hook_name}' to overwrite.")
        return

    shutil.copytree(src, dest)
    print(f"Installed '{hook_name}' → {dest}")


def doctor() -> None:
    hooks_dir = Path(get_hooks_dir())
    if not hooks_dir.exists():
        print("OK: No hooks installed yet. Run 'hermes-kit install <name>' to add hooks.")
        return

    installed = [d.name for d in hooks_dir.iterdir() if d.is_dir()]
    if not installed:
        print("OK: Hooks directory exists but is empty.")
        return

    for name in installed:
        hook_dir = hooks_dir / name
        hook_yaml = hook_dir / "HOOK.yaml"
        handler = hook_dir / "handler.py"

        status = []
        if hook_yaml.exists():
            status.append("HOOK.yaml ✓")
        else:
            status.append("HOOK.yaml ✗ (missing)")
        if handler.exists():
            status.append("handler.py ✓")
        else:
            status.append("handler.py ✗ (missing)")

        print(f"  {name}: {' '.join(status)}")

    print("Done.")


def gateway_run() -> None:
    from hermes_kit.bridge import patch_gateway_resolver

    patch_gateway_resolver()

    sys.argv = ["hermes", "gateway", "run"] + sys.argv[3:]

    from hermes_cli.main import main as hermes_main

    hermes_main()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hermes-kit <install|doctor|list|gateway run>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "install":
        if len(sys.argv) < 3:
            print(f"Usage: hermes-kit install <hook> [<hook> ...]. Available: {', '.join(AVAILABLE_HOOKS)}")
            sys.exit(1)
        for hook_name in sys.argv[2:]:
            install(hook_name)

    elif cmd == "doctor":
        doctor()

    elif cmd == "list":
        print("Available hooks:")
        for h in AVAILABLE_HOOKS:
            installed = " (installed)" if (Path(get_hooks_dir()) / h).exists() else ""
            print(f"  {h}{installed}")

    elif cmd == "gateway":
        if len(sys.argv) < 3 or sys.argv[2] != "run":
            print("Usage: hermes-kit gateway run [--accept-hooks] [-- ...]")
            sys.exit(1)
        gateway_run()

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
