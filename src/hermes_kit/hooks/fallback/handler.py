import yaml
from pathlib import Path
from hermes_kit import bridge

_CHAINS: dict[str, list[str]] = {}
_hook_dir = Path(__file__).parent
_chain_path = _hook_dir / "fallback_chain.yaml"
if _chain_path.exists():
    raw = yaml.safe_load(_chain_path.read_text()) or {}
    _CHAINS = raw.get("chains", {})


async def handle(event_type: str, context: dict) -> None:
    if event_type != "agent:start":
        return

    session_key = context.get("session_key")
    if not session_key:
        return

    chain = _CHAINS.get("global")
    if chain:
        bridge.set_fallback_chain(session_key, chain)
