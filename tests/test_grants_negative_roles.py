"""Negative tests for the grant map: what each database identity must NOT be able to do.

Written by a test-writer that did not build the code under test (plan v4 step B, session core-c; the builder of
step B and of the money store is session core-b). Two layers:

(a) Pure Python, no database. The whole role x table x privilege matrix is computed from `migrate.GRANTS` and
    compared with a second, hand-written and reviewed list of every write privilege. A grant that is added or
    widened in `GRANTS` fails here until this file is changed on purpose, by someone who is not the builder.
    Security facts are then asserted by name (the stop state, the audit log, TRUNCATE, wildcards).
(b) PostgreSQL. A migrated schema and one fresh login role per identity; each role connects as itself and
    runs real statements: what the map does not give must be refused by the database with
    `psycopg.errors.InsufficientPrivilege` exactly. Needs HADAVIN_TEST_PG_DSN (CI: the postgres service) and is
    skipped without it, like the other database tests (`pg_schema`).

TWO TREES, ONE FILE. The file must be green before and after step B is merged, so it holds two reviewed lists
and picks one with ONE feature test, `STEP_B`: does `migrate()` take a `reset_role` (a fourth identity)?
  - `WRITES_BEFORE_STEP_B`: main (roles runtime, portal, purge; the runtime role may UPDATE the stop row).
  - `WRITES_AFTER_STEP_B`: core-b at 576f292 (step B: reset identity, migration 0006; and the money store of
    step F: migration 0007, `spend_reservations`). Written by hand from the migrations and from `GRANTS`,
    one reason per privilege. A tree with step B and without 0007 fails the pin on purpose: change the list.
`test_the_feature_test_agrees_with_the_grant_map` fails on a half-built tree (a keyword without the `Grant`
field, or the reverse). No expected value in this file is computed from `GRANTS`; `GRANTS` is only what is
checked.

Not repeated here (they exist): `has_table_privilege` over the runtime and the portal map
(tests/test_k2_migrations.py), the purge role's column reads (tests/test_k5_round10_postgres.py), stop with the
audit store down in memory (tests/test_review_fixes.py::test_stop_works_when_audit_is_down), core-b's own
tests/test_stop_state_roles.py (written from the ticket by another agent; kept apart on purpose).

The 12 step-B cases (were "Cases to enable when step B lands"). Each is code now. "B" = runs only when `STEP_B`
is true and is skipped with a reason on a tree without the reset identity; "both" = runs on both trees.
  1. The reset identity is its own `migrate()` role keyword, and is refused when it is the same role as, or a
     member of, the runtime, portal or purge role (or the reverse). B:
     `test_case1_the_reset_role_is_refused_when_it_is_another_identity`, `test_case1_a_reset_role_name_...`,
     `test_pg_case1_migrate_refuses_membership_between_the_reset_role_and_another_identity`.
  2. The matrix row of the reset identity, by statement. B: `test_case2_the_reset_identity_holds_exactly_...`,
     `test_pg_case2_the_reset_role_is_refused_everything_outside_its_reviewed_cells`, and the `reset`
     parameter of `test_pg_each_role_is_refused_what_the_map_does_not_give`.
  3. The runtime identity cannot switch the stop OFF. Both (strict xfail before step B, plain tests after):
     `test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off`,
     `test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off`. B:
     `test_pg_case3_every_way_to_switch_the_stop_off_is_refused_to_the_runtime_role`.
  4. The reset identity CAN switch the stop OFF as itself, and the runtime identity can still switch it ON.
     B: `test_pg_case4_the_reset_role_switches_the_stop_off_and_the_runtime_role_can_stop_again`. Both:
     `test_pg_the_runtime_role_can_switch_the_stop_on`.
  5. The reset identity can append the audit intent and cannot UPDATE, DELETE or TRUNCATE an audit row. B:
     `test_pg_case5_the_reset_role_appends_its_audit_intent_and_can_change_no_audit_row`.
  6. The portal and the purge identity hold nothing on the relations of the stop state. Both:
     `test_pg_no_role_but_the_runtime_and_reset_role_can_read_or_write_the_stop_state`,
     `test_only_the_reviewed_roles_hold_anything_on_the_stop_state`.
  7. `limits reset` with the runtime DSN (reset DSN missing, equal to the runtime one, or holding the runtime
     login) ends with an error and the stop still ON; with the reset DSN it works. B: `test_case7_...` (three,
     no database) and `test_pg_case7_...` (two).
  8. Reset under the reset identity with the audit intent failing: the stop stays ON. B:
     `test_pg_case8_reset_with_the_audit_intent_refused_leaves_the_stop_on`,
     `test_case8_a_reset_the_store_refuses_is_audited_as_reset_failed`. Both: the two in-memory order tests.
  9. Stop under the runtime identity with the audit tables refusing writes: the stop is ON all the same. Both:
     `test_pg_case9_stop_by_the_runtime_role_works_with_the_audit_tables_refusing_writes`.
 10. The migrations and their `GRANTS` rows arrive together, and the released manifest names every file. Both:
     `test_case10_...` (two), and the two `..._stops_migrate_before_it_connects` tests. B:
     `test_case10_the_stop_state_migration_and_its_grant_rows_arrived_together`,
     `test_case10_a_stop_state_relation_without_its_grant_row_stops_migrate`,
     `test_case10_a_reset_grant_row_without_its_migration_stops_migrate`.
 11. `migrate()` run again takes back what was granted by hand to the reset identity, and refuses a reset role
     that is a superuser, owns a relation, can CREATE in the schema or inherits a right from PUBLIC. B:
     `test_pg_case11_...` (two).
 12. A missing stop row still reads as ON. Both: `test_pg_case12_a_missing_stop_row_reads_as_on`. B:
     `test_pg_case12_a_reset_cannot_turn_a_missing_stop_row_into_off`.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import re
import uuid
from dataclasses import fields
from pathlib import Path

import pytest

from hadavin_sdk.audit.protocol import AuditUnavailable
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import KillSwitch
from hadavin_sdk.store import migrate as mig
from tests.contracts.kinds.store_postgres import pg_schema

PRIVILEGES = ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE")
AUDIT_LOG = ("audit_entries", "audit_checkpoints")
MANIFEST = Path(__file__).parent / "fixtures" / "migrations_released.json"

# THE feature test. Everything that differs between the two trees is selected by this one name.
STEP_B = "reset_role" in inspect.signature(mig.migrate).parameters
needs_step_b = pytest.mark.skipif(
    not STEP_B,
    reason="step B is not in this tree: migrate() has no reset_role, so there is no reset identity to test",
)
_STEP_B_XFAIL = "step B not built: stop and reset are one row the runtime role may UPDATE"


def _split(privileges: str) -> set[str]:
    return {p.strip() for p in privileges.split(",") if p.strip()}


# How `migrate()` turns one Grant into the table-level privileges of each identity (the three or four
# `_apply_grants` calls at the end of `migrate()`).
HOLDS = {
    "runtime": lambda g: _split(g.runtime),
    "portal": lambda g: {"SELECT"} if g.portal else set(),
    "purge": lambda g: _split(g.purge),
}
if STEP_B:
    HOLDS["reset"] = lambda g: _split(g.reset)
ROLES = tuple(HOLDS)

# --- the reviewed lists: written by hand, never computed from GRANTS ------------------------------------

# Every write privilege (anything but SELECT) on main, written by hand from main on 2026-11-20.
WRITES_BEFORE_STEP_B: dict[str, dict[str, set[str]]] = {
    "runtime": {
        "runs": {"INSERT", "UPDATE"},
        "plans": {"INSERT", "UPDATE"},
        "gate_decisions": {"INSERT"},
        "approval_requests": {"INSERT", "UPDATE"},
        "approval_decisions": {"INSERT"},
        "dead_letters": {"INSERT"},
        "spend": {"INSERT", "UPDATE"},
        "spend_month": {"INSERT", "UPDATE"},
        "kill_switch": {"INSERT", "UPDATE"},
        "tick_state": {"INSERT", "UPDATE"},
        "audit_entries": {"INSERT"},
        "audit_checkpoints": {"INSERT"},
        "audit_outbox": {"INSERT", "DELETE"},
        "tool_calls": {"INSERT"},
        "redaction_maps": {"INSERT", "UPDATE"},
    },
    "portal": {},
    "purge": {"tool_calls": {"DELETE"}, "redaction_maps": {"DELETE"}},
}

# Every write privilege after step B (and step F's money store), written by hand on 2026-11-20 from core-b
# 576f292: migrations 0001 to 0007 and src/hadavin_sdk/store/migrate.py:48-76. REVIEWED: one reason each.
# "FINDING" marks a privilege that is wider than the job named beside it; see
# handover/core-c/evidence/B-grants-rework.md. A finding is recorded, not accepted: the list pins what IS.
WRITES_AFTER_STEP_B: dict[str, dict[str, set[str]]] = {
    "runtime": {
        # INSERT: a run starts. UPDATE: its state moves (the purge role reads state and updated_at).
        "runs": {"INSERT", "UPDATE"},
        # INSERT: a plan is stored. UPDATE: its status changes when it is approved or done.
        "plans": {"INSERT", "UPDATE"},
        # INSERT: one row per gate decision; written once, never changed.
        "gate_decisions": {"INSERT"},
        # INSERT: ask a person. UPDATE: the request is decided or expires (the tick).
        "approval_requests": {"INSERT", "UPDATE"},
        # INSERT: one row per decision; written once (its sequence is USAGE only).
        "approval_decisions": {"INSERT"},
        # INSERT: park an input that could not be handled; written once.
        "dead_letters": {"INSERT"},
        # INSERT: book the worst case before a model call. UPDATE: settle or expire the row.
        # FINDING: UPDATE is table-wide, so the runtime login can rewrite reserved_usd or a closed row; it
        # already holds UPDATE on the counters themselves (spend, spend_month), so no new power.
        "spend_reservations": {"INSERT", "UPDATE"},
        # INSERT: the first charge of a day. UPDATE: add to the day counter.
        "spend": {"INSERT", "UPDATE"},
        # INSERT: the first charge of a month. UPDATE: add to the month counter.
        "spend_month": {"INSERT", "UPDATE"},
        # INSERT: a stop is one new row; this is ALL the runtime may write to the stop state.
        # FINDING (small): "by", ts and id are free, so the runtime login can sign a stop with any name.
        "kill_switch_stops": {"INSERT"},
        # INSERT: the first run of a tick step. UPDATE: its last-run time and detail.
        "tick_state": {"INSERT", "UPDATE"},
        # INSERT: append to the audit chain (a trigger refuses UPDATE, DELETE, TRUNCATE to everybody).
        "audit_entries": {"INSERT"},
        # INSERT: the tick signs a checkpoint; written once.
        "audit_checkpoints": {"INSERT"},
        # INSERT: park an audit row while the chain is down. DELETE: reconcile removes it once chained.
        "audit_outbox": {"INSERT", "DELETE"},
        # INSERT: evidence of one tool call; append only.
        "tool_calls": {"INSERT"},
        # INSERT: a new map. UPDATE: the map of a run grows.
        # FINDING (old, also on main): the comment above the row says "append and purge only (no UPDATE)".
        "redaction_maps": {"INSERT", "UPDATE"},
        # NOT here on purpose: kill_switch (no INSERT, no UPDATE: that is step B) and kill_switch_clears.
    },
    "portal": {},  # reads only
    "purge": {
        # DELETE: evidence past its retention (finds the rows by call_id, run_id, created_at).
        "tool_calls": {"DELETE"},
        # DELETE: maps past their retention (finds the rows by run_id, updated_at).
        "redaction_maps": {"DELETE"},
        # DELETE: closed reservations past their retention (finds the rows by status, closed_at).
        # FINDING: the grant is table-wide, so the purge login can also delete an OPEN reservation; only
        # the WHERE of the purge statement keeps it to closed rows. The counters stay booked (safe side).
        "spend_reservations": {"DELETE"},
    },
    "reset": {
        # UPDATE: turn the old one-row flag off (and record who reset).
        # FINDING: table-wide, so the reset login can also set the flag ON or change id (both read as ON:
        # the safe direction; ticket B, resolution S4, accepts it; no column grant was built).
        "kill_switch": {"UPDATE"},
        # INSERT: one clear per open stop: this IS the reset.
        "kill_switch_clears": {"INSERT"},
        # INSERT: the audit intent of the reset, written before the clear.
        # FINDING: the right is "append any audit row", not "append a reset intent" (ticket B names this
        # as a known cost; the runtime login has the same right).
        "audit_entries": {"INSERT"},
    },
}
WRITES = WRITES_AFTER_STEP_B if STEP_B else WRITES_BEFORE_STEP_B

# The stop state: every privilege (SELECT too) of every role on every relation that holds it.
STOP_HOLDS_BEFORE_STEP_B: dict[str, dict[str, set[str]]] = {
    "kill_switch": {"runtime": {"SELECT", "INSERT", "UPDATE"}},
}
STOP_HOLDS_AFTER_STEP_B: dict[str, dict[str, set[str]]] = {
    # the old flag: the runtime reads it; the reset role reads it (the WHERE of its UPDATE) and turns it off
    "kill_switch": {"runtime": {"SELECT"}, "reset": {"SELECT", "UPDATE"}},
    # stops: the runtime adds and reads them; the reset role reads them to find the open ones
    "kill_switch_stops": {"runtime": {"SELECT", "INSERT"}, "reset": {"SELECT"}},
    # clears: the runtime reads them (an open stop is one without a clear); the reset role adds them
    "kill_switch_clears": {"runtime": {"SELECT"}, "reset": {"SELECT", "INSERT"}},
}
STOP_HOLDS = STOP_HOLDS_AFTER_STEP_B if STEP_B else STOP_HOLDS_BEFORE_STEP_B
STOP_RELATIONS = tuple(STOP_HOLDS)
STOP_TABLE = "kill_switch"  # the one-row flag; exists on both trees

# The whole row of the reset identity, SELECT too (ticket B, invariant 6): nothing else, on no other table.
RESET_HOLDS: dict[str, set[str]] = {
    "kill_switch": {"SELECT", "UPDATE"},
    "kill_switch_stops": {"SELECT"},
    "kill_switch_clears": {"SELECT", "INSERT"},
    "audit_entries": {
        "SELECT",
        "INSERT",
    },  # SELECT: the last hash and the duplicate check of an append
    "audit_checkpoints": {"SELECT"},  # the probe the chain audit runs when it is built
}
# Tables the reset identity must never touch, by name, so the refusals below cannot become vacuous.
RESET_NEVER = (
    "runs",
    "plans",
    "gate_decisions",
    "approval_requests",
    "approval_decisions",
    "dead_letters",
    "spend",
    "spend_month",
    "spend_reservations",
    "tick_state",
    "audit_outbox",
    "tool_calls",
    "redaction_maps",
)

AUDIT_HOLDERS_BEFORE_STEP_B = {
    "audit_entries": {"SELECT": {"runtime", "portal"}, "INSERT": {"runtime"}},
    "audit_checkpoints": {"SELECT": {"runtime", "portal"}, "INSERT": {"runtime"}},
}
AUDIT_HOLDERS_AFTER_STEP_B = {
    "audit_entries": {"SELECT": {"runtime", "portal", "reset"}, "INSERT": {"runtime", "reset"}},
    "audit_checkpoints": {"SELECT": {"runtime", "portal", "reset"}, "INSERT": {"runtime"}},
}
AUDIT_HOLDERS = AUDIT_HOLDERS_AFTER_STEP_B if STEP_B else AUDIT_HOLDERS_BEFORE_STEP_B

DELETES_BEFORE_STEP_B = {
    ("runtime", "audit_outbox"),
    ("purge", "tool_calls"),
    ("purge", "redaction_maps"),
}
DELETES_AFTER_STEP_B = DELETES_BEFORE_STEP_B | {("purge", "spend_reservations")}
DELETES = DELETES_AFTER_STEP_B if STEP_B else DELETES_BEFORE_STEP_B

# The only column reads of the purge role: what the WHERE of its DELETE needs, never a stored original.
PURGE_COLS_BEFORE_STEP_B = {
    "runs": ("run_id", "state", "updated_at"),
    "tool_calls": ("call_id", "run_id", "created_at"),
    "redaction_maps": ("run_id", "updated_at"),
}
PURGE_COLS_AFTER_STEP_B = PURGE_COLS_BEFORE_STEP_B | {"spend_reservations": ("status", "closed_at")}
PURGE_COLS = PURGE_COLS_AFTER_STEP_B if STEP_B else PURGE_COLS_BEFORE_STEP_B

PORTAL_NEVER_BEFORE_STEP_B = {
    "kill_switch",
    "redaction_maps",
    "tool_calls",
    "audit_outbox",
    "tick_state",
    "spend",
}
PORTAL_NEVER_AFTER_STEP_B = PORTAL_NEVER_BEFORE_STEP_B | {
    "kill_switch_stops",
    "kill_switch_clears",
    "spend_reservations",
}
PORTAL_NEVER = PORTAL_NEVER_AFTER_STEP_B if STEP_B else PORTAL_NEVER_BEFORE_STEP_B

GRANT_FIELDS_BEFORE_STEP_B = {"kind", "runtime", "portal", "purge", "purge_cols"}
GRANT_FIELDS_AFTER_STEP_B = GRANT_FIELDS_BEFORE_STEP_B | {"reset"}
ROLE_KEYWORDS_BEFORE_STEP_B = {"runtime_role", "portal_role", "purge_role"}
ROLE_KEYWORDS_AFTER_STEP_B = ROLE_KEYWORDS_BEFORE_STEP_B | {"reset_role"}
TABLES_AT_LEAST = 18 if STEP_B else 15  # 15 on main; + two stop tables + spend_reservations


def _tables() -> list[str]:
    return [name for name, grant in mig.GRANTS.items() if grant.kind != "sequence"]


def _matrix() -> dict[tuple[str, str, str], bool]:
    """(role, table, privilege) -> granted, for every table and view in `GRANTS`."""
    return {
        (role, table, privilege): privilege in HOLDS[role](mig.GRANTS[table])
        for role in ROLES
        for table in _tables()
        for privilege in PRIVILEGES
    }


def _holders(table: str, *privileges: str) -> set[str]:
    return {r for (r, t, p), yes in _matrix().items() if yes and t == table and p in privileges}


def _never_connect(monkeypatch) -> None:
    def never(*args, **kwargs):
        raise AssertionError("migrate() connected although it had to refuse first")

    monkeypatch.setattr(mig, "connect", never)


# --- (a) pure Python ---------------------------------------------------------------------------------


def test_the_feature_test_agrees_with_the_grant_map():
    """A half-built step B (the keyword without the Grant field, or a field nobody fills) is an error here,
    not a silent choice of the wrong reviewed list."""
    has_field = "reset" in {f.name for f in fields(mig.Grant)}
    assert has_field == STEP_B
    assert any(getattr(g, "reset", "") for g in mig.GRANTS.values()) == STEP_B
    assert ("kill_switch_stops" in mig.GRANTS) == STEP_B
    assert ROLES == (("runtime", "portal", "purge", "reset") if STEP_B else ROLES[:3])
    assert len(ROLES) == (4 if STEP_B else 3)


def test_the_identities_are_the_ones_this_file_knows():
    """A new role keyword or Grant field is a new identity: its denials must be written here first."""
    keywords = {p for p in inspect.signature(mig.migrate).parameters if p.endswith("_role")}
    assert keywords == (ROLE_KEYWORDS_AFTER_STEP_B if STEP_B else ROLE_KEYWORDS_BEFORE_STEP_B)
    assert keywords == {f"{role}_role" for role in ROLES}
    assert {f.name for f in fields(mig.Grant)} == (
        GRANT_FIELDS_AFTER_STEP_B if STEP_B else GRANT_FIELDS_BEFORE_STEP_B
    )


def test_the_matrix_covers_every_role_table_and_privilege():
    matrix = _matrix()
    assert len(matrix) == len(ROLES) * len(_tables()) * len(PRIVILEGES)
    assert len(_tables()) >= TABLES_AT_LEAST  # a shrinking map would make the tests below vacuous
    assert sum(matrix.values()) > 0
    assert sum(not held for held in matrix.values()) > sum(matrix.values())  # mostly refusals


def test_every_write_privilege_is_on_the_reviewed_list():
    actual = {role: {} for role in ROLES}
    for (role, table, privilege), held in _matrix().items():
        if held and privilege != "SELECT":
            actual[role].setdefault(table, set()).add(privilege)
    assert actual == WRITES


def test_the_two_reviewed_lists_differ_only_where_step_b_and_the_money_store_say():
    """The review of the second list in one place: what changed for the three old roles, and nothing else."""
    before, after = WRITES_BEFORE_STEP_B, WRITES_AFTER_STEP_B
    assert set(before) == {"runtime", "portal", "purge"} and set(after) == {*before, "reset"}
    changed = {t for t in {*before["runtime"], *after["runtime"]} if before["runtime"].get(t) != after["runtime"].get(t)}  # fmt: skip
    assert changed == {"kill_switch", "kill_switch_stops", "spend_reservations"}
    assert "kill_switch" not in after["runtime"]  # the whole point of step B
    assert after["portal"] == before["portal"] == {}
    assert {t for t in after["purge"] if t not in before["purge"]} == {"spend_reservations"}
    assert all(after["purge"][t] == before["purge"][t] for t in before["purge"])
    reset_writes = {(t, p) for t, ps in after["reset"].items() for p in ps}
    assert reset_writes == {
        ("kill_switch", "UPDATE"),
        ("kill_switch_clears", "INSERT"),
        ("audit_entries", "INSERT"),
    }
    assert after["reset"] == {t: ps - {"SELECT"} for t, ps in RESET_HOLDS.items() if ps - {"SELECT"}}  # fmt: skip


@pytest.mark.parametrize("role", ROLES)
def test_no_role_may_truncate_any_table(role):
    assert [
        t
        for t in _tables()
        if (role, t, "TRUNCATE") in _matrix() and _matrix()[role, t, "TRUNCATE"]
    ] == []


def test_no_grant_uses_a_wildcard_or_a_privilege_outside_the_plain_ones():
    name = re.compile(r"[a-z_][a-z0-9_]*")
    for relation, grant in mig.GRANTS.items():
        assert name.fullmatch(relation), relation
        allowed = {"USAGE", "SELECT"} if grant.kind == "sequence" else set(PRIVILEGES[:4])
        for text in (grant.runtime, grant.purge, getattr(grant, "reset", "")):
            tokens = [p.strip() for p in text.split(",")] if text else []
            assert all(tokens), (relation, text)  # no empty item
            assert len(tokens) == len(set(tokens)), (relation, text)
            assert set(tokens) <= allowed, (
                relation,
                text,
            )  # so no ALL, no *, no TRUNCATE, no TRIGGER
        assert all(name.fullmatch(col) for col in grant.purge_cols), relation
    assert (
        mig._TABLE_PRIVS[:5] == PRIVILEGES
    )  # the migrate-time check looks at the same five and more


def test_only_the_reviewed_roles_hold_anything_on_the_stop_state():
    """Case 6 (no database): the portal and the purge role hold nothing; nobody can remove a row."""
    assert set(STOP_RELATIONS) <= set(_tables())
    for relation, reviewed in STOP_HOLDS.items():
        held = {role: {p for p in PRIVILEGES if _matrix()[role, relation, p]} for role in ROLES}
        assert held == {role: reviewed.get(role, set()) for role in ROLES}, relation
        assert _holders(relation, "DELETE", "TRUNCATE") == set(), relation
        assert _holders(relation, *PRIVILEGES) & {"portal", "purge"} == set(), relation
        assert not mig.GRANTS[relation].purge_cols and not mig.GRANTS[relation].portal, relation
    # no relation of the stop state is missing from the reviewed list (a fourth one must be added by hand)
    assert {t for t in _tables() if t.startswith("kill_switch")} == set(STOP_RELATIONS)


@pytest.mark.parametrize("table", AUDIT_LOG)
def test_nobody_may_change_or_remove_an_audit_row(table):
    assert _holders(table, "UPDATE", "DELETE", "TRUNCATE") == set()
    assert _holders(table, "INSERT") == AUDIT_HOLDERS[table]["INSERT"]
    assert _holders(table, "SELECT") == AUDIT_HOLDERS[table]["SELECT"]


def test_delete_is_held_only_on_the_outbox_and_the_purged_tables():
    deletes = {(r, t) for (r, t, p), held in _matrix().items() if held and p == "DELETE"}
    assert deletes == DELETES


def test_the_portal_role_writes_nothing_and_reads_no_secret_or_control_table():
    assert all(HOLDS["portal"](g) <= {"SELECT"} for g in mig.GRANTS.values())
    assert PORTAL_NEVER <= set(_tables())
    assert {t for t in PORTAL_NEVER if _holders(t, *PRIVILEGES) & {"portal"}} == set()


def test_the_purge_role_holds_delete_only_and_no_whole_table_read():
    for table in _tables():
        assert HOLDS["purge"](mig.GRANTS[table]) <= {"DELETE"}, table
    # column reads exist only to find the rows to delete or the run they belong to, never on other tables
    assert {
        t: mig.GRANTS[t].purge_cols for t in _tables() if mig.GRANTS[t].purge_cols
    } == PURGE_COLS


def test_no_role_but_the_runtime_role_may_use_a_sequence():
    for relation, grant in mig.GRANTS.items():
        if grant.kind == "sequence":
            assert _split(grant.runtime) == {"USAGE"}, relation  # nextval only: no setval (UPDATE)
            assert not grant.portal and not grant.purge and not grant.purge_cols, relation
            assert not getattr(grant, "reset", ""), relation


def test_a_grant_row_without_its_migration_stops_migrate_before_it_connects(monkeypatch):
    monkeypatch.setitem(mig.GRANTS, "relation_no_migration_creates", mig.Grant("table", "SELECT"))
    _never_connect(monkeypatch)
    assert any(
        "relation_no_migration_creates, which no migration creates" in problem
        for problem in mig.check_grants(mig._migration_files())
    )
    with pytest.raises(ConfigError, match="which no migration creates"):
        mig.migrate("host=unused.invalid")


def test_a_migration_without_its_grant_row_stops_migrate_before_it_connects(monkeypatch):
    monkeypatch.delitem(mig.GRANTS, STOP_TABLE)
    _never_connect(monkeypatch)
    with pytest.raises(ConfigError, match=f"{STOP_TABLE} .table. is created by a migration"):
        mig.migrate("host=unused.invalid")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_case10_the_real_migrations_and_the_grant_map_agree():
    files = mig._migration_files()
    assert len(files) >= 5
    assert mig.check_ledger(files) == []
    assert mig.check_grants(files) == []
    created, unread = mig._scan(files)
    assert unread == []
    assert set(created) == set(mig.GRANTS)  # each relation has its row and each row its relation


def test_case10_the_released_manifest_names_every_migration_file():
    """A migration that arrives without its manifest row (or is edited after release) is caught here too."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest == {path.stem: _sha(path) for path in mig._migration_files()}


