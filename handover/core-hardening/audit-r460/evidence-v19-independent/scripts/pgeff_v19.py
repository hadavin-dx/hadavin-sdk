import sys, os, secrets
sock = sys.argv[1]; import psycopg
pw = os.environ["HV_ADMIN_PW"]
a = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={pw}", autocommit=True)
mp = secrets.token_hex(8); a.execute(f"CREATE ROLE mg LOGIN PASSWORD '{mp}'"); a.execute("CREATE DATABASE h OWNER mg")
c = psycopg.connect(f"host={sock} dbname=h user=mg password={mp}", autocommit=True)
c.execute("CREATE TABLE spend (agent_id text, day date, usd numeric)")
for lab, q in [("H42 CHECK pg_read_file on EMPTY table", "ALTER TABLE spend ADD CONSTRAINT c CHECK (pg_read_file('/etc/hostname') <> '')"),
               ("H42b same after one row exists", None), ("H43 DEFAULT current_setting", "ALTER TABLE spend ADD COLUMN z text DEFAULT current_setting('server_version')"),
               ("H90 index on lower()", "CREATE INDEX i ON spend (lower(agent_id))"), ("H90b index on pg_read_file (needs IMMUTABLE)", "CREATE INDEX i2 ON spend (pg_read_file(agent_id))")]:
    if q is None:
        c.execute("INSERT INTO spend(agent_id,day,usd) VALUES ('a','2026-11-16',1)")
        q = "ALTER TABLE spend ADD CONSTRAINT c2 CHECK (pg_read_file('/etc/hostname') <> '')"
    try: c.execute(q); print("PG-ACCEPTED", lab)
    except psycopg.Error as e: print("PG-REFUSED", lab, e.sqlstate, str(e).split("\n")[0][:100])
