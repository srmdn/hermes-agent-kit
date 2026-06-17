# Router — Per-Topic Model Routing

Route Telegram topics to different AI models. Finance chat uses a cheap model, coding chat uses a powerful one.

## How It Works

The router hook fires at `session:start` — before the AI agent processes your message. It reads the Telegram chat/topic ID, looks it up in the routing table, and sets the model override.

## Finding Your Chat/Topic IDs

**Telegram DMs and group chats** use numeric IDs. You can't see them in the app UI.

### Method 1: Message your bot

Send a message to your bot. The bot's logs will show the chat ID.

### Method 2: Check Hermes gateway logs

```bash
hermes logs | grep "chat_id"
```

### Method 3: Use @userinfobot on Telegram

Send `/start` to [@userinfobot](https://t.me/userinfobot) — it replies with your user ID and any group chat info.

> **Using /route?** The `/route` command uses your Telegram user ID automatically — no need to look up IDs. If you're managing routes via CLI or YAML, use the methods above.

Group chat IDs start with `-` (e.g., `-1001234567890`). Topic IDs within groups are numeric IDs specific to the topic thread.

## CLI Management

Instead of editing YAML directly, manage routes from the terminal:

```bash
# Set default model
hermes-kit router set-default --model opencode-go/qwen3.6-plus

# Add topic mappings
hermes-kit router add 42 --model opencode-go/deepseek-v4-pro
hermes-kit router add 7 --model opencode-go/qwen3.6-plus

# Route to a different provider
hermes-kit router add 42 --model gpt-4o --provider openai

# View current routing table
hermes-kit router show

# Remove a mapping
hermes-kit router remove 7
```

All commands read/write `~/.hermes/hooks/router/topic_router.yaml` — same file as manual editing below.

## Per-Topic Routing via Telegram (/route)

Switch models directly from Telegram without touching the server. The model-switch hook handles `/route` commands.

### Install the hook

```bash
hermes-kit install model-switch
```

### Commands

| Command | What it does |
|---------|-------------|
| `/route opencode-go/deepseek-v4-pro` | Switch this topic to `opencode-go/deepseek-v4-pro` |
| `/route show` | Show current routing for this topic |
| `/route default opencode-go/qwen3.6-plus` | Set the default model for unmapped topics |
| `/route reset` | Remove routing for this topic (fall back to default) |

### How it works

1. User sends `/route opencode-go/deepseek-v4-pro` in a Telegram DM or group topic
2. Model-switch hook fires, updates `topic_router.yaml` with the new mapping
3. Next `session:start` (next message), the router hook rereads the file and picks up the change

No gateway restart is required for `/route` changes.

### When to use /route vs CLI

| Use | Method |
|-----|--------|
| Quick model switch during chat | `/route` in Telegram |
| Multi-provider routing | `hermes-kit router add --provider openai` |
| Bulk setup (many topics) | `hermes-kit router` CLI |
| Session-scoped switch | `/route` then `/reset` when done |

## Manual YAML Configuration

Edit `~/.hermes/hooks/router/topic_router.yaml`:

```yaml
default:
  model: "opencode-go/qwen3.6-plus"      # fast default for unknown chats

topics:
  "123456789":                           # your DM chat ID
    model: "opencode-go/deepseek-v4-pro"
  "-1001234567890":                      # group or channel
    model: "opencode-go/qwen3.6-plus"
  "42":                                  # topic thread within a group
    model: "opencode-go/kimi-k2.6"
```

## Provider-Specific Model IDs

| Provider | Model ID Format | Example |
|---|---|---|
| opencode-go | `opencode-go/<model>` | `opencode-go/deepseek-v4-pro` |
| OpenAI | `gpt-5.5`, `gpt-5.4-mini` | `gpt-5.4-mini` |
| Anthropic | `claude-sonnet-4-6` | `claude-sonnet-4-6` |
| OpenRouter | `openrouter/<provider>/<model>` | `openrouter/anthropic/claude-sonnet-4` |
| DeepSeek | `deepseek-v4-pro`, `deepseek-v4-flash` | `deepseek-v4-pro` |
| Google | `gemini-2.5-flash`, `gemini-2.5-pro` | `gemini-2.5-flash` |

See the full [providers guide](../providers.md) for model lists and pricing.

## Multi-Provider Routing

Route specific topics to different AI providers. API keys are resolved from `~/.hermes/.env`:

```yaml
default:
  model: "opencode-go/qwen3.6-plus"    # uses OPENCODE_GO_API_KEY

topics:
  "42":
    model: "gpt-4o"
    provider: "openai"                # uses OPENAI_API_KEY
  "7":
    model: "claude-sonnet-4-6"
    provider: "anthropic"             # uses ANTHROPIC_API_KEY
  "99":
    model: "deepseek-v4-pro"
    provider: "deepseek"              # uses DEEPSEEK_API_KEY
```

Via CLI:
```bash
hermes-kit router set-default --model opencode-go/qwen3.6-plus
hermes-kit router add 42 --model gpt-4o --provider openai
hermes-kit router add 7 --model claude-sonnet-4-6 --provider anthropic
```

Supported provider keys: `opencode-go`, `openai`, `anthropic`, `deepseek`, `google`, `openrouter`.

## Example: Multi-Purpose Telegram Gateway

You run a Telegram group with three topics:

| Topic | Use Case | Model | Why |
|---|---|---|---|
| #finance | Stock analysis | `opencode-go/qwen3.6-plus` | Good enough, cheaper |
| #coding | Code reviews | `opencode-go/deepseek-v4-pro` | Best at code |
| #general | Casual chat | `opencode-go/deepseek-v4-flash` | Cheapest, fast |

```yaml
default:
  model: "opencode-go/deepseek-v4-flash"

topics:
  "42":      # #finance
    model: "opencode-go/qwen3.6-plus"
  "7":       # #coding
    model: "opencode-go/deepseek-v4-pro"
```

Topics #general and anything else fall back to `deepseek-v4-flash`.

## Verification

After configuring, restart the gateway:

```bash
hermes-kit gateway run --accept-hooks
```

Send messages in different topics. Check that responses use the assigned model by looking at gateway logs or token usage.

### Verify /route is working

```bash
hermes-kit install model-switch
hermes-kit doctor   # should show model-switch installed
hermes logs | grep "/route"   # after sending a command
```

Then send one normal follow-up message in the same topic or DM. That next message should use the new route.
