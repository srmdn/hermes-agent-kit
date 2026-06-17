# Providers

hermes-kit works with any provider Hermes supports. The router hook only needs a valid model ID plus the provider that can serve it.

**Last verified:** June 17, 2026

This page is a curated operator guide, not a complete live catalog. Provider model lists change often. For the newest releases, always confirm against the provider's official model or pricing page before changing production routes.

## How to Read This Page

- **Direct providers** expose their own native API and model IDs.
- **Inference routers** expose many model families behind one API surface.
- **Open-weight model families** are not always the same thing as API providers. For example, Qwen is a model family; Bailian, SiliconFlow, OpenRouter, and OpenCode Go are API providers that may serve Qwen models.

## Quick Recommendations

If you want the shortest path to strong open-model coverage:

- Use `opencode-go` if you want one provider with curated Chinese/open-model coverage baked into hermes-kit examples.
- Use `openrouter` if you want the widest multi-provider catalog through one API key.
- Use `siliconflow` if you want one API layer focused on open-weight and Chinese model families.
- Use direct providers such as `anthropic`, `openai`, `deepseek`, `google`, or `xai` when you want the vendor's native API behavior.

## Direct Providers

### opencode-go

Hermes has native `opencode-go` support. Set in `config.yaml`:

```yaml
model:
  provider: opencode-go
```

API key: `OPENCODE_GO_API_KEY` in `~/.hermes/.env`

Base URL: `https://opencode.ai/zen/go/v1` (auto-configured by hermes-kit bootstrap)

Example models used throughout this repo:

| Model ID | Best For | Notes |
|---|---|---|
| `opencode-go/deepseek-v4-pro` | General purpose, logic | DeepSeek flagship in the bundle |
| `opencode-go/deepseek-v4-flash` | Fast responses | Cheap default / fallback candidate |
| `opencode-go/kimi-k2.6` | Long context, research | Strong agentic coding and long-context tasks |
| `opencode-go/kimi-k2.5` | General purpose | Older Kimi line, still bundled |
| `opencode-go/qwen3.7-max` | High-end general use | Flagship Qwen in bundle |
| `opencode-go/qwen3.7-plus` | Balanced performance | Good default for mixed workloads |
| `opencode-go/qwen3.6-plus` | Coding, reasoning | Still used in many examples in this repo |
| `opencode-go/minimax-m3` | Latest MiniMax generation | General-purpose route option |
| `opencode-go/glm-5.1` | EN/ZH bilingual work | GLM family route option |

