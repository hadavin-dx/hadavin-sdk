"""Fake model: replays recorded answers keyed by ``<document sha256>-<attempt>.json``. An unknown key raises."""

from __future__ import annotations

import hashlib
import json
import threading
from collections import Counter
from pathlib import Path
from typing import Any

from hadavin_sdk.config import Route
from hadavin_sdk.llm.pricing import cost_usd
from hadavin_sdk.llm.protocol import build_usage
from hadavin_sdk.models import Reply, round_cost_up


class UnknownRecording(KeyError):
    pass


class FakeLLM:
    # A recorded run replays one attempt and one request: the k1b charge helper reads both.
    REQUESTS_PER_CHAT = 1
    max_attempts = 1

    def __init__(self, recorded_dir: Path, routes: dict[str, Route]) -> None:
        self.recorded_dir = Path(recorded_dir)
        self.routes = routes
        self.calls: list[dict[str, Any]] = []
        self._attempts: Counter[str] = Counter()
        self._lock = threading.Lock()

    def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        system: str,
        route: str,
        tools: list[dict[str, Any]] | None = None,
        documents: list[bytes] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> Reply:
        doc = documents[0] if documents else json.dumps(messages, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(doc).hexdigest()
        with self._lock:
            self._attempts[digest] += 1
            attempt = self._attempts[digest]
            self.calls.append({"route": route, "tools": tools, "messages": messages})
        path = self.recorded_dir / f"{digest}-{attempt}.json"
        if not path.is_file():
            raise UnknownRecording(path.name)
        data = json.loads(path.read_text(encoding="utf-8"))
        r = self.routes[route]
        data = dict(data)
        cache_write, cache_read = (
            data.pop("cache_write_tokens", None),
            data.pop("cache_read_tokens", None),
        )
        usage = build_usage(
            data.get("input_tokens"),
            data.get("output_tokens"),
            cache_write_tokens=cache_write,
            cache_read_tokens=cache_read,
        )
        cost = round_cost_up(cost_usd(usage, r))
        return Reply(**data, cost_usd=cost, model_id=r.model_id)
