# ruff: noqa: S608
"""P2 harm check against a REAL PostgreSQL (HADAVIN_TEST_PG_DSN: the CI service, or a local container).

Every ATTACK is run, unvalidated, as the administrator of a scratch database, to prove it would have done harm
(its `harm` tag in corpus.py), and is then shown to be refused by the validator. Attacks tagged `pg-refuses` are
the honest exception: PostgreSQL raises an error for them itself, so the validator is defence in depth there, and
this test proves that too instead of claiming harm.

Run as the superuser on purpose: it is the "what if the validator and the role both failed" case. Each harmful
statement runs in its own throwaway copy of the database (CREATE DATABASE ... TEMPLATE), so one cannot spoil the next.
"""

import secrets
from collections.abc import Iterator

import psycopg
import pytest
from askdata.validate import Rejected, validate
from psycopg.conninfo import make_conninfo

from tests.demo_askdata.attackrun import outcome
from tests.demo_askdata.conftest import Db
from tests.demo_askdata.corpus import ATTACKS, Attack

HARMFUL = [a for a in ATTACKS if a.harm != "none"]
EVIL_ROLE = "askdata_p2_evil"
TIMEOUT_MS = 1200


@pytest.fixture(scope="module")
def template(make_db) -> Iterator[Db]:
    """Schema, seed, views, the scratch schema, a purge procedure, and the dblink extension."""
    d = make_db(apply_roles=False)
    with d.admin() as conn:
        conn.execute("CREATE EXTENSION IF NOT EXISTS dblink")
        conn.execute("CREATE PROCEDURE shop.purge() LANGUAGE sql AS 'DELETE FROM shop.order_items'")
    yield d
    with d.admin() as conn:
        conn.execute(f'DROP ROLE IF EXISTS "{EVIL_ROLE}"')


@pytest.fixture
def maint_dsn(template: Db) -> str:
    return make_conninfo(template.admin_dsn, dbname="postgres")


