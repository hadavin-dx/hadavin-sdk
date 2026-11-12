"""Inbound ledger on a real PostgreSQL (AK-G2-a, Postgres only): rows L5 (8 processes), L14, L15, L21, L24, L25 (ii)-(iv)
with 8 processes, L26 and L28 with real database roles (nothing faked). Needs HADAVIN_TEST_PG_DSN and a login that can create
roles (the CI `postgres` user); skipped without it. Each test gets a fresh schema, migrated with all six roles."""

import multiprocessing
import re
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from hadavin_sdk.actions.secrets import FakeSecretProvider
from hadavin_sdk.backends.factory import make
from hadavin_sdk.backends.table import PostgresSettings
from hadavin_sdk.errors import ConfigError
from hadavin_sdk.models import (
    INBOUND_NEEDS_PERSON_REASONS,
    INBOUND_REFUSED_REASONS,
    OPEN_STATES,
    Run,
)
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store.postgres import REOPEN_SQL
from hadavin_sdk.store.protocol import StaleState
from hadavin_sdk.triggers.ledger import InboundKeyChanged, InboundSource, Inbox, run_id_for
from tests.contracts.kinds.store_postgres import INBOUND, PURGE_DSN, pg_schema

T0 = datetime(2030, 1, 1, tzinfo=UTC)
KEY = b"k" * 32
TENANT, SOURCE = "tenant-a", "src-orders"
KC = "0123456789abcdef"  # a made-up key check
HEX64 = "ab" * 32
INB = ("inbound_receipts", "inbound_bodies", "inbound_key_checks", "inbound_rerun_owner")
SRC = InboundSource(
    name=SOURCE,
    tenant=TENANT,
    readers=frozenset({"role:reader"}),
    agent_id="agent-a",
    principal_id="svc:trigger",
    max_open=100_000,
)


class _Clock:
    def __init__(self):
        self.t = T0

    def __call__(self):
        return self.t

    def advance(self, **kw):
        self.t += timedelta(**kw)


def _user(dsn):
    return conninfo_to_dict(dsn)["user"]


def _store(dsn):
    return make(
        "store",
        PostgresSettings(kind="postgres", dsn_secret_name="pg-dsn"),  # noqa: S106 - a name
        FakeSecretProvider({"pg-dsn": dsn}),
    )


class Env:
    """One fresh schema with the six roles (plus a portal role), the split store, and the admin helpers."""

    def __init__(self, dsn, split, portal_dsn):
        info = INBOUND[dsn]
        self.split, self.info, self.runtime_dsn = split, info, dsn
        self.migrator, self.schema = info["migrator"], info["schema"]
        self.door_dsn, self.dispatch_dsn = info["door"], info["dispatch"]
        self.purge_dsn, self.portal_dsn = PURGE_DSN[dsn], portal_dsn
        self.owner = info["rerun"]
        self.clock = _Clock()
        self.dsn_of = {
            "runtime": dsn,
            "door": self.door_dsn,
            "dispatch": self.dispatch_dsn,
            "purge": self.purge_dsn,
            "portal": portal_dsn,
        }
        self.role_of = {k: _user(v) for k, v in self.dsn_of.items()} | {"rerun": self.owner}

    def admin(self, query, params=None):
        """Run as the migrating superuser (the schema's owner); returns the rows, or the row count."""
        with psycopg.connect(self.migrator, autocommit=True) as db:
            cur = db.execute(query, params)
            return cur.fetchall() if cur.description else cur.rowcount

    def attempt(self, who, query, params=None):
        """Run as a login role: ("ok", rows) or (SQLSTATE, primary message)."""
        if who == "rerun":  # a role that cannot log in: act as it on the migrator connection
            return self.as_owner(query, params)
        dsn = self.dsn_of[who]
        with psycopg.connect(dsn, autocommit=True) as db:
            try:
                cur = db.execute(query, params)
                return "ok", (cur.fetchall() if cur.description else cur.rowcount)
            except psycopg.Error as exc:
                return exc.sqlstate, exc.diag.message_primary

    def as_owner(self, query, params=None):
        """Run as the re-run owner (the NOLOGIN role): the migrator connection acts as that role for one statement."""
        with psycopg.connect(self.migrator, autocommit=True) as db:
            db.execute(sql.SQL("SET ROLE {}").format(sql.Identifier(self.owner)))
            try:
                cur = db.execute(query, params)
                return "ok", (cur.fetchall() if cur.description else cur.rowcount)
            except psycopg.Error as exc:
                return exc.sqlstate, exc.diag.message_primary
            finally:
                db.execute("RESET ROLE")

    def receipt(self, dk):
        rows = self.admin(
            "SELECT state, reason, last_reason, attempts, generation, run_id, lease_until, claim_token "
            "FROM inbound_receipts WHERE delivery_key = %s",
            (dk,),
        )
        return rows[0] if rows else None

    def receive(self, i, body=b"body", src=SRC):
        return Inbox(self.split, hkey=KEY, clock=self.clock).receive(src, f"o-{i}", body)

    def claim(self):
        return self.split.claim_inbound(TENANT, SOURCE, self.clock(), 300)

    def finished(self, i, state, reason=None, body=b"body"):
        """Receive message i, claim it, finish it as `state`; return the receipt as claimed."""
        assert self.receive(i, body) == "new"
        rec = self.claim()
        self.split.finish_inbound(
            TENANT, SOURCE, rec.delivery_key, rec.claim_token, state, reason, self.clock()
        )
        return rec

    def make_run(self, rec, state="RECEIVED"):
        self.split.runtime.create_run(
            Run(
                run_id=rec.run_id,
                agent_id="a",
                principal_id="p",
                trigger_kind="event",
                trigger_ref="inb-x",
            )
        )
        self.admin("UPDATE runs SET state = %s WHERE run_id = %s", (state, rec.run_id))

    def columns(self, table):
        return [
            r[0]
            for r in self.admin(
                "SELECT column_name FROM information_schema.columns WHERE table_schema = %s AND table_name = %s "
                "ORDER BY ordinal_position",
                (self.schema, table),
            )
        ]

    def rights(self, role, tables=INB):
        """Everything `role` can really do on `tables`: {(table, column, privilege)} for column privileges and
        {(table, "*", privilege)} for DELETE, TRUNCATE and TRIGGER."""
        out = set()
        with psycopg.connect(self.migrator, autocommit=True) as db:
            for t in tables:
                qual = f"{self.schema}.{t}"
                for c in self.columns(t):
                    for p in ("SELECT", "INSERT", "UPDATE", "REFERENCES"):
                        if db.execute(
                            "SELECT has_column_privilege(%s, %s, %s, %s)", (role, qual, c, p)
                        ).fetchone()[0]:
                            out.add((t, c, p))
                for p in ("DELETE", "TRUNCATE", "TRIGGER"):
                    if db.execute(
                        "SELECT has_table_privilege(%s, %s, %s)", (role, qual, p)
                    ).fetchone()[0]:
                        out.add((t, "*", p))
        return out

    def expect(self, table, *, select=(), insert=False, update=(), delete=False):
        cols = self.columns(table)
        out = set()
        for c in cols if select == "all" else select:
            out.add((table, c, "SELECT"))
        for c in cols if update == "all" else update:
            out.add((table, c, "UPDATE"))
        if insert:
            out |= {(table, c, "INSERT") for c in cols}
        if delete:
            out.add((table, "*", "DELETE"))
        return out


