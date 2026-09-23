import pytest

from rde_reflex.engine import ReflexDecisionEngine
from rde_reflex.models import (
    CalibrationStatus,
    Candidate,
    DecisionBatchRequest,
    DecisionKind,
    DecisionPolicy,
    DecisionSpec,
    DecisionStatus,
    ProviderDecision,
)
from rde_reflex.providers.base import DecisionProvider


class FixedProvider(DecisionProvider):
    name = "fixed"

    def __init__(self, probabilities: dict[str, float], calibrated: bool = True):
        self.probabilities = probabilities
        self.calibrated = calibrated

    async def score(self, *, state: str, decision: DecisionSpec) -> ProviderDecision:
        return ProviderDecision(
            probabilities=self.probabilities,
            calibration_status=(
                CalibrationStatus.CALIBRATED
                if self.calibrated
                else CalibrationStatus.UNCALIBRATED
            ),
            model=self.name,
        )


def request(policy: DecisionPolicy | None = None) -> DecisionBatchRequest:
    return DecisionBatchRequest(
        state="known retryable timeout",
        policy=policy or DecisionPolicy(),
        decisions=[
            DecisionSpec(
                id="recovery",
                kind=DecisionKind.CHOICE,
                instruction="choose recovery",
                candidates=[
                    Candidate(id="retry", description="retry"),
                    Candidate(id="review", description="review"),
                ],
            )
        ],
    )


@pytest.mark.asyncio
async def test_high_confidence_decision_is_selected() -> None:
    engine = ReflexDecisionEngine(FixedProvider({"retry": 0.95, "review": 0.05}))
    response = await engine.decide(request())
    result = response.results[0]

    assert result.status is DecisionStatus.DECIDED
    assert result.selected == "retry"
    assert result.confidence == pytest.approx(0.95)


@pytest.mark.asyncio
async def test_low_confidence_escalates_without_selection() -> None:
    engine = ReflexDecisionEngine(FixedProvider({"retry": 0.51, "review": 0.49}))
    response = await engine.decide(request())
    result = response.results[0]

    assert result.status is DecisionStatus.ESCALATE
    assert result.selected is None
    assert "LOW_CONFIDENCE" in result.reason_codes


@pytest.mark.asyncio
async def test_calibration_can_be_required() -> None:
    engine = ReflexDecisionEngine(
        FixedProvider({"retry": 0.95, "review": 0.05}, calibrated=False)
    )
    response = await engine.decide(
        request(DecisionPolicy(require_calibrated=True))
    )
    result = response.results[0]

    assert result.status is DecisionStatus.ESCALATE
    assert result.selected is None
    assert "CALIBRATION_REQUIRED" in result.reason_codes


@pytest.mark.asyncio
async def test_provider_candidate_mismatch_becomes_bounded_error() -> None:
    engine = ReflexDecisionEngine(FixedProvider({"retry": 1.0, "invented": 0.0}))
    response = await engine.decide(request())
    result = response.results[0]

    assert result.status is DecisionStatus.ERROR
    assert result.selected is None
    assert result.reason_codes == ["PROVIDER_ERROR"]
