"""EVIDENCE RUNNER script: plants ONE a1 harness mutant at a time in the copy /home/user/build/EV-A3-mut (never the
full-run copy), runs its killer tests, restores the file in `finally`. Prints one line per mutant plus the failing lines.
The mutants are my reading of ticket tickets/P4d.md "Mutation plan" a1-1..a1-6 (the repo has no runner for them)."""
import pathlib, subprocess, sys, os
R = pathlib.Path("/home/user/build/EV-A3-mut")
PY = "/home/user/build/venv-A3-313/bin/python"
K = "tests/contracts/kinds/__init__.py"
SS = "tests/contracts/store_support.py"
CF = "tests/contracts/conftest.py"
PGK = "tests/contracts/kinds/store_postgres.py"
BI = "tests/contracts/kinds/builtin.py"
REG = "tests/contracts/test_store_registry.py"
TS = "tests/contracts/test_store.py"
M = [
 ("a1-1 require_backend never fails (always skips)", K, "    if _fail_rule():\n        pytest.fail(", "    if False:\n        pytest.fail(", [REG]),
 ("a1-2a session-end skip check removed", SS, 'if reason.startswith("require_backend:")', "if False", [REG]),
 ("a1-2b session-end counts ALL skips", SS, 'if reason.startswith("require_backend:")', "if True", [REG]),
 ("a1-2c session-end check inactive under the fail rule", SS, "if not state.fail_rule or not state.selected:", "if True:", [REG]),
 ("a1-3 proxy counts fixture calls (records outside test body)", SS, "        if self.in_body:\n            self.called.add", "        if True:\n            self.called.add", [REG]),
 ("a1-4 postgres store_pair yields one connection twice", PGK, "a, b = _open_split(dsn), _open_split(dsn)", "a = b = _open_split(dsn)", [TS, "-k", "store_pair_gives_two_handles"]),
 ("a1-5 memory pair is two separate stores (pair identity/shared data lost)", BI, "    return store, store\n", "    return store, make(\"store\", KindSettings(kind=\"memory\"))\n", [TS, "-k", "store_pair_gives_two_handles"]),
 ("a1-6 connect_runtime returns the admin connection", PGK, "        return psycopg.connect(dsn, autocommit=autocommit)\n\n    @contextlib", "        return psycopg.connect(OWNER_DSN.get(dsn, dsn), autocommit=autocommit)\n\n    @contextlib", [None]),
]
env = dict(os.environ, HADAVIN_TEST_PG_DSN="postgresql://postgres@127.0.0.1:55400/a3_evmut", PGHOST="127.0.0.1", PGPORT="55400", PGUSER="postgres")
def run(sel, label):
    r = subprocess.run([PY, "-m", "pytest", "-q", "-x", "-p", "no:cacheprovider", *sel], cwd=R, env=env, capture_output=True, text=True)
    out = r.stdout.splitlines()
    return r.returncode, [l for l in out if l.startswith("FAILED") or " passed" in l or " failed" in l][:4]
rc, tail = run([REG, TS, "-k", "pair or registry or require or session or proxy or connect"], "baseline")
print("== baseline (unmutated):", "PASS" if rc == 0 else f"NOT GREEN rc={rc}", tail, flush=True)
for name, f, old, new, sel in M:
    p = R / f
    src = p.read_text()
    if src.count(old) != 1:
        print(f"== {name}: PLANT FAILED (old text occurs {src.count(old)}x)", flush=True); continue
    if sel == [None]:
        sel = ['tests/contracts/test_store_reserve_pg.py', 'tests/contracts/test_store_reserve_proofs_pg.py', '-k', 'current_user or runtime or role or identity or privilege']
    try:
        p.write_text(src.replace(old, new))
        rc, tail = run(sel, name)
    finally:
        p.write_text(src)
    print(f"== {name}: {'KILLED' if rc != 0 else 'SURVIVED'} (rc={rc}) sel={' '.join(sel)[:120]}", flush=True)
    for l in tail: print("   ", l[:200], flush=True)