@pytest.fixture
def env():
    gen = pg_schema(runtime=True, inbound=True)
    dsn = next(gen)  # skips without HADAVIN_TEST_PG_DSN
    info = INBOUND[dsn]
    portal = "pt_" + uuid.uuid4().hex[:12]
    admin_dsn = info["migrator"]
    with psycopg.connect(admin_dsn, autocommit=True) as db:
        db.execute(sql.SQL("CREATE ROLE {} LOGIN").format(sql.Identifier(portal)))
    mig.migrate(
        admin_dsn,
        runtime_role=_user(dsn),
        portal_role=portal,
        purge_role=_user(PURGE_DSN[dsn]),
        inbound_door_role=_user(info["door"]),
        inbound_dispatch_role=_user(info["dispatch"]),
        rerun_owner_role=info["rerun"],
    )
    stores = [_store(d) for d in (dsn, info["door"], info["dispatch"], PURGE_DSN[dsn])]
    from tests.contracts.kinds.store_postgres import InboundSplitStore

    split = InboundSplitStore(*stores, info["migrator"], info["rerun"])
    yield Env(dsn, split, make_conninfo(admin_dsn, user=portal))
    split.close()
    next(gen, None)
    with psycopg.connect(
        make_conninfo(admin_dsn, options=""), autocommit=True
    ) as db:  # the portal role holds nothing once the schema is gone
        db.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(portal)))


# ---------------------------------------------------------------------------------------------------------------------
# L5 and L25 with 8 processes (a real second program per worker: nothing is shared but the database)


def _claim_proc(dsn, tenant, source, now, lease_s):
    store, seen = _store(dsn), []
    while (rec := store.claim_inbound(tenant, source, now, lease_s)) is not None:
        seen.append(rec.delivery_key)
    store._db.close()
    return seen


def _receive_proc(dsn, barrier, q, ids, bodies):
    store = _store(dsn)
    ib = Inbox(store, hkey=KEY, clock=lambda: T0)
    barrier.wait(60)
    out = []
    for sender_id, body in zip(ids, bodies, strict=True):
        try:
            out.append(ib.receive(SRC, sender_id, body))
        except Exception as exc:  # noqa: BLE001 - reported to the parent
            out.append("EXC:" + exc.__class__.__name__)
    store._db.close()
    q.put(out)


def _race(env, per_worker, n=8):
    """n processes start together: worker i receives per_worker[i] = [(sender id, body), ...]."""
    ctx = multiprocessing.get_context("spawn")
    barrier, q = ctx.Barrier(n), ctx.Queue()
    procs = [
        ctx.Process(
            target=_receive_proc,
            args=(env.door_dsn, barrier, q, [a for a, _ in w], [b for _, b in w]),
        )
        for w in per_worker
    ]
    [p.start() for p in procs]
    results = [q.get(timeout=180) for _ in procs]
    [p.join(60) for p in procs]
    assert all(p.exitcode == 0 for p in procs)
    return [r for rs in results for r in rs]


def test_l5_every_receipt_is_claimed_exactly_once_by_8_processes(env):
    n = 500
    ib = Inbox(env.split, hkey=KEY, clock=env.clock)
    for i in range(n):
        assert ib.receive(SRC, f"o-{i}", b"x") == "new"
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(8) as pool:
        got = pool.starmap(_claim_proc, [(env.dispatch_dsn, TENANT, SOURCE, env.clock(), 300)] * 8)
    seen = [k for part in got for k in part]
    assert len(seen) == n and len(set(seen)) == n
    assert sum(1 for part in got if part) >= 2  # the work really was shared


def test_l25_i_eight_processes_receiving_one_new_message_give_one_new_seven_duplicates(env):
    out = _race(env, [[("same-id", b"same-body")]] * 8)
    assert sorted(out) == ["duplicate"] * 7 + ["new"]
    assert env.admin("SELECT count(*) FROM inbound_receipts")[0][0] == 1
    assert env.admin("SELECT count(*) FROM inbound_bodies")[0][0] == 1


def test_l25_ii_eight_processes_receiving_one_reused_body_give_one_reuse_row(env):
    assert env.receive(1, b"first") == "new"
    out = _race(env, [[("o-1", b"second")]] * 8)
    assert out == ["id_reuse"] * 8
    rows = env.admin(
        "SELECT state, reason, run_id FROM inbound_receipts ORDER BY received_at, state"
    )
    assert len(rows) == 2 and ("refused", "id_reuse", None) in rows
    assert (
        env.admin("SELECT count(*) FROM inbound_bodies")[0][0] == 1
    )  # the reuse row holds no body


