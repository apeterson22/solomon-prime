# RDE-Reflex Architecture

## Architectural position

RDE-Reflex is a bounded decision plane. It is neither the reasoning plane nor the execution plane.

```text
┌────────────────────────────────────────────────────────────┐
│ Reasoning / orchestration                                  │
│ LLMs, agents, humans, planners                             │
└───────────────────────┬────────────────────────────────────┘
                        │ state + bounded candidates
                        ▼
┌────────────────────────────────────────────────────────────┐
│ RDE-Reflex                                                │
│ Contract validation → provider → normalization → policy    │
│                   → DECIDED / ESCALATE / ERROR             │
└───────────────────────┬────────────────────────────────────┘
                        │ decision only
                        ▼
┌────────────────────────────────────────────────────────────┐
│ Authorization / approvals / workflow / execution           │
└───────────────────────┬────────────────────────────────────┘
                        │ observed outcome
                        ▼
┌────────────────────────────────────────────────────────────┐
│ Feedback / evaluation / calibration / future compilation   │
└────────────────────────────────────────────────────────────┘
```

## v0.1 components

### Contract layer

`models.py` defines versionable typed request/response semantics.

### Provider layer

`DecisionProvider` is deliberately small. Provider implementations score the exact candidate set supplied by the caller.

The engine validates provider output so a provider cannot:

- add candidates,
- omit candidates,
- return negative/non-finite probabilities,
- return a zero-mass distribution.

### Policy layer

Policy converts scored distributions into bounded decisions.

Current signals:

- maximum candidate probability = confidence,
- normalized Shannon entropy,
- provider calibration status.

Current outcomes:

- `DECIDED`
- `ESCALATE`
- `ERROR`

### Feedback layer

v0.1 uses append-only JSONL for simplicity. The public semantic is the feedback record, not the storage backend.

### API layer

FastAPI exposes the engine as an independent service.

## Why provider and policy are separate

A model should estimate evidence/probability. It should not silently decide how much uncertainty a particular deployment accepts.

The same provider can therefore support:

- low-risk high-coverage policy,
- high-risk high-abstention policy,
- development policy,
- calibrated-production-only policy.

## Why candidate generation is outside the provider

A bounded decision provider should not gain hidden authority to redefine its available actions. When the action space appears incomplete, RDE-Reflex escalates. A reasoning system may then propose a changed action space through the future Reflex Compilation pipeline.

## Planned architecture

```text
                   ┌─────────────────────┐
                   │ Reflex Registry      │
                   │ version + policy     │
                   └─────────┬───────────┘
                             │
caller ──► contract ──► router/provider ──► policy ──► result
                             │                │
                       ┌─────┴─────┐          │
                       │ providers │          │
                       │ native    │          │
                       │ compact   │          │
                       │ external  │          │
                       └───────────┘          │
                                             ▼
                                      challenger/OOD
                                             │
                                    ┌────────┴────────┐
                                    │ feedback/event  │
                                    │ evaluation      │
                                    └────────┬────────┘
                                             ▼
                                    Reflex Compilation
                                             │
                                      proposed version
                                             │
                                     approval/promotion
```

## Integration rules

- Never import Solomon Prime code into `rde_reflex`.
- Caller-specific adapters live outside the engine core.
- Execution credentials do not belong in RDE-Reflex.
- Provider/model identity must be observable.
- Production reflex changes are versioned, never in-place mutations.
