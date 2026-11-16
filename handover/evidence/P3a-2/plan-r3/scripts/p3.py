"""Rev 3 probes for ticket P3a-2 r13 (plan round 3). Throwaway PostgreSQL 16.15 cluster, made-up roles only.
Usage: python p3.py <socket dir> <port> <dir of queries.py>. Prints raw results; judges nothing."""
import sys, threading, time, psycopg
from psycopg import errors as E
SOCK, PORT = sys.argv[1], sys.argv[2]
sys.path.insert(0, sys.argv[3]); import queries as q
def dsn(user="postgres", db="r3"): return f"host={SOCK} port={PORT} user={user} dbname={db}"
with psycopg.connect(dsn(db="postgres"), autocommit=True) as c:
    for d in ("r3", "r3o", "r3x"): c.execute(f"DROP DATABASE IF EXISTS {d} WITH (FORCE)")
    for r in ("r3_mig r3_login r3_rt r3_po r3_pu r3_third r3_boss r3_boss2 r3_grp r3_tm".split()):
        c.execute(f"DROP ROLE IF EXISTS {r}")
    c.execute("CREATE ROLE r3_mig LOGIN; CREATE ROLE r3_login LOGIN IN ROLE r3_mig; CREATE ROLE r3_rt LOGIN; CREATE ROLE r3_po; CREATE ROLE r3_pu;"
              "CREATE ROLE r3_third; CREATE ROLE r3_boss; CREATE ROLE r3_boss2; CREATE ROLE r3_grp; CREATE ROLE r3_tm LOGIN")
    c.execute("CREATE DATABASE r3"); c.execute("CREATE DATABASE r3o OWNER r3_mig"); c.execute("CREATE DATABASE r3x")
SETUP = """
CREATE SCHEMA app AUTHORIZATION r3_mig; CREATE SCHEMA other AUTHORIZATION r3_mig; CREATE SCHEMA scratch;
SET ROLE r3_mig;
CREATE TABLE app.t (id int PRIMARY KEY, c int); CREATE VIEW app.v AS SELECT count(*) AS n FROM app.t; CREATE VIEW app.sv AS SELECT id, c FROM app.t;
CREATE MATERIALIZED VIEW app.m AS SELECT id, c FROM app.t; CREATE SEQUENCE app.q; CREATE TYPE app.typ AS (a int); CREATE TABLE other.ot (i int);
CREATE TABLE app.g (i int); CREATE TABLE app.ct (i int);
CREATE FUNCTION app.slow() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN PERFORM pg_catalog.pg_sleep(3); RETURN NULL; END$$;
CREATE CONSTRAINT TRIGGER slow AFTER INSERT ON app.ct DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION app.slow();
GRANT USAGE ON SCHEMA app TO r3_rt, r3_boss, r3_boss2;
RESET ROLE;
REVOKE TEMPORARY ON DATABASE r3 FROM PUBLIC; REVOKE USAGE ON TYPE app.typ FROM PUBLIC; REVOKE USAGE ON LANGUAGE plpgsql FROM PUBLIC;
"""
su = psycopg.connect(dsn(), autocommit=True); su.execute(SETUP)
def attempt(label, role, sql, pre=()):
    try:
        with su.transaction():
            for p in pre: su.execute(p)
            su.execute(f"SET SESSION AUTHORIZATION {role}")
            su.execute(sql)
            su.execute("RESET SESSION AUTHORIZATION")
            raise psycopg.Rollback()
        res = "allowed (no error)"
    except psycopg.Error as e:
        res = f"{e.sqlstate} {str(e).splitlines()[0]}"
    su.execute("RESET SESSION AUTHORIZATION")
    print(f"{label:<62} | {res}")
