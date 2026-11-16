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


# 1 lost session: pg_terminate_backend just before the first file's wait (_refuse_unusual_strings has no db arg -> use _read_back)
for target in ("_take_the_lock", "_read_back", "_check_read_back", "_apply_grants"):
    s, dsn = scratch()
    undo = hook_before(target, terminate)
    run(f"1 terminate_backend before {target}", dsn)
    undo(); drop(s)

# 1b closed connection (client closes it) before steps
for target in ("_read_back", "_check_read_back"):
    s, dsn = scratch()
    undo = hook_before(target, lambda db: db.close())
    run(f"1b closed connection before {target}", dsn)
    undo(); drop(s)

# 1c killed backend mid-file: a migration file extra whose statement kills its own backend
s, dsn = scratch()
import pathlib, tempfile
tmp = pathlib.Path(tempfile.mkdtemp())
last = mig._migration_files()[-1].stem
num = int(last.split("_")[0]) + 1
bad = tmp / f"{num:04d}_hostile_kill.sql"
bad.write_text("SELECT pg_terminate_backend(pg_backend_pid());\n", encoding="utf-8")
files = mig._migration_files() + [bad]
orig_files = mig._migration_files
mig._migration_files = lambda *a, **k: files
run("1c file kills own backend", dsn)
mig._migration_files = orig_files; drop(s)

# 2 class 25 SQLSTATEs: 25P03 live; classifier on fabricated errors
s, dsn = scratch()
with adm() as a:
    helper.ensure_plain_role(a)
    a.execute(sql.SQL("ALTER ROLE {} SET idle_in_transaction_session_timeout = '150ms'").format(sql.Identifier(helper.PLAIN_ROLE)))
real = mig._refuse_unusual_strings
def waits(saved):
    time.sleep(0.6); return real(saved)
mig._refuse_unusual_strings = waits
run("2 25P03 idle_in_transaction timeout", dsn)
mig._refuse_unusual_strings = real
with adm() as a:
    a.execute(sql.SQL("ALTER ROLE {} RESET idle_in_transaction_session_timeout").format(sql.Identifier(helper.PLAIN_ROLE)))
drop(s)

class Fake:
    closed = False; broken = False
    class info: transaction_status = psycopg.pq.TransactionStatus.INERROR
for code in ["25000","25001","25002","25003","25004","25005","25006","25007","25008","25P01","25P02","25P03","25P04","08006","57P01","53100","XX000","23505","42601","40001","22012","P0001"]:
    e = psycopg.Error(); e.__dict__  # placeholder
    class E(psycopg.Error):
        sqlstate = code
    print(f"[2b classifier] sqlstate={code} is_a_files_own_error(usable conn)={mig._is_a_files_own_error(E('x'), Fake)}")
class Closed(Fake): closed = True
print("[2b classifier] 23505 on closed conn:", mig._is_a_files_own_error(type('E', (psycopg.Error,), {'sqlstate': '23505'})('x'), Closed))

# 3 O8 : schema owner changes mid-run, both settings
for flag in (False, True):
    mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = flag
    other = "evo8_" + uuid.uuid4().hex[:8]
    with adm() as a:
        a.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(other)))
    # 3a owner changes mid-run (before the second read-back)
    s, dsn = scratch()
    undo = hook_before("_check_read_back", lambda db, s=s, o=other: adm().execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(s), sql.Identifier(o))))
    run(f"3a O8 owner changed mid-run, ENFORCE={flag}", dsn)
    undo(); drop(s)
    # 3b schema owned outside the family at the start
    s, dsn = scratch()
    real_conn = mig.connect
    def conn(d, _s=s, _o=other, **kw):
        # owner is set to `other` after the plain-role swap made the plain role the owner: do it once per run on first connect
        db = real_conn(d, **kw)
        return db
    # make `other` owner before connect cannot survive the helper (it re-owns for the plain role); use plain real connect + role setup
    mig.connect = real_connect
    with adm() as a:
        a.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(s), sql.Identifier(other)))
        helper.ensure_plain_role(a)
        a.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(other), sql.Identifier(helper.PLAIN_ROLE))) if False else None
    mig.connect = helper.plain_role_connect(real_connect)
    run(f"3b schema owner outside family at start (helper re-owns to plain role), ENFORCE={flag}", dsn)
    drop(s)
    with adm() as a:
        a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(other)))
        a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(other)))
mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = False

# 4 third-role right on a family table with no role argument
third = "evthird_" + uuid.uuid4().hex[:8]
with adm() as a:
    a.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(third)))
table = next(iter(mig.GRANTS))
s, dsn = scratch()
run("4a baseline (no third role)", dsn)
with adm() as a:
    a.execute(sql.SQL("GRANT SELECT ON TABLE {}.{} TO {}").format(sql.Identifier(s), sql.Identifier(table), sql.Identifier(third)))
run("4b third-role SELECT on family table, no role argument", dsn)
with adm() as a:
    a.execute(sql.SQL("REVOKE SELECT ON TABLE {}.{} FROM {}").format(sql.Identifier(s), sql.Identifier(table), sql.Identifier(third)))
    a.execute(sql.SQL("GRANT SELECT ON TABLE {}.{} TO PUBLIC").format(sql.Identifier(s), sql.Identifier(table)))
run("4c PUBLIC SELECT on family table, no role argument", dsn)
drop(s)
with adm() as a:
    a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(third)))
print("DONE")
