"""Rev 3 probes, part 2: extension-owned objects, re-grant on ALTER EXTENSION UPDATE, file_fdw DML codes, a schema-USAGE attempt,
pg_database_owner, the grant-option SET ROLE variant, and the order of the time limits. Throwaway 16.15 cluster, made-up roles.
Usage: python p3b.py <socket dir> <port> <dir of queries.py>"""
import sys, time, psycopg
SOCK, PORT = sys.argv[1], sys.argv[2]
sys.path.insert(0, sys.argv[3]); import queries as q
def dsn(user="postgres", db="r3x"): return f"host={SOCK} port={PORT} user={user} dbname={db}"
with psycopg.connect(dsn(db="postgres"), autocommit=True) as c0:
    c0.execute("DROP DATABASE IF EXISTS r3x WITH (FORCE)"); c0.execute("CREATE DATABASE r3x")
su = psycopg.connect(dsn(), autocommit=True)
NOTES = []
su.add_notice_handler(lambda d: NOTES.append(f"{d.severity}: {d.message_primary}"))
def attempt(label, role, sql, pre=()):
    try:
        with su.transaction():
            for p in pre: su.execute(p)
            su.execute(f"SET SESSION AUTHORIZATION {role}"); su.execute(sql); su.execute("RESET SESSION AUTHORIZATION")
            raise psycopg.Rollback()
        res = "allowed (no error)"
    except psycopg.Error as e: res = f"{e.sqlstate} {str(e).splitlines()[0]}"
    su.execute("RESET SESSION AUTHORIZATION"); print(f"{label:<66} | {res}")
print("== I. extension-owned objects with a default grant to everyone (pg_stat_statements, contrib, installed by the superuser)")
su.execute("CREATE SCHEMA app AUTHORIZATION r3_mig; GRANT USAGE ON SCHEMA app TO r3_rt, r3_boss, r3_boss2")
su.execute("CREATE EXTENSION pg_stat_statements VERSION '1.9'")
print("I1 acl of the view after CREATE 1.9:", su.execute("SELECT relacl::text FROM pg_class WHERE relname = 'pg_stat_statements'").fetchone())
su.execute("REVOKE SELECT ON public.pg_stat_statements FROM PUBLIC")
print("I2 after REVOKE ... FROM PUBLIC:", su.execute("SELECT relacl::text FROM pg_class WHERE relname = 'pg_stat_statements'").fetchone())
su.execute("ALTER EXTENSION pg_stat_statements UPDATE")
print("I3 after ALTER EXTENSION UPDATE to", su.execute("SELECT extversion FROM pg_extension WHERE extname='pg_stat_statements'").fetchone()[0], ":",
      su.execute("SELECT relacl::text FROM pg_class WHERE relname = 'pg_stat_statements'").fetchone())
P = dict(named=["r3_rt"], family=["r3_mig"], schema="app", roles=["r3_rt"], managed=[])
with psycopg.connect(dsn("r3_mig")) as c:
    with c.transaction():
        c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
        cols = None
        cur = c.execute(q.Q2, P); cols = [d.name for d in cur.description]; rows = cur.fetchall()
        ext = [dict(zip(cols, r)) for r in rows if dict(zip(cols, r))["extension"]]
        print(f"I4 Q2 rows: {len(rows)}; rows of extension members: {len(ext)}")
        for r in ext: print("   ", {k: r[k] for k in ("kind", "schema", "name", "sub", "owner", "family_owned", "extension", "extension_owner", "extension_family_owned", "grantee", "privilege_type")})
        raise psycopg.Rollback()
print("== J. file_fdw foreign table: DML codes granted / not granted")
su.execute("CREATE EXTENSION file_fdw; CREATE SERVER fs FOREIGN DATA WRAPPER file_fdw; CREATE FOREIGN TABLE app.ft (a text) SERVER fs OPTIONS (filename '/dev/null')")
for g, pre in (("granted", ["GRANT ALL ON app.ft TO r3_rt"]), ("none", [])):
    for verb, sql in (("SELECT", "SELECT a FROM app.ft LIMIT 0"), ("INSERT", "INSERT INTO app.ft (a) SELECT NULL WHERE false"), ("UPDATE", "UPDATE app.ft SET a = NULL WHERE false"),
                      ("DELETE", "DELETE FROM app.ft WHERE false"), ("TRUNCATE", "TRUNCATE app.ft")):
        attempt(f"J foreign table {verb} [{g}]", "r3_rt", sql, pre)