@needs_step_b
def test_case10_the_stop_state_migration_and_its_grant_rows_arrived_together():
    files = mig._migration_files()
    home = [p for p in files if "kill_switch_stops" in mig._scan([p])[0]]
    assert len(home) == 1  # one file creates the new stop relations
    created, unread = mig._scan(home)
    assert unread == []
    # two tables, no sequence (the id is a UUID): nothing a role would need a sequence grant for
    assert created == {"kill_switch_stops": "table", "kill_switch_clears": "table"}
    assert all(name in mig.GRANTS and mig.GRANTS[name].kind == "table" for name in created)
    assert home[0].stem in json.loads(MANIFEST.read_text(encoding="utf-8"))


@needs_step_b
@pytest.mark.parametrize("relation", ["kill_switch_stops", "kill_switch_clears"])
def test_case10_a_stop_state_relation_without_its_grant_row_stops_migrate(monkeypatch, relation):
    monkeypatch.delitem(mig.GRANTS, relation)
    _never_connect(monkeypatch)
    with pytest.raises(ConfigError, match=f"{relation} .table. is created by a migration"):
        mig.migrate("host=unused.invalid", reset_role="some_reset_role")


@needs_step_b
def test_case10_a_reset_grant_row_without_its_migration_stops_migrate(monkeypatch):
    """A row that gives ONLY the reset role something on a relation no migration creates."""
    row = mig.Grant("table", "", reset="SELECT, INSERT")
    monkeypatch.setitem(mig.GRANTS, "kill_switch_no_migration_creates", row)
    _never_connect(monkeypatch)
    with pytest.raises(ConfigError, match="kill_switch_no_migration_creates, which no migration"):
        mig.migrate("host=unused.invalid", reset_role="some_reset_role")


