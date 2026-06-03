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


def _router_config_path() -> Path:
    return Path(get_hooks_dir()) / "router" / "topic_router.yaml"


def _read_router_config() -> dict:
    path = _router_config_path()
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _write_router_config(config: dict) -> None:
    path = _router_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))


def router_add(topic_id: str, model: str, provider: str | None = None) -> None:
    config = _read_router_config()
    topics = config.get("topics") or {}
    entry: dict[str, str] = {"model": model}
    if provider:
        entry["provider"] = provider
    topics[topic_id] = entry
    config["topics"] = topics
    _write_router_config(config)
    provider_msg = f" (provider: {provider})" if provider else ""
    print(f"Added topic '{topic_id}' → {model}{provider_msg}")


def router_remove(topic_id: str) -> None:
    config = _read_router_config()
    topics = config.get("topics") or {}
    if topic_id in topics:
        del topics[topic_id]
        _write_router_config(config)
        print(f"Removed topic '{topic_id}'.")
    else:
        print(f"Topic '{topic_id}' not found.")


def router_show() -> None:
    config = _read_router_config()
    default = config.get("default") or {}
    topics = config.get("topics") or {}

    if default:
        line = f"Default: {default.get('model', 'not set')}"
        if default.get("provider"):
            line += f" (provider: {default['provider']})"
        print(line)
    if topics:
        if default:
            print()
        for tid, route in topics.items():
            line = f"  {tid}  →  {route.get('model', 'unknown')}"
            if route.get("provider"):
                line += f" (provider: {route['provider']})"
            print(line)
    if not default and not topics:
        print("No routing configured.")


def router_set_default(model: str, provider: str | None = None) -> None:
    config = _read_router_config()
    entry: dict[str, str] = {"model": model}
    if provider:
        entry["provider"] = provider
    config["default"] = entry
    _write_router_config(config)
    provider_msg = f" (provider: {provider})" if provider else ""
    print(f"Default model: {model}{provider_msg}")


def _parse_flag(flag: str, args: list[str]) -> str | None:
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return None


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hermes-kit <install|doctor|list|gateway run|router>")
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

    elif cmd == "router":
        if len(sys.argv) < 3:
            print("Usage: hermes-kit router <add|remove|show|set-default> [args]")
            sys.exit(1)

        subcmd = sys.argv[2]
        args = sys.argv[3:]

        if subcmd == "show":
            router_show()

        elif subcmd == "add":
            topic_id = args[0] if args else None
            model = _parse_flag("--model", args)
            if not topic_id or not model:
                print("Usage: hermes-kit router add <topic-id> --model <model> [--provider <provider>]")
                sys.exit(1)
            router_add(topic_id, model, provider=_parse_flag("--provider", args))

        elif subcmd == "remove":
            if not args:
                print("Usage: hermes-kit router remove <topic-id>")
                sys.exit(1)
            router_remove(args[0])

        elif subcmd == "set-default":
            model = _parse_flag("--model", args)
            if not model:
                print("Usage: hermes-kit router set-default --model <model> [--provider <provider>]")
                sys.exit(1)
            router_set_default(model, provider=_parse_flag("--provider", args))

        else:
            print(f"Unknown router command: {subcmd}")
            sys.exit(1)

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
