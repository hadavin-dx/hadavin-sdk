"""Rev 3 probe part 3: the database owner read when the database's access list holds no row (readiness m1), and the new
version-and-owner read. Throwaway 16.15 cluster. Usage: python p3c.py <socket dir> <port> <dir of queries.py>"""
import sys, psycopg
SOCK, PORT = sys.argv[1], sys.argv[2]
sys.path.insert(0, sys.argv[3]); import queries as q
d = lambda u="postgres", db="r3y": f"host={SOCK} port={PORT} user={u} dbname={db}"
with psycopg.connect(d(db="postgres"), autocommit=True) as c:
    c.execute("DROP DATABASE IF EXISTS r3y WITH (FORCE)"); c.execute("CREATE DATABASE r3y OWNER r3_mig")
    c.execute("REVOKE ALL ON DATABASE r3y FROM PUBLIC")  # a common hardening step; the owner keeps its own rights
    print("datacl now:", c.execute("SELECT datacl::text FROM pg_database WHERE datname='r3y'").fetchone())
with psycopg.connect(d("r3_mig")) as c:
    with c.transaction():
        c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
        cur = c.execute(q.Q2, dict(named=["r3_rt"], family=["r3_mig"], schema="public", roles=["r3_rt"], managed=[])); cols = [x.name for x in cur.description]
        db_rows = [r for r in cur.fetchall() if dict(zip(cols, r))["kind"] == "database"]
        print("Q2 database rows:", len(db_rows))
        V2 = ("SELECT pg_catalog.current_setting('server_version_num')::int AS version_num, "
              "pg_catalog.pg_get_userbyid(d.datdba) AS database_owner FROM pg_catalog.pg_database d WHERE d.datname = pg_catalog.current_database()")
        print("V2 version and owner:", c.execute(V2).fetchone())
        raise psycopg.Rollback()
with psycopg.connect(d(db="postgres"), autocommit=True) as c: c.execute("DROP DATABASE r3y WITH (FORCE)")