# --- case 1 (no database): the reset identity is its own role ---------------------------------------


@needs_step_b
@pytest.mark.parametrize("other", ["runtime", "portal", "purge"])
def test_case1_the_reset_role_is_refused_when_it_is_another_identity(monkeypatch, other):
    _never_connect(monkeypatch)
    with pytest.raises(ConfigError, match="different roles"):
        mig.migrate("host=unused.invalid", reset_role="one_name", **{f"{other}_role": "one_name"})


@needs_step_b
@pytest.mark.parametrize(
    "name", ["public", "none", "session_user", "current_user", "", "Reset", "a b", "x; DROP ROLE x"]
)
def test_case1_a_reset_role_name_that_is_not_one_plain_role_is_refused(monkeypatch, name):
    """`GRANT ... TO public` is a grant to everybody: such a name must never reach a GRANT."""
    _never_connect(monkeypatch)
    with pytest.raises(ConfigError, match="not a plain database role name"):
        mig.migrate("host=unused.invalid", reset_role=name)


# --- case 2 (no database): the row of the reset identity ---------------------------------------------


@needs_step_b
def test_case2_the_reset_identity_holds_exactly_the_reviewed_cells():
    assert set(RESET_HOLDS) <= set(_tables()) and set(RESET_NEVER) <= set(_tables())
    assert set(RESET_HOLDS) | set(RESET_NEVER) == set(
        _tables()
    )  # every table is on one of the two lists
    held = {t: HOLDS["reset"](mig.GRANTS[t]) for t in _tables() if HOLDS["reset"](mig.GRANTS[t])}
    assert held == RESET_HOLDS
    assert all(not HOLDS["reset"](mig.GRANTS[t]) for t in RESET_NEVER)
    # it cannot add a stop row and cannot remove anything
    assert "INSERT" not in HOLDS["reset"](mig.GRANTS["kill_switch_stops"])
    assert not any({"DELETE", "TRUNCATE"} & HOLDS["reset"](g) for g in mig.GRANTS.values())


