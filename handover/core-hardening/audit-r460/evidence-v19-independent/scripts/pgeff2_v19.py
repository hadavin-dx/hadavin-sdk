import sys, os, secrets
sock = sys.argv[1]; import psycopg
pw = os.environ["HV_ADMIN_PW"]
a = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={pw}", autocommit=True)
mp = secrets.token_hex(8); a.execute(f"CREATE ROLE mg LOGIN PASSWORD '{mp}'"); a.execute("CREATE ROLE rt LOGIN PASSWORD 'x'"); a.execute("CREATE DATABASE h OWNER mg")
c = psycopg.connect(f"host={sock} dbname=h user=mg password={mp}", autocommit=True)
c.execute("CREATE TABLE spend (agent_id text, usd numeric)"); c.execute("INSERT INTO spend VALUES ('a',5)"); c.execute("CREATE TABLE kill_switch (id int, \"on\" bool)")
SP = "SET search_path = pg_catalog, pg_temp"
for lab, body in [("R01 DELETE FROM spend", "DELETE FROM spend"), ("R14 CTE delete", "WITH d AS (DELETE FROM spend RETURNING 1) SELECT 1"), ("R15 TRUNCATE", "TRUNCATE spend")]:
    try:
        c.execute(f"CREATE OR REPLACE FUNCTION f() RETURNS void LANGUAGE sql SECURITY DEFINER {SP} BEGIN ATOMIC {body}; END"); print("PG-ACCEPTED", lab)
        c.execute("REVOKE ALL ON FUNCTION f() FROM PUBLIC"); c.execute("GRANT EXECUTE ON FUNCTION f() TO rt"); c.execute("GRANT USAGE ON SCHEMA public TO rt")
        r = psycopg.connect(f"host={sock} dbname=h user=rt password=x", autocommit=True); r.execute("SELECT f()")
        print("   effect: rows left in spend =", c.execute("SELECT count(*) FROM spend").fetchone()[0]); c.execute("INSERT INTO spend VALUES ('a',5)") if c.execute("SELECT count(*) FROM spend").fetchone()[0] == 0 else None
    except psycopg.Error as e: print("PG-REFUSED", lab, e.sqlstate, str(e).split("\n")[0][:100])
try: c.execute(f"CREATE OR REPLACE FUNCTION g() RETURNS void LANGUAGE sql SECURITY DEFINER LEAKPROOF {SP} BEGIN ATOMIC SELECT 1; END"); print("PG-ACCEPTED R10 LEAKPROOF by non-superuser")
except psycopg.Error as e: print("PG-REFUSED R10 LEAKPROOF by non-superuser", e.sqlstate, str(e).split("\n")[0][:100])
