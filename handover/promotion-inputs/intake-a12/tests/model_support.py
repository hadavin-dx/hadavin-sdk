"""Shared helpers for the model-stage tests (budget, data gate, backends). Not a test module."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import replace

from conftest import CAP_SENTENCE, CONSENT_SENTENCE, settings_for_tests
from intake import budget, model
from intake.model_fake import FakeBackend

GOOD_FIELDS = {
    "invoice_no": "INV-1",
    "supplier_name": "Acme Ltd",
    "currency": "USD",
    "lines": [{"description": "Widget", "qty": 1, "unit_cost_minor": 100, "amount_minor": 100}],
    "adjustments": [],
    "total_minor": 100,
}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def live_settings(tmp_path, limit: int | None = 100, sentence_total: int = 100):
    """A live-backend Settings (any backend object may sit behind it) with a ledger, a recorded provider limit and the owner sentence."""
    s = settings_for_tests(tmp_path, backend="anthropic", with_ledger=True)
    set_sentence(s, sentence_total)
    if limit is not None:
        budget.confirm_limit(s, f"LIMIT SET {limit}")
    return s


def fake_settings(tmp_path):
    return settings_for_tests(tmp_path, backend="fake", with_ledger=True)


def set_sentence(s, total: int) -> None:
    s.owner_sentence_path.write_text(CONSENT_SENTENCE + " " + CAP_SENTENCE.replace("US$100", f"US${total}") + "\n", encoding="utf-8")


def set_prices(s, rin, rout, fin=None, fout=None, as_of=None) -> None:
    d = json.loads(s.prices_path.read_text(encoding="utf-8"))
    p = d["prices_micro_usd_per_million_tokens"]
    p["read"] = {"in": rin, "out": rout}
    p["fallback"] = {"in": fin or rin, "out": fout or rout}
    if as_of:
        d["prices_as_of"] = as_of
    s.prices_path.write_text(json.dumps(d), encoding="utf-8")


def with_model(s, **kw):
    return replace(s, model=replace(s.model, **kw))


def register(s, *texts: str) -> None:
    """Put the hashes of the texts on the made-up list (what ``demo_ctl register`` does)."""
    with (s.intake_home / "synthetic_hashes.txt").open("a", encoding="utf-8") as f:
        for t in texts:
            f.write(sha(t) + "\n")


def req(text: str, tier: str = "read") -> model.ExtractRequest:
    return model.ExtractRequest(sha(text), tier, model_text=text)


class _PlainCheck:
    """A body check for tests that are not about masking: it ties the request to the document and passes the body (see ``plain_check``)."""

    def __init__(self, document_text: str, source_sha256: str) -> None:
        self.document_text, self.source_sha256, self.key, self.last_code = document_text, source_sha256, b"", None

    def refuse(self, code: str) -> None:
        self.last_code = code

    def __call__(self, body: bytes) -> str | None:
        return None

    def __repr__(self) -> str:
        return "PlainCheck()"


def plain_check(document_text: str, source_sha256: str | None = None) -> _PlainCheck:
    """Test-only ``body_check`` that always passes the body. The real check is ``mask.BodyCheck``; an AST test keeps this name under ``tests/``."""
    return _PlainCheck(document_text, source_sha256 or sha(document_text))


def reply(error=None, fields=GOOD_FIELDS, i=100, o=50):
    return {"fields": fields if error is None else None, "model_id": "fake-x", "in_tok": i, "out_tok": o, "cost_micro": 0, "error": error}


def fake_with(s, text: str, **by_tier):
    """A FakeBackend whose replies for ``text`` are given per tier (read=..., fallback=...)."""
    return FakeBackend(s, {f"{sha(text)}:{t}": v for t, v in by_tier.items()})


def guarded(s, backend):
    return model.GuardedModel(backend, budget.Budget(s), s)


def rows(s, table: str) -> int:
    c = sqlite3.connect(budget.ledger_path(s))
    try:
        return c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # noqa: S608 (test helper, fixed table names)
    finally:
        c.close()


def calls(s) -> list[tuple]:
    c = sqlite3.connect(budget.ledger_path(s))
    try:
        return c.execute("SELECT tier,in_tok,out_tok,cost_micro,status FROM calls ORDER BY id").fetchall()
    finally:
        c.close()


def make_queue(s, costs: list[int] | None, table: bool = True) -> None:
    c = sqlite3.connect(s.intake_home / "queue.sqlite3")
    try:
        if table:
            c.execute("CREATE TABLE items(uid INTEGER PRIMARY KEY, cost_micro INTEGER)")
            c.executemany("INSERT INTO items(cost_micro) VALUES(?)", [(x,) for x in (costs or [])])
        c.commit()
    finally:
        c.close()


class UnexpectedCall(BaseException):
    """Raised by ``Scripted`` on a tier it was not scripted for. A ``BaseException`` on purpose: no ``except Exception`` in the code under test can swallow it."""


def ok(fields, cost=10, model_id="m"):
    return model.ModelResult(fields=fields, model_id=model_id, in_tok=5, out_tok=5, cost_micro=cost, error=None)


def err(code, cost=0, diag=None):
    return model.ModelResult(fields=None, model_id=None, in_tok=0, out_tok=0, cost_micro=cost, error=code, diag=diag)


class Scripted:
    """A model stand-in with the ``GuardedModel.call`` shape: ``script[tier]`` is the reply; ``None`` means the tier must NOT be called (``UnexpectedCall``)."""

    def __init__(self, read, fallback=None):
        self.script = {"read": read, "fallback": fallback}
        self.calls: list[model.ExtractRequest] = []

    def call(self, req, **kw):
        self.calls.append(req)
        r = self.script[req.tier]
        if r is None:
            raise UnexpectedCall("unexpected call of the " + req.tier + " tier")
        return r
