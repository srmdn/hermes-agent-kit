# Rate Limiter — Per-User Quotas

Prevent a single user or chat from draining your API budget by setting message limits.

## How It Works

The rate limiter tracks message counts per session. When a user exceeds the configured limit within a time window, the session is blocked — the bridge raises `RateLimitExceeded` on every request until the window resets at the next `session:start` event.

> Rate limiter enforces limits at the bridge level. Exceeding users cannot send messages until their window resets.

## Configuration

Edit `~/.hermes/hooks/rate-limiter/rate_limits.yaml`:

```yaml
limits:
  global:
    max_messages_per_window: 100
    window_seconds: 3600           # 1 hour

  per_user:
    "123456789":
      max_messages_per_window: 50
      window_seconds: 3600
    "987654321":
      max_messages_per_window: 200
      window_seconds: 3600
```

- `global` — applies to all users without a per-user override
- `per_user` — specific limits for individual Telegram user IDs
- `window_seconds` — sliding time window after which the counter resets

## Examples

### Default: 100 messages per hour for everyone

```yaml
limits:
  global:
    max_messages_per_window: 100
    window_seconds: 3600
```

### Strict limit for a known heavy user

```yaml
limits:
  global:
    max_messages_per_window: 100
    window_seconds: 3600
  per_user:
    "123456789":
      max_messages_per_window: 20    # only 20 per hour
      window_seconds: 3600
```

### Unlimited for trusted users, limited for everyone else

```yaml
limits:
  global:
    max_messages_per_window: 50
    window_seconds: 3600
  per_user:
    "admin123":
      max_messages_per_window: 1000   # effectively unlimited
      window_seconds: 3600
```

## Finding User IDs

See [Router docs](router.md) for methods to find Telegram user/chat IDs.

## Verification

Send rapid messages from a test account. After exceeding the limit, the bot should stop responding. Check logs for rate limit warnings.
