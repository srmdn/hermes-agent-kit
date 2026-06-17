# Quickstart

## Before You Begin

**hermes-kit is a plugin — Hermes must work first.**

1. [Install Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.16+
2. Configure a model and provider (see [README prerequisites](https://github.com/srmdn/hermes-agent-kit/blob/main/README.md#prerequisites))
3. Set up your gateway (Telegram, Discord, etc.)
4. **Verify**: send a test message → gateway responds with correct model
5. Only then install hermes-kit hooks

## Agent-Driven (Recommended)

Paste this to your Hermes agent and let it handle everything:

> "Install and configure hermes-kit for production hardening. Install all hooks (router, fallback, rate-limiter, cost-tracker, model-switch), discover my Telegram topic IDs, set up model routing per topic, configure fallback chains, enable rate limiting, and restart the gateway. I use opencode-go as my provider."

The agent will:
1. Install hermes-kit
2. Install all hooks
3. Read your Telegram topics and map them to models
4. Configure fallback chains
5. Set rate limits
6. Restart the gateway

## Manual Install

```bash
pip install hermes-agent-kit
```

### One-Command Setup

```bash
hermes-kit install router fallback rate-limiter cost-tracker model-switch
hermes-kit gateway run --accept-hooks
```

Route changes made later with `/route` do not require a restart. The next message in that topic or DM picks them up automatically.

### Verify

```bash
hermes-kit doctor
```

Expected output:
```
router: HOOK.yaml ✓ handler.py ✓
fallback: HOOK.yaml ✓ handler.py ✓
rate-limiter: HOOK.yaml ✓ handler.py ✓
cost-tracker: HOOK.yaml ✓ handler.py ✓
model-switch: HOOK.yaml ✓ handler.py ✓
```

### Gateway Management

```bash
# Start (with hooks)
hermes-kit gateway run --accept-hooks

# Stop — press Ctrl+C

# Check status
hermes-kit status
```

### Next Steps

- [Configure model routing](manual/router.md) — assign models to Telegram topics
- [Set up fallback chains](manual/fallback.md) — what happens when a model fails
- [Configure rate limits](manual/rate-limiter.md) — prevent budget drain
- [Set cost alerts](manual/cost-tracker.md) — get notified at budget thresholds

Behavior notes:
- `fallback` seeds an ordered chain for each session; retry progression uses `hermes_kit.bridge.retry_with_fallback(session_key)`.
- `rate-limiter` blocks requests only until the current time window expires.
- `cost-tracker` estimates cost from Hermes session totals at the end of the turn.
