# Cost Tracker — Budget Alerts

Track per-session token costs and get alerted when sessions exceed thresholds.

## How It Works

The cost tracker hooks into `agent:step` (each AI call) and `agent:end` (session completion). It accumulates token counts, calculates costs using known pricing, and alerts when thresholds are exceeded.

## Configuration

Edit `~/.hermes/hooks/cost-tracker/cost_tracker.yaml`:

```yaml
alert_threshold_usd: 1.0    # alert when any session exceeds $1.00
```

Set to `0` to disable alerts but continue tracking.

## Pricing Table (per 1M tokens)

| Model | Input Price | Output Price |
|---|---|---|
| opencode-go models | Flat-rate subscription ($10/mo) | See [Go plan](https://opencode.ai/go) |
| gpt-5.5 | $5.00 | $30.00 |
| gpt-5.4 | $2.50 | $15.00 |
| gpt-5.4-mini | $0.75 | $4.50 |
| o3 | $10.00 | $40.00 |
| claude-opus-4-8 | $5.00 | $25.00 |
| claude-sonnet-4-6 | $3.00 | $15.00 |
| claude-haiku-4-5 | $1.00 | $5.00 |
| grok-4.3 | $1.25 | $2.50 |
| grok-build-0.1 | $1.00 | $2.00 |
| deepseek-v4-pro | $1.74 | $3.48 |
| deepseek-v4-flash | $0.14 | $0.28 |
| qwen3.6-plus (via opencode-go) | $0.50 | $3.00 |
| kimi-k2.6 (via opencode-go) | $0.95 | $4.00 |
| gemini-3.5-flash | Free tier / pay-as-you-go | See [Google](https://ai.google.dev/pricing) |
| gemini-3.1-pro | Free tier / pay-as-you-go | See [Google](https://ai.google.dev/pricing) |

> OpenCode Go pricing is flat-rate via subscription ($10/month). See [OpenCode Go](https://opencode.ai/go) for current plans. For direct OpenAI/Anthropic/xAI providers, pricing matches the table above.

## Example Thresholds

| Use Case | Threshold | Rationale |
|---|---|---|
| Personal bot | $0.50 | Catch accidental spam loops |
| Small team (5 users) | $2.00 | Notice expensive sessions |
| Public bot | $5.00 | Detect abuse, heavy usage |

## Session Cost Visibility

During development, check session costs:

```bash
hermes logs | grep "hermes-kit.*cost"
```

Or inspect the bridge state directly:

```python
from hermes_kit import bridge
total = bridge.get_session_cost("agent:main:telegram:dm:123456")
print(f"${total:.4f}")
```

## Verification

Send a long conversation (multiple messages) to your bot. Check that the cost accumulates and resets when the session ends. If the alert threshold is set low enough, the warning should appear in gateway logs.