# --- stop and reset order (no database; true on both trees) ---------------------------------------


class _Recorder:
    """A store and an audit sink in one: records the order of the calls `Limits` makes."""

    def __init__(self, fail: str | None = None):
        self.calls: list[str] = []
        self._fail = fail
        self._state = KillSwitch(on=True, by="before")

    def _note(self, call: str) -> None:
        self.calls.append(call)
        if self._fail == call.split(":")[0]:
            raise AuditUnavailable("audit store down")

    def get_kill_switch(self) -> KillSwitch:
        return self._state

    def set_kill_switch(self, ks) -> None:
        self.calls.append(f"switch:{'on' if ks.on else 'off'}:{ks.by}")
        if self._fail == "switch":
            raise PermissionError("the store refused the switch")
        self._state = ks

    def write_intent(self, event) -> str:
        self._note(f"intent:{event.operation}:{event.result}:{event.principal}")
        return "key"

    def write_outcome(self, event) -> None:
        self._note(f"outcome:{event.operation}:{event.result}:{event.principal}")


def test_stop_switches_first_and_does_not_wait_for_the_audit_write():
    both = _Recorder()
    Limits(both, both, None).stop(by="user:a")
    assert both.calls == ["switch:on:user:a", "outcome:stop:on:user:a"]
    assert not any(
        call.startswith("intent") for call in both.calls
    )  # an intent can raise; stop must not


def test_reset_writes_the_audit_intent_before_it_touches_the_switch():
    both = _Recorder()
    Limits(both, both, None).reset(by="user:a")
    assert both.calls == ["intent:reset:off:user:a", "switch:off:user:a"]


def test_reset_leaves_the_switch_alone_when_the_audit_intent_fails():
    both = _Recorder(fail="intent")
    with pytest.raises(AuditUnavailable):
        Limits(both, both, None).reset(by="user:a")
    assert both.calls == ["intent:reset:off:user:a"]  # no switch call at all
    assert both.get_kill_switch().on is True


@needs_step_b
def test_case8_a_reset_the_store_refuses_is_audited_as_reset_failed():
    """Ticket B invariant 5: the chain then holds `reset` followed by `reset_failed`, and the error leaves."""
    both = _Recorder(fail="switch")
    with pytest.raises(PermissionError):
        Limits(both, both, None).reset(by="user:a")
    assert both.calls == [
        "intent:reset:off:user:a",
        "switch:off:user:a",
        "outcome:reset_failed:on:user:a",
    ]
    assert both.get_kill_switch().on is True


# --- case 7 (no database): `limits reset` and the reset DSN -------------------------------------------

RESET_REF = "reset-login"  # the NAME of a secret in the config, never a value
STORE_SETTINGS = {"kind": "postgres", "dsn_secret_name": "dsn"}  # a name again, not a value


def _pilot_config(tmp_path, ref: str | None, env: str = "pilot") -> Path:
    """A pilot config on a postgres store and a chain audit; `ref` sets backends.store.reset_credential_ref."""
    import yaml

    from tests.test_k3_pilot_env import pilot_cfg

    root = pilot_cfg(tmp_path, env=env)
    path = root / "config.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["backends"]["store"]["kind"] == "postgres"
    if ref:
        data["backends"]["store"]["reset_credential_ref"] = ref
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return root


def _limits_reset(cfg: Path, by: str = "user:op") -> int:
    from hadavin_sdk import cli

    return cli.main(["--config", str(cfg), "limits", "reset", "--by", by])


