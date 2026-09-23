from __future__ import annotations

import math
import re
from collections.abc import Iterable

from rde_reflex.models import CalibrationStatus, DecisionSpec, ProviderDecision
from rde_reflex.providers.base import DecisionProvider

_TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def _tokens(text: str) -> set[str]:
    return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1}


def _softmax(values: Iterable[float]) -> list[float]:
    numbers = list(values)
    if not numbers:
        return []
    max_value = max(numbers)
    exps = [math.exp(value - max_value) for value in numbers]
    total = sum(exps)
    return [value / total for value in exps]


class HeuristicProvider(DecisionProvider):
    """Dependency-light provider for integration testing and local demos.

    This is intentionally marked UNCALIBRATED. It is a vertical-slice provider,
    not the intended production model.
    """

    name = "heuristic-v0"

    async def score(self, *, state: str, decision: DecisionSpec) -> ProviderDecision:
        state_tokens = _tokens(state)
        instruction_tokens = _tokens(decision.instruction)
        context_tokens = state_tokens | instruction_tokens

        logits: list[float] = []
        for candidate in decision.candidates:
            candidate_tokens = _tokens(candidate.id + " " + candidate.description)
            overlap = len(state_tokens & candidate_tokens)
            union = max(1, len(state_tokens | candidate_tokens))
            jaccard = overlap / union

            instruction_overlap = len(instruction_tokens & candidate_tokens)
            instruction_union = max(1, len(instruction_tokens | candidate_tokens))
            instruction_jaccard = instruction_overlap / instruction_union

            coverage = len(context_tokens & candidate_tokens) / max(1, len(candidate_tokens))
            logits.append((5.0 * jaccard) + (1.5 * coverage) + (0.5 * instruction_jaccard))

        probabilities = _softmax(logits)
        return ProviderDecision(
            probabilities={
                candidate.id: probability
                for candidate, probability in zip(decision.candidates, probabilities, strict=True)
            },
            calibration_status=CalibrationStatus.UNCALIBRATED,
            model=self.name,
            metadata={"provider_class": "development-baseline"},
        )
