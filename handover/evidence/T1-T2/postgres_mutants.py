"""Plant one mutation at a time in a temp copy of the branch's postgres store and run the store time-rule tests on a
real Postgres (HADAVIN_TEST_PG_DSN). Usage: python postgres_mutants.py <worktree> (env HADAVIN_TEST_PG_DSN set).
The runner tools/mutation_runner.py strips the DSN from its child, so it cannot run these; this script can."""
import os, shutil, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1]).resolve()
TARGET = "src/hadavin_sdk/store/postgres.py"
TEST = "tests/contracts/test_store_time_rules.py"
M = [
    ("P1 day counter replaced instead of added", "DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd", "DO UPDATE SET usd = EXCLUDED.usd RETURNING usd"),
    ("P2 month counter replaced instead of added", "DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd", "DO UPDATE SET usd = EXCLUDED.usd"),
    ("P3 add_spend keys the month counter by the day", "month = day.replace(day=1)\n        with self._lock, self._db.transaction():", "month = day\n        with self._lock, self._db.transaction():"),
    ("P4 spend_totals reads the month counter by the day", "(agent_id, day.replace(day=1)),", "(agent_id, day),"),
]

def run(mut):
    tmp = Path(tempfile.mkdtemp(prefix="pgmut_"))
    try:
        for d in ("src", "tests", "tools"):
            shutil.copytree(root / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        shutil.copy(root / "pyproject.toml", tmp)
        if mut:
            f = tmp / TARGET
            text = f.read_text()
            assert text.count(mut[1]) == 1, f"{mut[0]}: old text found {text.count(mut[1])} times"
            f.write_text(text.replace(mut[1], mut[2]))
        env = dict(os.environ, PYTHONPATH=f"{tmp / 'src'}{os.pathsep}{tmp}")
        out = subprocess.run([sys.executable, "-m", "pytest", TEST, "-q", "-k", "postgres", "-p", "no:cacheprovider", "--tb=line", "-x" if False else "-q"],
                             cwd=tmp, env=env, capture_output=True, text=True)
        lines = out.stdout.strip().splitlines()
        failed = [l for l in lines if l.startswith("FAILED") or l.startswith("/")]
        return out.returncode, lines[-1] if lines else "", failed[:3]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

rc, last, _ = run(None)
print(f"baseline rc={rc} :: {last}")
bad = rc != 0
for m in M:
    rc, last, failed = run(m)
    print(f"{'KILLED' if rc == 1 else 'SURVIVED/ERR rc=%d' % rc} {m[0]} :: {last}")
    for f in failed:
        print("     ", f[:200])
    bad |= rc != 1
sys.exit(1 if bad else 0)
