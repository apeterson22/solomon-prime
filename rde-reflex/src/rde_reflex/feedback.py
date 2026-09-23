from __future__ import annotations

import json
import threading
from pathlib import Path

from rde_reflex.models import FeedbackRecord


class JsonlFeedbackStore:
    """Append-only local feedback sink for the v0.1 learning loop.

    A production backend can replace this without changing the public API.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._lock = threading.Lock()

    def append(self, record: FeedbackRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = record.model_dump(mode="json")
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, sort_keys=True))
                handle.write("\n")
