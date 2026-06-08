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
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `o3` | $10.00 | $40.00 |
| `claude-sonnet-4` | $3.00 | $15.00 |
| `claude-opus-4` | $15.00 | $75.00 |
| `deepseek-chat` | $0.14 | $0.28 |
| `deepseek-reasoner` | $0.55 | $2.19 |
| `qwen-3.6-plus` | $0.40 | $0.80 |

OpenCode Go pricing is flat-rate via subscription ($10/month). See [openCode Go](https://opencode.ai/go) for current plans. For direct OpenAI/Anthropic providers, pricing matches the table above.

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