@needs_step_b
@pytest.mark.parametrize("how", ["no_ref", "ref_is_the_runtime_secret"])
def test_case7_limits_reset_without_a_reset_dsn_of_its_own_is_refused_before_anything_is_built(
    tmp_path, monkeypatch, capsys, how
):
    """In pilot the reset must not run on the runtime login: no reset DSN named, or the reset DSN named is
    the runtime's own secret. Refused before a secret is read or a connection is made."""
    from hadavin_sdk import cli

    cfg = _pilot_config(tmp_path, None if how == "no_ref" else "pg-dsn")

    def never(capability, *args, **kwargs):
        raise AssertionError(f"make({capability!r}) was called: the refusal must come first")

    monkeypatch.setattr(cli, "make", never)
    assert _limits_reset(cfg) == 2
    err = capsys.readouterr().err
    assert err.startswith("refused:") and "reset_credential_ref" in err
    assert "The kill switch was not changed" in err and "Traceback" not in err


@needs_step_b
def test_case7_limits_reset_builds_its_store_and_audit_from_the_reset_dsn_only(
    tmp_path, monkeypatch
):
    """The secrets provider holds ONLY the reset secret. The store must be built from the settings that name
    it, the audit must sit on that same store with no signer and no anchor, and nothing else is built."""
    from hadavin_sdk import cli
    from hadavin_sdk.actions.secrets import FakeSecretProvider

    cfg = _pilot_config(tmp_path, RESET_REF)
    both, made = _Recorder(), []

    def fake(capability, settings, *args, **kwargs):
        made.append((capability, settings, kwargs))
        if capability == "secrets":
            return FakeSecretProvider({RESET_REF: "the reset login, not read by this test"})
        if capability in ("store", "audit"):
            return both
        raise AssertionError(f"limits reset built a {capability}: it runs as the reset login only")

    monkeypatch.setattr(cli, "make", fake)
    assert _limits_reset(cfg, "user:op") == 0
    assert [capability for capability, _, _ in made] == ["secrets", "store", "audit"]
    store_settings = made[1][1]
    assert store_settings.dsn_secret_name == RESET_REF  # not "pg-dsn", the runtime login
    assert store_settings.purge_dsn_secret_name is None
    assert made[2][2] == {"store": both, "signer": None, "anchor": None}
    assert both.calls == ["intent:reset:off:user:op", "switch:off:user:op"]


# --- (b) PostgreSQL ----------------------------------------------------------------------------------


@pytest.fixture
def identities():
    """(owner DSN, {role: login role name}): a migrated schema, one fresh login role per identity with the
    grants applied in ONE migrate() call, and a `stranger` role that was never granted anything."""
    import psycopg
    from psycopg import sql

    for dsn in pg_schema():
        names = {role: f"{role[:2]}_{uuid.uuid4().hex[:10]}" for role in (*ROLES, "stranger")}
        with psycopg.connect(dsn, autocommit=True) as db:
            for name in names.values():
                db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(name)))
        try:
            mig.migrate(dsn, **{f"{role}_role": names[role] for role in ROLES})
            yield dsn, names
        finally:
            with psycopg.connect(dsn, autocommit=True) as db:
                for name in names.values():
                    db.execute(sql.SQL("ALTER ROLE {} NOSUPERUSER").format(sql.Identifier(name)))
                    db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(name)))
                    db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(name)))


def _as(dsn: str, role_name: str):
    import psycopg
    from psycopg.conninfo import make_conninfo

    db = psycopg.connect(make_conninfo(dsn, user=role_name))
    assert db.execute("SELECT current_user").fetchone()[0] == role_name
    db.rollback()
    return db


def _catalog(dsn: str) -> tuple[dict[str, str], list[str]]:
    """({table or view: its first column}, [sequences]) of the schema, from the catalog: `schema_migrations`
    and anything a migration made outside `GRANTS` are included."""
    import psycopg

    q = (
        "SELECT c.relname, c.relkind, (SELECT a.attname FROM pg_attribute a WHERE a.attrelid = c.oid "
        "AND a.attnum > 0 AND NOT a.attisdropped ORDER BY a.attnum LIMIT 1) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        "WHERE n.nspname = current_schema() AND c.relkind IN ('r','p','v','m','f','S')"
    )
    with psycopg.connect(dsn, autocommit=True) as db:
        rows = db.execute(q).fetchall()
    return (
        {name: column for name, kind, column in rows if kind != "S"},
        [name for name, kind, _ in rows if kind == "S"],
    )


def _schema(dsn: str) -> str:
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute("SELECT current_schema()").fetchone()[0]


def _statements(schema: str, table: str, column: str) -> dict:
    """Schema-qualified, so a role with no right on the schema is refused ("permission denied for schema")
    instead of not finding the table through its search path."""
    from psycopg import sql

    t, c = sql.Identifier(schema, table), sql.Identifier(column)
    return {
        "SELECT": sql.SQL("SELECT * FROM {}").format(t),
        "INSERT": sql.SQL("INSERT INTO {} DEFAULT VALUES").format(t),
        "UPDATE": sql.SQL("UPDATE {} SET {} = DEFAULT").format(t, c),
        "DELETE": sql.SQL("DELETE FROM {}").format(t),
        "TRUNCATE": sql.SQL("TRUNCATE {}").format(t),
    }


def _expected(role: str, relation: str) -> set[str]:
    grant = mig.GRANTS.get(relation)
    return HOLDS[role](grant) if (grant and role in HOLDS) else set()


def _refused(db, statement, params=()) -> None:
    """The database itself says no, for a missing privilege and for no other reason."""
    import psycopg

    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        db.execute(statement, params)
    db.rollback()


# What ON means, written by hand for each tree and read by the schema OWNER (not by the code under test).
_ON_BEFORE_STEP_B = 'SELECT COALESCE((SELECT "on" FROM kill_switch WHERE id = 1), true)'
_ON_AFTER_STEP_B = (
    'SELECT COALESCE((SELECT "on" FROM kill_switch WHERE id = 1), true) '
    "OR EXISTS (SELECT 1 FROM kill_switch_stops s WHERE NOT EXISTS "
    "(SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id))"
)
# How the runtime identity switches the stop ON, as one statement, for each tree.
_STOP_BEFORE_STEP_B = 'UPDATE kill_switch SET "on" = true, "by" = %s, ts = now() WHERE id = 1'
_STOP_AFTER_STEP_B = 'INSERT INTO kill_switch_stops ("by") VALUES (%s)'
_STOP = _STOP_AFTER_STEP_B if STEP_B else _STOP_BEFORE_STEP_B


def _stop_is_on(dsn: str) -> bool:
    import psycopg

    with psycopg.connect(dsn, autocommit=True) as db:
        return db.execute(_ON_AFTER_STEP_B if STEP_B else _ON_BEFORE_STEP_B).fetchone()[0]


class _World:
    """The schema of `identities` plus what the step-B cases need: owner statements and the real store and
    chain audit under one identity's own login. Every store it builds is closed by the fixture."""

    def __init__(self, dsn: str, names: dict[str, str]):
        self.dsn, self.names, self.stores = dsn, names, []

    def dsn_of(self, role: str) -> str:
        from psycopg.conninfo import make_conninfo

        return make_conninfo(self.dsn, user=self.names[role])

    def owner(self, statement, params=()) -> list:
        import psycopg

        with psycopg.connect(self.dsn, autocommit=True) as db:
            cur = db.execute(statement, params)
            return cur.fetchall() if cur.description else []

    def grant(self, text: str, *roles: str) -> None:
        """An owner-side GRANT, REVOKE or ALTER; each `{}` is the login name of one identity."""
        from psycopg import sql

        self.owner(sql.SQL(text).format(*(sql.Identifier(self.names[r]) for r in roles)))

    def store(self, role: str):
        from hadavin_sdk.actions.secrets import FakeSecretProvider
        from hadavin_sdk.backends.factory import make
        from hadavin_sdk.backends.table import PostgresSettings

        store = make(
            "store",
            PostgresSettings(**STORE_SETTINGS),
            FakeSecretProvider({STORE_SETTINGS["dsn_secret_name"]: self.dsn_of(role)}),
        )
        self.stores.append(store)
        assert store._db.execute("SELECT current_user").fetchone()[0] == self.names[role]
        return store

    def audit(self, store):
        from hadavin_sdk.backends.factory import make
        from hadavin_sdk.backends.table import ChainSettings

        return make("audit", ChainSettings(kind="chain"), store=store, signer=None, anchor=None)

    def on(self) -> bool:
        return _stop_is_on(self.dsn)

    def reads_on(self) -> KillSwitch:
        """The stop state as the code reads it, on a NEW connection of the runtime login."""
        return self.store("runtime").get_kill_switch()

    def count(self, table: str) -> int:
        from psycopg import sql

        return self.owner(sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table)))[0][0]

    def kinds(self) -> list[str]:
        return [row[0] for row in self.owner("SELECT kind FROM audit_entries ORDER BY seq")]

    def can(self, role: str, table: str, privilege: str) -> bool:
        q = "SELECT has_table_privilege(%s, %s, %s)"
        return self.owner(q, (self.names[role], table, privilege))[0][0]