Check [opencode.ai/models](https://opencode.ai/models) for the current catalog.

### OpenAI

```yaml
model:
  provider: openai
```

API key: `OPENAI_API_KEY`

Base URL: `https://api.openai.com/v1`

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `gpt-5.5` | Flagship quality | Highest-end general/coding route |
| `gpt-5.4` | Balanced | Lower cost than `gpt-5.5` |
| `gpt-5.4-mini` | Fast, cheap | Good low-cost default |
| `o3` | Deep reasoning | Best when reasoning matters more than latency |

Official pricing page: [OpenAI API pricing](https://developers.openai.com/api/docs/pricing)

### Anthropic

```yaml
model:
  provider: anthropic
```

API key: `ANTHROPIC_API_KEY`

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `claude-opus-4-8` | Complex reasoning | Highest-end Anthropic route |
| `claude-sonnet-4-6` | Best balance | Strong default for many teams |
| `claude-haiku-4-5` | Fast, cheap | Lightweight route option |

Official model page: [Claude models overview](https://platform.claude.com/docs/en/about-claude/models/overview)

> `claude-sonnet-4-20250514` and `claude-opus-4-20250514` are legacy IDs. Prefer the stable aliases above.

### Google (Gemini)

```yaml
model:
  provider: google
```

API key: `GEMINI_API_KEY`

Use the current Gemini 2.5 family, not the older 3.1/3.5 naming previously documented here.

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `gemini-2.5-flash` | Fast general use | Cheapest mainstream Gemini route |
| `gemini-2.5-pro` | Strong reasoning | Higher quality, higher cost |
| `gemini-2.5-flash-image` | Image generation/multimodal | Specialized image-capable route |

Official pricing page: [Gemini Developer API pricing](https://ai.google.dev/gemini-api/docs/pricing)

> Gemini `2.0` models are shut down. Do not use them in new configs.

### DeepSeek

```yaml
model:
  provider: deepseek
```

API key: `DEEPSEEK_API_KEY`

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `deepseek-v4-pro` | Reasoning, coding | Main DeepSeek flagship |
| `deepseek-v4-flash` | Fast responses | Lower-cost default/fallback |

Official pricing page: [DeepSeek models and pricing](https://api-docs.deepseek.com/quick_start/pricing)

> `deepseek-chat` and `deepseek-reasoner` are compatibility aliases being retired on July 24, 2026. Prefer `deepseek-v4-pro` or `deepseek-v4-flash`.

### xAI

```yaml
model:
  provider: xai
```

API key: `XAI_API_KEY`

Base URL: `https://api.x.ai/v1`

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `grok-4.3` | Flagship general use | Highest-end xAI route |
| `grok-build-0.1` | Coding and agents | Tool-heavy development tasks |

### Mistral

```yaml
model:
  provider: mistral
```

API key: `MISTRAL_API_KEY`

Base URL: `https://api.mistral.ai/v1`

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `mistral-medium-3.5` | Flagship general use | Strong balanced route |
| `mistral-small-4` | Efficient workloads | Lower-cost Mistral route |
| `codestral` | Coding specialist | Purpose-built for code tasks |

## Chinese / Open-Model Direct Platforms

These matter a lot in current real-world routing setups, especially for coding, agent loops, and cost-sensitive deployment.

### Bailian / DashScope (Qwen via Alibaba Cloud)

Alibaba's Bailian platform is the primary direct platform for current Qwen releases.

Provider name in Hermes may depend on your Hermes installation or custom provider wiring. If Hermes exposes a dedicated Alibaba-compatible provider in your setup, use that provider name plus the platform's official model IDs.

Current examples visible on the official platform:

| Model | Best For | Notes |
|---|---|---|
| `qwen3.7-plus` | Balanced reasoning and coding | Widely useful default |
| `qwen3.7-max` | Flagship quality | Higher-end Qwen route |

Official platform: [Alibaba Bailian](https://cn.aliyun.com/product/bailian)

### Kimi / Moonshot

Moonshot's Kimi platform is now a major direct API option for coding and long-context work.

Current examples visible on the official platform:

| Model | Best For | Notes |
|---|---|---|
| `kimi-k2.6` | Long-context coding | Strong autonomous execution claims |
| `kimi-k2.5` | General multimodal tasks | Thinking/non-thinking modes |
| `kimi-k2.7-code` | Coding specialist | Latest dedicated code model on platform |

Official platform: [Kimi API Platform](https://platform.kimi.ai/)

### Z.ai / GLM

GLM models remain important for bilingual and Chinese-market workloads.

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `glm-5.1` | EN/ZH bilingual work | Already bundled in `opencode-go` examples |
| `glm-5` | General use | Older but still practical |

Official platform: [Z.ai / BigModel Open Platform](https://open.bigmodel.cn/)

### MiniMax

MiniMax is another major Chinese-family option for general and long-context routing.

Curated examples:

| Model | Best For | Notes |
|---|---|---|
| `minimax-m3` | Latest generation | Strong general-purpose route |
| `minimax-m2.7` | Long-context tasks | Common open-model bundle option |
| `minimax-m2.5` | Lower-cost general use | Older but still useful |

Official site: [MiniMax](https://www.minimaxi.com/)

## Inference Routers for Open Models

These are often the easiest way to access Chinese/open-weight ecosystems without managing separate direct-provider integrations.

### OpenRouter

```yaml
model:
  provider: openrouter
```

API key: `OPENROUTER_API_KEY`

OpenRouter exposes many providers behind one API. Prefix model IDs with the upstream family:

- `openrouter/openai/gpt-5.4-mini`
- `openrouter/anthropic/claude-sonnet-4-6`
- `openrouter/deepseek/deepseek-v4-pro`
- `openrouter/qwen/qwen-3.7-plus`
- `openrouter/moonshotai/kimi-k2.6`
- `openrouter/z-ai/glm-5.1`

Official catalog: [OpenRouter models](https://openrouter.ai/models)

### SiliconFlow

SiliconFlow is especially useful when you want one API surface focused on open-weight and Chinese model families.

Official docs explicitly list broad coverage including DeepSeek, Qwen, GLM, Kimi, MiniMax, Step, Wan, and others.

Representative model families mentioned in docs:

- DeepSeek
- Qwen / Qwen Coder
- GLM
- Kimi
- MiniMax

Official docs: [SiliconFlow introduction](https://docs.siliconflow.com/en/userguide/introduction)

If Hermes in your environment supports a custom OpenAI-compatible provider entry, SiliconFlow is a strong candidate for that slot.

## Multi-Provider Routing Examples

### Route different topics to different ecosystems

```yaml
default:
  model: "opencode-go/qwen3.7-plus"

topics:
  "42":
    model: "gpt-5.4-mini"
    provider: "openai"
  "7":
    model: "claude-sonnet-4-6"
    provider: "anthropic"
  "99":
    model: "deepseek-v4-pro"
    provider: "deepseek"
```

### Use an inference router for open-model coverage

```yaml
default:
  model: "openrouter/qwen/qwen-3.7-plus"
  provider: "openrouter"

topics:
  "42":
    model: "openrouter/deepseek/deepseek-v4-pro"
    provider: "openrouter"
  "7":
    model: "openrouter/moonshotai/kimi-k2.6"
    provider: "openrouter"
```

## Choosing a Provider

Pick based on operator needs, not hype alone:

| Need | Best Starting Point |
|---|---|
| One curated open-model bundle | `opencode-go` |
| Native OpenAI behavior | `openai` |
| Native Claude behavior | `anthropic` |
| Native Gemini behavior | `google` |
| Native DeepSeek API | `deepseek` |
| Broadest multi-provider catalog | `openrouter` |
| Open-model-heavy inference layer | `siliconflow` |
| Direct Qwen platform | Bailian / DashScope |
| Direct Kimi platform | Moonshot / Kimi |

## Important Caveats

- This page is a verified snapshot, not a live catalog.
- Provider names available in Hermes depend on Hermes itself. Some platforms here may require a custom OpenAI-compatible provider entry if Hermes does not expose a dedicated built-in provider name.
- `docs/manual/cost-tracker.md` documents hermes-kit's internal pricing estimates, which are narrower than the provider ecosystem listed here.
- For public docs, prefer stable aliases and well-known flagship IDs over preview IDs unless you are documenting a preview feature on purpose.
