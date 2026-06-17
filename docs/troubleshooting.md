# Troubleshooting

## Provider authentication failed

**Symptom:** `Provider authentication failed. Check the configured credentials.`

**Root cause:** Hermes doesn't have a working model + provider. hermes-kit hooks can't fix this — they only route models that Hermes already knows about.

**Fix — configure Hermes first, then install hooks:**

```bash
# 1. Set a model that actually exists on your provider
hermes /model opencode-go/mimo-v2.5-pro

# 2. Configure the provider with API key
cat > ~/.hermes/config.yaml << 'EOF'
model:
  default: opencode-go/mimo-v2.5-pro
  provider: opencode-go

providers:
  opencode-go:
    api_key: OPENCODE_GO_API_KEY
    base_url: https://opencode.ai/zen/go/v1
EOF

# 3. Add API key to .env
echo "OPENCODE_GO_API_KEY=sk-..." >> ~/.hermes/.env

# 4. Restart and verify Hermes works alone
hermes gateway run
# Send a test message. Only then install hermes-kit.
```

> **OpenCode Go specifically**: Only open-source models. See [providers guide](../providers.md) for the full model list. `gpt-4o` and `claude-sonnet-4` are NOT on opencode-go.

## Hook not loading

**Symptom:** `hermes-kit doctor` shows hooks but Hermes doesn't load them.

**Fix:**
```bash
hermes-kit doctor                # verify hooks are in ~/.hermes/hooks/
hermes-kit gateway run --accept-hooks  # restart with bridge patching
```

## Model override not working

**Symptom:** Router configured but wrong model is used.

**Causes:**
1. Chat/topic ID doesn't match your routing table. Check `hermes-kit router show`.
2. Default fallback is being used because no topic matches.
3. Hook not loaded. Run `hermes-kit doctor`.

**Fix:**
```bash
hermes-kit gateway run --accept-hooks
```

If you changed the route with `/route`, send one more normal message in the same topic or DM. No gateway restart is required for `/route` changes, but the new mapping is applied on the next `session:start`.

Also verify both hooks are installed:
```bash
hermes-kit doctor
```
`router` and `model-switch` should both appear.

## Fallback chain configured but no automatic retry happens

**Symptom:** `fallback_chain.yaml` exists, but a provider failure still surfaces immediately.

**Root cause:** hermes-kit currently registers the fallback chain and exposes `hermes_kit.bridge.retry_with_fallback(session_key)`, but it does not ship a full automatic retry loop in gateway code yet.

**Fix:** Use fallback as session-scoped retry state for your recovery logic or custom hook integration. See [fallback docs](manual/fallback.md).

## Cost tracker shows $0.0000

**Symptom:** Cost tracker runs, but the estimate is zero.

**Root cause:** The current built-in pricing table only covers the bundled OpenCode Go model IDs in `bridge.py`. Unknown model IDs are tracked as zero-cost estimates.

**Fix:** Confirm the routed model ID is one of the documented built-in pricing entries in [cost-tracker docs](manual/cost-tracker.md).

## API key errors

**Symptom:** `Provider 'opencode-go' is set but no API key was found.`

**Fix:** The `.env` file must be in `HERMES_HOME`:

```bash
echo "OPENCODE_GO_API_KEY=sk-..." >> ~/.hermes/.env
```

Not in the project root. Hermes reads from `~/.hermes/.env` (or `$HERMES_HOME/.env`).

## Gateway not responding on Telegram

**Symptom:** Bot is silent.

**Checklist:**
1. Is the gateway running? `hermes gateway status`
2. Is Telegram configured? Check `~/.hermes/config.yaml` for `platforms.telegram.enabled: true`
3. Is the bot token correct? Verify with `curl https://api.telegram.org/bot<TOKEN>/getMe`
4. Are users allowed? Set `GATEWAY_ALLOW_ALL_USERS=true` for testing

## Duplicate gateway instances

**Symptom:** `Gateway already running (PID ...)`

**Fix:**
```bash
hermes gateway stop
hermes gateway start
```

Or kill manually:
```bash
pkill -f "hermes gateway"
```

## Hook errors don't appear in logs

Hermes catches hook errors silently (hooks are fire-and-forget). To debug:

1. Add `print()` statements in your hook's `handler.py`
2. Check the gateway log for the output
3. Hook errors are logged by Hermes under the `[hooks]` prefix

## Getting help

If none of this helps, include these in your issue:

- `hermes-kit doctor` output
- `hermes gateway status`
- Relevant gateway log lines
- Your `.gitignore`d config files (topic_router.yaml, fallback_chain.yaml, etc.)
