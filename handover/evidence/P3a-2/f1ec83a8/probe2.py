import os, sys, uuid
sys.argv=['x']
src = open(os.path.join(os.path.dirname(__file__), 'probe.py')).read().split("print(\"PART A")[0]
exec(src)
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
print("PART C2: injections that skip the test helper's own first use of the statement; migrate's own use fires")
orig_exec = psycopg.Connection.execute
for marker, skip in (("pg_advisory_xact_lock", 1), ("pg_roles", 1)):
    schema, dsn = fresh(); st={"n":0}
    def fake(self, query, *a, **k):
        t = query if isinstance(query, str) else str(query)
        if marker in t:
            st["n"] += 1
            if st["n"] == skip + 1: raise psycopg.OperationalError("injected: connection lost")
        return orig_exec(self, query, *a, **k)
    psycopg.Connection.execute = fake
    try: res = run(dsn)
    finally: psycopg.Connection.execute = orig_exec
    print(f"{marker!r} (skip {skip}) seen={st['n']} | {res[0]} ({res[1][:170]}) | {len(tables(schema))} | {rows(schema)}"); drop(schema)
orig_commit = psycopg.Connection._commit_gen
def mk(kind):
    n = [0]
    def g(self):
        n[0] += 1
        if n[0] == 1: yield from orig_commit(self); return   # the test helper's own transaction
        if kind == "before":
            raise psycopg.OperationalError("injected: connection lost at COMMIT (before it reached the server)")
        yield from orig_commit(self)
        raise psycopg.OperationalError("injected: connection lost after COMMIT ran (reply lost)")
    return g
for kind in ("before", "after"):
    schema, dsn = fresh(); psycopg.Connection._commit_gen = mk(kind)
    try: res = run(dsn)
    finally: psycopg.Connection._commit_gen = orig_commit
    print(f"COMMIT {kind} | {res[0]} ({res[1][:230]}) | tables {len(tables(schema))} | ledger rows {rows(schema)}"); drop(schema)
# commit refused by the server with a real SQLSTATE (40001) while the session is idle
import psycopg.errors as pge
class Refused(pge.SerializationFailure): pass
for code, cls in (("40001", pge.SerializationFailure), ("40003", pge.StatementCompletionUnknown)):
    schema, dsn = fresh(); n=[0]
    def g(self, cls=cls):
        n[0]+=1
        if n[0]==1: yield from orig_commit(self); return
        # real rollback so the session is IDLE, then report the server's refusal
        yield from self._rollback_gen()
        raise cls("injected refusal")
    psycopg.Connection._commit_gen = g
    try: res = run(dsn)
    finally: psycopg.Connection._commit_gen = orig_commit
    print(f"COMMIT refused sqlstate {code} after real rollback | {res[0]} ({res[1][:230]}) | tables {len(tables(schema))} | ledger rows {rows(schema)}"); drop(schema)
