"""EVIDENCE RUNNER own probes (item 8). Records what migrate() does; judges nothing."""
import os, sys, uuid, traceback
import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from hadavin_sdk import errors
from hadavin_sdk.store import migrate as mig
from tests.fixtures.migration_role import plain_role_connect

DSN = os.environ["HADAVIN_TEST_PG_DSN"]
mig.connect = plain_role_connect(mig.connect)
EXIT = lambda e: 2 if isinstance(e, errors.ConfigError) else (5 if isinstance(e, errors.AppliedNotVerifiedError) else 3)

def admin(): return psycopg.connect(DSN, autocommit=True)
def tables(schema):
    with admin() as a:
        return [r[0] for r in a.execute("select table_name from information_schema.tables where table_schema=%s order by 1", (schema,)).fetchall()]
def run(dsn, **roles):
    try:
        r = mig.migrate(dsn, **roles)
        return "returned", f"{len(r)} applied"
    except BaseException as e:
        return type(e).__name__, f"exit {EXIT(e)}: " + " ".join(str(e).split())[:230]

X = {  # my own typing of the effect statements (from the ticket table E17.. via the 3d report names)
 "X17": (["GRANT CREATE ON SCHEMA public TO {rt}"], ["REVOKE CREATE ON SCHEMA public FROM {rt}"]),
 "X18": (["GRANT CREATE ON DATABASE {db} TO {rt}"], ["REVOKE CREATE ON DATABASE {db} FROM {rt}"]),
 "X19": (["GRANT TEMPORARY ON DATABASE {db} TO {rt}"], ["REVOKE TEMPORARY ON DATABASE {db} FROM {rt}"]),
 "X28": (["ALTER TABLE {schema}.runs OWNER TO {rt}"], []),
 "X31": (["GRANT pg_read_all_data TO {rt}"], ["REVOKE pg_read_all_data FROM {rt}"]),
 "X32": (["CREATE ROLE {flag} NOLOGIN CREATEROLE", "GRANT {flag} TO {rt}"], []),
 "X33": (["ALTER ROLE {rt} CREATEDB"], []),
 "X36": (["ALTER DEFAULT PRIVILEGES FOR ROLE {other} IN SCHEMA {schema} GRANT SELECT ON TABLES TO {rt}"], []),
 "X01t": (["CREATE TABLE {schema}.zz_t (a int)", "GRANT SELECT ON {schema}.zz_t TO {other}"], []),
 "X11": (["CREATE FUNCTION {schema}.hadavin_zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'"], []),
 "X12": (["CREATE FUNCTION {schema}.zz_d() RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'", "REVOKE ALL ON FUNCTION {schema}.zz_d() FROM PUBLIC"], []),
 "O24": (["ALTER FUNCTION {schema}.hadavin_audit_append_only() OWNER TO {other}", "GRANT EXECUTE ON FUNCTION {schema}.hadavin_audit_append_only() TO PUBLIC"], []),
}

def cell(eid, variant):
    u = uuid.uuid4().hex[:8]
    schema = "hadavin_test_" + uuid.uuid4().hex[:12]
    other, rt, flag = f"hadavin_test_pr_{u}", f"hadavin_test_prr_{u}", f"hadavin_test_prf_{u}"
    with admin() as a:
        a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        a.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(other)))
        a.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(rt)))
        db = a.execute("select current_database()").fetchone()[0]
    names = dict(schema=sql.Identifier(schema).as_string(), db=sql.Identifier(db).as_string(), other=other, rt=rt, flag=flag)
    dsn = make_conninfo(DSN, options=f"-c search_path={schema}")
    roles = {"runtime_role": rt} if variant == "with-roles" else {}
    make, undo = X[eid]
    try:
        first = run(dsn, **roles)
        with admin() as a:
            for s in make: a.execute(s.format(**names))
        t_before = tables(schema)
        second = run(dsn, **roles)
        return first, second, len(t_before), len(tables(schema))
    except BaseException as e:
        return ("PROBE-ERROR", traceback.format_exc()[-300:], 0, 0)
    finally:
        with admin() as a:
            for s in undo:
                try: a.execute(s.format(**names))
                except Exception: pass
            a.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
            a.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(flag)))
            for r in (other, rt):
                a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(r)))
                a.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(r)))

