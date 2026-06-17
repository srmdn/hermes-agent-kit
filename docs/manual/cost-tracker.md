# Cost Tracker — Budget Alerts

Estimate per-session token costs and get alerted when sessions exceed thresholds.

## How It Works

The cost tracker resets its session baseline at `session:start`, reads Hermes usage totals from the completed agent run, and estimates cost at `agent:end`.

Current implementation details:
- usage is estimated from Hermes session totals, not streamed token-by-token into the hook
- non-zero built-in pricing currently covers the bundled OpenCode Go model IDs in `bridge.py`
- unknown model IDs are still tracked, but estimate as `$0.00` until pricing is added

## Configuration

Edit `~/.hermes/hooks/cost-tracker/cost_tracker.yaml`:

```yaml
alert_threshold_usd: 1.0    # alert when any session exceeds $1.00
```

Set to `0` to disable alerts but continue tracking.

## Built-In Pricing Table (per 1M tokens)

| Model | Input Price | Output Price |
|---|---|---|
| deepseek-v4-pro | $1.74 | $3.48 |
| deepseek-v4-flash | $0.14 | $0.28 |
| qwen3.7-max | $2.50 | $7.50 |
| qwen3.7-plus | $0.40 | $1.60 |
| qwen3.6-plus (via opencode-go) | $0.50 | $3.00 |
| kimi-k2.6 (via opencode-go) | $0.95 | $4.00 |
| kimi-k2.5 (via opencode-go) | $0.60 | $3.00 |
| minimax-m2.7 (via opencode-go) | $0.30 | $1.20 |
| minimax-m2.5 (via opencode-go) | $0.30 | $1.20 |
| minimax-m3 (via opencode-go) | $0.30 | $1.20 |
| mimo-v2.5-pro (via opencode-go) | $1.74 | $3.48 |
| mimo-v2.5 (via opencode-go) | $0.14 | $0.28 |
| glm-5.1 (via opencode-go) | $1.40 | $4.40 |
| glm-5 (via opencode-go) | $1.00 | $3.20 |

> OpenCode Go pricing is flat-rate via subscription ($10/month). These per-token numbers are internal estimates for session cost tracking only.

> If you route to a model that is not listed above, hermes-kit still records the session but estimates `$0.00` for that model.

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

Or inspect the bridge state directly during the session:

```python
from hermes_kit import bridge
total = bridge.get_session_cost("agent:main:telegram:dm:123456")
print(f"${total:.4f}")
```

## Verification

Send a long conversation (multiple messages) to your bot. Check that the cost estimate appears when the turn completes and resets when the session ends. If the alert threshold is set low enough, the warning should appear in gateway logs.
