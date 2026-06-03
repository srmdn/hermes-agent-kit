# hermes-kit

Production hardening pack for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Self-hosted Hermes gateways are powerful but built for single-user setups. Multi-user deployments hit walls: no per-topic model routing, API failures surface as hard errors, one heavy user can burn your API budget with no alert.

hermes-kit fills these gaps with production-grade hooks.

## Prerequisites

- Python ≥ 3.11
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) installed
- A configured gateway (Telegram, Discord, etc.)

## Install

```bash
pip install hermes-kit
```

## Quickstart

```bash
# Install hooks
hermes-kit install router
hermes-kit install fallback
hermes-kit install rate-limiter
hermes-kit install cost-tracker

# Validate everything
hermes-kit doctor

# Enable model override support (add to your gateway startup)
# import hermes_kit.bridge
# hermes_kit.bridge.patch_gateway_resolver()

# Restart gateway
hermes gateway restart
```

Hooks land in `~/.hermes/hooks/<name>/`. Hermes discovers them on gateway restart.

## Bridge Setup

For the router and fallback modules to override AI models, add this to your Hermes gateway startup script:

```python
import hermes_kit.bridge
hermes_kit.bridge.patch_gateway_resolver()
```

No other Hermes source changes needed.

## Modules

### router — Per-Topic Model Routing

Route Telegram topics to different AI models. Finance chat uses Qwen, coding chat uses DeepSeek, everything else falls back to GPT-4o-mini.

```yaml
# ~/.hermes/hooks/router/topic_router.yaml
default:
  model: "opencode-go/gpt-4o-mini"

topics:
  "42":
    model: "opencode-go/qwen-3.6-plus"
  "7":
    model: "opencode-go/deepseek-v4-pro"
```

### fallback — Automatic Fallback Chain

Define a chain of models to try when the primary fails.

```yaml
# ~/.hermes/hooks/fallback/fallback_chain.yaml
chains:
  global:
    - "opencode-go/claude-sonnet-4"
    - "opencode-go/deepseek-v4-pro"
    - "opencode-go/gpt-4o-mini"
```

After a failure, call `hermes_kit.bridge.retry_with_fallback(session_key)` to advance to the next model.

### rate-limiter — Per-User Rate Limiting

Prevent a single user or chat from draining your API budget.

```yaml
# ~/.hermes/hooks/rate-limiter/rate_limits.yaml
limits:
  global:
    max_messages_per_window: 100
    window_seconds: 3600
  per_user:
    "123456789":
      max_messages_per_window: 50
```

### cost-tracker — Real-Time Cost Tracking

Track token costs per session and alert when thresholds are exceeded.

```yaml
# ~/.hermes/hooks/cost-tracker/cost_tracker.yaml
alert_threshold_usd: 1.0
```

## License

MIT