print("PART A: states made by the administrator after a first successful run; second run result")
print("id | variant | first run | second run | tables before/after second run")
for eid in X:
    for v in ("no-roles", "with-roles"):
        f, s, tb, ta = cell(eid, v)
        print(f"{eid} | {v} | {f[0]} ({f[1]}) | {s[0]} ({s[1]}) | {tb}/{ta}")

# ---------------- PART B: O24 in another schema owned by the migration role -------------------------------------------
print("\nPART B: O24 (function of the family in ANOTHER schema owned by the migration role, callable by everyone by default)")
from tests.fixtures.migration_role import PLAIN_ROLE
for v in ("no-roles", "with-roles"):
    u = uuid.uuid4().hex[:8]
    schema = "hadavin_test_" + uuid.uuid4().hex[:12]; osch = schema + "_o"
    rt = f"hadavin_test_prr_{u}"
    with admin() as a:
        a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema))); a.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(rt)))
    dsn = make_conninfo(DSN, options=f"-c search_path={schema}"); roles = {"runtime_role": rt} if v == "with-roles" else {}
    f = run(dsn, **roles)
    with admin() as a:
        a.execute(sql.SQL("CREATE SCHEMA {} AUTHORIZATION {}").format(sql.Identifier(osch), sql.Identifier(PLAIN_ROLE)))
        a.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO PUBLIC").format(sql.Identifier(osch)))
        a.execute(sql.SQL("CREATE FUNCTION {}.hadavin_zz_f() RETURNS int LANGUAGE sql AS 'SELECT 1'").format(sql.Identifier(osch)))
    s = run(dsn, **roles)
    print(f"O24 | {v} | first {f[0]} | second {s[0]} ({s[1]})")
    with admin() as a:
        a.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(osch))); a.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
        a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(rt)))

# ---------------- PART C: a driver error injected at each step, first run in a fresh schema ----------------------------
print("\nPART C: driver error injected (psycopg.OperationalError, no SQLSTATE) at the first statement containing the marker; fresh schema, first run (pending files)")
print("marker | result | tables in schema afterwards | rows in schema_migrations")
orig_exec = psycopg.Connection.execute
def inject(marker):
    state = {"n": 0}
    def fake(self, query, *a, **k):
        text = query if isinstance(query, str) else str(query)
        if marker in text and state["n"] == 0:
            state["n"] = 1
            raise psycopg.OperationalError("injected: connection lost")
        return orig_exec(self, query, *a, **k)
    return fake, state
def fresh():
    schema = "hadavin_test_" + uuid.uuid4().hex[:12]
    with admin() as a: a.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    return schema, make_conninfo(DSN, options=f"-c search_path={schema}")
def drop(schema):
    with admin() as a: a.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
def rows(schema):
    with admin() as a:
        try: return a.execute(sql.SQL("select count(*) from {}.schema_migrations").format(sql.Identifier(schema))).fetchone()[0]
        except Exception: return "no table"
markers = ["pg_try_advisory", "pg_advisory", "lock_timeout", "server_version", "pg_roles", "CREATE TABLE IF NOT EXISTS schema_migrations", "SELECT version FROM schema_migrations", "CREATE TABLE", "INSERT INTO schema_migrations", "GRANT ", "SET CONSTRAINTS ALL IMMEDIATE"]
for m in markers:
    schema, dsn = fresh()
    fake, st = inject(m)
    psycopg.Connection.execute = fake
    try: res = run(dsn, runtime_role=None)
    finally: psycopg.Connection.execute = orig_exec
    print(f"{m!r} | fired={st['n']} | {res[0]} ({res[1][:150]}) | {len(tables(schema))} | {rows(schema)}")
    drop(schema)
