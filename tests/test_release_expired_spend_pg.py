"""The release of expired spend holds (step F-store, ORDER 020 M1, migration 0008) against a real PostgreSQL
through real non-superuser logins: what it lowers and what it never touches, the audit order, the counters, the
rights of the release login and the refusal of every other login.

Every case gets a fresh schema, the four logins of `World` (runtime, portal, purge, reset) and a fifth, the
release login. "Denied" means `psycopg.errors.InsufficientPrivilege` exactly, and the relation is proven to exist
first. Needs HADAVIN_TEST_PG_DSN; skipped without it."""

from __future__ import annotations

import json
import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from psycopg import errors, sql

from hadavin_sdk import cli
from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.audit import AuditUnavailable
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import ChainSettings, PostgresSettings
from hadavin_sdk.config import ConfigError
from hadavin_sdk.models import new_id, now
from hadavin_sdk.store.migrate import GRANTS
from hadavin_sdk.store.protocol import SpendReleaser
from tests.test_stop_state_roles import SETTINGS, World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

D = Decimal
DENIED = errors.InsufficientPrivilege
AGENT = "agent-a"
DAY = date(now().year - 1, 1, 31)
OTHER_DAY = date(now().year - 1, 1, 30)  # the same month
BIG = D("1000")
FN = "hadavin_release_expired_spend(text, date)"


@pytest.fixture(name="w")
def release_world():
    world = World()
    with psycopg.connect(world.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(world.schema)))
        for r in world.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    world.release = world.new_role("rl")
    try:
        world.migrate(release_role=world.release)
        yield world
    finally:
        for s in world.stores:
            s._db.close()
        with psycopg.connect(world.dsn, autocommit=True) as db:
            for schema in world.schemas:
                db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
            for r in world.roles:
                db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


def _reserve(store, usd, *, agent=AGENT, day=DAY):
    rid = new_id("res")
    store.reserve_spend(rid, agent, day, D(usd), day_cap=BIG, month_cap=BIG)
    return rid


def _expire(w, *rids):
    """Age the named holds past the expiry and run the real expire step (the runtime login)."""
    for rid in rids:
        w.run(
            "UPDATE spend_reservations SET created_at = created_at - interval '2 hours' "
            "WHERE reservation_id = %s RETURNING 1",
            (rid,),
        )
    w.store(w.runtime).expire_spend_reservations(3600)


def _status(w, rid):
    return w.run(
        "SELECT status, settled_usd FROM spend_reservations WHERE reservation_id = %s", (rid,)
    )[0]