print("== A. E03 REFERENCES (rt as probed role)")
attempt("A1 temp table, rt HAS REFERENCES on app.t", "r3_rt", "CREATE TEMP TABLE u (x int REFERENCES app.t (id))", ["GRANT TEMPORARY ON DATABASE r3 TO r3_rt", "GRANT REFERENCES ON app.t TO r3_rt"])
attempt("A2 temp table, rt has NO REFERENCES", "r3_rt", "CREATE TEMP TABLE u (x int REFERENCES app.t (id))", ["GRANT TEMPORARY ON DATABASE r3 TO r3_rt"])
own = ["CREATE TABLE scratch.u (x int)", "ALTER TABLE scratch.u OWNER TO r3_rt", "GRANT USAGE ON SCHEMA scratch TO r3_rt"]
attempt("A3 permanent table owned by rt, HAS REFERENCES", "r3_rt", "ALTER TABLE scratch.u ADD FOREIGN KEY (x) REFERENCES app.t (id)", own + ["GRANT REFERENCES ON app.t TO r3_rt"])
attempt("A4 permanent table owned by rt, NO REFERENCES", "r3_rt", "ALTER TABLE scratch.u ADD FOREIGN KEY (x) REFERENCES app.t (id)", own)
attempt("A5 permanent, column-level REFERENCES (id) only", "r3_rt", "ALTER TABLE scratch.u ADD FOREIGN KEY (x) REFERENCES app.t (id)", own + ["GRANT REFERENCES (id) ON app.t TO r3_rt"])
print("== B. E19/E20/E21 and TEMPORARY (PUBLIC has no TEMPORARY, no USAGE on app.typ, no USAGE on plpgsql)")
attempt("B0 E19 temp table, no TEMPORARY", "r3_rt", "CREATE TEMP TABLE u (i int)")
attempt("B1 temp table of app.typ, HAS type USAGE, no TEMPORARY", "r3_rt", "CREATE TEMP TABLE u (x app.typ)", ["GRANT USAGE ON TYPE app.typ TO r3_rt"])
attempt("B2 SELECT NULL::app.typ, NO type USAGE", "r3_rt", "SELECT NULL::app.typ")
attempt("B3 SELECT NULL::app.typ, HAS type USAGE", "r3_rt", "SELECT NULL::app.typ", ["GRANT USAGE ON TYPE app.typ TO r3_rt"])
scr = ["GRANT USAGE, CREATE ON SCHEMA scratch TO r3_rt"]
attempt("B4 scratch-schema table of app.typ, HAS type USAGE", "r3_rt", "CREATE TABLE scratch.u (x app.typ)", scr + ["GRANT USAGE ON TYPE app.typ TO r3_rt"])
attempt("B5 scratch-schema table of app.typ, NO type USAGE", "r3_rt", "CREATE TABLE scratch.u (x app.typ)", scr)
attempt("B6 DO block plpgsql, NO language USAGE", "r3_rt", "DO $$BEGIN END$$ LANGUAGE plpgsql")
attempt("B7 DO block plpgsql, HAS language USAGE", "r3_rt", "DO $$BEGIN END$$ LANGUAGE plpgsql", ["GRANT USAGE ON LANGUAGE plpgsql TO r3_rt"])
attempt("B8 scratch function plpgsql, NO language USAGE", "r3_rt", "CREATE FUNCTION scratch.f() RETURNS int LANGUAGE plpgsql AS 'BEGIN RETURN 1; END'", scr)
attempt("B9 scratch function plpgsql, HAS language USAGE", "r3_rt", "CREATE FUNCTION scratch.f() RETURNS int LANGUAGE plpgsql AS 'BEGIN RETURN 1; END'", scr + ["GRANT USAGE ON LANGUAGE plpgsql TO r3_rt"])
attempt("B10 temp function plpgsql, HAS language USAGE, no TEMPORARY", "r3_rt", "CREATE FUNCTION pg_temp.f() RETURNS int LANGUAGE plpgsql AS 'BEGIN RETURN 1; END'", ["GRANT USAGE ON LANGUAGE plpgsql TO r3_rt"])
print("== C. DML and upkeep per relation kind (WITH all rights granted / with none)")
REL = {"table app.t": ("app.t", "c"), "simple view app.sv": ("app.sv", "c"), "aggregate view app.v": ("app.v", "n"), "matview app.m": ("app.m", "c"), "sequence app.q": ("app.q", "last_value")}
for kind, (o, col) in REL.items():
    for g, pre in (("granted", [f"GRANT ALL ON {o} TO r3_rt"]), ("none", [])):
        for verb, sql in (("INSERT", f"INSERT INTO {o} ({col}) SELECT NULL WHERE false"), ("UPDATE", f"UPDATE {o} SET {col} = NULL WHERE false"),
                          ("DELETE", f"DELETE FROM {o} WHERE false"), ("TRUNCATE", f"TRUNCATE {o}"), ("REINDEX", f"REINDEX TABLE {o}"),
                          ("SELECT", f"SELECT {col} FROM {o} LIMIT 0")):
            attempt(f"C {kind} {verb} [{g}]", "r3_rt", sql, pre)
