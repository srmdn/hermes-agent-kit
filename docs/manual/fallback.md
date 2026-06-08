# Fallback — Automatic Model Retry

When a model fails (API error, timeout, rate limit), the fallback hook automatically tries the next model in the chain.

## How It Works

The fallback hook registers a chain of models at `agent:start`. When the primary model errors, the gateway retries with the next model. The chain is ordered — first match wins.

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

Models are tried in order. If `deepseek-v4-pro` fails → try `kimi-k2.6` → try `qwen3.6-plus` → try `deepseek-v4-flash`.

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

When a model fails:

1. The error is caught
2. The next model in the chain is selected
3. The request is retried with the new model
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

Restart gateway and send a message. The response should come from `deepseek-v4-flash`.