def test_l25_iii_eight_processes_first_receives_on_a_new_address_make_one_key_check_row(env):
    out = _race(env, [[(f"m-{i}", b"x")] for i in range(8)])
    assert out == ["new"] * 8
    assert env.admin("SELECT count(*) FROM inbound_key_checks")[0][0] == 1


def test_l25_iv_a_key_change_between_the_read_and_the_insert_is_key_changed_and_writes_nothing(env):
    ib = Inbox(env.split, hkey=KEY, clock=env.clock)
    assert ib.receive(SRC, "o-1", b"x") == "new"
    old = ib.key_check
    new = "f" * 16
    fired = []

    def flip():  # a second connection, as the dispatch role, commits an acknowledged key change
        env.split.dispatch.set_inbound_key_check(TENANT, SOURCE, old, new, env.clock())
        fired.append(1)

    env.split.door._after_key_check_read = flip
    before = (
        env.admin("SELECT count(*) FROM inbound_receipts")[0][0],
        env.admin("SELECT count(*) FROM inbound_bodies")[0][0],
    )
    with pytest.raises(InboundKeyChanged):  # the door answers 503 for this
        ib.receive(SRC, "o-2", b"y")
    assert fired == [1]
    after = (
        env.admin("SELECT count(*) FROM inbound_receipts")[0][0],
        env.admin("SELECT count(*) FROM inbound_bodies")[0][0],
    )
    assert before == after == (1, 1)
    assert env.admin("SELECT key_check FROM inbound_key_checks")[0][0] == new
    # the store itself gives the plain word, and still raises nothing
    from hadavin_sdk.models import InboundReceipt

    probe = InboundReceipt(
        tenant=TENANT,
        source=SOURCE,
        readers=SRC.readers,
        delivery_key="c" * 64,
        body_sha256="d" * 64,
        key_check=old,
        run_id=run_id_for("c" * 64, 0),
        state="received",
        received_at=T0,
        updated_at=T0,
    )
    env.split.door._after_key_check_read = lambda: None
    assert env.split.door.receive_inbound(probe, b"z", max_reuse=8, max_open=10) == "key_changed"


# ---------------------------------------------------------------------------------------------------------------------
# L14, L24, L28: rights of every login (a matrix of what each role can REALLY do, then the refusals by name)

RECEIPT_COLS_DOOR = (
    "tenant",
    "source",
    "delivery_key",
    "body_sha256",
    "reuse_of",
    "state",
    "readers",
)
DISPATCH_UPDATE = (
    "state",
    "attempts",
    "lease_until",
    "claim_token",
    "reason",
    "last_reason",
    "updated_at",
)
RERUN_UPDATE = (
    "state",
    "generation",
    "run_id",
    "attempts",
    "reason",
    "last_reason",
    "lease_until",
    "claim_token",
    "updated_at",
)
PURGE_RECEIPT_COLS = ("tenant", "source", "delivery_key", "state", "run_id", "updated_at")


def _matrix(env):
    return {
        "door": env.expect("inbound_receipts", insert=True, select=RECEIPT_COLS_DOOR)
        | env.expect("inbound_bodies", insert=True)
        | env.expect("inbound_key_checks", insert=True, select=("tenant", "source", "key_check")),
        "dispatch": env.expect("inbound_receipts", select="all", update=DISPATCH_UPDATE)
        | env.expect("inbound_bodies", select="all")
        | env.expect("inbound_key_checks", select="all", update=("key_check", "set_at")),
        "rerun": env.expect("inbound_receipts", select="all", update=RERUN_UPDATE)
        | env.expect("inbound_rerun_owner", select="all"),
        "purge": env.expect("inbound_receipts", select=PURGE_RECEIPT_COLS)
        | env.expect("inbound_bodies", select=("tenant", "source", "delivery_key"), delete=True),
        "runtime": set(),
        "portal": set(),
    }


@pytest.mark.parametrize("who", ["door", "dispatch", "rerun", "purge", "runtime", "portal"])
def test_l24_each_login_holds_exactly_its_rights_on_the_four_inbound_tables(env, who):
    got, want = env.rights(env.role_of[who]), _matrix(env)[who]
    assert got == want, f"{who}: extra {sorted(got - want)}; missing {sorted(want - got)}"


def test_l24_runs_and_dead_letters_are_narrow_for_the_inbound_roles(env):
    def runs(role):
        return env.rights(role, ("runs",))

    cols = (
        "run_id",
        "agent_id",
        "principal_id",
        "trigger_ref",
        "state",
        "reason_code",
        "updated_at",
    )
    assert runs(env.role_of["door"]) == set()
    assert runs(env.role_of["dispatch"]) == {("runs", c, "SELECT") for c in cols}
    assert runs(env.role_of["rerun"]) == {("runs", c, "SELECT") for c in ("run_id", "state")}
    assert env.rights(env.role_of["door"], ("dead_letters",)) == set()
    assert env.rights(env.role_of["rerun"], ("dead_letters",)) == set()
    dl = env.rights(env.role_of["dispatch"], ("dead_letters",))
    assert {p for _, _, p in dl} == {"SELECT", "INSERT"} and (
        "dead_letters",
        "*",
        "DELETE",
    ) not in dl


