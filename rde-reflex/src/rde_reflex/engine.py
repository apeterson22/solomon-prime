from __future__ import annotations

import time

from rde_reflex import __version__
from rde_reflex.models import (
    DecisionBatchRequest,
    DecisionBatchResponse,
    DecisionKind,
    DecisionResult,
    DecisionStatus,
)
from rde_reflex.policy import evaluate_policy, normalize_probabilities
from rde_reflex.providers.base import DecisionProvider


class ReflexDecisionEngine:
    """Provider-neutral bounded decision runtime with mandatory escape paths."""

    def __init__(self, provider: DecisionProvider):
        self.provider = provider

    async def decide(self, request: DecisionBatchRequest) -> DecisionBatchResponse:
        started = time.perf_counter()
        results: list[DecisionResult] = []

        for decision in request.decisions:
            if len(decision.candidates) > request.policy.max_candidates:
                results.append(
                    DecisionResult(
                        id=decision.id,
                        kind=decision.kind,
                        status=DecisionStatus.ERROR,
                        reason_codes=["TOO_MANY_CANDIDATES"],
                        provider=self.provider.name,
                    )
                )
                continue

            try:
                provider_result = await self.provider.score(
                    state=request.state,
                    decision=decision,
                )
                expected_ids = {candidate.id for candidate in decision.candidates}
                probabilities = normalize_probabilities(
                    provider_result.probabilities,
                    expected_ids,
                )
                accepted, confidence, entropy, reasons = evaluate_policy(
                    probabilities=probabilities,
                    calibration_status=provider_result.calibration_status,
                    policy=request.policy,
                )

                selected = max(probabilities, key=probabilities.get) if accepted else None
                expected_score = None
                if accepted and decision.kind is DecisionKind.SCORE:
                    value_by_id = {
                        candidate.id: float(candidate.value)
                        for candidate in decision.candidates
                        if candidate.value is not None
                    }
                    expected_score = sum(
                        value_by_id[candidate_id] * probability
                        for candidate_id, probability in probabilities.items()
                    )

                results.append(
                    DecisionResult(
                        id=decision.id,
                        kind=decision.kind,
                        status=DecisionStatus.DECIDED if accepted else DecisionStatus.ESCALATE,
                        selected=selected,
                        probabilities=probabilities,
                        confidence=confidence,
                        normalized_entropy=entropy,
                        expected_score=expected_score,
                        calibration_status=provider_result.calibration_status,
                        reason_codes=reasons,
                        provider=provider_result.model,
                        metadata=provider_result.metadata,
                    )
                )
            except Exception as exc:  # provider boundary: convert failure into an escape path
                results.append(
                    DecisionResult(
                        id=decision.id,
                        kind=decision.kind,
                        status=DecisionStatus.ERROR,
                        reason_codes=["PROVIDER_ERROR"],
                        provider=self.provider.name,
                        metadata={"error_type": type(exc).__name__},
                    )
                )

        latency_ms = (time.perf_counter() - started) * 1000.0
        return DecisionBatchResponse(
            request_id=request.request_id,
            engine_version=__version__,
            provider=self.provider.name,
            results=results,
            latency_ms=round(latency_ms, 3),
        )
