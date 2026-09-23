from __future__ import annotations

import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException, status

from rde_reflex import __version__
from rde_reflex.engine import ReflexDecisionEngine
from rde_reflex.feedback import JsonlFeedbackStore
from rde_reflex.models import DecisionBatchRequest, DecisionBatchResponse, FeedbackRecord
from rde_reflex.providers.heuristic import HeuristicProvider

app = FastAPI(
    title="RDE-Reflex",
    summary="Reflex Decision Engine",
    version=__version__,
)

_provider = HeuristicProvider()
_engine = ReflexDecisionEngine(_provider)
_feedback = JsonlFeedbackStore(os.getenv("RDE_REFLEX_FEEDBACK_PATH", "data/feedback.jsonl"))


def require_api_key(x_rde_reflex_key: str | None = Header(default=None)) -> None:
    expected = os.getenv("RDE_REFLEX_API_KEY")
    if not expected:
        return
    if x_rde_reflex_key is None or not hmac.compare_digest(x_rde_reflex_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid RDE-Reflex API key",
        )


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "engine": "rde-reflex",
        "version": __version__,
        "provider": _provider.name,
    }


@app.get("/v1/capabilities", dependencies=[Depends(require_api_key)])
async def capabilities() -> dict[str, object]:
    return {
        "engine": "rde-reflex",
        "version": __version__,
        "provider": _provider.name,
        "decision_kinds": ["boolean", "choice", "score"],
        "escape_path": "escalate",
        "feedback": True,
        "calibration": "provider-declared",
    }


@app.post(
    "/v1/decide",
    response_model=DecisionBatchResponse,
    dependencies=[Depends(require_api_key)],
)
async def decide(request: DecisionBatchRequest) -> DecisionBatchResponse:
    return await _engine.decide(request)


@app.post("/v1/feedback", dependencies=[Depends(require_api_key)])
async def feedback(record: FeedbackRecord) -> dict[str, str]:
    _feedback.append(record)
    return {"status": "accepted"}
