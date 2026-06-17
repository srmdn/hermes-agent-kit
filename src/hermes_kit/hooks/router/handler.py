from pathlib import Path
import yaml

from hermes_kit import bridge

_hook_dir = Path(__file__).parent
_routing_path = _hook_dir / "topic_router.yaml"


def _read_routing() -> tuple[dict[str, dict], dict | None]:
    if not _routing_path.exists():
        return {}, None

    raw = yaml.safe_load(_routing_path.read_text()) or {}
    return raw.get("topics") or {}, raw.get("default")


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
        bridge.register_session(context.get("session_id"), session_key)
        routing_id = _extract_routing_id(context)
        if routing_id:
            user_id = context.get("user_id")
            if user_id:
                bridge.track_user_topic(user_id, routing_id)
            routing, default = _read_routing()
            route = routing.get(routing_id)
            if not route:
                route = default
            if route:
                bridge.set_override(
                    session_key,
                    model=route["model"],
                    provider=route.get("provider"),
                )

    elif event_type == "session:reset":
        bridge.clear_override(session_key)
