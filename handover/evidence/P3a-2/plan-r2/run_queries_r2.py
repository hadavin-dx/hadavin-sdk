import sys, time, psycopg
sys.path.insert(0, sys.argv[3]); import queries as q
SOCK, PORT = sys.argv[1], sys.argv[2]
SU = f"host={SOCK} port={PORT} user=postgres dbname=pq2"
with psycopg.connect(f"host={SOCK} port={PORT} user=postgres dbname=postgres", autocommit=True) as c:
    c.execute("CREATE DATABASE pq2")
setup = """
CREATE ROLE q_mig LOGIN; CREATE ROLE q_rt LOGIN; CREATE ROLE q_po LOGIN; CREATE ROLE q_pu LOGIN; CREATE ROLE q_grp; CREATE ROLE q_third; CREATE ROLE q_boss;
CREATE SCHEMA app AUTHORIZATION q_mig; CREATE SCHEMA other;
GRANT pg_monitor TO q_rt; GRANT q_grp TO q_po WITH INHERIT FALSE, SET TRUE;
SET ROLE q_mig;
CREATE TABLE app.runs (id int PRIMARY KEY, note text); CREATE TABLE app.extra (i int);
CREATE FUNCTION app.trg() RETURNS trigger LANGUAGE plpgsql AS $$BEGIN RETURN NEW; END$$;
CREATE FUNCTION app.door(q text) RETURNS int LANGUAGE sql SECURITY DEFINER AS 'SELECT 1';
CREATE TYPE app.comp AS (a int);
GRANT USAGE ON SCHEMA app TO q_rt, q_po, q_pu, q_boss;
GRANT SELECT, INSERT ON app.runs TO q_rt; GRANT SELECT ON app.runs TO q_boss WITH GRANT OPTION; GRANT SELECT ON app.extra TO q_third;
RESET ROLE;
SET ROLE q_boss; GRANT SELECT ON app.runs TO q_po; RESET ROLE;
CREATE TABLE other.secret (i int); CREATE TABLE app.handed (i int); ALTER TABLE app.handed OWNER TO q_third; GRANT SELECT ON other.secret TO q_grp; GRANT SELECT ON other.secret TO PUBLIC;
ALTER DEFAULT PRIVILEGES FOR ROLE q_mig IN SCHEMA app GRANT SELECT ON TABLES TO q_rt;
"""
with psycopg.connect(SU, autocommit=True) as c:
    c.execute(setup)
    # a 25-level diamond ladder of groups under q_pu: level i has dia_a_i and dia_b_i, each a member of both roles of level i+1
    for i in range(26):
        c.execute(f"CREATE ROLE dia_a_{i}; CREATE ROLE dia_b_{i}")
    for i in range(25):
        for x in "ab":
            c.execute(f"GRANT dia_a_{i+1}, dia_b_{i+1} TO dia_{x}_{i}")
    c.execute("GRANT dia_a_0, dia_b_0 TO q_pu")
P = dict(named=["q_rt", "q_po", "q_pu"], family=["q_mig"], schema="app", roles=["q_rt", "q_po", "q_pu"], managed=["trg"])
with psycopg.connect(f"host={SOCK} port={PORT} user=q_mig dbname=pq2") as c:
    print("connected as", c.execute("SELECT current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user)").fetchone())
    for name in ("Q1", "Q1B", "Q2", "Q3", "Q4", "STEP4"):
        with c.transaction():
            c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
            t = time.perf_counter(); rows = c.execute(getattr(q, name), P).fetchall(); ms = (time.perf_counter() - t) * 1000
            raise_rb = True
            print(f"\n== {name}: {len(rows)} rows, {ms:.1f} ms")
            show = rows if name != "Q1" else [r for r in rows if not r[1].startswith("dia_")] + [("...", f"{sum(1 for r in rows if r[1].startswith('dia_'))} dia_* rows", None)]
            for r in show[:60]: print("  ", r)
            raise psycopg.Rollback()
print("\n== the old Q1 shape (UNION ALL with depth) on the same ladder, limited to 10 s")
OLD = """WITH RECURSIVE closure(root, role, depth) AS (SELECT r.oid, r.oid, 0 FROM pg_catalog.pg_roles r WHERE r.rolname = 'q_pu'
 UNION ALL SELECT c.root, m.roleid, c.depth + 1 FROM closure c JOIN pg_catalog.pg_auth_members m ON m.member = c.role)
SELECT count(*) FROM closure"""
with psycopg.connect(f"host={SOCK} port={PORT} user=q_mig dbname=pq2", autocommit=True) as c:
    c.execute("SET statement_timeout = '10s'")
    t = time.perf_counter()
    try:
        print("rows:", c.execute(OLD).fetchone()[0])
    except psycopg.errors.QueryCanceled:
        print("cancelled by the 10 s limit")
    print(f"{time.perf_counter() - t:.1f} s")
