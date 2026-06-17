import time
import yaml
from pathlib import Path
from hermes_kit import bridge

_LIMITS: dict = {}
_hook_dir = Path(__file__).parent
_limits_path = _hook_dir / "rate_limits.yaml"
if _limits_path.exists():
    raw = yaml.safe_load(_limits_path.read_text()) or {}
    _LIMITS = raw.get("limits", {})


def _get_limit(user_id: str) -> dict | None:
    per_user = _LIMITS.get("per_user", {})
    if user_id in per_user:
        return per_user[user_id]
    return _LIMITS.get("global")


def _is_within_window(window_start: float, window_seconds: int) -> bool:
    return (time.time() - window_start) < window_seconds


def _resolve_session_key(context: dict) -> str | None:
    return context.get("session_key") or bridge.get_session_key_for_session_id(
        context.get("session_id")
    )


async def handle(event_type: str, context: dict) -> None:
    session_key = _resolve_session_key(context)
    if not session_key:
        return

    limit = _get_limit(context.get("user_id", ""))
    if not limit:
        return

    if event_type == "session:start":
        bridge.register_session(context.get("session_id"), session_key)
        bridge.reset_rate_counter(session_key)

    elif event_type == "agent:step":
        window_seconds = limit.get("window_seconds", 3600)
        max_messages = limit.get("max_messages_per_window", 100)

        window_start = bridge.get_rate_window_start(session_key)
        if not _is_within_window(window_start, window_seconds):
            bridge.reset_rate_counter(session_key)

        count = bridge.increment_rate_counter(session_key)

        if count > max_messages:
            bridge.set_rate_limited(session_key)
