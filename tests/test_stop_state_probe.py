"""The guard probe, the busy mapping and the lock-order claims against a real PostgreSQL (real logins)."""

from __future__ import annotations

import threading
import time

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg import sql

from hadavin_sdk.models import KillSwitch
from hadavin_sdk.runtime import stop_state
from hadavin_sdk.store.postgres import PostgresStore
from hadavin_sdk.store.protocol import StoreBusy
from tests.stop_state_helpers import RESET_GROUP
from tests.test_stop_state_db import CAP, LABEL_A
from tests.test_stop_state_db import (
    stop_world as _w_fixture,  # noqa: F401  (registers the `w` fixture)
)


def _report(world, as_role=None, group=RESET_GROUP, runtime=None, stop=None):
    conn = world.as_(as_role) if as_role else world.admin()
    try:
        return PostgresStore(conn).guard_report(
            runtime or world.runtime, stop or world.stoprole, group
        )
    finally:
        conn.close()


def test_a_clean_world_has_no_problem_and_a_superuser_owner_is_only_tolerated(w):
    r = _report(w)
    assert r.problems == ()
    assert any(
        "superuser" in t for t in r.dev_tolerated
    )  # the test cluster is migrated as `postgres`
    assert r.runtime_connection_limit == 20 and r.stop_connection_limit == 2


def test_the_report_names_roles_and_does_not_depend_on_who_asks(w):
    """B6: the probe reads the NAMED roles, never `current_user`: the same answer from every connection."""
    w.grant_usage(w.runtime)
    w.grant_usage(w.stoprole)
    base = _report(w)
    assert _report(w, w.runtime) == base
    assert _report(w, w.stoprole) == base


def _grant(w, text, role):
    with w.admin() as db:
        db.execute(sql.SQL(text).format(sql.Identifier(role)))


@pytest.mark.parametrize(
    "grant, expect",
    [
        ("GRANT UPDATE ON kill_switch TO {}", "UPDATE on kill_switch"),
        ("GRANT TRIGGER ON kill_switch TO {}", "TRIGGER on kill_switch"),
        ("GRANT REFERENCES ON kill_switch_resets TO {}", "REFERENCES on kill_switch_resets"),
        ("GRANT INSERT ON kill_switch_stop_requests TO {}", "INSERT on kill_switch_stop_requests"),
        (
            "GRANT USAGE ON SEQUENCE kill_switch_stop_requests_id_seq TO {}",
            "USAGE on kill_switch_stop_requests_id_seq",
        ),
    ],
)
def test_an_extra_right_on_a_guarded_relation_is_a_problem(w, grant, expect):
    _grant(w, grant, w.runtime)
    assert any(expect in p for p in _report(w).problems)


def test_a_right_the_server_does_not_know_is_not_asked_for(w):
    """B2: MAINTAIN exists only from PostgreSQL 17; asking 16 for it raises 22023."""
    with w.admin() as db:
        from hadavin_sdk.store.postgres import table_privileges

        n = int(db.execute("SHOW server_version_num").fetchone()[0])
        assert ("MAINTAIN" in table_privileges(db)) == (n >= 170000)


def test_maintain_on_17_is_a_problem(w):
    with w.admin() as db:
        if int(db.execute("SHOW server_version_num").fetchone()[0]) < 170000:
            pytest.skip("MAINTAIN needs PostgreSQL 17 (this run is 16; the CI 17 job runs it)")
    _grant(w, "GRANT MAINTAIN ON kill_switch TO {}", w.runtime)
    assert any("MAINTAIN" in p for p in _report(w).problems)


def test_a_disabled_guard_trigger_is_a_problem(w):
    with w.admin() as db:
        db.execute("ALTER TABLE kill_switch DISABLE TRIGGER kill_switch_guard")
    assert any("kill_switch_guard" in p for p in _report(w).problems)


def test_the_group_check_is_exact_not_a_substring(w):
    assert _report(
        w, group=RESET_GROUP + "2"
    ).problems  # the guard names RESET_GROUP, not RESET_GROUP + "2"
    assert any("reset group" in p for p in _report(w, group=RESET_GROUP + "2").problems)
    prefix = RESET_GROUP[
        :-1
    ]  # a REAL role whose name is a prefix of the named one: only the exact match tells
    with w.admin() as db:
        db.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(prefix)))
    try:
        assert any(
            "does not name the configured reset group" in p
            for p in _report(w, group=prefix).problems
        )
    finally:
        with w.admin() as db:
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(prefix)))


