"""The checkpoint role and the outbox functions (handover/core-b/tickets/A-audit-rights-review-1.md), against a real
PostgreSQL through real non-superuser logins. Needs HADAVIN_TEST_PG_DSN; skipped without it. The mutants of
tests/audit_rights_mutants.py name the tests below as their killers."""

from __future__ import annotations

import os
import re

import pytest

pytest.importorskip("psycopg", reason="needs hadavin-sdk[pg]")

import psycopg
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import errors, sql

from hadavin_sdk import defaults
from hadavin_sdk.audit import chain as audit
from hadavin_sdk.audit.signer import LocalSigner
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import AuditEvent
from tests.test_stop_state_roles import World

pytestmark = pytest.mark.skipif(
    not os.environ.get("HADAVIN_TEST_PG_DSN"),
    reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)",
)

PREFIX = defaults.AUDIT_QUARANTINE_PREFIX
DONE = "hadavin_audit_outbox_done"
QUARANTINE = "hadavin_audit_outbox_quarantine"


def _teardown(w: World) -> None:
    for s in w.stores:
        s._db.close()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        for schema in w.schemas:
            db.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
        for r in w.roles:
            db.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
            db.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)))


@pytest.fixture(scope="module", name="w")
def world():
    w = World()
    with psycopg.connect(w.dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(w.schema)))
        for r in w.roles:
            db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(r)))
    try:
        w.migrate()
        yield w
    finally:
        _teardown(w)


def _event(i: int, event_id: str | None = None) -> AuditEvent:
    kw = {"event_id": event_id} if event_id else {}
    return AuditEvent(
        run_id="run-1",
        domain="step",
        operation=f"n{i}",
        principal="p",
        source="s",
        result="ok",
        **kw,
    )


def _chain(w: World, signer=None, checkpoint: bool = False, every: int = 1) -> audit.ChainAudit:
    """A ChainAudit on the runtime login (and, with `checkpoint`, the checkpoint login for the signed rows)."""
    rt = w.store(w.runtime)
    db = audit._Db(rt._db, rt._lock, pg=True, schema=w.schema)
    cdb = None
    if checkpoint:
        ck = w.store(w.checkpoint)
        cdb = audit._Db(ck._db, ck._lock, pg=True, schema=w.schema)
    return audit.ChainAudit(db, signer, None, every, checkpoint_db=cdb)


def _can(w: World, role: str, table: str, priv: str) -> bool:
    return w.run("SELECT has_table_privilege(%s, %s, %s)", (role, f"{w.schema}.{table}", priv))[0][
        0
    ]


def _park(w: World, event_id: str, body: str) -> None:
    with w.admin() as db:
        db.execute(
            "INSERT INTO audit_outbox (event_id, body) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (event_id, body),
        )


def _outbox(w: World) -> set[str]:
    return {r[0] for r in w.run("SELECT event_id FROM audit_outbox")}


def _as_runtime(w: World, statement: str, params=()):
    with w.as_(w.runtime, autocommit=True) as db:
        return db.execute(statement, params).fetchall()


# --- the checkpoint login ---------------------------------------------------------------------------------------------


def test_the_checkpoint_role_holds_only_the_checkpoint_write_and_the_chain_read(w):
    want = {
        "audit_entries": {"SELECT"},
        "audit_checkpoints": {"SELECT", "INSERT"},
        "audit_outbox": set(),
    }
    for table, privs in want.items():
        for priv in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            assert _can(w, w.checkpoint, table, priv) is (priv in privs), (table, priv)
    others = w.rights(w.checkpoint)
    assert {k for k, v in others.items() if v} == set(want) - {"audit_outbox"}


def test_a_checkpoint_written_by_the_checkpoint_login_verifies(w):
    log = _chain(w, LocalSigner(Ed25519PrivateKey.generate()), checkpoint=True, every=1)
    for i in range(3):
        log.write_intent(_event(i))
    # The runtime login never attempts a checkpoint: nothing is signed until the tick step runs.
    assert w.run("SELECT COUNT(*) FROM audit_checkpoints")[0][0] == 0
    assert log.checkpoint() == 3
    assert w.run("SELECT seq, hash FROM audit_checkpoints")[0][0] == 3
    assert log.verify().ok


def test_the_runtime_login_cannot_write_a_checkpoint(w):
    with pytest.raises(errors.InsufficientPrivilege):
        _as_runtime(
            w,
            "INSERT INTO audit_checkpoints (seq, hash, signature) "
            "SELECT seq, hash, 'planted' FROM audit_entries ORDER BY seq DESC LIMIT 1",
        )


