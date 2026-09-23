from pathlib import Path

from fastapi.testclient import TestClient

import rde_reflex.api as api_module
from rde_reflex.feedback import JsonlFeedbackStore

client = TestClient(api_module.app)


def test_health() -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["engine"] == "rde-reflex"


def test_decide_returns_explicit_status() -> None:
    response = client.post(
        "/v1/decide",
        json={
            "state": "transient retry timeout retry",
            "policy": {
                "min_confidence": 0.0,
                "max_normalized_entropy": 1.0,
                "require_calibrated": False
            },
            "decisions": [
                {
                    "id": "recovery",
                    "kind": "choice",
                    "instruction": "choose",
                    "candidates": [
                        {"id": "retry", "description": "retry timeout"},
                        {"id": "review", "description": "human review"}
                    ]
                }
            ]
        },
    )
    assert response.status_code == 200
    result = response.json()["results"][0]
    assert result["status"] == "decided"
    assert result["selected"] in {"retry", "review"}
    assert set(result["probabilities"]) == {"retry", "review"}


def test_api_key_can_protect_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("RDE_REFLEX_API_KEY", "secret-value")

    denied = client.get("/v1/capabilities")
    assert denied.status_code == 401

    allowed = client.get(
        "/v1/capabilities",
        headers={"X-RDE-Reflex-Key": "secret-value"},
    )
    assert allowed.status_code == 200


def test_feedback_is_appended(tmp_path: Path, monkeypatch) -> None:
    store = JsonlFeedbackStore(tmp_path / "feedback.jsonl")
    monkeypatch.setattr(api_module, "_feedback", store)
    monkeypatch.delenv("RDE_REFLEX_API_KEY", raising=False)

    response = client.post(
        "/v1/feedback",
        json={
            "request_id": "req-1",
            "decision_id": "d-1",
            "selected_candidate_id": "retry",
            "correct": True,
            "reward": 1.0
        },
    )

    assert response.status_code == 200
    assert (tmp_path / "feedback.jsonl").read_text(encoding="utf-8").strip()
