from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class DecisionKind(str, Enum):
    BOOLEAN = "boolean"
    CHOICE = "choice"
    SCORE = "score"


class CalibrationStatus(str, Enum):
    CALIBRATED = "calibrated"
    UNCALIBRATED = "uncalibrated"
    UNKNOWN = "unknown"


class DecisionStatus(str, Enum):
    DECIDED = "decided"
    ESCALATE = "escalate"
    ERROR = "error"


class Candidate(BaseModel):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    description: str = Field(min_length=1, max_length=4000)
    value: float | None = None


class DecisionPolicy(BaseModel):
    min_confidence: float = Field(default=0.67, ge=0.0, le=1.0)
    max_normalized_entropy: float = Field(default=0.85, ge=0.0, le=1.0)
    require_calibrated: bool = False
    max_candidates: int = Field(default=32, ge=2, le=128)


class DecisionSpec(BaseModel):
    id: str = Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")
    kind: DecisionKind
    instruction: str = Field(min_length=1, max_length=8000)
    candidates: list[Candidate] = Field(min_length=2, max_length=128)

    @model_validator(mode="after")
    def validate_semantics(self) -> "DecisionSpec":
        ids = [candidate.id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate ids must be unique")

        if self.kind is DecisionKind.BOOLEAN:
            if len(self.candidates) != 2:
                raise ValueError("boolean decisions require exactly two candidates")

        if self.kind is DecisionKind.SCORE:
            values = [candidate.value for candidate in self.candidates]
            if any(value is None for value in values):
                raise ValueError("score decisions require a numeric value on every candidate")
            numeric = [float(value) for value in values if value is not None]
            if len(numeric) != len(set(numeric)):
                raise ValueError("score candidate values must be unique")
        return self


class DecisionBatchRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()), min_length=1, max_length=128)
    state: str = Field(min_length=1, max_length=200_000)
    decisions: list[DecisionSpec] = Field(min_length=1, max_length=64)
    policy: DecisionPolicy = Field(default_factory=DecisionPolicy)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProviderDecision(BaseModel):
    probabilities: dict[str, float]
    calibration_status: CalibrationStatus = CalibrationStatus.UNKNOWN
    model: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionResult(BaseModel):
    id: str
    kind: DecisionKind
    status: DecisionStatus
    selected: str | None = None
    probabilities: dict[str, float] = Field(default_factory=dict)
    confidence: float | None = None
    normalized_entropy: float | None = None
    expected_score: float | None = None
    calibration_status: CalibrationStatus = CalibrationStatus.UNKNOWN
    reason_codes: list[str] = Field(default_factory=list)
    provider: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class DecisionBatchResponse(BaseModel):
    request_id: str
    engine: str = "rde-reflex"
    engine_version: str
    provider: str
    results: list[DecisionResult]
    latency_ms: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FeedbackRecord(BaseModel):
    request_id: str = Field(min_length=1, max_length=128)
    decision_id: str = Field(min_length=1, max_length=128)
    selected_candidate_id: str | None = None
    correct_candidate_id: str | None = None
    correct: bool | None = None
    reward: float | None = Field(default=None, ge=-1.0, le=1.0)
    observed_outcome: str | None = Field(default=None, max_length=8000)
    notes: str | None = Field(default=None, max_length=8000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