attempt("C UPDATE app.t with only UPDATE (no SELECT)", "r3_rt", "UPDATE app.t SET c = NULL WHERE false", ["GRANT UPDATE ON app.t TO r3_rt"])
attempt("C REFRESH matview, granted ALL", "r3_rt", "REFRESH MATERIALIZED VIEW app.m", ["GRANT ALL ON app.m TO r3_rt"])
print("== D. schema USAGE confounder (other.ot, SELECT granted)")
attempt("D1 SELECT other.ot, HAS SELECT, NO USAGE on schema other", "r3_rt", "SELECT * FROM other.ot LIMIT 0", ["GRANT SELECT ON other.ot TO r3_rt"])
attempt("D2 SELECT other.ot, NO SELECT, NO USAGE", "r3_rt", "SELECT * FROM other.ot LIMIT 0")
attempt("D3 SELECT other.ot, HAS SELECT, HAS USAGE", "r3_rt", "SELECT * FROM other.ot LIMIT 0", ["GRANT SELECT ON other.ot TO r3_rt", "GRANT USAGE ON SCHEMA other TO r3_rt"])
attempt("D4 SELECT other.ot, NO SELECT, HAS USAGE", "r3_rt", "SELECT * FROM other.ot LIMIT 0", ["GRANT USAGE ON SCHEMA other TO r3_rt"])
print("== E. psycopg 3.3.6: isolation_level/read_only on an autocommit connection, then transaction()")
with psycopg.connect(dsn("r3_mig"), autocommit=True) as c:
    c.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ; c.read_only = True
    with c.transaction():
        print("E1 outer:", c.execute("SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only')").fetchone())
        try:
            with c.transaction():
                c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
                print("E2 inside savepoint:", c.execute("SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only'), current_setting('search_path')").fetchone())
                raise psycopg.Rollback()
        except Exception as e: print("E2 error", type(e).__name__, e)
        print("E3 after savepoint rollback, path:", c.execute("SELECT current_setting('search_path')").fetchone())
    c.isolation_level = None; c.read_only = None
    with c.transaction():
        print("E4 with both reset to None:", c.execute("SELECT current_setting('transaction_isolation'), current_setting('transaction_read_only')").fetchone())
print("== F. COMMIT failures on an autocommit connection, transaction() block (as store/postgres.connect makes it)")
def commit_case(label, killer):
    c = psycopg.connect(dsn("r3_mig"), autocommit=True); pid = c.info.backend_pid
    def kill():
        with psycopg.connect(dsn(), autocommit=True) as k:
            for _ in range(100):
                if k.execute("SELECT count(*) FROM pg_stat_activity WHERE pid = %s AND wait_event = 'PgSleep'", (pid,)).fetchone()[0]: break
                time.sleep(0.05)
            k.execute(f"SELECT {killer}(%s)", (pid,))
    th = threading.Thread(target=kill); th.start()
    try:
        with c.transaction():
            c.execute("INSERT INTO app.ct VALUES (%s)", (len(label),))
        print(f"{label}: no exception")
    except Exception as e:
        print(f"{label}: {type(e).__module__}.{type(e).__name__} sqlstate={getattr(e, 'sqlstate', None)} closed={c.closed} status={c.info.transaction_status.name} msg={str(e).splitlines()[0]!r}")
    th.join(15)
    with psycopg.connect(dsn(), autocommit=True) as k:
        print(f"{label}: row present afterwards = {k.execute('SELECT count(*) FROM app.ct WHERE i = %s', (len(label),)).fetchone()[0]}")
    c.close()
commit_case("F1 pg_terminate_backend during a commit-time trigger", "pg_terminate_backend")
commit_case("F2 pg_cancel_backend during a commit-time trigger (cancel)", "pg_cancel_backend")
print("== G. Q0 and the version read, as the plain login r3_mig, path pinned")
with psycopg.connect(dsn("r3_mig")) as c:
    with c.transaction():
        c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
        print("G1 version:", c.execute(q.VERSION).fetchone()[0])
        rows = c.execute(q.Q0).fetchall(); print(f"G2 Q0: {len(rows)} rows"); [print("   ", r[0]) for r in rows]
        raise psycopg.Rollback()
print("== H. Q1/Q1b/Q2/Q3/Q4/STEP4 with EMPTY named and roles arrays and a TWO-entry family, as r3_login (member of r3_mig)")
su.execute("GRANT SELECT ON app.t TO PUBLIC")
for P, lab in ((dict(named=[], family=["r3_mig", "r3_login"], schema="app", roles=[], managed=["slow"]), "empty named, family of 2"),
               (dict(named=["r3_rt", "r3_po", "r3_pu"], family=["r3_mig", "r3_login"], schema="app", roles=["r3_mig", "r3_login"], managed=["slow"]), "3 named, family of 2, roles = family")):
    with psycopg.connect(dsn("r3_login")) as c:
        c.execute("SET ROLE r3_mig")
        for name in ("Q1", "Q1B", "Q2", "Q3", "Q4", "STEP4"):
            try:
                with c.transaction():
                    c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
                    rows = c.execute(getattr(q, name), P).fetchall()
                    print(f"H [{lab}] {name}: {len(rows)} rows; first 3: {rows[:3]}")
                    raise psycopg.Rollback()
            except psycopg.Error as e: print(f"H [{lab}] {name}: ERROR {e.sqlstate} {e}")
su.close()