print("== K. schema USAGE by DROP ... IF EXISTS of a name that does not exist")
su.execute("CREATE SCHEMA other AUTHORIZATION r3_mig")
attempt("K1 no USAGE on other", "r3_rt", "DROP TABLE IF EXISTS other.oracle_no_such_name")
attempt("K2 USAGE on other", "r3_rt", "DROP TABLE IF EXISTS other.oracle_no_such_name", ["GRANT USAGE ON SCHEMA other TO r3_rt"])
attempt("K3 USAGE through PUBLIC", "r3_rt", "DROP TABLE IF EXISTS other.oracle_no_such_name", ["GRANT USAGE ON SCHEMA other TO PUBLIC"])
print("== L. pg_database_owner: is there any statement that removes it?")
with psycopg.connect(dsn(db="r3o"), autocommit=True) as c:
    LN = []; c.add_notice_handler(lambda d: LN.append(f"{d.severity}: {d.message_primary}"))
    for s in ("REVOKE pg_database_owner FROM r3_mig", "REVOKE pg_database_owner FROM r3_mig GRANTED BY postgres"):
        try: c.execute(s); print(f"L {s}: no error; notices: {LN}"); LN.clear()
        except psycopg.Error as e: print(f"L {s}: {e.sqlstate} {str(e).splitlines()[0]}")
    print("L owner of r3o:", c.execute("SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname='r3o'").fetchone())
print("== M. grant option held from two grantors")
su.execute("CREATE TABLE app.g (i int); ALTER TABLE app.g OWNER TO r3_mig")
su.execute("SET ROLE r3_mig; GRANT SELECT ON app.g TO r3_boss WITH GRANT OPTION; GRANT SELECT ON app.g TO r3_boss2 WITH GRANT OPTION; RESET ROLE")
su.execute("SET ROLE r3_boss2; GRANT SELECT ON app.g TO r3_boss WITH GRANT OPTION; RESET ROLE; SET ROLE r3_boss; GRANT SELECT ON app.g TO r3_rt; RESET ROLE")
acl = lambda: su.execute("SELECT relacl::text FROM pg_class WHERE oid = 'app.g'::regclass").fetchone()[0]
print("M1 start:", acl())
su.execute("REVOKE GRANT OPTION FOR SELECT ON app.g FROM r3_boss CASCADE"); print("M2 after superuser REVOKE GRANT OPTION ... CASCADE:", acl())
su.execute("SET ROLE r3_boss2; REVOKE GRANT OPTION FOR SELECT ON app.g FROM r3_boss CASCADE; RESET ROLE"); print("M3 after SET ROLE r3_boss2; same REVOKE:", acl())
print("== N. time-limit order on a role with a saved statement_timeout = 1ms, 100 fresh connections each")
su.execute("ALTER ROLE r3_tm SET statement_timeout = 1; GRANT USAGE ON SCHEMA app TO r3_tm")
PATH = "SET LOCAL search_path = pg_catalog, pg_temp"; LIM = ["SET LOCAL statement_timeout = '60s'", "SET LOCAL lock_timeout = '5s'"]
for lab, order in (("path first", [PATH] + LIM), ("limits first", LIM + [PATH])):
    fails = {}
    for i in range(100):
        with psycopg.connect(dsn("r3_tm"), autocommit=True) as c:
            try:
                c.execute("SET TIME ZONE 'UTC'")
                with c.transaction():
                    for j, s in enumerate(order): step = j; c.execute(s)
                    step = "Q2"; c.execute(q.Q2, P).fetchall()
            except psycopg.Error as e: fails[(step if isinstance(step, str) else order[step][:24], e.sqlstate)] = fails.get((step, e.sqlstate), 0) + 1
    print(f"N {lab}: failures {sum(fails.values())} of 100 {fails}")
print("N control, no limits:", end=" ")
f = 0
for i in range(20):
    with psycopg.connect(dsn("r3_tm"), autocommit=True) as c:
        try:
            with c.transaction(): c.execute(PATH); c.execute(q.Q2, P).fetchall()
        except psycopg.Error: f += 1
print(f"{f} of 20 cancelled")
su.close()