def test_l14_purge_and_portal(env):
    assert mig.check_grants(mig._migration_files()) == []
    for t in INB:  # the portal role reads none of them
        assert (
            env.attempt("portal", sql.SQL("SELECT 1 FROM {} LIMIT 1").format(sql.Identifier(t)))[0]
            == "42501"
        )
    env.finished(1, "refused", "forbidden")
    env.finished(2, "done")
    assert env.attempt("purge", "SELECT body FROM inbound_bodies")[0] == "42501"
    assert env.attempt("purge", "SELECT delivery_key FROM inbound_bodies")[0] == "ok"
    assert env.attempt("purge", "SELECT 1 FROM inbound_key_checks")[0] == "42501"
    assert (
        env.attempt("purge", "UPDATE inbound_receipts SET state = state WHERE false")[0] == "42501"
    )
    assert env.split.purge_inbound_bodies(T0 + timedelta(days=40), T0 + timedelta(days=400)) >= 1
    assert (
        env.admin("SELECT count(*) FROM inbound_receipts")[0][0] == 2
    )  # receipts are never deleted


_DOOR_BAD = [
    ("UPDATE inbound_receipts SET state = state WHERE false", "42501"),
    ("DELETE FROM inbound_receipts WHERE false", "42501"),
    ("SELECT run_id FROM inbound_receipts", "42501"),
    ("SELECT claim_token FROM inbound_receipts", "42501"),
    ("SELECT attempts FROM inbound_receipts", "42501"),
    ("SELECT generation FROM inbound_receipts", "42501"),
    ("SELECT * FROM inbound_receipts", "42501"),
    ("SELECT body FROM inbound_bodies", "42501"),
    ("SELECT delivery_key FROM inbound_bodies", "42501"),
    ("SELECT run_id FROM runs", "42501"),
    ("SELECT 1 FROM runs", "42501"),
    ("UPDATE inbound_key_checks SET key_check = key_check WHERE false", "42501"),
    ("SELECT role_name FROM inbound_rerun_owner", "42501"),
]
_DISPATCH_BAD = [
    ("INSERT INTO inbound_receipts (tenant) VALUES ('x')", "42501"),
    ("DELETE FROM inbound_receipts WHERE false", "42501"),
    ("INSERT INTO inbound_bodies (tenant) VALUES ('x')", "42501"),
    ("UPDATE inbound_bodies SET body = body WHERE false", "42501"),
    ("DELETE FROM inbound_bodies WHERE false", "42501"),
    ("UPDATE runs SET state = state WHERE false", "42501"),
    ("SELECT cost_usd FROM runs", "42501"),
    ("SELECT created_at FROM runs", "42501"),
    ("SELECT trigger_kind FROM runs", "42501"),
    ("SELECT * FROM runs", "42501"),
    ("UPDATE inbound_receipts SET generation = generation WHERE false", "42501"),
    ("UPDATE inbound_receipts SET run_id = run_id WHERE false", "42501"),
    ("UPDATE inbound_receipts SET body_sha256 = body_sha256 WHERE false", "42501"),
    ("UPDATE inbound_receipts SET key_check = key_check WHERE false", "42501"),
    ("UPDATE inbound_key_checks SET tenant = tenant WHERE false", "42501"),
    ("UPDATE inbound_key_checks SET source = source WHERE false", "42501"),
    ("UPDATE inbound_key_checks SET readers = readers WHERE false", "42501"),
    ("SELECT role_name FROM inbound_rerun_owner", "42501"),
    ("UPDATE inbound_key_checks SET key_check = 'not-hex'", "23514"),
]
_RERUN_BAD = [
    ("SELECT body FROM inbound_bodies", "42501"),
    ("INSERT INTO inbound_receipts (tenant) VALUES ('x')", "42501"),
    ("DELETE FROM inbound_receipts WHERE false", "42501"),
    ("UPDATE inbound_receipts SET tenant = tenant WHERE false", "42501"),
    ("UPDATE inbound_receipts SET readers = readers WHERE false", "42501"),
    ("UPDATE inbound_receipts SET body_sha256 = body_sha256 WHERE false", "42501"),
    ("UPDATE inbound_receipts SET key_check = key_check WHERE false", "42501"),
    ("SELECT key_check FROM inbound_key_checks", "42501"),
    ("INSERT INTO inbound_rerun_owner (id, role_name) VALUES (true, 'x')", "42501"),
    ("UPDATE inbound_rerun_owner SET role_name = 'x'", "42501"),
    ("DELETE FROM inbound_rerun_owner", "42501"),
    ("SELECT agent_id FROM runs", "42501"),
    ("SELECT * FROM runs", "42501"),
]
_RUNTIME_BAD = [
    (sql.SQL(template).format(sql.Identifier(t)), "42501")
    for t in INB
    for template in (
        "SELECT 1 FROM {}",
        "INSERT INTO {} DEFAULT VALUES",
        "DELETE FROM {} WHERE false",
    )
] + [
    (
        sql.SQL("UPDATE {} SET state = state WHERE false").format(
            sql.Identifier("inbound_receipts")
        ),
        "42501",
    )
]


@pytest.mark.parametrize(
    ("who", "query", "code"),
    [("door", q, c) for q, c in _DOOR_BAD]
    + [("dispatch", q, c) for q, c in _DISPATCH_BAD]
    + [("rerun", q, c) for q, c in _RERUN_BAD]
    + [("runtime", q, c) for q, c in _RUNTIME_BAD],
)
def test_l24_the_forbidden_statement_is_refused_by_the_database(env, who, query, code):
    if who == "dispatch" and "key_check = 'not-hex'" in str(query):  # needs one stored check to hit
        assert env.receive(1) == "new"
    got = env.attempt(who, query)
    assert got[0] == code, got


def _row(dk, **over):
    row = {
        "tenant": TENANT,
        "source": SOURCE,
        "delivery_key": dk,
        "schema_version": 1,
        "readers": ["role:reader"],
        "body_sha256": HEX64,
        "key_check": KC,
        "generation": 0,
        "run_id": "run-" + dk[:28] + "0000",
        "state": "received",
        "reason": None,
        "last_reason": None,
        "attempts": 0,
        "lease_until": None,
        "claim_token": None,
        "reuse_of": None,
        "received_at": T0,
        "updated_at": T0,
    }
    row.update(over)
    return row


