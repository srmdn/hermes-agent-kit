import yaml
from pathlib import Path
from hermes_kit import bridge

_ROUTING: dict[str, dict] = {}
_DEFAULT: dict | None = None
_hook_dir = Path(__file__).parent
_routing_path = _hook_dir / "topic_router.yaml"
if _routing_path.exists():
    raw = yaml.safe_load(_routing_path.read_text()) or {}
    _ROUTING = raw.get("topics", {})
    _DEFAULT = raw.get("default")


def _extract_routing_id(context: dict) -> str | None:
    session_key = context.get("session_key", "")
    chat_id = context.get("chat_id")
    if not session_key:
        return None

    parts = session_key.split(":")
    return parts[-1] if len(parts) >= 5 else chat_id


async def handle(event_type: str, context: dict) -> None:
    session_key = context.get("session_key")
    if not session_key:
        return

    if event_type == "session:start":
        routing_id = _extract_routing_id(context)
        if routing_id:
            user_id = context.get("user_id")
            if user_id:
                bridge.track_user_topic(user_id, routing_id)
            route = _ROUTING.get(routing_id)
            if not route:
                route = _DEFAULT
            if route:
                bridge.set_override(
                    session_key,
                    model=route["model"],
                    provider=route.get("provider"),
                )

    elif event_type == "session:reset":
        bridge.clear_override(session_key)
