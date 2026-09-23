from __future__ import annotations

import math

from rde_reflex.models import CalibrationStatus, DecisionPolicy


def normalized_entropy(probabilities: dict[str, float]) -> float:
    values = [value for value in probabilities.values() if value > 0.0]
    if len(probabilities) <= 1:
        return 0.0
    entropy = -sum(value * math.log(value) for value in values)
    return entropy / math.log(len(probabilities))


def normalize_probabilities(
    probabilities: dict[str, float],
    expected_ids: set[str],
) -> dict[str, float]:
    if set(probabilities) != expected_ids:
        raise ValueError("provider returned a candidate set that does not match the request")
    if any((not math.isfinite(value)) or value < 0.0 for value in probabilities.values()):
        raise ValueError("provider returned invalid probability values")

    total = sum(probabilities.values())
    if total <= 0.0:
        raise ValueError("provider returned a zero-mass probability distribution")

    return {key: value / total for key, value in probabilities.items()}


def evaluate_policy(
    *,
    probabilities: dict[str, float],
    calibration_status: CalibrationStatus,
    policy: DecisionPolicy,
) -> tuple[bool, float, float, list[str]]:
    confidence = max(probabilities.values())
    entropy = normalized_entropy(probabilities)
    reasons: list[str] = []

    if confidence < policy.min_confidence:
        reasons.append("LOW_CONFIDENCE")
    if entropy > policy.max_normalized_entropy:
        reasons.append("HIGH_ENTROPY")
    if policy.require_calibrated and calibration_status is not CalibrationStatus.CALIBRATED:
        reasons.append("CALIBRATION_REQUIRED")

    return (not reasons), confidence, entropy, reasons
