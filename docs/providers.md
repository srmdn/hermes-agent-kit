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
| `opencode-go/qwen3.7-max` | General purpose | Qwen3.7 Max |
| `opencode-go/qwen3.7-plus` | Balanced performance | Qwen3.7 Plus |
| `opencode-go/qwen3.6-plus` | Coding, reasoning | Qwen3.6 Plus |
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

Base URL: `https://api.openai.com/v1`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `gpt-5.5` | Flagship, coding | $5.00 / $30.00 |
| `gpt-5.4` | Balanced | $2.50 / $15.00 |
| `gpt-5.4-mini` | Fast, cheap | $0.75 / $4.50 |
| `o3` | Deep reasoning | $10.00 / $40.00 |

## Anthropic

```yaml
model:
  provider: anthropic
```

API key: `ANTHROPIC_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `claude-opus-4-8` | Complex reasoning, agentic coding | $5.00 / $25.00 |
| `claude-sonnet-4-6` | Best speed/intelligence balance | $3.00 / $15.00 |
| `claude-haiku-4-5` | Fast, cheap | $1.00 / $5.00 |

> **Deprecation notice:** `claude-sonnet-4-20250514` and `claude-opus-4-20250514` are deprecated and retiring June 15, 2026. Migrate to the latest stable IDs above.

## xAI (Grok)

```yaml
model:
  provider: xai
```

API key: `XAI_API_KEY`

Base URL: `https://api.x.ai/v1`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `grok-4.3` | Flagship, general purpose | $1.25 / $2.50 |
| `grok-build-0.1` | Coding, agentic tasks | $1.00 / $2.00 |

## Mistral

```yaml
model:
  provider: mistral
```

API key: `MISTRAL_API_KEY`

Base URL: `https://api.mistral.ai/v1`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `mistral-medium-3.5` | Flagship, coding, reasoning (128B, 256k) | Contact Mistral |
| `mistral-small-4` | Balanced, efficient | Contact Mistral |
| `codestral` | Coding specialist | Contact Mistral |

## Google (Gemini)

```yaml
model:
  provider: google
```

API key: `GEMINI_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `gemini-3.5-flash` | Latest, fast, agentic coding | Free tier available |
| `gemini-3.1-pro` | Deep reasoning | Free tier available |
| `gemini-3.1-deep-think` | Extended reasoning | Free tier available |
| `gemini-3.1-flash-lite` | Cheapest, speed | Free tier available |

> **Shutdown notice:** Gemini 2.0 models shut down June 1, 2026. Use 3.x models above.

## DeepSeek

```yaml
model:
  provider: deepseek
```

API key: `DEEPSEEK_API_KEY`

| Model | Best For | Cost (per 1M tokens) |
|---|---|---|
| `deepseek-v4-pro` | Latest, reasoning | See website |
| `deepseek-v4-flash` | Fast, cheap | See website |

> **Deprecation notice:** `deepseek-chat` and `deepseek-reasoner` are deprecated and retiring July 24, 2026. Migrate to `deepseek-v4-pro` or `deepseek-v4-flash`.

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
