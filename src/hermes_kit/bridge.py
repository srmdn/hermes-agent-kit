from typing import Optional
import time

_model_overrides: dict[str, dict[str, Optional[str]]] = {}
_fallback_chains: dict[str, list[str]] = {}
_fallback_index: dict[str, int] = {}

_rate_counters: dict[str, int] = {}
_rate_windows: dict[str, float] = {}
_rate_limited: set[str] = set()


def set_override(session_key: str, model: str, provider: Optional[str] = None) -> None:
    _model_overrides[session_key] = {
        "model": model,
        "provider": provider,
    }


def get_override(session_key: str) -> Optional[dict]:
    return _model_overrides.get(session_key)


def clear_override(session_key: str) -> None:
    _model_overrides.pop(session_key, None)


def set_fallback_chain(session_key: str, chain: list[str]) -> None:
    _fallback_chains[session_key] = chain
    _fallback_index[session_key] = 0


def get_fallback_chain(session_key: str) -> list[str] | None:
    return _fallback_chains.get(session_key)


def advance_fallback(session_key: str) -> None:
    if session_key in _fallback_index:
        _fallback_index[session_key] += 1


def get_current_fallback(session_key: str) -> str | None:
    chain = _fallback_chains.get(session_key)
    if not chain:
        return None
    idx = _fallback_index.get(session_key, 0)
    if idx < len(chain):
        return chain[idx]
    return None


def retry_with_fallback(session_key: str) -> str | None:
    advance_fallback(session_key)
    model = get_current_fallback(session_key)
    if model:
        set_override(session_key, model=model)
    return model


def reset_rate_counter(session_key: str) -> None:
    _rate_counters[session_key] = 0
    _rate_windows[session_key] = time.time()
    _rate_limited.discard(session_key)


def increment_rate_counter(session_key: str) -> int:
    _rate_counters[session_key] = _rate_counters.get(session_key, 0) + 1
    if session_key not in _rate_windows:
        _rate_windows[session_key] = time.time()
    return _rate_counters[session_key]


def get_rate_window_start(session_key: str) -> float:
    return _rate_windows.get(session_key, 0.0)


def set_rate_limited(session_key: str) -> None:
    _rate_limited.add(session_key)


def is_rate_limited(session_key: str) -> bool:
    return session_key in _rate_limited


_session_costs: dict[str, dict[str, float]] = {}
_cost_pricing: dict[str, tuple[float, float]] = {
    "gpt-4o": (2.50, 10.00),
    "gpt-4o-mini": (0.15, 0.60),
    "claude-sonnet-4": (3.00, 15.00),
    "deepseek-chat": (0.14, 0.28),
    "qwen-3.6-plus": (0.40, 0.80),
}


def track_cost(session_key: str, model: str, prompt_tokens: int, completion_tokens: int) -> None:
    if session_key not in _session_costs:
        _session_costs[session_key] = {}
    if model not in _session_costs[session_key]:
        _session_costs[session_key][model] = 0.0

    input_price, output_price = _cost_pricing.get(model, (0.0, 0.0))
    cost = (prompt_tokens / 1_000_000) * input_price + (completion_tokens / 1_000_000) * output_price
    _session_costs[session_key][model] += cost


def get_session_cost(session_key: str) -> float:
    if session_key not in _session_costs:
        return 0.0
    return sum(_session_costs[session_key].values())


def get_session_cost_breakdown(session_key: str) -> dict[str, float]:
    return _session_costs.get(session_key, {})


def reset_session_cost(session_key: str) -> None:
    _session_costs.pop(session_key, None)


def alert_cost_exceeded(session_key: str, total: float, threshold: float) -> None:
    print(f"[hermes-kit] COST ALERT: session {session_key} total ${total:.4f} exceeds threshold ${threshold:.2f}")


def patch_gateway_resolver() -> None:
    import asyncio
    from gateway.run import GatewayRunner

    original = GatewayRunner._resolve_session_agent_runtime
    original_is_async = asyncio.iscoroutinefunction(original)

    if original_is_async:
        async def patched_resolver(self, *args, **kwargs):
            model, runtime_kwargs = await original(self, *args, **kwargs)
            session_key = kwargs.get("session_key") or (args[0] if args else None)
            if session_key:
                override = get_override(session_key)
                if override:
                    model = override["model"]
            return model, runtime_kwargs
    else:
        def patched_resolver(self, *args, **kwargs):
            model, runtime_kwargs = original(self, *args, **kwargs)
            session_key = kwargs.get("session_key") or (args[0] if args else None)
            if session_key:
                override = get_override(session_key)
                if override:
                    model = override["model"]
            return model, runtime_kwargs

    GatewayRunner._resolve_session_agent_runtime = patched_resolver
