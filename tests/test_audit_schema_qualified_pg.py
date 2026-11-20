"""A9 (ORDER 021 M3): every statement of the postgres chain kind names the schema of the migrated tables. The chain
runs here in a non-default schema with search_path=<schema>,public, and a decoy set of the three table names sits in
public and in pg_temp (the session's temporary schema is searched FIRST for an unqualified name). The decoys must
stay unchanged. Needs HADAVIN_TEST_PG_DSN (skipped without it)."""

from __future__ import annotations

import datetime as dt
import threading

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("cryptography")

import psycopg
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql
from psycopg.conninfo import make_conninfo

from hadavin_sdk.audit import chain as audit
from hadavin_sdk.audit.signer import LocalSigner
from hadavin_sdk.models import AuditEvent
from tests.contracts.kinds.store_postgres import pg_schema

NAMES = ("audit_entries", "audit_checkpoints", "audit_outbox")
EXPECTED = {"audit_entries": 3, "audit_checkpoints": 1, "audit_outbox": 0}


def _event(i, **kw):
    fields = {"run_id": "run-1", "domain": "step", "principal": "p", "source": "s", "result": "ok"}
    ts = dt.datetime(2026, 1, 1, tzinfo=dt.UTC) + dt.timedelta(seconds=i)
    return AuditEvent(operation=f"n{i}", ts=ts, **{**fields, **kw})


def _rel(where, name):
    return sql.SQL("{}.{}").format(sql.Identifier(where), sql.Identifier(name))


def _decoys(conn, schema):
    """Decoy tables of the three names in public and pg_temp, with grants, each outbox holding a sentinel row."""
    for n in NAMES:
        conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(_rel("public", n)))
    for where in ("public", "pg_temp"):
        for n in NAMES:
            conn.execute(
                sql.SQL("CREATE TABLE {} (LIKE {} INCLUDING DEFAULTS)").format(
                    _rel(where, n), _rel(schema, n)
                )
            )
            conn.execute(sql.SQL("GRANT ALL ON {} TO PUBLIC").format(_rel(where, n)))
    conn.execute("INSERT INTO public.audit_outbox (event_id, body) VALUES ('decoy-public', 'x')")
    conn.execute("INSERT INTO pg_temp.audit_outbox (event_id, body) VALUES ('decoy-temp', 'x')")


def _snapshot(conn):
    return {
        (where, n): sorted(
            conn.execute(sql.SQL("SELECT t::text FROM {} t").format(_rel(where, n))).fetchall()
        )
        for where in ("public", "pg_temp")
        for n in NAMES
    }


def _exercise(dsn, schema):
    """Run the chain; return (decoys before, decoys after, row counts of the real tables)."""
    conn = psycopg.connect(
        make_conninfo(dsn, options=f"-c search_path={schema},public"), autocommit=True
    )
    try:
        got = conn.execute("SELECT current_schema()").fetchone()[0]
        assert got == schema
        signer = LocalSigner(Ed25519PrivateKey.generate())
        log = audit.ChainAudit(
            audit._Db(conn, threading.Lock(), pg=True, schema=got), signer, None, 100
        )
        _decoys(conn, schema)
        before = _snapshot(conn)
        log.write_intent(_event(1))
        log.write_outcome(_event(2))
        parked = _event(3)
        log._db.run(
            "INSERT INTO audit_outbox (event_id, body) VALUES (?, ?)",
            (parked.event_id, parked.model_dump_json()),
        )
        assert log.reconcile() == 1
        assert log.checkpoint() == 3
        assert log.verify().ok
        after = _snapshot(conn)
        real = {
            n: conn.execute(sql.SQL("SELECT count(*) FROM {}").format(_rel(schema, n))).fetchone()[
                0
            ]
            for n in NAMES
        }
        return before, after, real
    finally:
        for n in NAMES:  # public outlives the test schema
            conn.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(_rel("public", n)))
        conn.close()


def _schema_of(dsn):
    return dsn.split("search_path=")[1].split()[0].strip("'")


def test_the_chain_in_a_non_default_schema_leaves_decoy_tables_in_public_and_pg_temp_unchanged():
    for dsn in pg_schema():
        before, after, real = _exercise(dsn, _schema_of(dsn))
        assert after == before  # both decoy sets untouched
        assert real == EXPECTED


def test_unqualified_names_fail_this_test(monkeypatch):
    """The mutant: the statements are not qualified. The same run then fails or touches a decoy."""
    monkeypatch.setattr(
        audit._Db, "_t", lambda self, text: text.replace("?", "%s") if self.pg else text
    )
    for dsn in pg_schema():
        try:
            before, after, real = _exercise(dsn, _schema_of(dsn))
        except Exception:  # noqa: BLE001 - failing is the expected outcome
            return
        assert after != before or real != EXPECTED
