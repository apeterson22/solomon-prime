# RDE-Reflex Roadmap

## v0.1 — Foundation (current)

- [x] Bounded decision contracts
- [x] Boolean / choice / score primitives
- [x] Provider abstraction
- [x] Development baseline provider
- [x] Probability validation/normalization
- [x] Confidence + normalized entropy
- [x] Explicit calibration status
- [x] Escape/escalation policy
- [x] Provider failure containment
- [x] Feedback API/store
- [x] Optional API key
- [x] HTTP service
- [x] Unit/API tests
- [x] Container/developer workflow
- [x] Solomon integration contract
- [ ] Run CI and resolve environment-specific failures
- [ ] Decide initial open-source license
- [ ] Complete formal name/package/domain/trademark clearance
- [ ] Extract into dedicated `RDE-Reflex` repository once repository creation is available/approved

## v0.2 — Native provider

- dataset schema and loader
- benchmark harness
- first trainable native candidate scorer
- calibration pipeline
- latency/cost baseline
- CPU/GPU runtime benchmark
- artifact/version metadata
- Jev/OpenJev benchmark adapters where licensing/interfaces permit

## v0.3 — Registry and shadow mode

- reflex definition schema
- immutable version registry
- shadow-only evaluation
- request → decision → outcome linkage
- evidence reports
- canary hooks
- rollback

## v0.4 — Challenger / novelty / drift

- calibration monitoring
- OOD/novelty experiment suite
- action-space-incomplete signals
- independent challenger provider
- drift monitoring
- reflex degradation alerts

## v0.5 — Reflex Compilation

- mine repeated reasoning decisions
- cluster decision families
- candidate-set proposal
- train candidate reflex
- automated offline evaluation
- red/blue/adversarial test suite
- promotion proposal package
- human/policy approval boundary

## v0.6 — Production platform

- persistence adapters
- metrics/OpenTelemetry
- mTLS/OIDC/scoped clients
- HA deployment
- signed model/reflex artifacts
- model registry integration
- AegisQR provenance/package integration

## v1.0 — Decision fabric

- stable API/SDK
- calibrated native models
- production registry
- challenger/drift subsystem
- Reflex Compilation
- reversible promotion lifecycle
- multi-provider routing
- documented enterprise deployment patterns