@pytest.fixture
def world(identities):
    w = _World(*identities)
    try:
        yield w
    finally:
        for store in w.stores:
            store._db.close()


@pytest.mark.parametrize("role", [*ROLES, "stranger"])
def test_pg_each_role_is_refused_what_the_map_does_not_give(identities, role):
    """One real statement per cell, connected AS the role. Every statement is rolled back. A cell the map
    gives must get past the privilege check (it may fail later on a constraint or a trigger: not our subject),
    which also proves a refusal is about the table and not about a missing right on the schema."""
    import psycopg

    dsn, names = identities
    tables, _ = _catalog(dsn)
    schema = _schema(dsn)
    assert set(_tables()) <= set(tables) and "schema_migrations" in tables
    wrong, refused, passed = [], 0, 0
    with _as(dsn, names[role]) as db:
        for table, column in sorted(tables.items()):
            for privilege, statement in _statements(schema, table, column).items():
                try:
                    db.execute(statement)
                    denied = False
                except psycopg.errors.InsufficientPrivilege:
                    denied = True
                except psycopg.Error:
                    denied = False  # past the privilege check; stopped by a constraint or a trigger
                finally:
                    db.rollback()
                if denied == (privilege in _expected(role, table)):
                    wrong.append(
                        f"{role} {privilege} {table}: {'refused' if denied else 'allowed'}"
                    )
                refused, passed = refused + denied, passed + (not denied)
    assert wrong == []
    assert refused + passed == len(tables) * len(PRIVILEGES)
    assert refused >= len(tables)  # TRUNCATE at least, on every table
    if role in ("runtime", "portal", "reset"):
        assert passed > 0
    if role == "stranger":
        assert passed == 0


def test_pg_the_catalog_agrees_with_the_matrix_for_every_relation_of_the_schema(identities):
    """`has_table_privilege` (direct, inherited and PUBLIC grants) for the five privileges plus REFERENCES and
    TRIGGER, on every relation of the schema, with all the roles granted together."""
    import psycopg

    dsn, names = identities
    tables, sequences = _catalog(dsn)
    wrong = []
    with psycopg.connect(dsn, autocommit=True) as db:
        for role, name in names.items():
            for table in tables:
                held = {
                    p
                    for p in mig._TABLE_PRIVS
                    if db.execute(
                        "SELECT has_table_privilege(%s, %s, %s)", (name, table, p)
                    ).fetchone()[0]
                }
                if held != _expected(role, table):
                    wrong.append(f"{role} on {table}: {sorted(held)}")
            for sequence in sequences:
                held = {
                    p
                    for p in ("USAGE", "SELECT", "UPDATE")
                    if db.execute(
                        "SELECT has_sequence_privilege(%s, %s, %s)", (name, sequence, p)
                    ).fetchone()[0]
                }
                if held != (_expected(role, sequence) if role == "runtime" else set()):
                    wrong.append(f"{role} on sequence {sequence}: {sorted(held)}")
        schema = db.execute("SELECT current_schema()").fetchone()[0]
        q = "SELECT has_schema_privilege(%s, %s, %s)"
        assert not db.execute(q, (names["stranger"], schema, "USAGE")).fetchone()[0]
        for role in ROLES:
            assert db.execute(q, (names[role], schema, "USAGE")).fetchone()[0], role
            assert not db.execute(q, (names[role], schema, "CREATE")).fetchone()[0], role
    assert wrong == []


@pytest.mark.parametrize("role", [r for r in (*ROLES, "stranger") if r != "runtime"])
def test_pg_only_the_runtime_role_may_draw_from_a_sequence(identities, role):
    dsn, names = identities
    _, sequences = _catalog(dsn)
    schema = _schema(dsn)
    assert sequences
    with _as(dsn, names[role]) as db:
        for sequence in sequences:
            _refused(db, "SELECT nextval(%s::regclass)", (f"{schema}.{sequence}",))


@pytest.mark.parametrize("role", ["portal", "purge"])  # the stranger: see the matrix test above
def test_pg_no_role_but_the_runtime_and_reset_role_can_read_or_write_the_stop_state(
    identities, role
):
    """Case 6: one statement per privilege on every relation of the stop state, and the catalog."""
    import psycopg

    dsn, names = identities
    tables, _ = _catalog(dsn)
    schema = _schema(dsn)
    assert set(STOP_RELATIONS) <= set(tables)  # a missing relation would prove nothing
    with _as(dsn, names[role]) as db:
        for relation in STOP_RELATIONS:
            for statement in _statements(schema, relation, tables[relation]).values():
                _refused(db, statement)
        _refused(db, 'SELECT "on" FROM kill_switch')
        _refused(db, 'UPDATE kill_switch SET "on" = false')
        _refused(
            db, 'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, false, now())'
        )
    with psycopg.connect(dsn, autocommit=True) as db:
        for relation in STOP_RELATIONS:
            for privilege in mig._TABLE_PRIVS:
                q = "SELECT has_table_privilege(%s, %s, %s)"
                assert not db.execute(q, (names[role], relation, privilege)).fetchone()[0]
            for privilege in ("SELECT", "INSERT", "UPDATE", "REFERENCES"):
                q = "SELECT has_any_column_privilege(%s, %s, %s)"
                assert not db.execute(q, (names[role], relation, privilege)).fetchone()[0]
    assert _stop_is_on(dsn) is False  # the seeded row, untouched


def test_pg_the_runtime_role_can_switch_the_stop_on(identities):
    """The emergency stop works with the runtime identity alone, with one statement. True on both trees."""
    dsn, names = identities
    assert _stop_is_on(dsn) is False
    with _as(dsn, names["runtime"]) as db:
        assert db.execute(_STOP, ("t",)).rowcount == 1
        db.commit()
    assert _stop_is_on(dsn) is True


def test_pg_the_runtime_role_cannot_remove_a_row_of_the_stop_state(identities):
    """A missing flag row reads as ON (fail closed), but a role that could delete rows could hide who
    stopped, and after step B deleting a stop row would be a reset."""
    from psycopg import sql

    dsn, names = identities
    with _as(dsn, names["runtime"]) as db:
        db.execute(_STOP, ("t",))
        db.commit()
        for relation in STOP_RELATIONS:
            _refused(db, sql.SQL("DELETE FROM {}").format(sql.Identifier(relation)))
            _refused(db, sql.SQL("TRUNCATE {} CASCADE").format(sql.Identifier(relation)))
    assert _stop_is_on(dsn) is True


def test_pg_case9_stop_by_the_runtime_role_works_with_the_audit_tables_refusing_writes(world):
    """The audit chain AND its outbox refuse the runtime login. The stop must still be ON afterwards, with
    its `by`, and `Limits.stop` must not raise (an emergency stop that reports a failure invites a retry
    loop, or a belief that nothing was stopped)."""
    store = world.store("runtime")
    audit = world.audit(store)
    world.grant("REVOKE INSERT ON audit_entries FROM {}", "runtime")
    world.grant("REVOKE INSERT ON audit_outbox FROM {}", "runtime")
    with _as(world.dsn, world.names["runtime"]) as db:
        _refused(db, "INSERT INTO audit_outbox DEFAULT VALUES")  # the audit really is refusing
    Limits(store, audit, None).stop(by="user:op")
    assert world.on() is True
    state = world.reads_on()
    assert (state.on, state.by) == (True, "user:op")
    assert world.count("audit_entries") == 0 and world.count("audit_outbox") == 0


def test_pg_case12_a_missing_stop_row_reads_as_on(world):
    assert world.reads_on().on is False
    world.owner("DELETE FROM kill_switch")
    assert world.count("kill_switch") == 0
    state = world.reads_on()
    assert state.on is True and state.by == "system:kill_switch_row_missing"
    assert world.on() is True


# --- step B: the runtime identity cannot switch the stop OFF (case 3) ----------------------------------
# Before step B these two are strict xfails: they say what must hold using only names that exist on main,
# and the day they pass without step B being detected, pytest reports that as a failure. After step B the
# condition is false and they are plain tests. raises=AssertionError: a renamed table or column is an ERROR,
# not a silent "still expected to fail".


