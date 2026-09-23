# RDE-Reflex

**RDE-Reflex** (pronounced **"Ready Reflex"**) is a provider-neutral **Reflex Decision Engine** for fast, bounded, auditable AI decisions.

It is designed to sit beneath slower reasoning systems. An LLM or agent can reason broadly, while RDE-Reflex handles recurring decisions with explicit candidates, probabilities, confidence, uncertainty, calibration status, and a mandatory escape path.

> **Core idea:** compile successful reasoning into monitored reflexes without turning those reflexes into an unchallengeable ceiling.

## Status

**v0.1 bootstrap / experimental.** The API, decision contracts, policy engine, feedback loop, and provider abstraction are functional. The included `heuristic-v0` provider exists only as a dependency-light development baseline and is explicitly **uncalibrated**. It is not the intended production model.

RDE-Reflex is **not** a Jev/OpenJev wrapper. Those systems are useful references and future benchmark targets. RDE-Reflex owns its contracts, lifecycle, evaluation model, provider interface, and future native model architecture.

## What v0.1 provides

- `boolean`, `choice`, and `score` decision primitives.
- Batched bounded decisions against a shared state/context.
- Provider-neutral scoring interface.
- Explicit probability distributions.
- Confidence and normalized-entropy measurement.
- Calibration status carried through the contract.
- Configurable policy thresholds.
- Mandatory `escalate` path for uncertain/unsupported decisions.
- Provider failures converted into bounded errors rather than hidden action.
- Append-only feedback capture for later calibration/training.
- Optional API-key protection.
- FastAPI HTTP service and OpenAPI schema.
- Tests and container-ready local deployment.

## Non-negotiable invariant

**RDE-Reflex does not execute actions.**

It evaluates declared candidate decisions and returns a result. The caller remains responsible for authorization, approval, side effects, and execution. This separation is deliberate: scoring must not silently become authority.

## Decision lifecycle

```text
Reason
  ↓
Propose bounded decision + candidates
  ↓
RDE-Reflex scores candidates
  ↓
Normalize + uncertainty/calibration policy
  ├── sufficiently supported → DECIDED
  └── insufficient/novel/error → ESCALATE
                                  ↓
                         slower reasoning / human / policy
                                  ↓
                             observed outcome
                                  ↓
                               feedback
                                  ↓
                   evaluate / calibrate / promote
                                  ↓
                        reusable monitored reflex
```

The long-term lifecycle is:

**Reason → propose → simulate → evaluate → calibrate → approve/promote → Reflex → monitor → challenge → evolve.**

## Quick start

Requires Python 3.11+.

```bash
cd rde-reflex
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
python -m rde_reflex
```

The API listens on `127.0.0.1:8787` by default.

Health:

```bash
curl http://127.0.0.1:8787/healthz
```

Capabilities:

```bash
curl http://127.0.0.1:8787/v1/capabilities
```

Example decision:

```bash
curl -s http://127.0.0.1:8787/v1/decide \
  -H 'content-type: application/json' \
  -d '{
    "state": "EDI partner 102 returned an intermittent timeout. Previous retry succeeded.",
    "policy": {
      "min_confidence": 0.45,
      "max_normalized_entropy": 1.0,
      "require_calibrated": false
    },
    "decisions": [{
      "id": "edi-recovery",
      "kind": "choice",
      "instruction": "Choose the bounded recovery action. Escalate when unsupported.",
      "candidates": [
        {"id": "retry", "description": "retry transient timeout"},
        {"id": "quarantine", "description": "quarantine invalid payload"},
        {"id": "human_review", "description": "send for human review"}
      ]
    }]
  }' | python -m json.tool
```

Production policy should generally require a calibrated provider. The development provider deliberately reports `uncalibrated`, which lets integration work proceed while preventing accidental claims that the v0.1 baseline is production intelligence.

## HTTP surface

| Endpoint | Purpose |
| --- | --- |
| `GET /healthz` | Liveness and active provider |
| `GET /v1/capabilities` | Supported primitives and engine metadata |
| `POST /v1/decide` | Evaluate one or more bounded decisions |
| `POST /v1/feedback` | Record observed outcomes |

## Project layout

```text
rde-reflex/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── PRD-v0.1.md
│   ├── ROADMAP.md
│   └── SOLOMON-INTEGRATION.md
├── examples/
│   └── edi_decision.json
├── src/rde_reflex/
│   ├── api.py
│   ├── engine.py
│   ├── feedback.py
│   ├── models.py
│   ├── policy.py
│   └── providers/
│       ├── base.py
│       └── heuristic.py
├── tests/
│   ├── test_api.py
│   ├── test_engine.py
│   └── test_models.py
├── .env.example
├── .gitignore
├── Dockerfile
├── Makefile
└── pyproject.toml
```

## Design principles

1. **Bounded decisions, not hidden agency.**
2. **Uncertainty is a first-class output.**
3. **Abstention/escalation is success when evidence is weak.**
4. **Providers are replaceable; the contract is stable.**
5. **Every production reflex is measurable and challengeable.**
6. **Reasoning may create candidates; reflexes may not silently expand authority.**
7. **Promotion is evidence-based, reversible, and auditable.**
8. **RDE-Reflex remains independently deployable from Solomon Prime.**

See [the v0.1 PRD](docs/PRD-v0.1.md) for the complete product specification.