_INSERT = (
    "INSERT INTO inbound_receipts (tenant, source, delivery_key, schema_version, readers, body_sha256, key_check, "
    "generation, run_id, state, reason, last_reason, attempts, lease_until, claim_token, reuse_of, received_at, "
    "updated_at) VALUES (%(tenant)s, %(source)s, %(delivery_key)s, %(schema_version)s, %(readers)s, %(body_sha256)s, "
    "%(key_check)s, %(generation)s, %(run_id)s, %(state)s, %(reason)s, %(last_reason)s, %(attempts)s, "
    "%(lease_until)s, %(claim_token)s, %(reuse_of)s, %(received_at)s, %(updated_at)s)"
)
_KEY_CHECK_INSERT = (
    "INSERT INTO inbound_key_checks (tenant, source, schema_version, readers, key_check, set_at) "
    "VALUES (%(tenant)s, %(source)s, 1, %(readers)s, %(key_check)s, %(set_at)s)"
)
_REUSE = {"state": "refused", "reason": "id_reuse", "reuse_of": "e" * 64, "run_id": None}
_DK = "1" * 64


@pytest.mark.parametrize(
    ("name", "over", "message"),
    [
        ("done", {"state": "done"}, "inbound_insert_refused"),
        ("needs_person", {"state": "needs_person", "reason": "policy"}, "inbound_insert_refused"),
        (
            "claimed",
            {"state": "claimed", "lease_until": T0, "claim_token": "clm-" + "a" * 32},
            "inbound_insert_refused",
        ),
        ("attempts 3", {"attempts": 3}, "inbound_insert_refused"),
        ("generation 1", {"generation": 1}, "inbound_insert_refused"),
        ("wrong run id", {"run_id": "run-" + "0" * 32}, "inbound_insert_refused"),
        ("received with reuse_of", {"reuse_of": "e" * 64}, None),
        ("new-shape key check differs", {"key_check": "f" * 16}, "inbound_key_changed"),
        ("reuse-shape key check differs", {**_REUSE, "key_check": "f" * 16}, "inbound_key_changed"),
        ("no stored check", {"source": "src-none"}, "inbound_key_changed"),
        (
            "63-character delivery key",
            {"delivery_key": "1" * 63, "run_id": "run-" + "1" * 28 + "0000"},
            None,
        ),
        (
            "upper-case delivery key",
            {"delivery_key": "A" * 64, "run_id": "run-" + "A" * 28 + "0000"},
            None,
        ),
        ("upper-case body hash", {"body_sha256": "AB" * 32}, None),
        ("non-hex reuse_of", {**_REUSE, "reuse_of": "z" * 64}, None),
    ],
)
def test_l24_door_inserts_outside_the_two_legal_shapes_are_refused_and_nothing_is_written(
    env, name, over, message
):
    env.attempt("door", _KEY_CHECK_INSERT, _kc_row(KC))
    code, msg = env.attempt("door", _INSERT, _row(over.get("delivery_key", _DK), **over))
    assert code == "23514", (name, code, msg)
    if message:
        assert msg == message, (name, msg)
    assert env.admin("SELECT count(*) FROM inbound_receipts")[0][0] == 0


def _kc_row(check, source=SOURCE):
    return {
        "tenant": TENANT,
        "source": source,
        "readers": ["role:reader"],
        "key_check": check,
        "set_at": T0,
    }


def test_l24_door_the_two_legal_shapes_succeed_and_a_first_non_hex_check_is_refused(env):
    assert env.attempt("door", _KEY_CHECK_INSERT, _kc_row("zz" * 8))[0] == "23514"
    assert env.attempt("door", _KEY_CHECK_INSERT, _kc_row(KC))[0] == "ok"
    assert env.attempt("door", _INSERT, _row(_DK))[0] == "ok"
    assert env.attempt("door", _INSERT, _row("2" * 64, **_REUSE))[0] == "ok"


def test_l24_door_bodies_only_for_a_new_receipt(env):
    body = (
        "INSERT INTO inbound_bodies (tenant, source, delivery_key, schema_version, readers, body, received_at) "
        "VALUES (%(tenant)s, %(source)s, %(delivery_key)s, 1, %(readers)s, 'x', %(received_at)s)"
    )
    p = {"tenant": TENANT, "source": SOURCE, "readers": ["role:reader"], "received_at": T0}
    env.attempt("door", _KEY_CHECK_INSERT, _kc_row(KC))
    assert env.attempt("door", body, {**p, "delivery_key": _DK}) == (
        "23514",
        "inbound_insert_refused",
    )
    env.attempt("door", _INSERT, _row("2" * 64, **_REUSE))
    assert env.attempt("door", body, {**p, "delivery_key": "2" * 64}) == (
        "23514",
        "inbound_insert_refused",
    )
    env.attempt("door", _INSERT, _row(_DK))
    assert (
        env.attempt("door", body, {**p, "delivery_key": _DK, "readers": ["role:other"]})[0]
        == "23514"
    )
    assert env.attempt("door", body, {**p, "delivery_key": _DK})[0] == "ok"


def test_l24_the_receipts_key_check_check_alone_refuses_a_non_hex_value(env):
    env.admin(
        "INSERT INTO inbound_key_checks VALUES (%s, %s, 1, %s, %s, %s)",
        (TENANT, SOURCE, ["r"], KC, T0),
    )
    env.admin("ALTER TABLE inbound_receipts DISABLE TRIGGER inbound_receipts_insert")
    try:
        with (
            psycopg.connect(env.migrator, autocommit=True) as db,
            pytest.raises(psycopg.errors.CheckViolation) as ex,
        ):
            db.execute(_INSERT, _row(_DK, key_check="not-a-hex-value!"))
        assert "inbound_receipts_key_check_check" in ex.value.diag.constraint_name
    finally:
        env.admin("ALTER TABLE inbound_receipts ENABLE ALWAYS TRIGGER inbound_receipts_insert")
    assert env.admin(
        "SELECT tgenabled FROM pg_trigger WHERE tgname = 'inbound_receipts_insert' AND tgrelid = to_regclass('inbound_receipts')"
    ) == [("A",)]