def _counters(w, agent=AGENT, day=DAY):
    d = w.run("SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent, day))
    m = w.run(
        "SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",
        (agent, day.replace(day=1)),
    )
    return (d[0][0] if d else None, m[0][0] if m else None)


def _audit(w, store):
    return make("audit", ChainSettings(kind="chain"), store=store, signer=None, anchor=None)


def _release(w, agent=AGENT, day=DAY, actor="user:op"):
    rl = w.store(w.release)
    return rl.release_expired_spend(agent, day, actor, _audit(w, rl))


def _world_with_holds(w):
    """Expired: a 1.00 and a 2.00 hold of DAY. Live: a 4.00 hold of DAY. Another day: an expired 8.00 hold.
    Another agent: an expired 16.00 hold of DAY. Returns the ids."""
    rt = w.store(w.runtime)
    a, b = _reserve(rt, "1.00"), _reserve(rt, "2.00")
    live = _reserve(rt, "4.00")
    other_day = _reserve(rt, "8.00", day=OTHER_DAY)
    other_agent = _reserve(rt, "16.00", agent="agent-b")
    _expire(w, a, b, other_day, other_agent)
    assert _status(w, live)[0] == "open"
    return SimpleNamespace(a=a, b=b, live=live, other_day=other_day, other_agent=other_agent)


# --- what it does --------------------------------------------------------------------------------------------------


def test_release_lowers_only_the_expired_rows_of_the_named_day_and_moves_both_counters(w):
    ids = _world_with_holds(w)
    assert _counters(w) == (
        D("7.00"),
        D("15.00"),
    )  # day: 1+2+4; month adds the 8.00 of the other day
    done = _release(w)
    assert (done.reservations, done.released_usd) == (2, D("3.00"))
    assert (done.day_usd, done.month_usd) == (D("4.00"), D("12.00"))
    assert _counters(w) == (D("4.00"), D("12.00"))
    assert _status(w, ids.a) == ("settled", 0) and _status(w, ids.b) == ("settled", 0)
    assert _status(w, ids.live) == ("open", None)  # a live hold is never touched
    assert _status(w, ids.other_day)[0] == "expired" and _counters(w, day=OTHER_DAY)[0] == D("8.00")
    assert _status(w, ids.other_agent)[0] == "expired" and _counters(w, "agent-b")[0] == D("16.00")


def test_a_second_release_changes_nothing(w):
    _world_with_holds(w)
    _release(w)
    again = _release(w)
    assert (again.reservations, again.released_usd) == (0, D("0"))
    assert _counters(w) == (D("4.00"), D("12.00"))


def test_release_of_a_day_with_no_expired_hold_reports_zero(w):
    _world_with_holds(w)
    done = _release(w, day=date(DAY.year, 1, 15))
    assert (done.reservations, done.released_usd, done.day_usd) == (0, D("0"), None)


def test_a_counter_below_the_released_sum_stops_at_zero_not_below(w):
    ids = _world_with_holds(w)
    w.run("UPDATE spend SET usd = 1.5 WHERE agent_id = %s AND day = %s RETURNING 1", (AGENT, DAY))
    w.run("UPDATE spend_month SET usd = 2 WHERE agent_id = %s RETURNING 1", (AGENT,))
    done = _release(w)
    assert (done.day_usd, done.month_usd) == (D("0"), D("0"))
    assert _status(w, ids.a)[0] == "settled"


def test_a_late_settle_after_the_release_changes_nothing(w):
    ids = _world_with_holds(w)
    _release(w)
    row, applied = w.store(w.runtime).settle_spend(ids.a, D("0.50"), agent_id=AGENT)
    assert applied is False and row.status == "settled" and row.settled_usd == 0
    assert _counters(w) == (D("4.00"), D("12.00"))


def test_a_missing_counter_row_aborts_the_whole_release(w):
    ids = _world_with_holds(w)
    w.run("DELETE FROM spend_month WHERE agent_id = %s RETURNING 1", (AGENT,))
    with pytest.raises(psycopg.errors.RaiseException):
        _release(w)
    assert _status(w, ids.a)[0] == "expired"  # the claim rolled back with it
    assert _counters(w)[0] == D("7.00")


def test_the_store_has_the_optional_protocol_and_the_memory_store_need_not(w):
    assert hasattr(w.store(w.release), "release_expired_spend")
    assert SpendReleaser is not None


# --- the audit order -----------------------------------------------------------------------------------------------


def _release_rows(w):
    return [
        (seq, json.loads(body))
        for seq, body in w.run(
            "SELECT seq, body FROM audit_entries WHERE kind = 'limits.release_expired' ORDER BY seq"
        )
    ]


def test_the_intent_row_is_written_before_the_change_and_the_outcome_after(w):
    _world_with_holds(w)
    seen = []

    class Spy:
        def __init__(self, inner):
            self.inner = inner

        def write_intent(self, event):
            seen.append(("intent", _counters(w)[0], w.count("audit_entries")))
            return self.inner.write_intent(event)

        def write_outcome(self, event):
            seen.append(("outcome", _counters(w)[0], w.count("audit_entries")))
            return self.inner.write_outcome(event)

    rl = w.store(w.release)
    rl.release_expired_spend(AGENT, DAY, "user:op", Spy(_audit(w, rl)))
    assert seen == [("intent", D("7.00"), 0), ("outcome", D("4.00"), 1)]
    rows = _release_rows(w)
    assert [r["principal"] for _, r in rows] == ["user:op", "user:op"]
    assert rows[0][1]["object_ref"] == f"{AGENT}:{DAY.isoformat()}"
    assert rows[1][1]["result"] == "released rows=2 requested_usd=3.00 applied_usd=3.00"
    assert w.count("audit_checkpoints") == 0  # the release login signs nothing


def test_when_the_intent_cannot_be_written_nothing_changes(w):
    ids = _world_with_holds(w)

    class Down:
        def write_intent(self, event):
            raise AuditUnavailable("down")

        def write_outcome(self, event):  # pragma: no cover - must not be reached
            raise AssertionError("no outcome without a release")

    with pytest.raises(AuditUnavailable):
        w.store(w.release).release_expired_spend(AGENT, DAY, "user:op", Down())
    assert _status(w, ids.a)[0] == "expired" and _counters(w) == (D("7.00"), D("15.00"))


def test_a_login_that_may_not_release_changes_nothing(w):
    ids = _world_with_holds(w)
    for role in (w.runtime, w.reset, w.portal, w.purge):
        with pytest.raises(DENIED):
            w.store(role).release_expired_spend(AGENT, DAY, "user:op", _NoAudit())
    assert _status(w, ids.a)[0] == "expired" and _counters(w) == (D("7.00"), D("15.00"))


class _NoAudit:
    """The portal and purge logins cannot append to the audit at all; this stands in for it."""

    def write_intent(self, event):
        return event.event_id

    def write_outcome(self, event):
        return event.event_id


def test_a_refused_release_by_the_runtime_login_is_audited_as_failed(w):
    _world_with_holds(w)
    rt = w.store(w.runtime)
    with pytest.raises(DENIED):
        rt.release_expired_spend(AGENT, DAY, "user:op", _audit(w, rt))
    results = [r["result"] for _, r in _release_rows(w)]
    assert results == ["intent", "release_failed"]


# --- rights --------------------------------------------------------------------------------------------------------


def test_the_release_login_holds_the_audit_append_and_nothing_on_any_other_table(w):
    assert w.rights(w.release) == {
        "audit_entries": {"SELECT", "INSERT"},
        "audit_checkpoints": {"SELECT"},
    }
    assert w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (w.release, FN)) == [(True,)]


