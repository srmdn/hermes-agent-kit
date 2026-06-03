# hermes-kit

Production hardening pack for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Self-hosted Hermes gateways are powerful but built for single-user setups. Multi-user deployments hit walls: no per-topic model routing, API failures surface as hard errors, one heavy user can burn your API budget with no alert.

hermes-kit fills these gaps with production-grade hooks.

> ⚠️ **How it works**: hermes-kit monkey-patches Hermes Agent's internal model resolver at runtime. This is intentionally fragile — Hermes Agent updates may break your setup. We're working on an upstream PR to replace the patch with native hook return values. Until then, test after every Hermes upgrade.

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
# Install all hooks in one command
hermes-kit install router fallback rate-limiter cost-tracker

# Verify
hermes-kit doctor

# Start gateway with bridge auto-patched
hermes-kit gateway run --accept-hooks

# If new users get "I don't recognize you":
GATEWAY_ALLOW_ALL_USERS=true hermes-kit gateway run --accept-hooks
```

Hooks land in `~/.hermes/hooks/<name>/`. Hermes discovers them on restart.

## Modules

### router — Per-Topic Model Routing

Route Telegram topics to different AI models. Finance chat uses Qwen, coding chat uses DeepSeek, everything else falls back to GPT-4o-mini.

**Via CLI:**
```bash
hermes-kit router set-default --model opencode-go/gpt-4o-mini
hermes-kit router add 42 --model opencode-go/deepseek-v4-pro
hermes-kit router show
```

**Via YAML** (`~/.hermes/hooks/router/topic_router.yaml`):
```yaml
default:
  model: "opencode-go/gpt-4o-mini"

topics:
  "42":
    model: "opencode-go/deepseek-v4-pro"
```

**Multi-provider** — route specific topics to native providers:
```bash
hermes-kit router add 42 --model gpt-4o --provider openai
hermes-kit router add 7 --model claude-sonnet-4-20250514 --provider anthropic
```

Hermes resolves API keys from `~/.hermes/.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.). See [providers guide](docs/providers.md) for all supported providers and model IDs.

### fallback — Automatic Fallback Chain

Define a chain of models to try when the primary fails.

**Via YAML** (`~/.hermes/hooks/fallback/fallback_chain.yaml`):
```yaml
chains:
  global:
    - "opencode-go/deepseek-v4-pro"     # primary
    - "opencode-go/claude-sonnet-4"      # fallback
    - "opencode-go/gpt-4o-mini"          # last resort
```

After a failure, call `hermes_kit.bridge.retry_with_fallback(session_key)` to advance to the next model.

### rate-limiter — Per-User Rate Limiting

Prevent a single user or chat from draining your API budget.

**Via YAML** (`~/.hermes/hooks/rate-limiter/rate_limits.yaml`):
```yaml
limits:
  global:
    max_messages_per_window: 100
    window_seconds: 3600
  per_user:
    "123456789":
      max_messages_per_window: 50
```

> ⚠️ Rate limiter currently tracks usage but does not block messages. Enforcement is planned for an upcoming release.

### cost-tracker — Real-Time Cost Tracking

Track token costs per session and alert when thresholds are exceeded.

**Via YAML** (`~/.hermes/hooks/cost-tracker/cost_tracker.yaml`):
```yaml
alert_threshold_usd: 1.0
```

Set to `0` to disable alerts but continue tracking.

## Docs

- [Quickstart](docs/quickstart.md) — agent-driven and manual install
- [Providers](docs/providers.md) — supported AI providers and model lists
- Manual setup per module:
  - [Router](docs/manual/router.md) — per-topic model routing
  - [Fallback](docs/manual/fallback.md) — automatic retry chains
  - [Rate Limiter](docs/manual/rate-limiter.md) — per-user quotas
  - [Cost Tracker](docs/manual/cost-tracker.md) — budget alerts
- [Troubleshooting](docs/troubleshooting.md) — common issues

## License

MIT