def test_a_runtime_that_is_a_member_of_the_reset_group_is_a_problem(w):
    _grant(w, "GRANT " + RESET_GROUP + " TO {}", w.runtime)
    assert any("member of the reset group" in p for p in _report(w).problems)


def test_a_role_that_does_not_exist_is_a_problem(w):
    assert any("does not exist" in p for p in _report(w, runtime="p2a1_nobody").problems)


def test_the_probe_fails_pilot_on_a_superuser_owned_function_and_passes_dev(w):
    store = PostgresStore(w.admin())
    args = {"runtime_role": w.runtime, "stop_role": w.stoprole, "reset_group": RESET_GROUP}
    assert stop_state.probe(store, environment="dev", **args).status == stop_state.OK
    assert stop_state.probe(store, environment="pilot", **args).status == stop_state.FAILED


# --- busy answers, lock order, the cap across open transactions -------------------------------------------------


def _store_with_short(w, role, lock_ms):
    def short():
        c = w.as_(role)
        c.execute("SELECT set_config('lock_timeout', %s, false)", (str(lock_ms),))
        return c

    return PostgresStore(w.as_(role), short_connect=short)


def test_a_stop_that_waits_behind_a_table_lock_is_store_busy_and_works_afterwards(w):
    """S33: a migration's table lock queues the stop's INSERT; the stop ends with StoreBusy (NOT done), no raw error."""
    store = _store_with_short(w, w.runtime, 300)
    holder = w.admin()
    holder.autocommit = False
    holder.execute("LOCK TABLE kill_switch_stop_requests IN ACCESS EXCLUSIVE MODE")
    t0 = time.monotonic()
    try:
        with pytest.raises(StoreBusy):
            store.set_kill_switch(KillSwitch(on=True, by=LABEL_A))
        assert time.monotonic() - t0 < 5
    finally:
        holder.rollback()
        holder.close()
    assert w.state()[3] == 0  # nothing was added by the busy call
    assert store.set_kill_switch(KillSwitch(on=True, by=LABEL_A)).on is True


def test_a_migration_that_takes_kill_switch_first_never_makes_the_stop_a_deadlock_victim(w):
    """B7: lock order is kill_switch, then the request table. The stop's first statement reads kill_switch, so it
    waits for the migration instead of holding the request table and deadlocking with it."""
    store = _store_with_short(w, w.stoprole, 5000)
    mig = w.admin()
    mig.autocommit = False
    mig.execute("LOCK TABLE kill_switch IN ACCESS EXCLUSIVE MODE")
    result = []

    def stopper():
        try:
            result.append(store.set_kill_switch(KillSwitch(on=True, by=LABEL_A)).on)
        except Exception as exc:  # noqa: BLE001 - the test classifies below
            result.append(exc)

    t = threading.Thread(target=stopper)
    t.start()
    time.sleep(0.4)
    mig.execute(
        "LOCK TABLE kill_switch_stop_requests IN SHARE ROW EXCLUSIVE MODE"
    )  # would deadlock without the order
    mig.commit()
    mig.close()
    t.join(10)
    assert result == [True], result


def test_open_transactions_can_overshoot_the_cap_but_only_by_their_number(w):
    """B9: each open transaction counts only what it and the committed rows show, so N transactions can add up to
    N x cap rows; a later stop still reads ON."""
    a, b = w.as_(w.stoprole), w.as_(w.runtime)
    for c in (a, b):
        c.autocommit = False
        for _ in range(CAP + 2):
            c.execute("SELECT * FROM hadavin_kill_switch_stop(%s)", (LABEL_A,))
    a.commit()
    b.commit()
    a.close()
    b.close()
    assert CAP < w.state()[3] <= 2 * CAP
    assert w.stop(w.stoprole)[0] is True


def test_function_not_found_maps_to_not_migrated_and_a_missing_row_to_hd005(w):
    from hadavin_sdk.store.protocol import NotMigrated, SwitchRowMissing

    store = PostgresStore(w.as_(w.runtime))
    with w.admin() as db:
        db.execute("DELETE FROM kill_switch")
    with pytest.raises(SwitchRowMissing):
        PostgresStore(w.as_(w.member)).reset_kill_switch(LABEL_A, 0, 0)
    assert store.get_kill_switch().by == "system:kill_switch_row_missing"
    with w.admin() as db:
        db.execute("DROP FUNCTION hadavin_kill_switch_stop(text)")
    with pytest.raises(NotMigrated):
        store.set_kill_switch(KillSwitch(on=True, by=LABEL_A))