@pytest.mark.parametrize(
    "table",
    sorted(
        n
        for n, g in GRANTS.items()
        if g.kind != "sequence" and n not in ("audit_entries", "audit_checkpoints")
    ),
)
def test_the_release_login_is_denied_on_every_other_relation(w, table):
    assert w.exists(table), f"{table} does not exist: a refusal would prove nothing"
    rel = sql.Identifier(table)
    for statement in (
        sql.SQL("SELECT * FROM {}").format(rel),
        sql.SQL("INSERT INTO {} DEFAULT VALUES").format(rel),
        sql.SQL("DELETE FROM {}").format(rel),
    ):
        with w.as_(w.release) as db, pytest.raises(DENIED):
            db.execute(statement)


def test_the_release_login_cannot_lower_a_counter_or_a_hold_by_hand(w):
    _world_with_holds(w)
    for statement in (
        "UPDATE spend SET usd = 0",
        "UPDATE spend_month SET usd = 0",
        "UPDATE spend_reservations SET status = 'settled', settled_usd = 0",
    ):
        with w.as_(w.release) as db, pytest.raises(DENIED):
            db.execute(statement)


def test_no_other_login_and_not_public_can_execute_the_function(w):
    stranger = w.new_role("st")
    w.grant(
        "GRANT USAGE ON SCHEMA {} TO {}", w.schema, stranger
    )  # sees the function; only PUBLIC could run it
    for role in (w.runtime, w.portal, w.purge, w.reset, stranger):
        assert w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (role, FN)) == [
            (False,)
        ], role
        with w.as_(role) as db, pytest.raises(DENIED):
            db.execute("SELECT * FROM hadavin_release_expired_spend(%s, %s)", (AGENT, DAY))


def test_the_function_of_a_named_day_never_touches_another_day_or_agent_whatever_the_arguments(w):
    ids = _world_with_holds(w)
    with w.as_(w.release) as db:
        db.execute("SELECT * FROM hadavin_release_expired_spend(%s, %s)", ("agent-b", OTHER_DAY))
    assert _status(w, ids.a)[0] == "expired" and _status(w, ids.other_day)[0] == "expired"
    assert _status(w, ids.other_agent)[0] == "expired"
    assert _counters(w) == (D("7.00"), D("15.00"))


# --- migrate -------------------------------------------------------------------------------------------------------


def test_migrate_again_keeps_the_grants_and_applies_nothing(w):
    before = {r: w.rights(r) for r in w.roles}
    assert w.migrate(release_role=w.release) == []
    assert {r: w.rights(r) for r in w.roles} == before
    assert w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (w.release, FN)) == [(True,)]


def test_migrate_refuses_a_release_role_that_is_another_named_role(w):
    for other in (w.runtime, w.reset, w.purge, w.portal):
        with pytest.raises(ConfigError, match="different"):
            w.migrate(release_role=other)


def test_migrate_refuses_a_named_role_that_can_still_run_the_function_through_public(w):
    w.do(f"GRANT EXECUTE ON FUNCTION {FN} TO PUBLIC")
    with pytest.raises(ConfigError, match="can run"):
        w.migrate(release_role=w.release)


def test_migrate_takes_a_direct_execute_back_from_the_runtime_role(w):
    w.grant(f"GRANT EXECUTE ON FUNCTION {FN} TO {{}}", w.runtime)
    w.migrate(release_role=w.release)
    assert w.run("SELECT has_function_privilege(%s, %s, 'EXECUTE')", (w.runtime, FN)) == [(False,)]


def test_migration_0008_adds_the_closed_at_index(w):
    assert w.run(
        "SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND indexname = 'spend_reservations_closed'",
        (w.schema,),
    )
    assert ("0008_release_expired_spend",) in w.run("SELECT version FROM schema_migrations")


# --- the command ---------------------------------------------------------------------------------------------------

REL_REF = "release-dsn"  # the NAME of a secret (config), never a value


