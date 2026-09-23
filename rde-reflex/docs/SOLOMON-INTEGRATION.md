# Solomon Prime ↔ RDE-Reflex Integration Contract

## Version target

RDE-Reflex integration is targeted for **Solomon Prime v1.2**, after the v1.1 Spatial release is stabilized.

RDE-Reflex remains a standalone project/service.

## Responsibility split

### Solomon Prime owns

- reasoning
- candidate generation
- tool/agent orchestration
- identity
- authorization
- approval gates
- action execution
- outcome observation
- deciding when a reflex is eligible for use
- deciding when to bypass/disable RDE-Reflex

### RDE-Reflex owns

- validation of bounded decision contracts
- scoring declared candidates
- probability/uncertainty output
- calibration metadata
- abstention/escalation policy
- reflex/provider/version metadata
- decision feedback ingestion
- future reflex evaluation/compilation lifecycle

## Invocation pattern

```text
Solomon receives task/event
        ↓
Solomon determines decision family
        ↓
Solomon builds exact candidate set
        ↓
POST RDE /v1/decide
        ↓
 ┌──────┴─────────────────┐
 │                         │
DECIDED                 ESCALATE/ERROR
 │                         │
Solomon independently     Solomon invokes normal
checks permission,        reasoning / human path
approval, policy
 │
execute outside RDE
 │
observe result
 │
POST RDE /v1/feedback
```

## Critical rule

A `DECIDED` result means:

> "The bounded decision engine supports candidate X under the supplied policy."

It does **not** mean:

> "Candidate X is authorized to execute."

Solomon's existing approval/security model remains authoritative.

## ChatGPT/Gemini control bridge relationship

The planned Solomon control bridge and RDE-Reflex solve different problems:

- **Control bridge:** lets authorized external assistants submit structured tasks to Solomon.
- **RDE-Reflex:** gives Solomon fast bounded decision capability.

Expected future flow:

```text
ChatGPT / Gemini
      ↓
Solomon Control Bridge
      ↓
Solomon reasoning/orchestration
      ↓
RDE-Reflex when a registered bounded decision applies
      ↓
Solomon authorization/approval
      ↓
execution
```

Neither external assistant nor RDE-Reflex bypasses Solomon's execution controls.
