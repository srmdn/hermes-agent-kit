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
    - "opencode-go/claude-sonnet-4"      # first fallback
    - "opencode-go/gpt-4o"               # second fallback
    - "openai/gpt-4o-mini"               # last resort
```

Models are tried in order. If `deepseek-v4-pro` fails → try `claude-sonnet-4` → try `gpt-4o` → try `gpt-4o-mini`.

## Best Practices

### Cross-Provider Fallback

Always include models from different providers. If opencode-go is down entirely, an opencode-go fallback chain won't help:

```yaml
chains:
  global:
    - "opencode-go/deepseek-v4-pro"     # primary (opencode-go)
    - "anthropic/claude-sonnet-4"        # fallback (different provider)
    - "openai/gpt-4o-mini"               # last resort (different provider)
```

### Cost-Conscious Ordering

Put cheaper models last:

```yaml
chains:
  global:
    - "opencode-go/gpt-4o"               # $2.50/$10.00 per 1M
    - "anthropic/claude-sonnet-4"        # $3.00/$15.00
    - "opencode-go/gpt-4o-mini"          # $0.15/$0.60 — cheap safety net
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
    - "opencode-go/gpt-4o-mini"          # should be used instead
```

Restart gateway and send a message. The response should come from `gpt-4o-mini`.
