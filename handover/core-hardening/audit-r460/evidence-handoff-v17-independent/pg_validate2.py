"""Run each spelling from spellings.json on a scratch database and report whether Postgres accepted it and whether a SECURITY DEFINER routine now exists."""
import sys, os, json
import psycopg
sock = sys.argv[1]; pw = os.environ["HV_ADMIN_PW"]
C = json.load(open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[0])), "spellings2.json")))
adm = psycopg.connect(f"host={sock} dbname=postgres user=postgres password={pw}", autocommit=True)
for k, t in C.items():
    db = "w" + k[:2]; adm.execute(f"CREATE DATABASE {db}")
    c = psycopg.connect(f"host={sock} dbname={db} user=postgres password={pw}", autocommit=True)
    err = None
    try:
        if k.startswith(("04", "17")): c.execute("CREATE FUNCTION evil() RETURNS int LANGUAGE sql AS 'SELECT 1'")
        c.execute(t)
    except psycopg.Error as e: err = f"{e.sqlstate} {str(e).splitlines()[0][:80]}"
    r = c.execute("SELECT p.proname, p.prosecdef, coalesce(p.proacl::text,'NULL(=PUBLIC can execute)') FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public' ORDER BY 1").fetchall()
    print(f"{k[:70]} | pg_error={err} | secdef_routines={[x for x in r if x[1]]}")
