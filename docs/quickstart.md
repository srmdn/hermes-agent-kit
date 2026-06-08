# Quickstart

## Before You Begin

**hermes-kit is a plugin — Hermes must work first.**

1. [Install Hermes Agent](https://github.com/NousResearch/hermes-agent) v0.16+
2. Configure a model and provider (see [Prerequisites](#prerequisites) in README)
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
