import importlib.metadata
import os
import shutil
import sys
from pathlib import Path

import yaml

from hermes_kit.lib.hermes_api import get_hooks_dir


def _get_version() -> str:
    try:
        return importlib.metadata.version("hermes-agent-kit")
    except importlib.metadata.PackageNotFoundError:
        return "dev"


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


def reinstall(hook_name: str) -> None:
    dir_name = _hook_dirs.get(hook_name)
    if not dir_name:
        print(f"Unknown hook: {hook_name}. Available: {', '.join(AVAILABLE_HOOKS)}")
        sys.exit(1)

    src = HOOKS_SRC / dir_name
    dest = Path(get_hooks_dir()) / hook_name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    print(f"Reinstalled '{hook_name}' → {dest}")


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

    findings = _doctor_findings(
        installed,
        _read_router_config(),
        _read_hermes_config(),
    )
    if findings:
        print()
        print("Warnings:")
        for finding in findings:
            print(f"  - {finding}")

    print("Done.")


def status() -> None:
    import subprocess
    from hermes_kit import bridge

    print(f"hermes-agent-kit v{_get_version()} (CLI: hermes-kit)")
    print()

    hooks_dir = Path(get_hooks_dir())
    if hooks_dir.exists():
        installed = [d.name for d in hooks_dir.iterdir() if d.is_dir() and (d / "handler.py").exists()]
        print(f"Hooks: {len(installed)} installed")
        for h in sorted(installed):
            print(f"  {h}")
    else:
        print("Hooks: none installed")
    print()

    print("Bridge state:")
    print(f"  Active model overrides: {len(bridge._model_overrides)}")
    print(f"  Rate-limited sessions:  {len(bridge._rate_limited)}")
    print(f"  Sessions cost-tracked:  {len(bridge._session_costs)}")
    print(f"  Fallback chains:        {len(bridge._fallback_chains)}")
    print()

    try:
        result = subprocess.run(["pgrep", "-f", "hermes.*gateway"], capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split("\n")
            print(f"Gateway: running ({len(pids)} process) — PID: {', '.join(pids)}")
        else:
            print("Gateway: not running")
    except FileNotFoundError:
        print("Gateway: unknown (pgrep not available)")


def gateway_run() -> None:
    from hermes_kit.bridge import patch_gateway_resolver

    version = _get_version()
    print(f"[hermes-kit] v{version} — checking Hermes Agent...")

    try:
        import hermes_cli.main  # noqa: F401
    except ImportError:
        print("[hermes-kit] ERROR: Hermes Agent not found.")
        print("[hermes-kit] Install it first, then run this command.")
        print("[hermes-kit] See: https://github.com/NousResearch/hermes-agent")
        sys.exit(1)

    for note in _ensure_runtime_from_router_default():
        print(f"[hermes-kit] bootstrap: {note}")

    print(f"[hermes-kit] patching bridge...")

    try:
        patch_gateway_resolver()
        print(f"[hermes-kit] bridge patched successfully.")
    except ImportError:
        print("[hermes-kit] WARNING: could not patch bridge — Hermes internals may have changed")
        print("[hermes-kit] gateway will start but hooks will NOT override model routing")

    sys.argv = ["hermes", "gateway", "run"] + sys.argv[3:]

    from hermes_cli.main import main as hermes_main

    hermes_main()


def _router_config_path() -> Path:
    return Path(get_hooks_dir()) / "router" / "topic_router.yaml"


def _hermes_config_path() -> Path:
    hermes_home = os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes"))
    return Path(hermes_home) / "config.yaml"


def _read_router_config() -> dict:
    path = _router_config_path()
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _write_router_config(config: dict) -> None:
    path = _router_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))


def _read_hermes_config() -> dict:
    path = _hermes_config_path()
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _write_hermes_config(config: dict) -> None:
    path = _hermes_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))


def _infer_provider_from_model(model: str | None) -> str | None:
    if not model or "/" not in model:
        return None
    prefix, _ = model.split("/", 1)
    if prefix in {"opencode-go", "openrouter"}:
        return prefix
    return None


def _ensure_runtime_from_router_default() -> list[str]:
    router_config = _read_router_config()
    default_route = router_config.get("default") or {}
    model = default_route.get("model")
    provider = default_route.get("provider") or _infer_provider_from_model(model)
    if not model or not provider:
        return []

    hermes_config = _read_hermes_config()
    changed: list[str] = []

    model_config = hermes_config.get("model")
    if not isinstance(model_config, dict):
        model_config = {}
        hermes_config["model"] = model_config

    if not model_config.get("default"):
        model_config["default"] = model
        changed.append(f"set Hermes default model to {model}")
        model_config["provider"] = provider
        changed.append(f"set Hermes default provider to {provider}")
    elif not model_config.get("provider") and provider:
        model_config["provider"] = provider
        changed.append(f"set Hermes default provider to {provider}")

    if provider == "opencode-go":
        providers = hermes_config.get("providers")
        if not isinstance(providers, dict):
            providers = {}
            hermes_config["providers"] = providers

        provider_config = providers.get("opencode-go")
        if not isinstance(provider_config, dict):
            provider_config = {}
            providers["opencode-go"] = provider_config

        if not provider_config.get("api_key"):
            provider_config["api_key"] = "OPENCODE_GO_API_KEY"
            changed.append("set providers.opencode-go.api_key to OPENCODE_GO_API_KEY")
        if not provider_config.get("base_url"):
            provider_config["base_url"] = "https://opencode.ai/zen/go/v1"
            changed.append("set providers.opencode-go.base_url to https://opencode.ai/zen/go/v1")

    if changed:
        _write_hermes_config(hermes_config)
    return changed


