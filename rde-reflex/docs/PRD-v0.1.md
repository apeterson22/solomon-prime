# RDE-Reflex v0.1 Product Requirements Document

**Product:** RDE-Reflex  
**Pronunciation:** "Ready Reflex"  
**Expansion:** Reflex Decision Engine  
**Version:** 0.1  
**Status:** Build-ready bootstrap  
**Product type:** Standalone bounded-decision platform and model/runtime research project  
**Primary initial consumer:** Solomon Prime v1.2  
**Dependency policy:** Provider-neutral; no Jev/OpenJev dependency

---

## 1. Executive summary

RDE-Reflex is a standalone decision-intelligence system that turns recurring, well-understood reasoning problems into fast, bounded, measurable "reflexes."

Modern agents often use a large generative model for every step: classification, routing, retry decisions, tool selection, policy checks, anomaly triage, and many other repeated choices. This is flexible but can be expensive, slow, nondeterministic, difficult to calibrate, and unnecessarily verbose.

RDE-Reflex separates **reasoning** from **bounded decision execution**.

A caller supplies current state/context, a precise decision instruction, an explicit candidate/action space, and policy thresholds. RDE-Reflex returns candidate probabilities, selected candidate when safe to decide, confidence, uncertainty/entropy, calibration status, reason codes, provider/model identity and metadata, or an explicit **ESCALATE** result.

The engine never executes the selected action.

The product is broader than a single "Jev-style" scorer. RDE-Reflex owns the full lifecycle by which reasoning can become a reflex and later be challenged:

**Reason → propose → simulate → evaluate → calibrate → approve/promote → Reflex → monitor → challenge → evolve.**

The intended outcome is not to replace reasoning. It is to let a system acquire safe, efficient reflexes while retaining the ability to recognize novelty, question those reflexes, and return to deeper reasoning.

## 2. Problem statement

Agentic systems repeatedly spend high-cost reasoning on bounded questions such as tool/model routing, IDoc/EDI exception triage, retry decisions, known incident remediation selection, workflow-state transitions, and whether a familiar case still fits an established pattern.

General-purpose LLMs can answer these questions but introduce avoidable cost and latency. Hard-coded if/then logic is fast but brittle and difficult to extend across fuzzy boundaries.

A bounded scorer can also fail when the correct action is absent from the candidate set, inputs drift, confidence is miscalibrated, a human authored a flawed action space, the environment changes, or downstream outcomes reveal that an old reflex has become obsolete.

The defining requirement is therefore:

> **Choose quickly when the decision is known and supported; detect when the reflex should not be trusted.**

## 3. Product vision

RDE-Reflex will become a general-purpose reflex layer for AI and automation systems, independent of any single agent framework, LLM provider, decision model, or deployment topology.

Long-term it should accept decision candidates produced by humans/software/reasoning agents; score them with interchangeable providers; recognize uncertainty and novelty; collect outcomes; measure calibration and decision quality; identify failing or obsolete reflexes; propose new or refined reflexes; test proposals in shadow/simulation mode; promote only evidence-supported versions; roll back degraded versions; and expose all of this through stable APIs/SDKs.

RDE-Reflex should be useful without Solomon Prime. Solomon Prime should consume it as an independent decision service.

## 4. Product identity

**RDE-Reflex** is the working brand and is pronounced **"Ready Reflex."**

Product vocabulary:

- **RDE-Reflex** — platform/project.
- **RDE Engine** — bounded decision runtime.
- **Reflex** — versioned bounded decision behavior.
- **Reflex Provider** — model/scorer implementation.
- **Reflex Policy** — uncertainty/calibration/authority rules.
- **Reflex Compilation** — evidence-driven conversion of repeated successful reasoning into proposed fast reflexes.
- **Reflex Registry** — future versioned store of tested/promoted reflexes.
- **Reflex Challenger** — future independent monitor/evaluator that questions degraded or anomalous reflexes.

Formal trademark/domain/package-name clearance remains a launch prerequisite.

## 5. v0.1 goals

RDE-Reflex v0.1 MUST:

1. exist as an independently separable project with a stable package layout;
2. expose a versioned HTTP API;
3. define stable bounded-decision contracts;
4. support boolean, choice, and score primitives;
5. return explicit probability distributions;
6. calculate confidence and normalized entropy;
7. represent calibration status explicitly;
8. implement policy-based abstention/escalation;
9. ensure provider errors do not silently become decisions;
10. capture outcome feedback through an append-only interface;
11. support pluggable decision providers;
12. include a lightweight local provider for integration testing;
13. clearly mark the bootstrap provider as uncalibrated/non-production;
14. include automated tests for the core invariants;
15. remain independent from Solomon Prime internals;
16. document a Solomon Prime v1.2 integration contract;
17. define the roadmap for native trained providers and Reflex Compilation.

