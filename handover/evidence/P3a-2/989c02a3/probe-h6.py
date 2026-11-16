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


def hook_before(target, fn):
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

import pathlib, tempfile
tmp = pathlib.Path(tempfile.mkdtemp())
SH = mig._migration_files()
def extra(name_sql, stmt):
    last = SH[-1].stem; num = int(last.split("_")[0]) + 1
    p = tmp / f"{num:04d}_{name_sql}.sql"
    p.write_text(stmt + "\n", encoding="utf-8")
    return SH + [p]
orig_files = mig._migration_files

def split_wrap(stmt):
    chunks = [stmt[i:i+3].replace("'", "''") for i in range(0, len(stmt), 3)]
    lit = " || ".join("'" + c + "'" for c in chunks)
    return ("CREATE OR REPLACE FUNCTION ev_runner() RETURNS void LANGUAGE plpgsql AS $$ BEGIN EXECUTE " + lit + "; END $$;\nSELECT ev_runner();")

# ---- 5a O8 own typing: a REAL plain login (no helper re-own), schema owned by an outsider role from the start ----
def real_o8(flag, with_clean_first):
    mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = flag
    mig.connect = real_connect
    tag = uuid.uuid4().hex[:8]
    mrole, outsider = f"evm_{tag}", f"evo_{tag}"
    schema = f"hadavin_test_{uuid.uuid4().hex[:10]}"
    with adm() as a:
        a.execute(sql.SQL("CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEROLE NOCREATEDB NOBYPASSRLS NOREPLICATION").format(sql.Identifier(mrole)))
        a.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(outsider)))
        a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        a.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(mrole)))
        a.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {} WITH GRANT OPTION").format(sql.Identifier(schema), sql.Identifier(mrole)))
        a.execute("GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC")
        if not with_clean_first:
            a.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(schema), sql.Identifier(outsider)))
    dsn = make_conninfo(DSN, user=mrole, options=f"-c search_path={schema}")
    if with_clean_first:
        run(f"6a-clean-first ENFORCE={flag} (as {mrole} owning schema)", dsn)
        with adm() as a:
            a.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(schema), sql.Identifier(outsider)))
        mig._migration_files = lambda *a, **k: extra("o8", split_wrap("CREATE TABLE zz_o8 (a int)"))
        run(f"6a-then-outsider-owner+pending-file ENFORCE={flag}", dsn)
        mig._migration_files = orig_files
    else:
        run(f"6a-outsider-owns-from-start ENFORCE={flag}", dsn)
    with adm() as a:
        a.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(mrole)))
        a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(mrole)))
        a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(outsider)))
    mig.connect = helper.plain_role_connect(real_connect)

for flag in (False, True):
    for wc in (True, False):
        try: real_o8(flag, wc)
        except BaseException as e:
            print(f"[6a ENFORCE={flag} clean_first={wc}] PROBE-ERROR {type(e).__name__}: {str(e)[:200]!r}")
            mig.connect = helper.plain_role_connect(real_connect); mig._migration_files = orig_files
mig.ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = False

# ---- 6b C10 carrier, O13-O16, with the helper's plain role (own scripts), roles argument given and not ----
STM = {
 "O13": "GRANT CREATE ON SCHEMA {o} TO {rt}",
 "O14": "GRANT USAGE ON SCHEMA {o} TO {rt} WITH GRANT OPTION",
 "O15": "GRANT CREATE ON SCHEMA {o} TO PUBLIC",
 "O16": "ALTER DEFAULT PRIVILEGES IN SCHEMA {o} GRANT SELECT ON TABLES TO {rt}",
}
for eid, tmpl in STM.items():
    for withroles in (False, True):
        s, dsn = scratch()
        osch = s + "_o"
        rt = "evrt_" + uuid.uuid4().hex[:8]
        with adm() as a:
            helper.ensure_plain_role(a)
            a.execute(sql.SQL("CREATE ROLE {} NOLOGIN").format(sql.Identifier(rt)))
            a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(osch)))
            a.execute(sql.SQL("ALTER SCHEMA {} OWNER TO {}").format(sql.Identifier(osch), sql.Identifier(helper.PLAIN_ROLE)))
            a.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(osch)))
        stmt = tmpl.format(o=sql.Identifier(osch).as_string(), rt=sql.Identifier(rt).as_string())
        mig._migration_files = lambda *a, _st=stmt, **k: extra("c10", split_wrap(_st))
        kw = {"runtime_role": rt} if withroles else {}
        run(f"6b C10 {eid} roles_arg={withroles}", dsn, **kw)
        mig._migration_files = orig_files
        drop(s)
        with adm() as a:
            a.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(osch)))
            a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(rt)))
            a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(rt)))

# lost session after the second file has run (kill from the second pending file)
s, dsn = scratch()
files2 = extra("ok_before_kill", split_wrap("CREATE TABLE zz_ok (a int)"))
num = int(files2[-1].stem.split("_")[0]) + 1
p = tmp / f"{num:04d}_kill2.sql"; p.write_text("SELECT pg_terminate_backend(pg_backend_pid());\n")
mig._migration_files = lambda *a, **k: files2 + [p]
run("6d second extra file kills its backend (first extra ran in same run)", dsn)
mig._migration_files = orig_files; drop(s)

print("DONE")
