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


async def handle(event_type: str, context: dict) -> None:
    session_key = context.get("session_key")
    if not session_key:
        return

    limit = _get_limit(context.get("user_id", ""))
    if not limit:
        return

    if event_type == "session:start":
        bridge.reset_rate_counter(session_key)

    elif event_type == "agent:step":
        count = bridge.increment_rate_counter(session_key)
        window_seconds = limit.get("window_seconds", 3600)
        max_messages = limit.get("max_messages_per_window", 100)

        window_start = bridge.get_rate_window_start(session_key)
        if not _is_within_window(window_start, window_seconds):
            bridge.reset_rate_counter(session_key)
            return

        if count > max_messages:
            bridge.set_rate_limited(session_key)
