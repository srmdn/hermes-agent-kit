import logging
import yaml
from pathlib import Path

from hermes_kit import bridge
from hermes_kit.lib.hermes_api import get_hooks_dir

logger = logging.getLogger(__name__)

_HOOK_DIR = Path(__file__).parent
_ROUTER_HOOKS_DIR = _HOOK_DIR.parent / "router"
_ROUTING_PATH = None


def _get_routing_path() -> Path:
    global _ROUTING_PATH
    if _ROUTING_PATH is None:
        installed = Path(get_hooks_dir()) / "router" / "topic_router.yaml"
        if installed.exists():
            _ROUTING_PATH = installed
        else:
            _ROUTING_PATH = _ROUTER_HOOKS_DIR / "topic_router.yaml"
    return _ROUTING_PATH


def _read_routing() -> dict:
    path = _get_routing_path()
    if path.exists():
        return yaml.safe_load(path.read_text()) or {}
    return {}


def _write_routing(config: dict) -> None:
    path = _get_routing_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump(config, default_flow_style=False, sort_keys=False))


def _routing_id(context: dict) -> str | None:
    user_id = context.get("user_id", "")
    if user_id:
        return user_id
    return None


async def handle(event_type: str, context: dict) -> dict | None:
    args = str(context.get("args", "") or "").strip()
    routing_id = _routing_id(context)

    if not routing_id:
        logger.warning("model-switch: no routing_id — cannot identify topic")
        return {
            "decision": "handled",
            "message": "⚠️ Cannot identify topic. This command works in DMs for now.",
        }

    if not args:
        return _show_usage()

    parts = args.split(None, 1)
    subcmd = parts[0].lower()
    subcmd_args = parts[1] if len(parts) > 1 else ""

    if subcmd == "show":
        return _handle_show(routing_id)

    if subcmd == "reset":
        return _handle_reset(routing_id)

    if subcmd == "default":
        return _handle_default(subcmd_args)

    return _handle_set_model(routing_id, args)


def _build_session_key(context: dict) -> str | None:
    platform = context.get("platform", "")
    user_id = context.get("user_id", "")
    if platform and user_id:
        return f"agent:main:{platform}:dm:{user_id}"
    return None


def _handle_set_model(routing_id: str, model: str) -> dict:
    config = _read_routing()
    topics = config.get("topics") or {}
    topics[routing_id] = {"model": model}
    config["topics"] = topics
    _write_routing(config)

    msg = f"✅ Topic {routing_id} → {model}"
    return {"decision": "handled", "message": msg}


def _handle_show(routing_id: str) -> dict:
    config = _read_routing()
    topics = config.get("topics") or {}
    default = config.get("default")

    lines = []
    if routing_id in topics:
        lines.append(f"🔹 This topic: {topics[routing_id]['model']}")
    elif default:
        lines.append(f"🔹 This topic: {default['model']} (default)")

    if default and routing_id in topics:
        lines.append(f"🔸 Default: {default['model']}")

    mapped = [k for k in topics if k != routing_id]
    if mapped:
        lines.append(f"📋 {len(mapped)} other topic(s) configured")

    return {
        "decision": "handled",
        "message": "\n".join(lines) if lines else "No routing configured. Use /route <model> to set one.",
    }


def _handle_reset(routing_id: str) -> dict:
    config = _read_routing()
    topics = config.get("topics") or {}
    if routing_id in topics:
        del topics[routing_id]
        config["topics"] = topics
        _write_routing(config)
        default_model = (config.get("default") or {}).get("model", "default")
        return {
            "decision": "handled",
            "message": f"✅ Removed routing for topic {routing_id}. Falling back to {default_model}.",
        }
    return {"decision": "handled", "message": f"ℹ️ No routing set for this topic."}


def _handle_default(model: str) -> dict:
    if not model:
        return {"decision": "handled", "message": "Usage: /route default <model>"}

    config = _read_routing()
    config["default"] = {"model": model}
    _write_routing(config)

    return {"decision": "handled", "message": f"✅ Default model → {model}"}


def _show_usage() -> dict:
    return {
        "decision": "handled",
        "message": (
            "/route <model>          Set model for this topic\n"
            "/route show             Show current routing\n"
            "/route default <model>  Set default model\n"
            "/route reset            Remove routing for this topic"
        ),
    }