def _cfg(**store):
    s = PostgresSettings(**{**SETTINGS, "release_credential_ref": REL_REF, **store})
    return SimpleNamespace(
        environment="pilot",
        backends=SimpleNamespace(store=s, audit=ChainSettings(kind="chain"), secrets=None),
    )


def _provide(w, monkeypatch, held):
    real = cli.make

    def fake(capability, settings, *a, **k):
        if capability == "secrets":
            return FakeSecretProvider(dict(held))
        made = real(capability, settings, *a, **k)
        if capability == "store":
            w.stores.append(made)
        return made

    monkeypatch.setattr(cli, "make", fake)


def test_the_command_runs_on_the_release_login_only_and_prints_what_it_changed(
    w, monkeypatch, capsys
):
    ids = _world_with_holds(w)
    _provide(w, monkeypatch, {REL_REF: w.dsn_of(w.release), "pg-dsn": w.dsn_of(w.runtime)})
    assert cli.release_expired_cmd(_cfg(), AGENT, DAY, "user:op") == 0
    assert "released 2 expired hold(s)" in capsys.readouterr().out
    assert _status(w, ids.a) == ("settled", 0) and _status(w, ids.live)[0] == "open"
    assert w.run("SELECT count(*) FROM kill_switch_clears") == [(0,)]  # no reset ran


def _fail_appends_after(monkeypatch, n):
    """The real chain audit, whose `_append` works n times and then raises (the intent lands, the outcome fails)."""
    real = cli.make

    def fake(capability, settings, *a, **k):
        made = real(capability, settings, *a, **k)
        if capability == "audit":
            orig, calls = made._append, {"n": 0}

            def flaky(event):
                calls["n"] += 1
                if calls["n"] > n:
                    raise RuntimeError("append down")
                return orig(event)

            made._append = flaky
        return made

    monkeypatch.setattr(cli, "make", fake)


def test_a_lost_outcome_with_the_real_chain_is_not_reported_as_audited(w):
    """The real chain never raises: it parks the event (the release login has no INSERT on audit_outbox, so in
    memory) and returns None. That must show as outcome_audited False."""
    _world_with_holds(w)
    rl = w.store(w.release)
    audit = _audit(w, rl)
    orig, calls = audit._append, {"n": 0}

    def flaky(event):
        calls["n"] += 1
        if calls["n"] > 1:
            raise RuntimeError("append down")
        return orig(event)

    audit._append = flaky
    done = rl.release_expired_spend(AGENT, DAY, "user:op", audit)
    assert done.outcome_audited is False and len(audit._pending) == 1
    assert _counters(w) == (D("4.00"), D("12.00"))  # the release itself did commit
    assert len(_release_rows(w)) == 1  # only the intent row is in the chain


def test_the_command_exits_5_and_names_the_intent_when_the_real_chain_loses_the_outcome(
    w, monkeypatch, capsys
):
    _world_with_holds(w)
    _provide(w, monkeypatch, {REL_REF: w.dsn_of(w.release), "pg-dsn": w.dsn_of(w.runtime)})
    _fail_appends_after(monkeypatch, 1)
    assert cli.release_expired_cmd(_cfg(), AGENT, DAY, "user:op") == 5
    intent_id = _release_rows(w)[0][1]["event_id"]
    assert intent_id in capsys.readouterr().err
    assert len(_release_rows(w)) == 1


def test_the_command_with_the_runtime_dsn_as_its_reference_is_refused_before_any_connection(
    w, monkeypatch, capsys
):
    ids = _world_with_holds(w)
    _provide(w, monkeypatch, {"pg-dsn": w.dsn_of(w.runtime)})
    assert cli.release_expired_cmd(_cfg(release_credential_ref="pg-dsn"), AGENT, DAY, "u") == 2
    assert _status(w, ids.a)[0] == "expired"


def test_the_command_with_the_runtime_login_behind_the_reference_is_refused_by_the_database(
    w, monkeypatch, capsys
):
    ids = _world_with_holds(w)
    _provide(w, monkeypatch, {REL_REF: w.dsn_of(w.runtime)})
    assert cli.release_expired_cmd(_cfg(), AGENT, DAY, "u") == 2
    assert _status(w, ids.a)[0] == "expired" and _counters(w) == (D("7.00"), D("15.00"))


def test_the_command_with_the_reset_login_behind_the_reference_is_refused_by_the_database(
    w, monkeypatch, capsys
):
    ids = _world_with_holds(w)
    _provide(w, monkeypatch, {REL_REF: w.dsn_of(w.reset)})
    assert cli.release_expired_cmd(_cfg(), AGENT, DAY, "u") == 2
    assert _status(w, ids.a)[0] == "expired"
