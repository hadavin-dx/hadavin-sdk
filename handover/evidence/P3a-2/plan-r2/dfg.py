"""Probes d, f, g for P3a-2 errata rev 2. Throwaway PG16 cluster, made-up roles only."""
import socket, sys, threading, time
import psycopg
from psycopg import conninfo, errors

SOCK, PORT = sys.argv[1], int(sys.argv[2])
SU = f"host={SOCK} port={PORT} user=postgres dbname=pd"

def su():
    return psycopg.connect(SU, autocommit=True)

print("== setup")
with psycopg.connect(f"host={SOCK} port={PORT} user=postgres dbname=postgres", autocommit=True) as c:
    c.execute("CREATE DATABASE pd")
with su() as c:
    for s in ("CREATE ROLE dlogin LOGIN", "CREATE ROLE drole", "GRANT drole TO dlogin",
              "CREATE ROLE gmig LOGIN", "CREATE TABLE ledger (v text)", "GRANT ALL ON ledger TO gmig",
              "CREATE TABLE p (i int PRIMARY KEY)",
              "CREATE TABLE ch (i int REFERENCES p DEFERRABLE INITIALLY DEFERRED)", "GRANT ALL ON p, ch TO gmig"):
        c.execute(s)

print("\n== (d1) make_conninfo: DSN with options=-c role=drole, plus keyword options=-c search_path=pg_catalog,pg_temp")
dsn = f"host={SOCK} port={PORT} user=dlogin dbname=pd options='-c role=drole'"
merged = conninfo.make_conninfo(dsn, options="-c search_path=pg_catalog,pg_temp")
print("merged conninfo:", merged)
print("options in merged dict:", conninfo.conninfo_to_dict(merged).get("options"))
print("== (d2) a real connection with the DSN alone")
with psycopg.connect(dsn) as c:
    print("current_user, session_user, search_path:", c.execute("SELECT current_user, session_user, current_setting('search_path')").fetchone())
print("== (d3) a real connection with the DSN plus the keyword")
with psycopg.connect(dsn, options="-c search_path=pg_catalog,pg_temp") as c:
    print("current_user, session_user, search_path:", c.execute("SELECT current_user, session_user, current_setting('search_path')").fetchone())

print("\n== (f1) COMMIT that the server refuses: deferred foreign key violated at COMMIT")
c = psycopg.connect(f"host={SOCK} port={PORT} user=gmig dbname=pd")
c.execute("INSERT INTO ch VALUES (42)")
try:
    c.commit()
except psycopg.Error as e:
    print("class:", type(e).__name__, "| sqlstate:", e.sqlstate, "| transaction_status after:", c.info.transaction_status.name, "| closed:", c.closed)
c.close()

print("\n== (f2) connection cut AFTER the COMMIT message reached the server (TCP proxy forwards COMMIT, then drops the reply)")
srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); pport = srv.getsockname()[1]
def proxy():
    cli, _ = srv.accept()
    up = socket.socket(socket.AF_UNIX); up.connect(f"{SOCK}/.s.PGSQL.{PORT}")
    cut = threading.Event()
    def c2s():
        while True:
            d = cli.recv(65536)
            if not d: break
            up.sendall(d)
            if b"COMMIT\x00" in d:
                time.sleep(0.5)  # let the server finish the commit
                cut.set(); cli.shutdown(socket.SHUT_RDWR); cli.close(); return
    def s2c():
        while not cut.is_set():
            try:
                d = up.recv(65536)
            except OSError:
                return
            if not d or cut.is_set(): return
            try: cli.sendall(d)
            except OSError: return
    t1 = threading.Thread(target=c2s); t2 = threading.Thread(target=s2c); t1.start(); t2.start(); t1.join(); time.sleep(0.2); up.close()
threading.Thread(target=proxy, daemon=True).start()
c = psycopg.connect(f"host=127.0.0.1 port={pport} user=gmig dbname=pd sslmode=disable")
c.execute("INSERT INTO ledger VALUES ('0099_made_up')")
try:
    c.commit()
    print("commit returned normally")
except psycopg.Error as e:
    print("class:", type(e).__name__, "| sqlstate:", e.sqlstate, "| message:", str(e).splitlines()[0][:120])
    print("transaction_status after:", c.info.transaction_status.name, "| closed:", c.closed)
with su() as s:
    print("row visible on a NEW connection (the commit happened):", s.execute("SELECT count(*) FROM ledger WHERE v = '0099_made_up'").fetchone()[0])

print("\n== (g1) ALTER ROLE gmig SET statement_timeout = 1 (as the role itself), then fresh connections")
with psycopg.connect(f"host={SOCK} port={PORT} user=gmig dbname=pd", autocommit=True) as c:
    c.execute("ALTER ROLE gmig SET statement_timeout = 1")
Q = open(sys.argv[3]).read()  # the Q2-shaped catalog read (all access-list columns)
def fresh(first=None, n=100):
    ok = cancelled = other = 0
    for _ in range(n):
        try:
            with psycopg.connect(f"host={SOCK} port={PORT} user=gmig dbname=pd", autocommit=True) as c:
                c.execute("SET TIME ZONE 'UTC'")  # what store/postgres.connect sends
                with c.transaction():
                    c.execute("SET LOCAL search_path = pg_catalog, pg_temp")
                    if first: c.execute(first)
                    c.execute(Q).fetchall()
            ok += 1
        except errors.QueryCanceled:
            cancelled += 1
        except psycopg.Error as e:
            other += 1; print("other:", type(e).__name__, e.sqlstate)
    return ok, cancelled, other
with psycopg.connect(f"host={SOCK} port={PORT} user=gmig dbname=pd") as c:
    print("statement_timeout seen by a fresh session:", c.execute("SHOW statement_timeout").fetchone()[0])
print("(g2) no limit set by the step (100 fresh connections): ok, cancelled 57014, other =", fresh())
print("(g3) step sets SET LOCAL statement_timeout = '60s' first (100 fresh connections): ok, cancelled, other =",
      fresh("SET LOCAL statement_timeout = '60s'; SET LOCAL lock_timeout = '5s'"))
with su() as s:
    s.execute("ALTER ROLE gmig RESET statement_timeout")
print("done")