## 6. Strategic goals

Future versions SHOULD materially reduce latency and inference cost for recurring decisions; support local/offline deployment; provide statistically defensible calibration; support shadow mode and safe promotion; learn from observed outcomes; discover obsolete/incomplete action spaces; independently evaluate reflex quality; support distributed/high-availability deployment; and provide an interoperable protocol usable by other agent systems.

## 7. Non-goals

RDE-Reflex v0.1 is NOT a general reasoning model, replacement for an LLM, tool executor, workflow engine, permissions system, authorization authority, self-modifying production agent, clone/wrapper of Jev/OpenJev, guarantee that a candidate set is complete, calibrated production model, or autonomous production-promotion mechanism.

The v0.1 baseline provider exists only to exercise the architecture.

## 8. Core use cases

### 8.1 EDI / IDoc exception triage

Given partner context, message state, error category, retry history, and declared actions such as retry, quarantine, corrected-source-data request, route-to-handler, or human review, RDE-Reflex scores only the bounded gray-area decision. Schema, protocol, security, and contractual rules remain deterministic.

### 8.2 Agent/tool/model routing

Choose among a declared set of agents, tools, or models. If confidence is inadequate, return to a reasoning router.

### 8.3 Known operational remediation

For established incident signatures, score pre-approved remediation options without gaining execution authority.

### 8.4 Approval classification

Classify a proposed task into a known approval tier. The authorization system still enforces the actual gate.

### 8.5 Reflex evaluation

A separate evaluator/provider can later review another reflex's outcomes for drift, anomaly, or poor calibration. Evaluation should intentionally support architectural diversity to reduce correlated blind spots.

## 9. Fundamental invariants

### INV-1: No execution authority
RDE-Reflex returns decisions; it never performs the action.

### INV-2: Explicit bounded action space
Every decision request declares its candidate set.

### INV-3: Escape path always exists
The engine can return `ESCALATE` rather than force a selection.

### INV-4: Provider failure is not a decision
Malformed scores, invalid probability mass, mismatched candidates, provider exceptions, and invalid values become bounded errors.

### INV-5: Uncertainty is observable
Confidence and normalized entropy are returned with every successful provider evaluation.

### INV-6: Calibration is not implied
Providers declare calibration status. Unknown or uncalibrated providers cannot be silently treated as calibrated.

### INV-7: Candidate expansion is external
A provider cannot silently add an action. Novel actions require a reasoning/design path outside the bounded inference call.

### INV-8: Promotion is separate from inference
Future Reflex Compilation may propose candidate reflexes, but production promotion is a versioned policy action with evidence and rollback.

### INV-9: Feedback is provenance-bearing
Outcome records include request and decision identity and are append-only at ingestion.

### INV-10: Challengeability
Every reflex remains replaceable, disableable, measurable, and bypassable through policy/escalation.

## 10. Functional requirements

### FR-1 Decision primitives

**Boolean** — exactly two candidates.

**Choice** — two or more named candidates.

**Score** — ordered numeric candidate values; provider returns probabilities and the engine may calculate expected score.

### FR-2 Request contract

Each decision batch includes request ID, shared state/context, one or more decision specifications, policy, and metadata.

Each decision includes stable ID, decision kind, instruction, candidates, and optional numeric values for score decisions.

### FR-3 Response contract

Each result includes decision ID, kind, status, selected candidate or null, probability map when scoring succeeds, confidence, normalized entropy, expected score where applicable, calibration status, reason codes, provider/model identity, and metadata.

The batch includes request ID, engine/version, provider, total engine latency, and timestamp.

### FR-4 Policy

v0.1 supports minimum confidence, maximum normalized entropy, require-calibrated-provider, and maximum candidates.

Any failed requirement causes `ESCALATE` or bounded `ERROR`, never a forced choice.

### FR-5 Provider interface

Providers receive state plus an exact decision specification and return probabilities keyed exactly by candidate ID, calibration status, provider/model ID, and metadata.

### FR-6 Probability validation

The engine rejects missing/extra candidate IDs, negative values, NaN/infinite values, and zero total probability, then normalizes valid positive mass to 1.0.

### FR-7 Development provider

A dependency-light local provider is included so contracts can be exercised offline without model downloads. It identifies itself as uncalibrated and is not the target native model.

### FR-8 Feedback API

Feedback accepts request ID, decision ID, selected candidate, correct candidate when known, correctness, bounded reward, observed outcome, notes, metadata, and timestamp. Initial storage may be JSONL but is replaceable.