# ---------------------------------------------------------------------------------------------------------------------
# L15: the database triggers, by direct SQL


def test_l15_a_the_reopen_move_is_refused_to_dispatch_door_and_runtime_and_the_row_is_unchanged(
    env,
):
    rec = env.finished(1, "needs_person", "run_interrupted")
    before = env.receipt(rec.delivery_key)
    p = {"now": env.clock(), "tenant": TENANT, "source": SOURCE, "delivery_key": rec.delivery_key}
    for who in ("dispatch", "door", "runtime"):
        assert env.attempt(who, REOPEN_SQL, p)[0] == "42501", who
    assert env.receipt(rec.delivery_key) == before


def test_l15_b_the_owner_is_refused_while_the_run_is_in_any_open_state(env):
    rec = env.finished(1, "needs_person", "run_interrupted")
    env.make_run(rec)
    p = {"now": env.clock(), "tenant": TENANT, "source": SOURCE, "delivery_key": rec.delivery_key}
    for state in sorted(s.value for s in OPEN_STATES):
        env.admin("UPDATE runs SET state = %s WHERE run_id = %s", (state, rec.run_id))
        assert env.as_owner(REOPEN_SQL, p) == ("55000", "rerun_run_open"), state
    assert env.receipt(rec.delivery_key)[4] == 0  # generation untouched
    with pytest.raises(StaleState):  # the store maps 55000 to StaleState
        env.split.rerun_owner_reopen(TENANT, SOURCE, rec.delivery_key, env.clock())


def test_l15_c_the_owner_reopens_when_the_run_is_needs_person(env):
    rec = env.finished(1, "needs_person", "run_interrupted")
    env.make_run(rec, "NEEDS_PERSON")
    again = env.split.rerun_owner_reopen(TENANT, SOURCE, rec.delivery_key, env.clock())
    assert again.generation == 1 and again.run_id == run_id_for(rec.delivery_key, 1)
    state, reason, last, attempts, gen, run_id, lease, token = env.receipt(rec.delivery_key)
    assert (state, reason, last, attempts, gen) == ("received", None, None, 0, 1)
    assert (lease, token) == (None, None) and run_id == run_id_for(rec.delivery_key, 1)


def test_l15_d_an_emptied_owner_table_refuses_the_reopen(env):
    rec = env.finished(1, "needs_person", "run_interrupted")
    env.admin("DELETE FROM inbound_rerun_owner")
    p = {"now": env.clock(), "tenant": TENANT, "source": SOURCE, "delivery_key": rec.delivery_key}
    assert env.as_owner(REOPEN_SQL, p) == ("42501", "rerun_owner_only")


def test_l15_e_dispatch_claims_releases_and_finishes_with_no_right_on_the_owner_table(env):
    assert env.attempt("dispatch", "SELECT role_name FROM inbound_rerun_owner")[0] == "42501"
    assert env.receive(1) == "new"
    rec = env.claim()
    env.split.release_inbound(
        TENANT, SOURCE, rec.delivery_key, rec.claim_token, "step_error", env.clock()
    )
    env.clock.advance(seconds=1)
    rec = env.claim()
    env.split.finish_inbound(
        TENANT, SOURCE, rec.delivery_key, rec.claim_token, "done", None, env.clock()
    )
    assert env.receipt(rec.delivery_key)[:2] == ("done", None)


def _in_list(text, anchor):
    m = re.search(re.escape(anchor) + r"\s*\(([^)]*)\)", text)
    assert m, anchor
    return {w.strip().strip("'") for w in m.group(1).split(",")}


def test_l15_f_the_migration_lists_equal_the_python_sets():
    text = (Path(mig.__file__).parent / "migrations" / "0006_inbound.sql").read_text(
        encoding="utf-8"
    )
    assert _in_list(text, "AND state IN") == {s.value for s in OPEN_STATES}
    assert _in_list(text, "WHEN 'refused' THEN COALESCE(reason IN") == set(INBOUND_REFUSED_REASONS)
    assert _in_list(text, "WHEN 'needs_person' THEN COALESCE(reason IN") == set(
        INBOUND_NEEDS_PERSON_REASONS
    )
    assert _in_list(text, "last_reason IN") == {"step_error", "audit_unavailable"}


def test_l15_g_a_second_row_in_the_owner_table_is_refused(env):
    for stmt in (
        "INSERT INTO inbound_rerun_owner (id, role_name) VALUES (false, 'x')",
        "INSERT INTO inbound_rerun_owner (id, role_name) VALUES (true, 'x')",
    ):
        with (
            psycopg.connect(env.migrator, autocommit=True) as db,
            pytest.raises(psycopg.Error) as ex,
        ):
            db.execute(stmt)
        assert ex.value.sqlstate in ("23514", "23505")
    assert env.admin("SELECT count(*) FROM inbound_rerun_owner")[0][0] == 1


def test_l15_h_each_function_is_pinned_to_the_schema_and_pg_temp(env):
    rows = env.admin(
        "SELECT p.proname, p.proconfig FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace "
        "WHERE n.nspname = %s AND p.proname = ANY(%s) ORDER BY 1",
        (env.schema, list(mig.INBOUND_FUNCTIONS)),
    )
    assert [r[0] for r in rows] == sorted(mig.INBOUND_FUNCTIONS)
    assert all(r[1] == [f"search_path={env.schema}, pg_temp"] for r in rows)