def test_the_inline_checkpoint_is_skipped_when_the_checkpoint_login_is_set(w):
    """With checkpoint_every = 1 every append would checkpoint inline: the runtime connection must not even try."""
    log = _chain(w, LocalSigner(Ed25519PrivateKey.generate()), checkpoint=True, every=1)
    seen: list[str] = []
    real = log._db.run
    log._db.run = lambda s, p=(): (seen.append(s), real(s, p))[1]
    log.write_intent(_event(10))
    assert not [s for s in seen if "audit_checkpoints" in s], seen


def test_without_a_checkpoint_login_the_inline_checkpoint_still_runs_on_the_one_db():
    log = audit.ChainAudit(
        audit._Db.memory(), LocalSigner(Ed25519PrivateKey.generate()), None, checkpoint_every=1
    )
    log.write_intent(_event(0))
    assert log.signed_through() == 1


# --- the outbox functions ---------------------------------------------------------------------------------------------


def test_the_runtime_has_no_delete_or_update_on_the_outbox_but_runs_both_functions(w):
    assert _can(w, w.runtime, "audit_outbox", "INSERT") and _can(
        w, w.runtime, "audit_outbox", "SELECT"
    )
    assert not _can(w, w.runtime, "audit_outbox", "DELETE")
    assert not _can(w, w.runtime, "audit_outbox", "UPDATE")
    for fn, sig in ((DONE, "text"), (QUARANTINE, "text, text")):
        assert w.run(
            "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
            (w.runtime, f"{w.schema}.{fn}({sig})"),
        )[0][0]
        for role in (w.portal, w.purge, w.reset, w.caps, w.checkpoint):
            assert not w.run(
                "SELECT has_function_privilege(%s, %s, 'EXECUTE')",
                (role, f"{w.schema}.{fn}({sig})"),
            )[0][0], (role, fn)


def test_public_cannot_execute_the_outbox_functions(w):
    for sig in (f"{DONE}(text)", f"{QUARANTINE}(text, text)"):
        acl = w.run(
            "SELECT EXISTS (SELECT 1 FROM pg_proc p, aclexplode(p.proacl) a WHERE p.oid = %s::regprocedure "
            "AND a.grantee = 0)",
            (f"{w.schema}.{sig}",),
        )[0][0]
        assert not acl, sig


def test_the_outbox_functions_are_pinned_to_the_catalog_the_schema_and_the_temp_schema(w):
    for sig in (f"{DONE}(text)", f"{QUARANTINE}(text, text)"):
        cfg, definer = w.run(
            "SELECT proconfig, prosecdef FROM pg_proc WHERE oid = %s::regprocedure",
            (f"{w.schema}.{sig}",),
        )[0]
        assert definer is True
        assert cfg == [f"search_path=pg_catalog, {w.schema}, pg_temp"], cfg


def test_a_hand_reset_search_path_is_pinned_again_by_the_next_migrate(w):
    w.do(f"ALTER FUNCTION {DONE}(text) RESET search_path")
    assert w.migrate() == []
    cfg = w.run(
        "SELECT proconfig FROM pg_proc WHERE oid = %s::regprocedure", (f"{w.schema}.{DONE}(text)",)
    )[0][0]
    assert cfg == [f"search_path=pg_catalog, {w.schema}, pg_temp"]


def test_done_deletes_nothing_while_the_event_is_not_in_the_chain(w):
    _park(w, "ghost-1", "{}")
    assert _as_runtime(w, f"SELECT {DONE}('ghost-1')") == [(0,)]
    assert "ghost-1" in _outbox(w)
    # and a direct DELETE is the grant's refusal
    with pytest.raises(errors.InsufficientPrivilege):
        _as_runtime(w, "DELETE FROM audit_outbox WHERE event_id = 'ghost-1'")


def test_done_deletes_the_row_once_the_event_is_in_the_chain(w):
    log = _chain(w)
    log.write_intent(_event(20, event_id="in-chain-1"))
    _park(w, "in-chain-1", "{}")
    assert _as_runtime(w, f"SELECT {DONE}('in-chain-1')") == [(1,)]
    assert "in-chain-1" not in _outbox(w)
    assert _as_runtime(w, f"SELECT {DONE}('in-chain-1')") == [(0,)]