### FR-9 Authentication

When configured with an API key, protected endpoints require constant-time key comparison. Health may remain unauthenticated.

### FR-10 Capabilities and OpenAPI

The service exposes machine-readable capabilities and generated OpenAPI documentation.

## 11. Non-functional requirements

- Python 3.11+ local-first bootstrap with no GPU requirement.
- Provider-neutral core contracts.
- Stateless inference apart from provider/model internals.
- Response metadata sufficient to reconstruct engine/provider/version.
- Deterministic unit-testable policy and normalization.
- Engine-side latency instrumentation.
- Fail-closed selection behavior.
- Independent deployment from Solomon Prime.
- No Solomon-specific imports in the engine package.

## 12. Native RDE provider strategy

The project will not lock itself to Jev, OpenJev, or a single model family.

Provider architecture must support deterministic/rules providers, classical ML rankers/classifiers, compact transformer encoders, specialized decision-head models, locally distilled models, external Jev/OpenJev-compatible benchmark adapters, ensemble/evaluator providers, and future hardware-specific runtimes.

Native-model research should evaluate shared-context plus candidate encoders, cross-encoders, energy-based scoring, classification/ranking heads, pairwise/listwise objectives, calibrated logits, abstention/open-set heads, uncertainty estimators, distillation from reasoning traces, quantization, and CPU/GPU/NPU runtimes.

No single model architecture is permanently selected in v0.1.

## 13. Reflex Compilation

Reflex Compilation is the future process that turns repeated successful reasoning into proposed fast reflexes.

Lifecycle:

1. Capture a recurring decision family.
2. Collect state, candidates, reasoning outcome, and observed result.
3. Normalize/label examples.
4. Train or derive a candidate provider/reflex version.
5. Evaluate on holdout and adversarial sets.
6. Calibrate probabilities.
7. Run shadow mode against live traffic without authority.
8. Compare against reasoning/human outcomes.
9. Produce a promotion proposal.
10. Approve according to deployment policy.
11. Canary.
12. Monitor calibration, regret, failure distribution, novelty, and drift.
13. Demote/disable or propose revision when thresholds fail.

A reflex is a **versioned learned operational artifact**, not merely a prompt.

## 14. Detecting an incomplete action space

A bounded decision system must recognize evidence that the action space itself may be wrong.

Future `ACTION_SPACE_INCOMPLETE` signals include persistently high entropy, repeated low confidence, elevated escalation rate, disagreement with reasoning/human outcomes, correct labels not represented by candidates, degradation after environment change, high regret, outcome anomalies clustered around a reflex, out-of-distribution metrics, and challenger disagreement.

The inference path does not invent and execute new actions. It escalates to a reasoning path, which may propose a changed action space, simulate/evaluate it, and submit a versioned promotion proposal.

## 15. Meta-evaluation: a reflex evaluating a reflex

A future **Reflex Challenger** may consume decision distributions, calibration metrics, outcome history, environment metadata, drift statistics, and error clusters.

Potential challengers include deterministic invariants, statistical drift monitors, a separate RDE provider, a reasoning model, a human approval path, and domain validators.

No single evaluator becomes absolute authority.

## 16. API v0.1

### POST /v1/decide

Representative request:

```json
{
  "request_id": "req-123",
  "state": "Partner returned an intermittent timeout. Prior retry succeeded.",
  "policy": {
    "min_confidence": 0.67,
    "max_normalized_entropy": 0.85,
    "require_calibrated": true,
    "max_candidates": 32
  },
  "decisions": [{
    "id": "recovery",
    "kind": "choice",
    "instruction": "Choose among the approved recovery paths.",
    "candidates": [
      {"id": "retry", "description": "Retry a transient failure"},
      {"id": "quarantine", "description": "Quarantine structurally invalid payload"},
      {"id": "human_review", "description": "Escalate for review"}
    ]
  }],
  "metadata": {"caller": "solomon-prime"}
}
```

An accepted result has `status: "decided"` and a selected candidate. An uncertain result has `status: "escalate"`, `selected: null`, and reason codes such as `LOW_CONFIDENCE`, `HIGH_ENTROPY`, or `CALIBRATION_REQUIRED`.

### POST /v1/feedback

Feedback is observational. It does not mutate the active reflex during the request.

## 17. Data and training requirements

Future examples should preserve decision family/version, context, candidate set, selected action, probabilities where available, reasoning/human reference outcome, downstream outcome, reward/correctness, provenance, timestamp/environment, applied policy, provider/model version, and security classification.

