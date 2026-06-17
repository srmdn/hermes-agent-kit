# hermes-kit

Production hardening pack for [Hermes Agent](https://github.com/NousResearch/hermes-agent).

Self-hosted Hermes gateways are powerful but built for single-user setups. Multi-user deployments hit walls: no per-topic model routing, API failures surface as hard errors, one heavy user can burn your API budget with no alert.

hermes-kit fills these gaps with production-grade hooks.

> ⚠️ **How it works**: hermes-kit monkey-patches Hermes Agent's internal model resolver at runtime. This is intentionally fragile — Hermes Agent updates may break your setup. We're working on an upstream PR to replace the patch with native hook return values. Until then, test after every Hermes upgrade.

## Prerequisites

- Python 3.11 to 3.13
- [Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.16.0 (pinned)
- **Hermes configured with a working model + provider** — hermes-kit is a plugin, not standalone. Hermes must be able to respond to messages BEFORE installing hooks.
- A configured gateway (Telegram, Discord, etc.)

### Verify Hermes works first

> **Critical**: hermes-kit won't fix a broken Hermes setup. Make sure your gateway responds to messages with the model you want BEFORE installing hooks.

```bash
# Set your model (pick one from opencode-go)
hermes /model opencode-go/mimo-v2.5-pro

# Or via config.yaml at ~/.hermes/config.yaml:
cat > ~/.hermes/config.yaml << 'EOF'
model:
  default: opencode-go/mimo-v2.5-pro
  provider: opencode-go

providers:
  opencode-go:
    api_key: OPENCODE_GO_API_KEY
    base_url: https://opencode.ai/zen/go/v1
EOF

# Ensure API keys in ~/.hermes/.env
echo "OPENCODE_GO_API_KEY=sk-..." >> ~/.hermes/.env
echo "GATEWAY_ALLOW_ALL_USERS=true" >> ~/.hermes/.env

# Start gateway
hermes gateway run

# Send a test message on Telegram → verify you get a response
# Only then install hermes-kit
```

### Gateway Management

```bash
# Start (with hooks)
hermes-kit gateway run --accept-hooks

# Stop
# Press Ctrl+C in the terminal running the gateway

# Restart after config changes
# Ctrl+C then:
hermes-kit gateway run --accept-hooks

# Check status
hermes-kit status
```

## Install

```bash
pip install hermes-agent-kit
```

> **🔵 Naming — same project, two names:**
> | Context | Name |
> |---------|------|
> | PyPI / pip install | `hermes-agent-kit` |
> | GitHub repo | [`srmdn/hermes-agent-kit`](https://github.com/srmdn/hermes-agent-kit) |
> | CLI command | `hermes-kit` |
>
> Why the split? PyPI name matches the repo (`hermes-agent-kit`). The short CLI alias (`hermes-kit`) keeps commands terse — `hermes-kit install router` instead of `hermes-agent-kit install router`. Same project, same code, two names.

## Quickstart

```bash
# Install all hooks in one command
hermes-kit install router fallback rate-limiter cost-tracker model-switch

# Verify
hermes-kit doctor

# Start gateway with bridge auto-patched
hermes-kit gateway run --accept-hooks

# If new users get "I don't recognize you":
GATEWAY_ALLOW_ALL_USERS=true hermes-kit gateway run --accept-hooks
```

Hooks land in `~/.hermes/hooks/<name>/`. Hermes discovers them on restart.

`/route` updates do not require a gateway restart. The model-switch hook writes the routing file, and the router hook picks up the change on the next message in that topic or DM.

## Modules

### router — Per-Topic Model Routing

Route Telegram topics to different AI models. Finance chat uses Qwen, coding chat uses DeepSeek, everything else falls back to GPT-4o-mini.

**Via CLI:**
```bash
hermes-kit router set-default --model opencode-go/qwen3.6-plus
hermes-kit router add 42 --model opencode-go/deepseek-v4-pro
hermes-kit router show
```

**Via YAML** (`~/.hermes/hooks/router/topic_router.yaml`):
```yaml
default:
  model: "opencode-go/qwen3.6-plus"

topics:
  "42":
    model: "opencode-go/deepseek-v4-pro"
```

**Multi-provider** — route specific topics to native providers:
```bash
hermes-kit router add 42 --model gpt-4o --provider openai
hermes-kit router add 7 --model claude-sonnet-4-6 --provider anthropic
```

Hermes resolves API keys from `~/.hermes/.env` (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.). See [providers guide](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/providers.md) for all supported providers and model IDs.

### fallback — Session Fallback Chain

Define a chain of models to use for fallback decisions within a session.

**Via YAML** (`~/.hermes/hooks/fallback/fallback_chain.yaml`):
```yaml
chains:
  global:
    - "opencode-go/deepseek-v4-pro"     # primary
    - "opencode-go/kimi-k2.6"      # fallback
    - "opencode-go/qwen3.6-plus"          # last resort
```

The fallback hook registers the chain for the active session. To actually advance to the next model after an error, call `hermes_kit.bridge.retry_with_fallback(session_key)` from your recovery logic or custom hook integration.

> Current state: hermes-kit ships the fallback chain and bridge helpers, but not a full automatic retry loop in gateway code yet.

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

> Rate limiter enforces limits at the bridge level. Exceeding users get `RateLimitExceeded` until the current time window expires; a brand-new session is not required.

### cost-tracker — Real-Time Cost Tracking

Estimate token costs per session and alert when thresholds are exceeded.

**Via YAML** (`~/.hermes/hooks/cost-tracker/cost_tracker.yaml`):
```yaml
alert_threshold_usd: 1.0
```

Set to `0` to disable alerts but continue tracking.

Cost estimates are computed from Hermes session totals at `agent:end`. Built-in non-zero pricing currently covers the bundled OpenCode Go model IDs in `bridge.py`; unknown model IDs are tracked as `$0.00` until pricing is added.

### model-switch — `/route` Commands

Manage routing from Telegram without editing files on the server.

```bash
/route show
/route opencode-go/deepseek-v4-pro
/route default opencode-go/qwen3.6-plus
/route reset
```

`/route` writes `~/.hermes/hooks/router/topic_router.yaml`. The next message in that topic or DM uses the updated route.

## Docs

- [Quickstart](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/quickstart.md) — agent-driven and manual install
- [Providers](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/providers.md) — supported AI providers and model lists
- Manual setup per module:
  - [Router](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/manual/router.md) — per-topic model routing + `/route` command
  - [Fallback](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/manual/fallback.md) — session fallback chains
  - [Rate Limiter](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/manual/rate-limiter.md) — per-user quotas
  - [Cost Tracker](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/manual/cost-tracker.md) — budget alerts
- [Troubleshooting](https://github.com/srmdn/hermes-agent-kit/blob/main/docs/troubleshooting.md) — common issues

## License

MIT