@pytest.fixture
def clone(template: Db, maint_dsn: str) -> Iterator[str]:
    """A fresh database copied from the template; dropped afterwards. Yields its admin DSN."""
    name = "askdata_h_" + secrets.token_hex(4)
    with psycopg.connect(maint_dsn, autocommit=True) as c:
        c.execute(f'DROP ROLE IF EXISTS "{EVIL_ROLE}"')
        c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{template.name}"')
    yield make_conninfo(template.admin_dsn, dbname=name)
    with psycopg.connect(maint_dsn, autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        c.execute(f'DROP ROLE IF EXISTS "{EVIL_ROLE}"')


_TABLES = ("customers", "products", "orders", "order_items")


def fingerprint(dsn: str) -> tuple:
    """What a write could change: relations and columns and ACLs, row contents, roles, large objects."""
    with psycopg.connect(dsn, autocommit=True) as c:
        rels = c.execute(
            "SELECT coalesce(string_agg(n.nspname || '.' || c.relname || ':' || c.relkind::text || ':' || coalesce(c.relacl::text, ''),"
            " ',' ORDER BY n.nspname, c.relname), '') FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace"
            " WHERE n.nspname IN ('shop', 'public', 'scratch', 'analytics')"
        ).fetchone()[0]
        cols = c.execute(
            "SELECT coalesce(string_agg(c.relname || '.' || a.attname, ',' ORDER BY c.relname, a.attnum), '') FROM pg_attribute a"
            " JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace"
            " WHERE n.nspname IN ('shop', 'public', 'scratch') AND a.attnum > 0 AND NOT a.attisdropped AND c.relkind IN ('r', 'v')"
        ).fetchone()[0]
        rows = []
        for t in _TABLES:
            if c.execute("SELECT to_regclass(%s)", (f"shop.{t}",)).fetchone()[0] is None:
                rows.append("missing")
            else:
                rows.append(
                    c.execute(
                        f"SELECT md5(coalesce(string_agg(t::text, '|' ORDER BY t::text), '')) FROM shop.{t} t"
                    ).fetchone()[0]
                )
        roles = c.execute(
            "SELECT coalesce(string_agg(rolname, ',' ORDER BY rolname), '') FROM pg_roles"
        ).fetchone()[0]
        lobjects = c.execute("SELECT count(*) FROM pg_largeobject_metadata").fetchone()[0]
        procs = c.execute(
            "SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname IN ('shop', 'public')"
        ).fetchone()[0]
    return rels, cols, tuple(rows), roles, lobjects, procs


def _cells(cur) -> list[str]:
    return [
        str(v) for row in (cur.fetchall() if cur.description else []) for v in row if v is not None
    ]


def prove_harm(attack: Attack, dsn: str) -> str:
    """Run the attack unvalidated on a privileged session; return a short note of the harm observed, or raise."""
    kind, _, needle = attack.harm.partition(":")
    if kind == "write":
        before = fingerprint(dsn)
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(attack.sql)  # simple protocol: a stacked string runs whole
        after = fingerprint(dsn)
        assert before != after, "the statement ran but changed nothing"
        return "committed state changed"
    if kind == "lock":
        with psycopg.connect(dsn) as c:
            c.execute(attack.sql)
            modes = {
                r[0]
                for r in c.execute(
                    "SELECT mode FROM pg_locks WHERE pid = pg_backend_pid() AND locktype = 'relation'"
                    " AND relation = 'shop.orders'::regclass"
                )
            }
            c.rollback()
        assert modes & {"RowShareLock", "RowExclusiveLock"}, modes
        return f"row lock on the base table ({sorted(modes)})"
    if kind == "abuse":
        with psycopg.connect(dsn, autocommit=True) as c:
            c.execute(f"SET statement_timeout = {TIMEOUT_MS}")
            with pytest.raises(psycopg.errors.QueryCanceled):
                c.execute(attack.sql)
        return f"still running when the {TIMEOUT_MS} ms statement_timeout cancelled it"
    if kind in ("leak", "exec"):
        with psycopg.connect(dsn, autocommit=True) as c:
            cur = c.execute(attack.sql)
            cells = _cells(cur) if kind == "leak" else []
        if kind == "leak":
            assert any(needle in cell for cell in cells), f"no cell contains {needle!r}"
            return f"returned data the exposed views hide ({needle!r})"
        return "ran to completion on a privileged session"
    if kind == "pg-refuses":
        with psycopg.connect(dsn, autocommit=True) as c, pytest.raises((psycopg.Error, ValueError)):
            c.execute(attack.sql)
        return "PostgreSQL refuses it itself"
    raise AssertionError(f"unknown harm tag {attack.harm}")


@pytest.fixture(scope="module")
def shared(template: Db) -> Iterator[str]:
    """One copy for the statements that cannot change the database (reads, session settings, errors)."""
    maint = make_conninfo(template.admin_dsn, dbname="postgres")
    name = "askdata_h_" + secrets.token_hex(4)
    with psycopg.connect(maint, autocommit=True) as c:
        c.execute(f'CREATE DATABASE "{name}" TEMPLATE "{template.name}"')
    yield make_conninfo(template.admin_dsn, dbname=name)
    with psycopg.connect(maint, autocommit=True) as c:
        c.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


def _refused_when_validated(attack: Attack) -> None:
    with pytest.raises(
        Rejected
    ) as caught:  # the validator refuses it, so none of this ever reaches a server
        validate(attack.sql)
    assert caught.value.rule == attack.rule
    assert outcome(attack) == attack.rule


WRITERS = [a for a in HARMFUL if a.harm.split(":")[0] in ("write", "lock")]
READERS = [a for a in HARMFUL if a not in WRITERS]


@pytest.mark.parametrize("attack", WRITERS, ids=[a.name for a in WRITERS])
def test_writing_attack_does_harm_unvalidated_and_is_refused_when_validated(attack, clone):
    assert prove_harm(attack, clone)
    _refused_when_validated(attack)


@pytest.mark.parametrize("attack", READERS, ids=[a.name for a in READERS])
def test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated(attack, shared):
    assert prove_harm(attack, shared)
    _refused_when_validated(attack)


def test_the_harm_kinds_are_all_exercised():
    kinds = {a.harm.split(":")[0] for a in HARMFUL}
    assert {"write", "lock", "leak", "exec", "abuse", "pg-refuses"} <= kinds
    assert sum(a.harm.startswith("pg-refuses") for a in HARMFUL) < 0.35 * len(HARMFUL)
