# Memory SNN-LNN Hybrid Extension

Memory optimization for OpenClaw using a hybrid **Spiking Neural Network (SNN)** and **Liquid Neural Network (LNN)** architecture.

## Architecture

```
OpenClaw Agent ──► TypeScript Plugin ──HTTP──► Python Model Server
                                    ◄──JSON──┘
                                           │
                                    ┌──────┴──────┐
                                    │  SNN Encoder │  Temporal pattern detection
                                    │  (LIF neurons)│  via leaky integrate-and-fire
                                    ├──────────────┤
                                    │  LNN Processor│  Adaptive context modeling
                                    │  (LTC-ODE)    │  via liquid time constants
                                    └──────────────┘
```

- **SNN Component**: Leaky Integrate-and-Fire (LIF) neurons encode text into spike trains. Temporal features (burst index, pattern complexity, spike rate) guide optimization decisions.
- **LNN Component**: Liquid Time-Constant (LTC) neural ODE network with adaptive time constants for context-dependent semantic encoding.
- **Hybrid Processing**: Four optimization modes — summarize, extract, compress, full.

## Quick Start

### 1. Install Dependencies

```bash
# Python dependencies
pip install flask

# Node.js dependencies (handled by pnpm workspace)
cd /path/to/openclaw-solomon && pnpm install
```

### 2. Start the Model Server

```bash
# Option A: Direct
python3 extensions/memory-snn-lnn/model/server.py

# Option B: Via OpenClaw CLI
pnpm openclaw snn-lnn serve --port 5001

# Option C: Docker (see below)
docker compose up snn-lnn
```

The server listens on `http://127.0.0.1:5001` by default.

### 3. Verify Health

```bash
curl http://127.0.0.1:5001/health
# {"status": "ok", "model": "snn-lnn-hybrid", "version": "0.1.0"}
```

### 4. Register the Plugin

Add to your OpenClaw config (`.env` or config):

```yaml
plugins:
  - id: memory-snn-lnn
    config:
      modelEndpoint: "http://127.0.0.1:5001"
      enabled: true
      autoOptimize: true
      optimizationMode: full
      fallbackToBuiltin: true
```

## API Endpoints

| Endpoint      | Method | Description                                |
| ------------- | ------ | ------------------------------------------ |
| `/health`     | GET    | Service health check                       |
| `/optimize`   | POST   | Optimize text (body: `{text, mode}`)       |
| `/similarity` | POST   | Compare two texts (body: `{text1, text2}`) |
| `/encode`     | POST   | Get LNN semantic vector (body: `{text}`)   |

### Optimization Modes

- **summarize**: Condenses text using SNN burst detection + LNN context scoring
- **extract**: Pulls key facts, preferences, decisions with importance scores
- **compress**: Produces 32-dim semantic vector + temporal features
- **full**: All of the above

## Tools

The extension registers these agent tools:

| Tool                    | Description                          |
| ----------------------- | ------------------------------------ |
| `memory_optimize`       | Optimize text via SNN-LNN processing |
| `memory_compare`        | Semantic similarity comparison       |
| `memory_snn_lnn_status` | Check service health                 |

## CLI Commands

```bash
# Check status
pnpm openclaw snn-lnn status

# Optimize text
pnpm openclaw snn-lnn optimize --text "Some long text..." --mode summarize

# Start the model server
pnpm openclaw snn-lnn serve --port 5001
```

## Configuration

| Key                 | Default                 | Description                                   |
| ------------------- | ----------------------- | --------------------------------------------- |
| `modelEndpoint`     | `http://127.0.0.1:5001` | Python server URL                             |
| `enabled`           | `true`                  | Enable/disable optimization                   |
| `autoOptimize`      | `true`                  | Enable lifecycle hook auto-optimization       |
| `optimizationMode`  | `full`                  | Default mode: summarize/extract/compress/full |
| `maxInputTokens`    | `8192`                  | Max tokens per request                        |
| `timeoutMs`         | `30000`                 | Request timeout                               |
| `fallbackToBuiltin` | `true`                  | Fall back if service down                     |

## Testing

```bash
# Unit tests (no server needed)
npx vitest run extensions/memory-snn-lnn/index.test.ts --config vitest.extensions.config.ts

# Integration tests (requires running server)
npx vitest run extensions/memory-snn-lnn/index.integration.test.ts --config vitest.extensions.config.ts
```

All tests should pass (11 unit + 21 integration = 32 tests).

## Edge Deployment (Jetson Orin)

### Docker Compose

```yaml
services:
  snn-lnn:
    build:
      context: .
      dockerfile: extensions/memory-snn-lnn/model/Dockerfile
    ports:
      - "5001:5001"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  openclaw:
    image: openclaw/openclaw:latest
    environment:
      - MEMORY_SNN_LNN_ENDPOINT=http://snn-lnn:5001
    depends_on:
      - snn-lnn
```

### Direct deployment on Jetson

```bash
# Install Python deps
pip install flask

# Start server
python3 extensions/memory-snn-lnn/model/server.py &

# Configure OpenClaw to point to it
openclaw config set plugins.memory-snn-lnn.modelEndpoint "http://localhost:5001"
openclaw config set plugins.memory-snn-lnn.enabled true
openclaw gateway restart
```

This extension uses **zero external API tokens** — all inference runs locally on your hardware.
