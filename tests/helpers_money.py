"""Shared test doubles and builders for the PR #48 money-path tests (one home, so test modules do not import each other's
private helpers): fake LLMs, the limits and Postgres-store builders, the route table, a fixed clock."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.config import Route
from hadavin_sdk.limits import Limits
from hadavin_sdk.llm.metered import MeteredLLM
from hadavin_sdk.llm.protocol import ProviderExhausted
from hadavin_sdk.models import Reply

D = Decimal
MID = datetime(2026, 3, 15, 12, 0, tzinfo=UTC)
DAY = MID.date()


def _limits(store, tenant="", daily="1", monthly="100", max_run=None):
    agent = SimpleNamespace(
        budget_usd=SimpleNamespace(daily=D(daily), monthly=D(monthly)),
        max_run_usd=None if max_run is None else D(max_run),
    )
    return Limits(store, None, SimpleNamespace(agents={"a": agent}), tenant=tenant)  # type: ignore[arg-type]


def _pg_store(dsn, **kw):
    pytest.importorskip("psycopg")
    from hadavin_sdk.actions.secrets import FakeSecretProvider
    from hadavin_sdk.backends import make
    from hadavin_sdk.backends.table import PostgresSettings

    settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
    store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
    for k, v in kw.items():
        setattr(store, k, v)
    return store


class Stub:
    label = "stub"

    def __init__(self, *outcomes):
        self.outcomes, self.n = list(outcomes), 0

    def chat(self, messages, **kw):
        self.n += 1
        o = self.outcomes[min(self.n, len(self.outcomes)) - 1]
        if isinstance(o, BaseException):
            raise o
        return o


ROUTES = {
    "r": Route(model_id="m-1", input_usd_per_mtok=D(3), output_usd_per_mtok=D(15), max_tokens=100)
}


class FreshRaises:
    """A test double that raises a NEW exception on every call (a shared instance would accumulate the carry)."""

    label = "fresh"

    def __init__(self, cls, msg="x", **attrs):
        self.cls, self.msg, self.attrs, self.made = cls, msg, attrs, []

    def chat(self, *a, **k):
        e = self.cls(self.msg)
        for n, v in self.attrs.items():
            setattr(e, n, v)
        self.made.append(e)
        raise e


def _fallback_reply(cost="0.0007"):

    return Reply(text="ok", model_id="fb", cost_usd=D(cost))


def _unknown_total(store):
    lim = _limits(store, daily="1")
    with pytest.raises(ProviderExhausted):
        MeteredLLM(Stub(ProviderExhausted("t")), lim, "a", ROUTES).chat([], system="", route="r")
    return store.spend_totals("a", DAY)
