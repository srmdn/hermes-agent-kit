# hermes-kit

Production hardening for [Hermes Agent](https://github.com/NousResearch/hermes-agent) gateways.

Self-hosted Hermes gateways hit walls when serving multiple users:

- Every chat uses the same AI model regardless of topic
- API failures surface as hard errors to users
- One spammer drains your API budget with no warning
- Zero cost visibility per user or topic

hermes-kit fills these gaps with production-grade hooks — no core Hermes changes needed.

## Quickstart

Paste this to your Hermes agent:

> "Install and configure hermes-kit for production hardening. Install all four hooks (router, fallback, rate-limiter, cost-tracker), configure my Telegram topic IDs for model routing, and restart the gateway."

Or do it manually:

```bash
pip install hermes-kit
hermes-kit install router fallback rate-limiter cost-tracker
hermes-kit gateway run --accept-hooks
```

## Docs

- [Quickstart](quickstart.md) — agent-driven and manual install
- [Providers](providers.md) — supported AI providers and model lists
- Manual setup per module:
  - [Router](manual/router.md) — per-topic model routing
  - [Fallback](manual/fallback.md) — automatic retry chains
  - [Rate Limiter](manual/rate-limiter.md) — per-user quotas
  - [Cost Tracker](manual/cost-tracker.md) — budget alerts
- [Troubleshooting](troubleshooting.md) — common issues

## License

MIT
