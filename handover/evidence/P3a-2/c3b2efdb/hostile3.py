"""EVIDENCE RUNNER own probes (not the builder's tests). Records what migrate() returns/raises for hostile inputs."""
import os, sys, time, uuid, traceback
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from hadavin_sdk.store import migrate as mig
from hadavin_sdk.store import migration_verify as v
from tests.fixtures import migration_role as helper

DSN = os.environ["HADAVIN_TEST_PG_DSN"]
real_connect = mig.connect
mig.connect = helper.plain_role_connect(real_connect)


def adm():
    return psycopg.connect(DSN, autocommit=True)


def scratch():
    schema = f"hadavin_test_{uuid.uuid4().hex[:12]}"
    with adm() as a:
        a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    return schema, make_conninfo(DSN, options=f"-c search_path={schema}")


def drop(schema):
    with adm() as a:
        a.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))


def ledger(dsn):
    with psycopg.connect(dsn, autocommit=True) as db:
        if db.execute("SELECT to_regclass('schema_migrations')").fetchone()[0] is None:
            return []
        return [r[0] for r in db.execute("SELECT version FROM schema_migrations ORDER BY 1")]


def run(name, dsn, **kw):
    try:
        r = mig.migrate(dsn, **kw)
        out = f"RETURNED {len(r)} versions"
    except BaseException as e:
        out = f"RAISED {type(e).__name__}: {str(e)[:420]!r}"
    print(f"[{name}] {out} | ledger_count_after={len(ledger(dsn))}", flush=True)


def hook_before(target, fn, once=True):
    real = getattr(mig, target)
    st = {"n": 0}

    def w(*a, **k):
        st["n"] += 1
        if st["n"] == 1:
            fn(a[0] if a else None)
        return real(*a, **k)

    setattr(mig, target, w)
    return lambda: setattr(mig, target, real)


def terminate(db):
    with adm() as a:
        a.execute("SELECT pg_terminate_backend(%s)", (db.info.backend_pid,))
    time.sleep(0.3)



def hook_nth(target, n, fn):
    real = getattr(mig, target); st = {"n": 0}
    def w(*a, **k):
        st["n"] += 1
        if st["n"] == n: fn()
        return real(*a, **k)
    setattr(mig, target, w)
    return lambda: setattr(mig, target, real)
for flag in (False, True):
    mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = flag
    other = "evo8_" + uuid.uuid4().hex[:8]
    with adm() as a:
        a.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(other)))
    s, dsn = scratch()
    undo = hook_nth("_state_problems", 2, lambda s=s, o=other: adm().execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(s), sql.Identifier(o))))
    run(f"3e O8 owner changed just before the step-6 state read, ENFORCE={flag}", dsn)
    undo(); drop(s)
    with adm() as a:
        a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
        a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))
mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = False
print("DONE")