# with a runtime role so step 4 GRANTs run
for m in ["GRANT ", "REVOKE "]:
    schema, dsn = fresh(); rt = "hadavin_test_prr_" + uuid.uuid4().hex[:8]
    with admin() as a: a.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(rt)))
    fake, st = inject(m); psycopg.Connection.execute = fake
    try: res = run(dsn, runtime_role=rt)
    finally: psycopg.Connection.execute = orig_exec
    print(f"{m!r}+runtime_role | fired={st['n']} | {res[0]} ({res[1][:150]}) | {len(tables(schema))} | {rows(schema)}")
    drop(schema)
    with admin() as a:
        a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(rt))); a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(rt)))
# commit step
orig_commit = psycopg.Connection._commit_gen
def before_commit(self):
    raise psycopg.OperationalError("injected: connection lost at COMMIT (before it reached the server)")
    yield
def after_commit(self):
    yield from orig_commit(self)
    raise psycopg.OperationalError("injected: connection lost after COMMIT ran (reply lost)")
for name, fn in (("COMMIT error before commit ran", before_commit), ("COMMIT reply lost after commit ran", after_commit)):
    schema, dsn = fresh(); psycopg.Connection._commit_gen = fn
    try: res = run(dsn)
    finally: psycopg.Connection._commit_gen = orig_commit
    print(f"{name} | {res[0]} ({res[1][:200]}) | {len(tables(schema))} | {rows(schema)}")
    drop(schema)
# step 8 (new connection after the commit)
schema, dsn = fresh(); real = mig.connect; calls = [0]
def second_fails(*a, **k):
    calls[0] += 1
    if calls[0] == 2: raise psycopg.OperationalError("injected: cannot connect for the check after the commit")
    return real(*a, **k)
mig.connect = second_fails
try: res = run(dsn)
finally: mig.connect = real
print(f"step 8 connect fails | {res[0]} ({res[1][:200]}) | {len(tables(schema))} | {rows(schema)}")
drop(schema)

# ---------------- PART D: K8 forms -------------------------------------------------------------------------------------
print("\nPART D: K8 (a file hands a map table to a group the migration role belongs to), three forms, in a scratch schema")
import pytest
from tests import test_migration_postgres as tp
from tests.test_migration_matrix import _split_function
import tempfile, pathlib
schema, dsn = fresh(); g = "hadavin_test_prg_" + uuid.uuid4().hex[:8]
print("first run:", run(dsn))
with admin() as a:
    a.execute(sql.SQL("CREATE ROLE {}").format(sql.Identifier(g)))
    a.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(g), sql.Identifier(PLAIN_ROLE)))
gid = sql.Identifier(g).as_string()
forms = {"(1) in the open": "ALTER TABLE spend OWNER TO " + gid + ";\n",
         "(2) dynamic SQL": _split_function("ALTER TABLE spend OWNER TO " + gid)}
for name, text in forms.items():
    with pytest.MonkeyPatch.context() as mp:
        tp._with_files(mp, pathlib.Path(tempfile.mkdtemp()), {"0006_hand_over.sql": text})
        print(name, run(dsn))
with admin() as a: a.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(sql.Identifier(schema), sql.Identifier(g)))
with pytest.MonkeyPatch.context() as mp:
    tp._with_files(mp, pathlib.Path(tempfile.mkdtemp()), {"0006_hand_over.sql": forms["(2) dynamic SQL"]})
    print("(3) dynamic SQL after CREATE on schema given to the group", run(dsn))
with admin() as a:
    print("owner of spend now:", a.execute(sql.SQL("select tableowner from pg_tables where schemaname=%s and tablename='spend'"), (schema,)).fetchone())
drop(schema)
with admin() as a:
    a.execute(sql.SQL("DROP OWNED BY {}").format(sql.Identifier(g))); a.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(g)))
