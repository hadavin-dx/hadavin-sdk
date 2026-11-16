"""Fake backend: replies keyed by ``"<doc_sha>:<tier>"`` (tier = read or fallback) from ``model.fake_replies_path``. It sits behind ``GuardedModel`` like
the live backend, so the gate, prices and budget checks apply to it too; it has no key, host or consent check (``preflight`` returns None)."""

from __future__ import annotations

import json

from . import budget, strictjson
from . import settings as cfg
from .codes import MODEL_ERRORS
from .model import ExtractRequest, ModelResult, failed


class FakeBackend:
    live = False

    def __init__(self, s: cfg.Settings, replies: dict | None = None) -> None:
        self._s = s
        self._replies = replies  # tests may pass a dict instead of the file

    def preflight(self) -> str | None:
        return None

    def request_body(self, req: ExtractRequest) -> bytes:
        """A stand-in body that embeds the doc_sha, the tier and the model text (the text the live body would carry), so ``sha256(body)`` differs per
        document, tier and text. ``json.dumps`` keeps the default ``ensure_ascii=True``: a non-ASCII character costs up to 12 bytes here against 4 in the
        live body, so the fake worst-case body is larger (a test with a SMALL fake cap must monkeypatch ``budget.min_limit_micro``)."""
        return json.dumps({"fake": True, "doc_sha": req.doc_sha, "tier": req.tier, "text": req.model_text}, sort_keys=True).encode("utf-8")

    def _load(self) -> dict:
        if self._replies is not None:
            return self._replies
        try:
            data = strictjson.loads(self._s.model.fake_replies_path.read_bytes())
        except (OSError, ValueError):
            return {}
        return data if isinstance(data, dict) else {}

    def send(self, body: bytes, reservation: budget.Reservation) -> ModelResult:
        budget.begin_send(reservation, body)  # first action, always
        value = self._load().get(f"{reservation.doc_sha}:{reservation.tier}")
        if isinstance(value, str):
            return failed(value if value in MODEL_ERRORS and value != "body_unsafe" else "bad_reply")  # body_unsafe is a guard decision
        if not isinstance(value, dict):
            return failed("bad_reply")
        err = value.get("error")
        if err is not None and (err not in MODEL_ERRORS or err == "body_unsafe"):
            return failed("bad_reply")
        fields = value.get("fields")
        i, o = value.get("in_tok", 0), value.get("out_tok", 0)
        return ModelResult(
            fields if isinstance(fields, dict) else None,
            str(value.get("model_id") or f"fake-{reservation.tier}"),
            i if isinstance(i, int) and not isinstance(i, bool) else 0,
            o if isinstance(o, int) and not isinstance(o, bool) else 0,
            0,
            err,
        )