def _doctor_findings(installed_hooks: list[str], router_config: dict, hermes_config: dict) -> list[str]:
    findings: list[str] = []

    default_route = router_config.get("default") or {}
    route_model = default_route.get("model")
    route_provider = default_route.get("provider")
    inferred_provider = _infer_provider_from_model(route_model)

    if "router" in installed_hooks and route_model and not route_provider and inferred_provider:
        findings.append(
            f"router default '{route_model}' has no provider; use '--provider {inferred_provider}' to avoid provider fallback drift."
        )

    if "router" in installed_hooks and "model-switch" not in installed_hooks:
        findings.append("router is installed but model-switch is missing; '/route' will not work.")

    model_config = hermes_config.get("model")
    if not isinstance(model_config, dict):
        model_config = {}
    global_model = model_config.get("default")
    global_provider = model_config.get("provider")
    expected_provider = route_provider or inferred_provider

    if route_model and expected_provider and not global_model:
        findings.append(
            f"Hermes model.default is empty while router default is '{route_model}'; reset/system paths may fall back to the wrong provider."
        )

    if route_model and expected_provider and not global_provider:
        findings.append(
            f"Hermes model.provider is empty while router default expects '{expected_provider}'."
        )

    if route_model and expected_provider and not global_model and global_provider and global_provider != expected_provider:
        findings.append(
            f"Hermes model.provider is '{global_provider}' but router default expects '{expected_provider}'; first-turn auth failures are likely."
        )

    if expected_provider == "opencode-go":
        providers = hermes_config.get("providers")
        if not isinstance(providers, dict):
            providers = {}
        go_config = providers.get("opencode-go")
        if not isinstance(go_config, dict):
            go_config = {}
        if not go_config.get("api_key"):
            findings.append("providers.opencode-go.api_key is missing; set it to OPENCODE_GO_API_KEY.")
        if not go_config.get("base_url"):
            findings.append("providers.opencode-go.base_url is missing; set it to https://opencode.ai/zen/go/v1.")

    return findings


def router_add(topic_id: str, model: str, provider: str | None = None) -> None:
    config = _read_router_config()
    topics = config.get("topics") or {}
    resolved_provider = provider or _infer_provider_from_model(model)
    entry: dict[str, str] = {"model": model}
    if resolved_provider:
        entry["provider"] = resolved_provider
    topics[topic_id] = entry
    config["topics"] = topics
    _write_router_config(config)
    provider_msg = f" (provider: {resolved_provider})" if resolved_provider else ""
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
    resolved_provider = provider or _infer_provider_from_model(model)
    entry: dict[str, str] = {"model": model}
    if resolved_provider:
        entry["provider"] = resolved_provider
    config["default"] = entry
    _write_router_config(config)
    bootstrap_notes = _ensure_runtime_from_router_default()
    provider_msg = f" (provider: {resolved_provider})" if resolved_provider else ""
    print(f"Default model: {model}{provider_msg}")
    for note in bootstrap_notes:
        print(f"Bootstrap: {note}")


def _parse_flag(flag: str, args: list[str]) -> str | None:
    try:
        idx = args.index(flag)
        return args[idx + 1]
    except (ValueError, IndexError):
        return None


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: hermes-kit <install|reinstall|doctor|status|list|gateway run|router|version>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd in ("--help", "-h", "help"):
        print("Usage: hermes-kit <command> [args]")
        print()
        print("Commands:")
        print("  install <hooks>        Install one or more hooks")
        print("  reinstall <hooks>      Reinstall (overwrite) one or more hooks")
        print("  doctor                 Check installed hooks health")
        print("  status                 Show bridge state and gateway status")
        print("  list                   List available hooks")
        print("  gateway run            Run gateway with bridge auto-patched")
        print("  router <subcommand>    Manage topic routing (add|remove|show|set-default)")
        print("  version                Show version")
        print()
        print(f"Hooks: {', '.join(AVAILABLE_HOOKS)}")

    elif cmd == "install":
        if len(sys.argv) < 3:
            print(f"Usage: hermes-kit install <hook> [<hook> ...]. Available: {', '.join(AVAILABLE_HOOKS)}")
            sys.exit(1)
        for hook_name in sys.argv[2:]:
            install(hook_name)

    elif cmd == "reinstall":
        if len(sys.argv) < 3:
            print(f"Usage: hermes-kit reinstall <hook> [<hook> ...]. Available: {', '.join(AVAILABLE_HOOKS)}")
            sys.exit(1)
        for hook_name in sys.argv[2:]:
            reinstall(hook_name)

    elif cmd in ("--version", "version", "-v", "-V"):
        print(f"hermes-agent-kit v{_get_version()} (CLI: hermes-kit)")

    elif cmd == "doctor":
        doctor()

    elif cmd == "status":
        status()

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
