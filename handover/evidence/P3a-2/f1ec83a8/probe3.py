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

import psycopg.errors as pge
orig_ec = psycopg.Connection._exec_command
def mk(kind, cls=None):
    n = [0]
    def g(self, command, *a, **k):
        if command == b"COMMIT" or (isinstance(command, (bytes, str)) and bytes(command if isinstance(command, bytes) else command.encode()).strip().upper() == b"COMMIT"):
            n[0] += 1
            if n[0] == 2:   # 1 = the test helper's own transaction
                if kind == "before":
                    raise psycopg.OperationalError("injected: connection lost at COMMIT (before it reached the server)")
                if kind == "refused":
                    yield from orig_ec(self, b"ROLLBACK")      # server rolled back, session idle
                    raise cls("injected refusal")
                yield from orig_ec(self, command, *a, **k)
                raise psycopg.OperationalError("injected: connection lost after COMMIT ran (reply lost)")
        return (yield from orig_ec(self, command, *a, **k))
    return g, n
for label, kind, cls in (("COMMIT lost before reaching server (no SQLSTATE)", "before", None), ("COMMIT ran, reply lost (no SQLSTATE)", "after", None),
                         ("server refuses COMMIT 40001, rolled back, session idle", "refused", pge.SerializationFailure),
                         ("server refuses COMMIT 40003, rolled back, session idle", "refused", pge.StatementCompletionUnknown),
                         ("server refuses COMMIT 23505 (unique violation class 23), rolled back, idle", "refused", pge.UniqueViolation)):
    schema, dsn = fresh(); fn, n = mk(kind, cls); psycopg.Connection._exec_command = fn
    try: res = run(dsn)
    finally: psycopg.Connection._exec_command = orig_ec
    print(f"{label} | commits seen {n[0]} | {res[0]} ({res[1][:260]}) | tables {len(tables(schema))} | ledger rows {rows(schema)}"); drop(schema)