@pytest.mark.parametrize("bad", ["NULL", "''"])
def test_done_refuses_an_empty_or_null_id(w, bad):
    with pytest.raises(errors.InvalidParameterValue):
        _as_runtime(w, f"SELECT {DONE}({bad})")


def test_quarantine_renames_and_never_deletes(w):
    _park(w, "poison-1", '{"x": 1}')
    assert _as_runtime(w, f"SELECT {QUARANTINE}('poison-1', %s)", (PREFIX,)) == [(1,)]
    ids = _outbox(w)
    assert "poison-1" not in ids and PREFIX + "poison-1" in ids
    body = w.run("SELECT body FROM audit_outbox WHERE event_id = %s", (PREFIX + "poison-1",))[0][0]
    assert body == '{"x": 1}'
    # already under the prefix: not renamed again
    assert _as_runtime(w, f"SELECT {QUARANTINE}(%s, %s)", (PREFIX + "poison-1", PREFIX)) == [(0,)]
    # a rename onto an existing row is refused: it can never replace (hence remove) a parked event
    w.do(
        "INSERT INTO audit_outbox (event_id, body) VALUES ('poison-1', '{}') ON CONFLICT DO NOTHING"
    )
    assert _as_runtime(w, f"SELECT {QUARANTINE}('poison-1', %s)", (PREFIX,)) == [(0,)]
    assert {"poison-1", PREFIX + "poison-1"} <= _outbox(w)


@pytest.mark.parametrize("args", ["NULL, 'p'", "'', 'p'", "'a', NULL", "'a', ''"])
def test_quarantine_refuses_an_empty_or_null_argument(w, args):
    with pytest.raises(errors.InvalidParameterValue):
        _as_runtime(w, f"SELECT {QUARANTINE}({args})")


def test_the_chain_quarantines_through_the_function_on_the_runtime_login(w):
    log = _chain(w)
    event = _event(30, event_id="poison-2")
    _park(w, "poison-2", event.model_dump_json())
    assert log._quarantine(event, "poison-2") == 1
    ids = _outbox(w)
    assert "poison-2" not in ids and PREFIX + "poison-2" in ids


def test_the_chain_drains_a_parked_event_on_the_runtime_login(w):
    w.do(
        "DELETE FROM audit_outbox"
    )  # the cases above leave poison and unreadable rows that make reconcile report
    log = _chain(w)
    event = _event(31, event_id="parked-1")
    _park(w, "parked-1", event.model_dump_json())
    assert log.reconcile() >= 1
    assert "parked-1" not in _outbox(w)
    assert "parked-1" in {e.event_id for e in log.events()}


# --- owner and membership refusals ------------------------------------------------------------------------------------


def _owner_of(w: World, table: str) -> str:
    return w.run(
        "SELECT tableowner FROM pg_tables WHERE schemaname = %s AND tablename = %s",
        (w.schema, table),
    )[0][0]


@pytest.mark.parametrize("table", ["audit_entries", "audit_checkpoints", "audit_outbox"])
def test_migrate_refuses_a_checkpoint_login_that_owns_an_audit_table(w, table):
    owner = _owner_of(w, table)
    w.grant(f"ALTER TABLE {table} OWNER TO {{}}", w.checkpoint)
    try:
        with pytest.raises(ConfigError, match=re.escape(table)):
            w.migrate()
    finally:
        w.grant(f"ALTER TABLE {table} OWNER TO {{}}", owner)
    assert w.migrate() == []


def test_migrate_refuses_a_checkpoint_login_that_is_a_member_of_the_owner_role(w):
    owner = _owner_of(w, "audit_entries")
    w.grant("GRANT {} TO {}", owner, w.checkpoint)
    try:
        with pytest.raises(ConfigError, match=rf"{w.checkpoint} is a member of {owner}"):
            w.migrate()
    finally:
        w.grant("REVOKE {} FROM {}", owner, w.checkpoint)
    assert w.migrate() == []


def test_migrate_refuses_the_checkpoint_role_named_twice(w):
    with pytest.raises(ConfigError, match="must be different roles"):
        w.migrate(checkpoint_role=w.runtime)


def test_migrate_takes_a_hand_grant_back_from_the_checkpoint_role(w):
    for priv, table in (
        ("UPDATE", "audit_checkpoints"),
        ("INSERT", "audit_entries"),
        ("DELETE", "audit_checkpoints"),
    ):
        w.grant(f"GRANT {priv} ON TABLE {table} TO {{}}", w.checkpoint)
        assert w.migrate() == []
        assert not _can(w, w.checkpoint, table, priv), (table, priv)
