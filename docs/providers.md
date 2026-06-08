# Providers

hermes-kit works with any provider Hermes supports. Your hooks route messages to any model, any provider.

> **OpenCode Go models are open-source only.** For OpenAI (GPT-4o), Anthropic (Claude), or Google (Gemini) models, use the respective provider section below. You'll need your own API keys.

## opencode-go (14 models)

Hermes has native `opencode-go` support. Set in `config.yaml`:

```yaml
model:
  provider: opencode-go
```

API key: `OPENCODE_GO_API_KEY` in `~/.hermes/.env`

Base URL: `https://opencode.ai/zen/go/v1` (auto-configured)

### Available Models

| Model ID | Best For | Notes |
|---|---|---|
| `opencode-go/deepseek-v4-pro` | General purpose, logic | DeepSeek V4 Pro — flagship |
| `opencode-go/deepseek-v4-flash` | Fast responses | DeepSeek V4 Flash |
| `opencode-go/kimi-k2.6` | Long context, research | Kimi K2.6 — up to 128K tokens |
| `opencode-go/kimi-k2.5` | Long context | Kimi K2.5 |
| `opencode-go/qwen-3.7-max` | General purpose | Qwen3.7 Max |
| `opencode-go/qwen-3.7-plus` | Balanced performance | Qwen3.7 Plus |
| `opencode-go/qwen-3.6-plus` | Coding, reasoning | Qwen3.6 Plus |
| `opencode-go/minimax-m2.7` | Long context | MiniMax M2.7 |
| `opencode-go/minimax-m2.5` | General purpose | MiniMax M2.5 |
| `opencode-go/minimax-m3` | Latest generation | MiniMax M3 |
| `opencode-go/mimo-v2.5-pro` | Multimodal, vision | MiMo-V2.5-Pro |
| `opencode-go/mimo-v2.5` | Multimodal | MiMo-V2.5 |
| `opencode-go/glm-5.1` | Bilingual (EN/ZH) | GLM-5.1 |
| `opencode-go/glm-5` | Bilingual (EN/ZH) | GLM-5 |

Check [opencode.ai/models](https://opencode.ai/models) for the full current list.

## OpenAI

```yaml
model:
  provider: openai
```

API key: `OPENAI_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `gpt-4o` | General purpose | $2.50 / $10.00 |
| `gpt-4o-mini` | Fast, cheap | $0.15 / $0.60 |
| `o4-mini` | Reasoning | $1.10 / $4.40 |
| `o3` | Deep reasoning | $10.00 / $40.00 |

## Anthropic

```yaml
model:
  provider: anthropic
```

API key: `ANTHROPIC_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `claude-sonnet-4-20250514` | Coding, analysis | $3.00 / $15.00 |
| `claude-opus-4-20250514` | Complex reasoning | $15.00 / $75.00 |
| `claude-haiku-4-20250514` | Fast, cheap | $0.80 / $4.00 |

## OpenRouter (multi-provider gateway)

```yaml
model:
  provider: openrouter
```

API key: `OPENROUTER_API_KEY`

Access to 200+ models. Prefix model IDs with the provider:

- `openrouter/openai/gpt-4o-mini`
- `openrouter/anthropic/claude-sonnet-4`
- `openrouter/deepseek/deepseek-chat`
- `openrouter/qwen/qwen-3.6-plus`

## Google (Gemini)

```yaml
model:
  provider: google
```

API key: `GEMINI_API_KEY`

| Model | Best For |
|---|---|
| `gemini-2.5-pro` | Deep reasoning |
| `gemini-2.5-flash` | Speed, cost-effective |

## DeepSeek

```yaml
model:
  provider: deepseek
```

API key: `DEEPSEEK_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `deepseek-chat` | Coding, general | $0.14 / $0.28 |
| `deepseek-reasoner` | Complex reasoning | $0.55 / $2.19 |
