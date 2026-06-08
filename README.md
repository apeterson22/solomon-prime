# SolomonPrime — Enterprise AI Gateway

SolomonPrime is a production-hardened fork of [OpenClaw](https://github.com/openclaw/openclaw) with enterprise-grade enhancements for security, observability, model management, and cross-provider session portability.

## What's Included

### Core Enhancements

| Enhancement | Description | Location |
|-------------|-------------|----------|
| **SNN-LNN Memory Optimization** | Hybrid Spiking Neural Network + Liquid Neural Network for memory compression, summarization, and extraction | `extensions/memory-snn-lnn/` |
| **Cross-Provider Session Memory** | Canonical session key resolution — memory persists across provider switches | `src/config/sessions/cross-provider-memory.ts` |
| **Model Quota Tracking** | Track token usage, costs, and health across 14+ models with auto-failover | `tools/model-quota/` |
| **AegisQR Integration** | Encrypted, signed capsule format for secure model artifact distribution | `docs/integration/aegisqr-integration-plan.md` |
| **Security Guidance** | Hermes plugin that warns on dangerous file-write patterns | Hermes bundled plugin |
| **Langfuse Tracing** | OpenClaw plugin for LLM observability via Langfuse | `extensions/langfuse-tracer/` |

### Model Ecosystem

- **94 models** across 10 providers (OpenRouter, Ollama, Google, Anthropic, GitHub Copilot, OpenAI, etc.)
- **12 free tier models** via OpenRouter (zero cost)
- **Cross-provider fallbacks** — automatic failover when a provider is unavailable
- **Model quota tracking** — per-model token usage, cost, and health monitoring

### Security

- **AegisQR encrypted capsules** — XChaCha20-Poly1305 + Ed25519 for model artifact distribution
- **Security guidance** — Automatic warnings on dangerous code patterns
- **Fail-closed defaults** — Auto-execute disabled, executable quarantine
- **Audit trail** — Signed, tamper-evident audit logging

## Quick Start

```bash
# Clone
git clone git@github.com:apeterson22/solomon-prime.git
cd solomon-prime

# Install dependencies
pnpm install

# Build
pnpm build

# Configure
cp .env.example .env
# Edit .env with your API keys

# Start gateway
pnpm openclaw gateway start
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SolomonPrime Gateway                       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ memory-snn-lnn│  │ cross-provider│  │ model-quota │      │
│  │ extension     │  │ session memory│  │ tracker     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │                                 │
│                   ┌────────┴────────┐                        │
│                   │  AegisQR        │                        │
│                   │  Integration    │                        │
│                   └────────┬────────┘                        │
│                            │                                 │
│              ┌─────────────┼─────────────┐                   │
│              │             │             │                   │
│              v             v             v                   │
│       ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│       │ aegisqr  │  │  aicx    │  │ langfuse │             │
│       │ CLI      │  │  CLI     │  │ tracer   │             │
│       └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────────┘
```

## Extensions

| Extension | Purpose | Tests |
|-----------|---------|-------|
| `memory-snn-lnn` | SNN-LNN hybrid memory optimization | 32/32 passing |
| `langfuse-tracer` | LLM observability via Langfuse | — |
| `memory-core` | File-backed memory search | Built-in |
| `memory-lancedb` | LanceDB vector memory | Built-in |

## Model Management

```bash
# List all available models
openclaw models list

# Check model health
python3 tools/model-quota/model_quota.py status

# Auto-switch to best available free model
python3 tools/model-quota/switch_model.py free

# Regenerate models.json after config changes
python3 tools/model-quota/regenerate_models.py
```

## SNN-LNN Memory Optimization

```bash
# Start the model server
python3 extensions/memory-snn-lnn/model/server.py

# Or via CLI
pnpm openclaw snn-lnn serve --port 5001

# Optimize text
pnpm openclaw snn-lnn optimize --text "Long text to summarize..." --mode summarize

# Check service status
pnpm openclaw snn-lnn status
```

## AegisQR Secure Distribution

```bash
# Pack model artifacts
aicx pack extensions/memory-snn-lnn/model/ --out model.aicx
aegisqr pack model.aicx --out model.aqr --passphrase-stdin

# QR air-gap transfer
aegisqr export qr model.aqr --out qr-packets/ --packet-size 512
aegisqr import qr qr-packets/ --out rebuilt.aqr

# Verify integrity
sha256sum model.aqr rebuilt.aqr
```

## Configuration

Key environment variables in `~/.openclaw/.env`:

```bash
# OpenRouter (12 free models)
OPENROUTER_API_KEY=sk-or-...

# Langfuse observability
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=http://localhost:3050

# Google Gemini
GEMINI_API_KEY=...

# Ollama (local)
OLLAMA_API_KEY=ollama
```

## License

Apache 2.0 — See [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run `pnpm test` and `pnpm check`
4. Submit a pull request
