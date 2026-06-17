import yaml
from pathlib import Path
from hermes_kit import bridge

_ALERT_THRESHOLD: float = 0.0
_hook_dir = Path(__file__).parent
_cfg_path = _hook_dir / "cost_tracker.yaml"
if _cfg_path.exists():
    raw = yaml.safe_load(_cfg_path.read_text()) or {}
    _ALERT_THRESHOLD = raw.get("alert_threshold_usd", 0.0)


async def handle(event_type: str, context: dict) -> None:
    session_key = context.get("session_key") or bridge.get_session_key_for_session_id(
        context.get("session_id")
    )

    if event_type == "session:start":
        if session_key:
            bridge.register_session(context.get("session_id"), session_key)
            bridge.reset_session_cost(session_key)
            bridge.reset_usage_baseline(session_key)
        return

    if not session_key:
        return

    if event_type == "agent:step":
        usage = context.get("usage", {})
        if usage:
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            model = context.get("model", "unknown")
            bridge.track_cost(session_key, model, prompt_tokens, completion_tokens)

    elif event_type == "agent:end":
        snapshot = bridge.get_latest_agent_run(context.get("session_id"))
        if snapshot and snapshot.get("model"):
            bridge.track_cost_from_totals(
                session_key,
                snapshot["model"],
                int(snapshot.get("input_tokens", 0) or 0),
                int(snapshot.get("output_tokens", 0) or 0),
            )
        total = bridge.get_session_cost(session_key)
        if total > 0 and _ALERT_THRESHOLD > 0 and total > _ALERT_THRESHOLD:
            bridge.alert_cost_exceeded(session_key, total, _ALERT_THRESHOLD)
        bridge.reset_session_cost(session_key)
