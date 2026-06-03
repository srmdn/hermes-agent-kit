import shutil
import sys
from pathlib import Path

from hermes_kit.lib.hermes_api import get_hooks_dir


HOOKS_SRC = Path(__file__).parent / "hooks"
AVAILABLE_HOOKS = [d.name for d in HOOKS_SRC.iterdir() if d.is_dir()]


def install(hook_name: str) -> None:
    src = HOOKS_SRC / hook_name
    if not src.is_dir():
        print(f"Unknown hook: {hook_name}. Available: {', '.join(AVAILABLE_HOOKS)}")
        sys.exit(1)

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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hermes-kit <install|doctor|list>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "install":
        if len(sys.argv) < 3:
            print(f"Usage: hermes-kit install <hook>. Available: {', '.join(AVAILABLE_HOOKS)}")
            sys.exit(1)
        install(sys.argv[2])

    elif cmd == "doctor":
        doctor()

    elif cmd == "list":
        print("Available hooks:")
        for h in AVAILABLE_HOOKS:
            installed = " (installed)" if (Path(get_hooks_dir()) / h).exists() else ""
            print(f"  {h}{installed}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
