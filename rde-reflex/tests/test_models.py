import pytest
from pydantic import ValidationError

from rde_reflex.models import Candidate, DecisionKind, DecisionSpec


def test_boolean_requires_two_candidates() -> None:
    with pytest.raises(ValidationError):
        DecisionSpec(
            id="bool",
            kind=DecisionKind.BOOLEAN,
            instruction="yes or no",
            candidates=[
                Candidate(id="yes", description="yes"),
                Candidate(id="no", description="no"),
                Candidate(id="maybe", description="maybe"),
            ],
        )


def test_candidate_ids_are_unique() -> None:
    with pytest.raises(ValidationError):
        DecisionSpec(
            id="duplicate",
            kind=DecisionKind.CHOICE,
            instruction="choose",
            candidates=[
                Candidate(id="same", description="first"),
                Candidate(id="same", description="second"),
            ],
        )


def test_score_requires_unique_numeric_values() -> None:
    with pytest.raises(ValidationError):
        DecisionSpec(
            id="score",
            kind=DecisionKind.SCORE,
            instruction="score",
            candidates=[
                Candidate(id="low", description="low", value=1),
                Candidate(id="high", description="high", value=1),
            ],
        )
