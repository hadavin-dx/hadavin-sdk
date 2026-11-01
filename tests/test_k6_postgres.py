# ruff: noqa: S311, B023  - seeded test randomness; threads are joined inside the loop that defines them
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


@pytest.fixture
def two_connections():
    """Two stores on two database connections: the in-process lock does not order them, only the database does."""
    for dsn in pg_schema(runtime=True):
        settings = PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn")  # noqa: S106 - a name
        a = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        b = make("store", settings, FakeSecretProvider({"pg-dsn": dsn}))
        yield a, b
        a._db.close()
        b._db.close()


def _lab(rid, name, who, i):
    from hadavin_sdk.models import Label, now

    return Label(
        run_id=rid,
        label=name,
        principal_id=who,
        channel="chat",
        created_at=now(),
        label_id=f"t{i}-{who}",
    )


def test_k6_two_connections_never_let_a_non_owner_lower_a_harmful_verdict(two_connections):
    """Threads on two connections race labels on three runs, each clock read before the database lock; the stored
    order must never show a non-owner lowering a harmful verdict (advisory lock + created_at order)."""
    import random
    import threading

    from hadavin_sdk.models import latest_labels
    from hadavin_sdk.store.protocol import HarmfulSticky

    a, b = two_connections
    runs = ["q0", "q1", "q2"]
    counter = iter(range(10**6))

    def work(store, seed):
        rnd = random.Random(seed)
        for _ in range(30):
            who = rnd.choice(["user:1", "user:2", "owner"])
            lab = _lab(
                rnd.choice(runs),
                rnd.choice(["agree", "harmful", "wrong", "partial"]),
                who,
                next(counter),
            )
            try:
                store.add_labels([(lab, None)], may_lower_harmful=who == "owner")
            except HarmfulSticky:
                pass

    threads = [threading.Thread(target=work, args=(s, i)) for i, s in enumerate([a, b, a, b])]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    for rid in runs:
        seen = []
        for lab in a.list_labels(rid):
            cur = latest_labels(seen).get(rid)
            lowered = cur is not None and cur.label == "harmful" and lab.label != "harmful"
            assert not lowered or lab.principal_id == "owner", (rid, lab.label_id)
            seen.append(lab)


def test_k6_two_connections_one_nonce_one_winner(two_connections):
    import threading

    a, b = two_connections
    results = []
    start = threading.Barrier(8)

    def go(store):
        start.wait()
        results.append(store.claim_action("9:v0=zz", NOW))

    threads = [threading.Thread(target=go, args=(s,)) for s in [a, b] * 4]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(results) == [False] * 7 + [True]


def test_k6_two_connections_a_clear_never_buries_a_demotion_it_did_not_see(two_connections):
    import threading

    from hadavin_sdk.models import LevelEvent

    a, b = two_connections
    for i in range(25):
        agent = f"agent{i}"
        base = LevelEvent(
            agent_id=agent, action_id="x", kind="demote", reason="old", by="s", at=NOW
        )
        a.add_level_event(base)
        seen = a.list_level_events()[-1]
        clear = LevelEvent(agent_id=agent, action_id="x", kind="clear", reason="o", by="o", at=NOW)
        start = threading.Barrier(2)

        def do_clear():
            start.wait()
            a.clear_demotion(clear, seen.seq)

        def do_demote():
            start.wait()
            b.add_level_event(base.model_copy(update={"reason": "new"}))

        t1, t2 = threading.Thread(target=do_clear), threading.Thread(target=do_demote)
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        events = [e for e in a.list_level_events() if e.agent_id == agent]
        newest = max(e.seq for e in events if e.reason == "new")
        assert not [e for e in events if e.kind == "clear" and e.seq > newest], i
        assert (agent, "x") in a.current_overrides(), i


def test_k6_two_connections_one_demotion_row_per_reason(two_connections):
    import threading

    from hadavin_sdk.models import LevelEvent

    a, b = two_connections
    ev = LevelEvent(agent_id="a", action_id="x", kind="demote", reason="ceiling:t", by="s", at=NOW)
    start = threading.Barrier(8)

    def go(store):
        start.wait()
        store.add_level_event(ev)

    threads = [threading.Thread(target=go, args=(s,)) for s in [a, b] * 4]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len(a.list_level_events()) == 1


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