Datasets should separate training, calibration, validation, adversarial/edge, temporal holdout, and out-of-distribution evaluation sets.

## 18. Evaluation metrics

RDE-Reflex cannot be judged only by raw accuracy.

Required benchmark dimensions include top-1 accuracy, log loss/NLL, Brier score, expected calibration error, selective accuracy vs coverage, abstention quality, novelty/OOD metrics where applicable, regret/cost-weighted error, p50/p95/p99 latency, throughput, memory footprint, energy when measurable, decision cost, escalation rate, false-confidence rate, action-space-incomplete detection rate, and drift-detection delay.

For operational systems, reducing **false confident decisions** is usually more important than maximizing coverage.

## 19. Observability

Production runtime should expose request/decision counts; decided/escalated/error rates; confidence and entropy distributions; calibration status; provider latency/error rates; feedback correctness/reward; model/reflex versions; and drift/challenger alerts.

Tracing should support Solomon Prime/TED/Langfuse/OpenTelemetry integration without hard coupling.

## 20. Security model

v0.1: optional API key, constant-time compare, no arbitrary code execution, no action execution, strict candidate IDs, bounded validation, append-only feedback sink, environment-sourced secrets.

Future: mTLS/service identity, JWT/OIDC, per-client scopes, signed reflex artifacts, supply-chain provenance, encrypted feedback stores, tenant isolation, audit signing, and AegisQR provenance/package integration.

## 21. Solomon Prime integration

Solomon Prime is a client, not the owner of RDE-Reflex internals.

Target v1.2 flow:

```text
User/environment
      ↓
Solomon reasoning/orchestrator
      ↓
registered bounded reflex?
   no ───────────────► normal reasoning
   yes
      ↓
RDE-Reflex /v1/decide
      ├── DECIDED → Solomon applies authorization/approval rules
      └── ESCALATE/ERROR → Solomon returns to reasoning/human path
                                  ↓
                         execution outside RDE
                                  ↓
                           observed outcome
                                  ↓
                         RDE /v1/feedback
```

Solomon must never treat an RDE result as authorization.

## 22. IDoc/EDI boundary

Recommended layering:

```text
schema/protocol validation        → deterministic
security/authorization            → deterministic
partner contractual requirements  → deterministic
known gray-area decision           → RDE-Reflex
novel/uncertain situation          → reasoning/human escalation
action execution                   → workflow/agent platform
```

This preserves deterministic validation where deterministic logic is superior.

## 23. Versioning

Future production decision records preserve three versions: engine/API version, provider/model version, and reflex definition/version.

Breaking API changes require a new API version. Promoted reflex definitions are immutable; updates create a new version.

## 24. v0.1 acceptance criteria

v0.1 is accepted when package installation works on Python 3.11+, tests pass, health/capabilities respond, primitive validation works, providers are replaceable, low confidence escalates, calibration-required rejects the uncalibrated dev provider, invalid provider distributions become bounded errors, score decisions can produce expected score, feedback appends, API-key behavior is tested, docs cover architecture and Solomon integration, CI runs tests/lint, the container builds, and no Solomon-specific import exists in the package.

## 25. Roadmap

- **v0.1 Foundation:** contracts, provider abstraction, policy/escape path, feedback, API, tests, docs.
- **v0.2 Native Provider:** first trainable RDE-native scorer, dataset schema, benchmark harness, calibration.
- **v0.3 Registry + Shadow Mode:** versioned reflexes, shadow evaluation, decision/outcome linkage, promotion evidence.
- **v0.4 Challenger + Drift:** independent evaluation, novelty/OOD signals, action-space-incomplete suspicion.
- **v0.5 Reflex Compilation:** mine reasoning patterns, propose reflexes, simulation/evaluation pipeline.
- **v0.6 Production Platform:** telemetry, persistence, auth scopes, HA, artifact signing.
- **v0.7 Provider Ecosystem:** native/local/external benchmark adapters and ensemble challengers.
- **v1.0 Decision Fabric:** stable contracts, calibrated providers, registry, reversible promotion, mature security/observability.

## 26. Open design questions

Still intentionally unresolved until measured: optimal native model family, energy-based vs explicit novelty heads, candidate-count limits, per-reflex vs shared multi-task providers, calibration technique by model class, reward normalization, retention policy, risk-specific promotion thresholds, registry implementation, and a standardized agent-to-agent decision envelope.

## 27. Definition of success

RDE-Reflex succeeds when an AI system can safely say:

> "I know this situation well enough to use a fast reflex."

and just as importantly:

> "This no longer looks like something my reflex should decide."

That second capability is a defining feature, not a fallback failure.