@pytest.mark.xfail(not STEP_B, strict=True, raises=AssertionError, reason=_STEP_B_XFAIL)
def test_step_b_the_grant_map_gives_the_runtime_role_no_way_to_switch_the_stop_off():
    runtime = HOLDS["runtime"](mig.GRANTS[STOP_TABLE])
    assert "UPDATE" not in runtime
    assert runtime == {"SELECT"}  # no INSERT either: the upsert of the old code needs it


@pytest.mark.xfail(not STEP_B, strict=True, raises=AssertionError, reason=_STEP_B_XFAIL)
def test_pg_step_b_the_runtime_role_cannot_switch_the_stop_off(identities):
    """With the flag ON, the runtime identity tries both ways the old code had (a plain UPDATE, and the
    upsert). Whatever the database answers, the stop must still be ON afterwards."""
    import psycopg

    dsn, names = identities
    with psycopg.connect(dsn, autocommit=True) as db:
        db.execute('UPDATE kill_switch SET "on" = true WHERE id = 1')
    for statement in (
        'UPDATE kill_switch SET "on" = false WHERE id = 1',
        (
            'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, false, now()) '
            'ON CONFLICT (id) DO UPDATE SET "on" = EXCLUDED."on"'
        ),
    ):
        with _as(dsn, names["runtime"]) as db:
            try:
                db.execute(statement)
                db.commit()
            except psycopg.Error:
                db.rollback()  # refused: what step B wants
        assert _stop_is_on(dsn) is True, statement


# Every statement that would turn the switch from ON to OFF (or hide a stop) in the step-B shape.
RUNTIME_OFF_ATTEMPTS = (
    'UPDATE kill_switch SET "on" = false WHERE id = 1',
    'UPDATE kill_switch SET "on" = false',
    (
        'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (1, 1, false, now()) '
        'ON CONFLICT (id) DO UPDATE SET "on" = EXCLUDED."on"'
    ),
    'INSERT INTO kill_switch (id, schema_version, "on", ts) VALUES (2, 1, false, now())',
    "DELETE FROM kill_switch",
    "TRUNCATE kill_switch",
    "INSERT INTO kill_switch_clears (stop_id, \"by\") SELECT id, 'x' FROM kill_switch_stops",
    "INSERT INTO kill_switch_clears (stop_id) VALUES (gen_random_uuid())",
    "UPDATE kill_switch_clears SET \"by\" = 'x'",
    "DELETE FROM kill_switch_clears",
    "TRUNCATE kill_switch_clears",
    "UPDATE kill_switch_stops SET id = gen_random_uuid()",
    "UPDATE kill_switch_stops SET ts = now() + interval '100 years'",
    "DELETE FROM kill_switch_stops",
    "TRUNCATE kill_switch_stops CASCADE",
    "SELECT 1 FROM kill_switch_stops FOR UPDATE",  # a row lock needs UPDATE too
)


@needs_step_b
def test_pg_case3_every_way_to_switch_the_stop_off_is_refused_to_the_runtime_role(world):
    """The flag is ON and a stop is open. Each attempt, connected as the runtime login, is refused by the
    database for a missing privilege; the real store's reset is refused the same way; nothing changed."""
    import psycopg

    runtime = world.store("runtime")
    runtime.set_kill_switch(KillSwitch(on=True, by="ops:kept"))
    world.owner('UPDATE kill_switch SET "on" = true, "by" = %s WHERE id = 1', ("owner:flag",))
    with _as(world.dsn, world.names["runtime"]) as db:
        for statement in RUNTIME_OFF_ATTEMPTS:
            _refused(db, statement)
    with pytest.raises(psycopg.errors.InsufficientPrivilege):
        runtime.set_kill_switch(KillSwitch(on=False, by="agent:hostile"))
    assert world.on() is True
    assert world.owner('SELECT "on", "by" FROM kill_switch') == [(True, "owner:flag")]
    assert world.owner('SELECT "by" FROM kill_switch_stops') == [("ops:kept",)]
    assert world.count("kill_switch_clears") == 0
    # and with the flag off, the open stop alone keeps it ON for the code that reads it
    world.owner('UPDATE kill_switch SET "on" = false WHERE id = 1')
    state = world.reads_on()
    assert (state.on, state.by) == (True, "ops:kept")


# --- step B: the reset identity (cases 1, 2, 4, 5, 7, 8, 11, 12) -----------------------------------------


@needs_step_b
@pytest.mark.parametrize("other", ["runtime", "portal", "purge"])
@pytest.mark.parametrize("direction", ["reset_is_member", "other_is_member"])
def test_pg_case1_migrate_refuses_membership_between_the_reset_role_and_another_identity(
    world, other, direction
):
    """A member keeps the other role's rights whatever is revoked: the reset role inside the runtime role
    could no longer be told apart, and the runtime role inside the reset role could reset."""
    group, member = ("reset", other) if direction == "other_is_member" else (other, "reset")
    world.grant("GRANT {} TO {}", group, member)
    with pytest.raises(ConfigError, match="members of each other"):
        mig.migrate(world.dsn, **{f"{role}_role": world.names[role] for role in ROLES})


@needs_step_b
def test_pg_case2_the_reset_role_is_refused_everything_outside_its_reviewed_cells(world):
    """Connected as the reset login. On the 13 tables of RESET_NEVER (and the migration ledger) every one of
    the five statements is refused; on its own five tables every cell RESET_HOLDS does not name is refused.
    The catalog agrees, column grants included. Then the cells it holds are shown to work."""
    tables, sequences = _catalog(world.dsn)
    schema = _schema(world.dsn)
    assert set(RESET_NEVER) <= set(tables) and set(RESET_HOLDS) <= set(tables)
    assert set(tables) == {*RESET_NEVER, *RESET_HOLDS, "schema_migrations"}
    refused = 0
    with _as(world.dsn, world.names["reset"]) as db:
        for table in sorted(tables):
            for privilege, statement in _statements(schema, table, tables[table]).items():
                if privilege not in RESET_HOLDS.get(table, set()):
                    _refused(db, statement)
                    refused += 1
        _refused(db, 'INSERT INTO kill_switch_stops ("by") VALUES (%s)', ("reset",))  # cannot stop
        _refused(db, "SELECT count(*) FROM redaction_maps")  # not even a count of the evidence
        for sequence in sequences:
            _refused(db, "SELECT nextval(%s::regclass)", (f"{schema}.{sequence}",))
        # what it holds gets past the privilege check
        assert db.execute('SELECT "on" FROM kill_switch').fetchall() == [(False,)]
        assert db.execute("SELECT count(*) FROM kill_switch_stops").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM kill_switch_clears").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM audit_entries").fetchone()[0] == 0
        assert db.execute("SELECT count(*) FROM audit_checkpoints").fetchone()[0] == 0
    assert refused == len(tables) * len(PRIVILEGES) - sum(len(p) for p in RESET_HOLDS.values())
    for table in tables:
        held = {p for p in mig._TABLE_PRIVS if world.can("reset", table, p)}
        assert held == RESET_HOLDS.get(table, set()), table
        if table not in RESET_HOLDS:
            for privilege in ("SELECT", "INSERT", "UPDATE", "REFERENCES"):
                q = "SELECT has_any_column_privilege(%s, %s, %s)"
                assert not world.owner(q, (world.names["reset"], table, privilege))[0][0], table


@needs_step_b
def test_pg_case4_the_reset_role_switches_the_stop_off_and_the_runtime_role_can_stop_again(world):
    """First by hand, with only the statements its grants are for (so the grants are enough, whatever the
    store does); then through the real store under the reset login."""
    runtime = world.store("runtime")
    runtime.set_kill_switch(KillSwitch(on=True, by="ops:a"))
    runtime.set_kill_switch(KillSwitch(on=True, by="ops:b"))
    world.owner('UPDATE kill_switch SET "on" = true WHERE id = 1')
    assert world.on() is True and world.reads_on().on is True
    with _as(world.dsn, world.names["reset"]) as db:
        done = db.execute('UPDATE kill_switch SET "on" = false, "by" = %s WHERE id = 1', ("op",))
        assert done.rowcount == 1
        done = db.execute(
            'INSERT INTO kill_switch_clears (stop_id, "by") SELECT s.id, %s FROM kill_switch_stops s '
            "WHERE NOT EXISTS (SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id)",
            ("op",),
        )
        assert done.rowcount == 2
        db.commit()
    assert world.on() is False and world.reads_on().on is False
    # the runtime identity can stop again, with one statement, and the stop is open again
    with _as(world.dsn, world.names["runtime"]) as db:
        assert db.execute(_STOP, ("ops:later",)).rowcount == 1
        db.commit()
    state = world.reads_on()
    assert world.on() is True and (state.on, state.by) == (True, "ops:later")
    world.store("reset").set_kill_switch(KillSwitch(on=False, by="op:again"))
    assert world.on() is False and world.reads_on().on is False
    assert world.count("kill_switch_stops") == 3 and world.count("kill_switch_clears") == 3


