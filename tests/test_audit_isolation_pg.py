"""M1 (xr-abc-lead-1): two writers on the audit chain under a role whose default isolation is REPEATABLE READ.
The session pins READ COMMITTED, so the advisory-lock wait ends with a fresh snapshot: no duplicate seq (23505) and
no guard violation (23514), nothing is quarantined. Needs HADAVIN_TEST_PG_DSN (skipped without it)."""

from __future__ import annotations

import datetime as dt
import os
import threading

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("cryptography")

import psycopg
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from hadavin_sdk.audit import chain as audit
from hadavin_sdk.audit.signer import LocalSigner
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.store import postgres
from tests.contracts.kinds.store_postgres import pg_schema

N = 15


def _event(tag, i):
    ts = dt.datetime(2026, 1, 1, tzinfo=dt.UTC) + dt.timedelta(seconds=i)
    return AuditEvent(
        run_id=f"run-{tag}", domain="step", principal="p", source="s", result="ok",
        operation=f"{tag}{i}", ts=ts,
    )  # fmt: skip


def test_the_isolation_is_one_of_the_read_back_pins():
    assert ("default_transaction_isolation", "'read committed'") in postgres._SESSION_PINS


def test_two_writers_under_a_repeatable_read_role_default_leave_one_gapless_chain():
    admin = os.environ.get("HADAVIN_TEST_PG_DSN")
    for dsn in pg_schema(runtime=True):
        role = conninfo_to_dict(dsn)["user"]
        with psycopg.connect(admin, autocommit=True) as db:
            dbname = db.execute("SELECT current_database()").fetchone()[0]
            db.execute(
                sql.SQL(
                    "ALTER ROLE {} IN DATABASE {} SET default_transaction_isolation = 'repeatable read'"
                ).format(sql.Identifier(role), sql.Identifier(dbname))
            )
        try:
            conns = [postgres.connect(dsn) for _ in range(2)]
            try:
                for c in conns:
                    assert c.execute("SHOW transaction_isolation").fetchone()[0] == "read committed"
                schema = conns[0].execute("SELECT current_schema()").fetchone()[0]
                signer = LocalSigner(Ed25519PrivateKey.generate())
                logs = [
                    audit.ChainAudit(
                        audit._Db(c, threading.Lock(), pg=True, schema=schema), signer, None, 1000
                    )
                    for c in conns
                ]
                errors: list[BaseException] = []

                def work(log, tag, errors=errors):
                    try:
                        for i in range(N):
                            log.write_intent(_event(tag, i))
                    except BaseException as exc:  # noqa: BLE001
                        errors.append(exc)

                threads = [
                    threading.Thread(target=work, args=(log, tag))
                    for log, tag in zip(logs, "ab", strict=True)
                ]
                for t in threads:
                    t.start()
                for t in threads:
                    t.join(timeout=60)
                assert not errors, errors
                seqs = [r[0] for r in logs[0]._db.run("SELECT seq FROM audit_entries ORDER BY seq")]
                assert seqs == list(range(1, 2 * N + 1))
                assert logs[0]._db.run("SELECT count(*) FROM audit_outbox")[0][0] == 0
            finally:
                for c in conns:
                    c.close()
        finally:
            with psycopg.connect(admin, autocommit=True) as db:
                db.execute(
                    sql.SQL(
                        "ALTER ROLE {} IN DATABASE {} RESET default_transaction_isolation"
                    ).format(sql.Identifier(role), sql.Identifier(dbname))
                )
