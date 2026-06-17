# Fallback — Session Fallback Chain

Define an ordered chain of fallback models for each session.

## How It Works

The fallback hook registers a chain of models for the active session before model resolution. The chain is ordered — first item is the primary, later items are fallback candidates.

What hermes-kit ships today:
- session-scoped fallback chain registration
- bridge helpers such as `hermes_kit.bridge.get_current_fallback(...)`
- `hermes_kit.bridge.retry_with_fallback(session_key)` to advance to the next model

What hermes-kit does **not** ship yet:
- a full automatic retry loop in gateway code that calls `retry_with_fallback(...)` for you on provider failure

## Configuration

Edit `~/.hermes/hooks/fallback/fallback_chain.yaml`:

```yaml
chains:
  global:
    - "opencode-go/deepseek-v4-pro"     # primary
    - "opencode-go/kimi-k2.6"            # first fallback
    - "opencode-go/qwen3.6-plus"        # second fallback
    - "opencode-go/deepseek-v4-flash"    # last resort
```

Models are ordered from primary to last resort. If your recovery logic calls `retry_with_fallback(session_key)`, Hermes advances from `deepseek-v4-pro` → `kimi-k2.6` → `qwen3.6-plus` → `deepseek-v4-flash`.

> All models in the chain must use the same provider. The examples above all use `opencode-go` — this is same-provider fallback and is fully supported. To switch providers per topic (e.g. opencode-go for coding, OpenAI for general chat), use [multi-provider routing](router.md) instead.

## Best Practices

### Cross-Provider Fallback

Cross-provider fallback is planned but not yet available. For now, all models in the chain use the same provider. To switch providers per topic, use [multi-provider routing](router.md) instead.

### Cost-Conscious Ordering

Put cheaper models last:

```yaml
chains:
  global:
    - "opencode-go/deepseek-v4-pro"       # primary
    - "opencode-go/kimi-k2.6"             # first fallback
    - "opencode-go/qwen3.6-plus"         # last resort — fast and cheap
```

### Chain Length

Keep chains to 3-4 models. Longer chains mean longer retry delays and user-visible latency. After 3 failures, the user probably needs to know something is wrong.

## Retry Behavior

When a model fails and your integration calls `retry_with_fallback(session_key)`:

1. The fallback index advances
2. The next model in the chain becomes the active override
3. Your retry logic resubmits the request
4. This repeats until success or chain exhausted
5. If all models fail, the error surfaces to the user

## Verification

Test by temporarily using an invalid model as primary — the fallback should kick in:

```yaml
chains:
  global:
    - "opencode-go/nonexistent-model"    # will fail
    - "opencode-go/deepseek-v4-flash"    # should be used instead
```

Restart gateway and send a message. Then trigger your retry path or custom recovery logic. The next retry should use `deepseek-v4-flash`.
