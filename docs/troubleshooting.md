# Troubleshooting

## Hook not loading

**Symptom:** `hermes-kit doctor` shows hooks but Hermes doesn't load them.

**Fix:**
```bash
hermes-kit doctor                # verify hooks are in ~/.hermes/hooks/
hermes gateway restart           # Hermes only discovers hooks on restart
hermes gateway run --accept-hooks  # ensure hooks are enabled
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