@needs_step_b
def test_pg_case5_the_reset_role_appends_its_audit_intent_and_can_change_no_audit_row(world):
    """`Limits.reset` on a store and a chain audit that both hold ONLY the reset login's connection."""
    world.store("runtime").set_kill_switch(KillSwitch(on=True, by="ops:a"))
    reset = world.store("reset")
    Limits(reset, world.audit(reset), None).reset(by="user:op")
    assert world.kinds() == ["limits.reset"]  # the intent, written by the reset login itself
    assert world.on() is False
    assert world.count("audit_checkpoints") == 0  # it signs nothing
    with _as(world.dsn, world.names["reset"]) as db:
        for statement in (
            "UPDATE audit_entries SET kind = 'x'",
            "DELETE FROM audit_entries",
            "TRUNCATE audit_entries",
            "INSERT INTO audit_checkpoints DEFAULT VALUES",
            "UPDATE audit_checkpoints SET seq = 0",
            "DELETE FROM audit_checkpoints",
            "TRUNCATE audit_checkpoints",
            "SELECT * FROM audit_outbox",
            "INSERT INTO audit_outbox DEFAULT VALUES",
            "DELETE FROM audit_outbox",
        ):
            _refused(db, statement)
    assert world.kinds() == ["limits.reset"]


def _cli_secrets(world, monkeypatch, held: dict[str, str]) -> list:
    """The secrets kind of the CLI answers from `held`; everything else is the real thing. Returns the list
    of stores the CLI built (closed by the `world` fixture)."""
    from hadavin_sdk import cli
    from hadavin_sdk.actions.secrets import FakeSecretProvider

    real, built = cli.make, []

    def fake(capability, settings, *args, **kwargs):
        if capability == "secrets":
            return FakeSecretProvider(dict(held))
        made = real(capability, settings, *args, **kwargs)
        if capability == "store":
            built.append(made)
            world.stores.append(made)
        return made

    monkeypatch.setattr(cli, "make", fake)
    return built


@needs_step_b
def test_pg_case7_limits_reset_with_the_runtime_login_ends_in_an_error_and_the_stop_stays_on(
    world, tmp_path, monkeypatch, capsys
):
    """The secret the reset ref names holds the RUNTIME login (a copied secret, or an attacker's config).
    The command must fail, say so, leave the stop ON, and the audit holds the attempt and its failure."""
    world.store("runtime").set_kill_switch(KillSwitch(on=True, by="ops:kept"))
    cfg = _pilot_config(tmp_path, RESET_REF)
    built = _cli_secrets(world, monkeypatch, {RESET_REF: world.dsn_of("runtime")})
    assert _limits_reset(cfg, "agent:hostile") == 2
    err = capsys.readouterr().err
    assert "NOT reset" in err and "InsufficientPrivilege" in err and "Traceback" not in err
    assert len(built) == 1
    assert built[0]._db.execute("SELECT current_user").fetchone()[0] == world.names["runtime"]
    assert world.on() is True
    state = world.reads_on()
    assert (state.on, state.by) == (True, "ops:kept")
    assert world.count("kill_switch_clears") == 0
    assert world.kinds() == ["limits.reset", "limits.reset_failed"]


@needs_step_b
def test_pg_case7_limits_reset_with_the_reset_dsn_works_and_runs_as_the_reset_login(
    world, tmp_path, monkeypatch, capsys
):
    """The provider holds ONLY the reset login: a reset that needed the runtime DSN could not even start."""
    world.store("runtime").set_kill_switch(KillSwitch(on=True, by="ops:a"))
    cfg = _pilot_config(tmp_path, RESET_REF)
    built = _cli_secrets(world, monkeypatch, {RESET_REF: world.dsn_of("reset")})
    assert _limits_reset(cfg, "user:op") == 0
    assert "kill switch OFF" in capsys.readouterr().out
    assert len(built) == 1
    assert built[0]._db.execute("SELECT current_user").fetchone()[0] == world.names["reset"]
    assert world.on() is False and world.reads_on().on is False
    assert world.owner('SELECT "by" FROM kill_switch_clears') == [("user:op",)]
    assert world.kinds() == ["limits.reset"]


@needs_step_b
def test_pg_case8_reset_with_the_audit_intent_refused_leaves_the_stop_on(world):
    """Under the reset login, with the audit chain refusing its append: no audit intent, so no reset. The
    flag, the open stop and the clears are as before."""
    world.store("runtime").set_kill_switch(KillSwitch(on=True, by="ops:kept"))
    world.owner('UPDATE kill_switch SET "on" = true WHERE id = 1')
    reset = world.store("reset")
    audit = world.audit(reset)
    world.grant("REVOKE INSERT ON audit_entries FROM {}", "reset")
    with pytest.raises(AuditUnavailable):
        Limits(reset, audit, None).reset(by="user:op")
    assert world.kinds() == []
    assert world.count("kill_switch_clears") == 0
    assert world.owner('SELECT "on" FROM kill_switch') == [(True,)]
    assert world.on() is True and world.reads_on().on is True
    # and the rights to clear were there all along: with the audit back, the same call resets
    world.grant("GRANT INSERT ON audit_entries TO {}", "reset")
    Limits(reset, audit, None).reset(by="user:op")
    assert world.kinds() == ["limits.reset"] and world.on() is False


@needs_step_b
def test_pg_case11_migrate_again_takes_back_what_was_granted_by_hand_to_the_reset_role(world):
    extra = [
        ("kill_switch_clears", "DELETE"),
        ("kill_switch_stops", "INSERT"),
        ("audit_entries", "DELETE"),
        ("runs", "SELECT"),
        ("redaction_maps", "SELECT"),
        ("spend", "UPDATE"),
    ]
    for table, privilege in extra:
        world.grant(f"GRANT {privilege} ON {table} TO {{}}", "reset")
        assert world.can("reset", table, privilege)
    assert mig.migrate(world.dsn, **{f"{r}_role": world.names[r] for r in ROLES}) == []
    for table, privilege in extra:
        assert not world.can("reset", table, privilege), (table, privilege)
    tables, _ = _catalog(world.dsn)
    for table in tables:
        held = {p for p in mig._TABLE_PRIVS if world.can("reset", table, p)}
        assert held == RESET_HOLDS.get(table, set()), table


@needs_step_b
@pytest.mark.parametrize("how", ["superuser", "owns_a_relation", "can_create", "public_grant"])
def test_pg_case11_migrate_refuses_a_reset_role_that_holds_more_than_it_can_take_back(world, how):
    """What a REVOKE from the role cannot remove must stop migrate(), and the transaction rolls back."""
    if how == "superuser":
        world.grant("ALTER ROLE {} SUPERUSER", "reset")
        match = "members of each other|reset role holds more than the grant map.*superuser"
    elif how == "owns_a_relation":
        world.owner("CREATE TABLE stray (x INT)")
        world.grant("ALTER TABLE stray OWNER TO {}", "reset")
        match = "reset role holds more than the grant map.*owns stray"
    elif how == "can_create":
        from psycopg import sql

        world.owner(
            sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                sql.Identifier(_schema(world.dsn)), sql.Identifier(world.names["reset"])
            )
        )
        match = "reset role holds more than the grant map.*can CREATE in schema"
    else:
        world.owner("GRANT SELECT ON redaction_maps TO PUBLIC")
        match = "holds more than the grant map.*redaction_maps"
    try:
        with pytest.raises(ConfigError, match=match):
            mig.migrate(world.dsn, **{f"{r}_role": world.names[r] for r in ROLES})
    finally:
        if how == "superuser":
            world.grant("ALTER ROLE {} NOSUPERUSER", "reset")


@needs_step_b
def test_pg_case12_a_reset_cannot_turn_a_missing_stop_row_into_off(world):
    """The flag row is gone (a broken schema). It reads ON; a reset by the reset login fails loudly, is
    audited as failed, clears nothing, and it still reads ON."""
    world.store("runtime").set_kill_switch(KillSwitch(on=True, by="ops:a"))
    world.owner("DELETE FROM kill_switch")
    reset = world.store("reset")
    with pytest.raises(ConfigError, match="kill_switch row missing"):
        Limits(reset, world.audit(reset), None).reset(by="user:op")
    assert world.kinds() == ["limits.reset", "limits.reset_failed"]
    assert world.count("kill_switch_clears") == 0
    state = world.reads_on()
    assert state.on is True and world.on() is True
