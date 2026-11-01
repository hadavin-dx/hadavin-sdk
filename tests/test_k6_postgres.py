"""K6 on a real postgres: the caught_by view equals the python count, and the label -> demotion -> report path
works through the runtime role's grants only. Skipped without HADAVIN_TEST_PG_DSN (CI runs the postgres service)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

from hadavin_sdk import measure
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.audit.signer import LocalSigner
from hadavin_sdk.backends import make
from hadavin_sdk.backends.table import ChainSettings, PostgresSettings
from hadavin_sdk.models import AuditEvent
from tests.contracts.kinds.store_postgres import pg_schema
from tests.test_k6_measure import ACTION, NOW, WEEK, World, day


@pytest.fixture
def pg_world(tmp_path):
    for dsn in pg_schema(runtime=True):
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        store = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        audit = make(
            "audit",
            ChainSettings(kind="chain"),
            store=store,
            signer=LocalSigner(Ed25519PrivateKey.generate()),
            anchor=None,
        )
        yield World(tmp_path, store=store, audit=audit)
        store._db.close()


def _event(when, caught, run="r"):
    return AuditEvent(
        ts=when,
        run_id=run,
        domain="runtime",
        operation="x",
        principal="p",
        source="s",
        caught_by=caught,
    )


def test_k6_caught_view_matches_python(pg_world):
    w = pg_world
    for when, caught, run in [
        (day(7), "gate", "r1"),
        (day(7), "gate", "r1"),  # the same run caught twice counts once
        (day(7), "gate", "r2"),
        (day(7), "guard", "r3"),
        (day(7), None, "r4"),  # no caught_by: not counted
        (day(14), "gate", "r5"),  # another week
        (NOW, "human_reject", "r6"),
    ]:
        w.audit.write_outcome(_event(when, caught, run))
    events = w.audit.events()
    for week in (WEEK, WEEK - timedelta(days=7), NOW.date()):
        rows = w.store._db.execute(
            "SELECT caught_by, n FROM v_caught_week WHERE week = %s", (week,)
        ).fetchall()
        assert dict(rows) == measure.caught_week(events, week), week
    assert dict(
        w.store._db.execute(
            "SELECT caught_by, n FROM v_caught_week WHERE week = %s", (WEEK,)
        ).fetchall()
    ) == {"gate": 2, "guard": 1}


def test_k6_label_demotion_and_report_on_postgres(pg_world):
    """Labels, the demotion and the report go through the runtime role: SELECT and INSERT only."""
    w = pg_world
    w.labelled("agree", 3, when=day(7))
    bad = w.run(created=day(7))
    assert w.label(bad, "harmful", when=day(7)).demoted
    assert w.store.current_overrides() == {("test-agent", ACTION): "shadow"}
    assert w.measure.level_override("test-agent", ACTION) == "shadow"
    assert w.store.held_run_ids() == {bad}
    assert w.click("owner", f"clear|test-agent|{ACTION}")[0] == 200
    assert w.store.current_overrides() == {}
    body = w.measure.weekly_report(NOW)
    assert body and "ceiling: 1 of 4 in the last 90 days, breached yes" in body
    assert w.store.get_report(WEEK) == body
    assert "- human_label: 1" in body and "- Runs: 4" in body
    # The ceiling breach demotes every action once, and a second pass adds nothing.
    assert w.measure.enforce(NOW) and w.measure.enforce(NOW) == []


def test_k6_runtime_role_cannot_rewrite_labels_or_levels(pg_world):
    w = pg_world
    rid = w.run()
    w.label(rid, "agree")
    import psycopg

    for stmt in (
        "UPDATE labels SET label = 'harmful'",
        "DELETE FROM labels",
        "UPDATE level_events SET kind = 'clear'",
        "DELETE FROM level_events",
        "UPDATE reports SET body_md = 'x'",
    ):
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            w.store._db.execute(stmt)