def _expect_refused(env, query, params, message):
    with (
        psycopg.connect(env.migrator, autocommit=True) as db,
        pytest.raises(psycopg.errors.CheckViolation) as ex,
    ):
        db.execute(query, params)
    assert ex.value.diag.message_primary == message, ex.value.diag.message_primary


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("tenant", "tenant-x"),
        ("source", "src-x"),
        ("delivery_key", "9" * 64),
        ("body_sha256", "9" * 64),
        ("key_check", "9" * 16),
        ("readers", ["role:other"]),
        ("reuse_of", "9" * 64),
        ("received_at", T0 + timedelta(days=1)),
        ("schema_version", 2),
    ],
)
def test_l15_h_an_immutable_column_cannot_change_even_for_the_migrator(env, column, value):
    rec = env.finished(1, "done")
    del rec
    query = sql.SQL("UPDATE inbound_receipts SET {} = %s").format(sql.Identifier(column))
    _expect_refused(env, query, (value,), "inbound_immutable")


def test_l15_h_run_id_and_generation_change_only_by_reopen_and_other_moves_are_refused(env):
    assert env.receive(1) == "new"
    rec = env.claim()
    _expect_refused(
        env, "UPDATE inbound_receipts SET run_id = %s", ("run-" + "0" * 32,), "inbound_immutable"
    )
    _expect_refused(
        env, "UPDATE inbound_receipts SET generation = generation + 1", (), "inbound_immutable"
    )
    env.split.finish_inbound(
        TENANT, SOURCE, rec.delivery_key, rec.claim_token, "done", None, env.clock()
    )
    _expect_refused(
        env, "UPDATE inbound_receipts SET state = 'received'", (), "inbound_state_move"
    )  # done -> received
    _expect_refused(
        env, "UPDATE inbound_receipts SET attempts = attempts", (), "inbound_state_move"
    )  # any update of done
    env.finished(2, "refused", "forbidden")
    _expect_refused(
        env,
        "UPDATE inbound_receipts SET state = 'claimed', lease_until = %s, claim_token = %s WHERE state = 'refused'",
        (T0, "clm-" + "a" * 32),
        "inbound_state_move",
    )


def test_l15_h_attempts_cannot_go_down(env):
    assert env.receive(1) == "new"
    rec = env.claim()
    env.split.release_inbound(
        TENANT, SOURCE, rec.delivery_key, rec.claim_token, "step_error", env.clock()
    )
    assert env.receipt(rec.delivery_key)[3] == 1
    _expect_refused(env, "UPDATE inbound_receipts SET attempts = 0", (), "inbound_attempts_down")


def test_l15_h_a_reopen_must_raise_the_generation_by_one_and_spell_the_new_run_id(env):
    rec = env.finished(1, "needs_person", "run_interrupted")
    base = (
        "UPDATE inbound_receipts SET state = 'received', attempts = 0, reason = NULL, last_reason = NULL, "
        "lease_until = NULL, claim_token = NULL, "
    )
    for tail, params in (
        ("generation = generation + 1", ()),  # keeps the old run id
        (
            "generation = generation + 2, run_id = %s",
            (run_id_for(rec.delivery_key, 2),),
        ),  # skips one
    ):
        code, msg = env.as_owner(base + tail, params)
        assert (code, msg) == ("23514", "inbound_reopen_shape"), tail
    assert env.receipt(rec.delivery_key)[4] == 0


# ---------------------------------------------------------------------------------------------------------------------
# L21: an index can serve each statement of the ledger


def _spy(store):
    seen, orig = [], store._exec

    def spy(query, params=()):
        seen.append((query, params))
        return orig(query, params)

    store._exec = spy
    return seen


def test_l21_no_statement_of_the_ledger_needs_a_sequential_scan_of_the_receipts(env):
    ib = Inbox(env.split, hkey=KEY, clock=env.clock)
    for i in range(30):
        assert ib.receive(SRC, f"o-{i}", b"x") == "new"
    for st in (env.split.door, env.split.dispatch, env.split.purge):
        st._exec("SET enable_seqscan = off")
    seen = {
        "door": _spy(env.split.door),
        "dispatch": _spy(env.split.dispatch),
        "purge": _spy(env.split.purge),
    }
    ib.receive(
        SRC, "o-1", b"different"
    )  # a conflict: the dedupe, the reuse count, the reuse insert
    ib.receive(SRC, "o-new", b"y")  # the open count
    rec = env.claim()
    env.split.finish_inbound(
        TENANT, SOURCE, rec.delivery_key, rec.claim_token, "done", None, env.clock()
    )
    env.split.list_inbound_sources()
    env.split.purge_inbound_bodies(T0 + timedelta(days=40), T0 + timedelta(days=400))
    plans, checked = [], 0
    for who, statements in seen.items():
        store = getattr(env.split, who)
        for query, params in statements:
            if "inbound_receipts" not in str(query) or str(query).lstrip().upper().startswith(
                ("SET", "EXPLAIN")
            ):
                continue
            text = "\n".join(
                next(iter(r.values()))
                for r in store._exec("EXPLAIN " + str(query), params).fetchall()
            )
            plans.append(f"--- {who}: {' '.join(str(query).split())[:110]}\n{text}")
            assert "Seq Scan on inbound_receipts" not in text, plans[-1]
            checked += 1
    print("\n".join(plans))  # the raw plans, kept by `pytest -s` / `-rP` in the evidence file
    assert checked >= 6  # dedupe, reuse count, open count, claim, list, purge, finish ...


# ---------------------------------------------------------------------------------------------------------------------
# L26, L28 with real roles


def test_l26_a_partial_role_set_is_refused_and_a_real_database_is_left_untouched():
    gen = pg_schema(migrated=False)
    scoped = next(gen)
    try:
        for given in (
            {"inbound_door_role": "x1"},
            {"inbound_door_role": "x1", "inbound_dispatch_role": "x2"},
        ):
            with pytest.raises(ConfigError, match="missing"):
                mig.migrate(scoped, **given)
        with psycopg.connect(scoped, autocommit=True) as db:
            assert db.execute("SELECT to_regclass('schema_migrations')").fetchone()[0] is None
    finally:
        next(gen, None)


