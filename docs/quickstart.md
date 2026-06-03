# Quickstart

## Agent-Driven (Recommended)

Paste this to your Hermes agent and let it handle everything:

> "Install and configure hermes-kit for production hardening. Install all four hooks (router, fallback, rate-limiter, cost-tracker), discover my Telegram topic IDs, set up model routing per topic, configure fallback chains, enable rate limiting, and restart the gateway. I use opencode-go as my provider."

The agent will:
1. Install hermes-kit
2. Install all hooks
3. Read your Telegram topics and map them to models
4. Configure fallback chains
5. Set rate limits
6. Restart the gateway

## Manual Install

```bash
pip install hermes-kit
```

### One-Command Setup

```bash
hermes-kit install router fallback rate-limiter cost-tracker
hermes gateway restart
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
```

### Next Steps

- [Configure model routing](manual/router.md) — assign models to Telegram topics
- [Set up fallback chains](manual/fallback.md) — what happens when a model fails
- [Configure rate limits](manual/rate-limiter.md) — prevent budget drain
- [Set cost alerts](manual/cost-tracker.md) — get notified at budget thresholds