def test_l28_i_no_inbound_roles_leave_the_old_rights_as_the_grant_map_says():
    """A schema migrated with only the runtime and purge roles: each holds exactly what GRANTS says, and the owner
    table is empty (nothing can use inbound: fail closed)."""
    gen = pg_schema(runtime=True)
    dsn = next(gen)
    try:
        with psycopg.connect(dsn, autocommit=True) as db:
            schema = db.execute("SELECT current_schema()").fetchone()[0]
        admin = make_conninfo(dsn, user="postgres", options=f"-c search_path={schema}")
        with psycopg.connect(admin, autocommit=True) as adm:
            assert adm.execute("SELECT count(*) FROM inbound_rerun_owner").fetchone()[0] == 0
            for role, who in ((_user(dsn), "runtime"), (_user(PURGE_DSN[dsn]), "purge")):
                for rel, g in mig.GRANTS.items():
                    privs = {
                        p.strip()
                        for p in (g.runtime if who == "runtime" else g.purge).split(",")
                        if p.strip()
                    }
                    qual = f"{schema}.{rel}"
                    if g.kind == "sequence":
                        for p in ("USAGE", "SELECT", "UPDATE"):
                            got = adm.execute(
                                "SELECT has_sequence_privilege(%s, %s, %s)", (role, qual, p)
                            ).fetchone()[0]
                            assert got == (p in privs), (who, rel, p)
                        continue
                    for p in ("SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"):
                        got = adm.execute(
                            "SELECT has_table_privilege(%s, %s, %s)", (role, qual, p)
                        ).fetchone()[0]
                        assert got == (p in privs), (who, rel, p)
                    for c in g.purge_cols if who == "purge" else ():
                        assert adm.execute(
                            "SELECT has_column_privilege(%s, %s, %s, 'SELECT')", (role, qual, c)
                        ).fetchone()[0]
    finally:
        next(gen, None)


def test_l28_ii_effective_problems_flags_a_hand_granted_column_update_and_passes_without_it(env):
    role = _user(env.dispatch_dsn)

    def problems(db):
        return mig.effective_problems(
            db,
            role,
            lambda g: g.dispatch if g else "",
            lambda g: g.dispatch_select_cols if g else (),
            lambda g: g.dispatch_update_cols if g else (),
        )

    with psycopg.connect(env.migrator, autocommit=True) as db:
        assert problems(db) == []
        db.execute(
            sql.SQL("GRANT UPDATE (generation) ON inbound_receipts TO {}").format(
                sql.Identifier(role)
            )
        )
        bad = problems(db)
        assert bad and any("generation" in p for p in bad), bad
        db.execute(
            sql.SQL("REVOKE UPDATE (generation) ON inbound_receipts FROM {}").format(
                sql.Identifier(role)
            )
        )
        assert problems(db) == []


def test_l28_every_login_passes_the_effective_problems_check(env):
    f = mig.effective_problems
    with psycopg.connect(env.migrator, autocommit=True) as db:
        assert f(db, env.role_of["runtime"], lambda g: g.runtime if g else "") == []
        assert (
            f(
                db,
                env.role_of["door"],
                lambda g: g.door if g else "",
                lambda g: g.door_select_cols if g else (),
                lambda g: (),
            )
            == []
        )
        assert (
            f(
                db,
                env.owner,
                lambda g: g.rerun if g else "",
                lambda g: g.rerun_select_cols if g else (),
                lambda g: g.rerun_update_cols if g else (),
            )
            == []
        )


def test_l24_a_stray_holder_of_update_generation_makes_migrate_refuse_and_roll_back(env):
    stray = "sy_" + uuid.uuid4().hex[:10]
    new_owner = "r2_" + uuid.uuid4().hex[:10]
    env.admin(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(stray)).as_string())
    env.admin(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(new_owner)).as_string())
    try:
        env.admin(
            sql.SQL("GRANT UPDATE (generation) ON inbound_receipts TO {}")
            .format(sql.Identifier(stray))
            .as_string()
        )
        with pytest.raises(ConfigError, match="revoke it by hand"):
            mig.migrate(
                env.migrator,
                runtime_role=env.role_of["runtime"],
                purge_role=env.role_of["purge"],
                inbound_door_role=env.role_of["door"],
                inbound_dispatch_role=env.role_of["dispatch"],
                rerun_owner_role=new_owner,
            )
        assert env.admin("SELECT role_name FROM inbound_rerun_owner") == [
            (env.owner,)
        ]  # rolled back
        assert env.rights(new_owner) == set() and env.rights(env.owner) == _matrix(env)["rerun"]
    finally:
        env.admin(
            sql.SQL("REVOKE ALL ON inbound_receipts FROM {}")
            .format(sql.Identifier(stray))
            .as_string()
        )
        for r in (stray, new_owner):
            env.admin(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)).as_string())
            env.admin(sql.SQL("DROP ROLE {}").format(sql.Identifier(r)).as_string())


def test_l24_a_renamed_rerun_owner_leaves_the_old_one_with_no_right_on_any_granted_relation(env):
    new_owner = "r3_" + uuid.uuid4().hex[:10]
    env.admin(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(new_owner)).as_string())
    try:
        mig.migrate(
            env.migrator,
            runtime_role=env.role_of["runtime"],
            purge_role=env.role_of["purge"],
            inbound_door_role=env.role_of["door"],
            inbound_dispatch_role=env.role_of["dispatch"],
            rerun_owner_role=new_owner,
        )
        assert env.admin("SELECT role_name FROM inbound_rerun_owner") == [(new_owner,)]
        assert env.rights(env.owner, tuple(mig.GRANTS)) == set()  # nothing left on any relation
        assert env.rights(new_owner) == _matrix(env)["rerun"]
    finally:
        env.admin(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(new_owner)).as_string())
        env.admin(sql.SQL("DROP ROLE {}").format(sql.Identifier(new_owner)).as_string())
