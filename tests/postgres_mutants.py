"""Mutants of the postgres spend ledger (the production money store), run against the meter contract tests on a real
PostgreSQL. Each mutant changes ONE thing in a temp copy of ``src/hadavin_sdk/store/postgres.py``; the tests of
``tests/contracts/test_store_time_rules.py`` and ``tests/contracts/test_t1_meter_cap.py`` (postgres cases only) must
fail, and a failing test line must be an ASSERTION holding the mutant's ``expect`` text. A mutant that only crashes is
not good, except the one marked ``constraint`` (it shows the database's own CHECK as a second guard).

``tools/mutation_runner.py`` cannot run these: it strips the database address from its child process and runs without
conftest files. This script keeps the one variable it needs, HADAVIN_TEST_PG_DSN, and nothing else of the caller's
environment except the basics. Not collected by pytest. Run from the repo root, against a throwaway database:

    HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:5432/postgres python tests/postgres_mutants.py
    python tests/postgres_mutants.py P3         # only mutants whose name contains the text

Exit 0 only if the unmutated copy passes and every mutant is killed as described. Without the variable the script
FAILS (exit 2): a run that skipped the postgres cases would prove nothing.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = "src/hadavin_sdk/store/postgres.py"
TESTS = [
    "tests/contracts/test_store_time_rules.py",
    "tests/contracts/test_t1_meter_cap.py",
]
KEEP_ENV = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "HADAVIN_TEST_PG_DSN",
)  # nothing else is passed on
TIMEOUT_S = 900.0

DAY_UPSERT = "DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd"
MONTH_UPSERT = "DO UPDATE SET usd = spend_month.usd + EXCLUDED.usd"
MONTH_KEY = "month = day.replace(day=1)\n        with self._lock, self._db.transaction():"
MONTH_READ_KEY = "(agent_id, day.replace(day=1)),"
DAY_INSERT = (
    '"INSERT INTO spend (agent_id, day, usd) VALUES (%s, %s, %s) "\n'
    '                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd",\n'
    "                (agent_id, day, usd),"
)
MONTH_KEY_EARLY = (
    "month = (day.replace(day=1) - __import__('datetime').timedelta(days=1)).replace(day=1)\n"
    "        with self._lock, self._db.transaction():"
)
MONTH_KEY_NO_YEAR = (
    "month = day.replace(year=2000, day=1)\n        with self._lock, self._db.transaction():"
)
DAY_INSERT_SERVER_DATE = (
    '"INSERT INTO spend (agent_id, day, usd) VALUES (%s, CURRENT_DATE, %s) "\n'
    '                "ON CONFLICT (agent_id, day) DO UPDATE SET usd = spend.usd + EXCLUDED.usd RETURNING usd",\n'
    "                (agent_id, usd),"
)


@dataclass(frozen=True)
class PgMutant:
    name: str
    changes: tuple[
        tuple[str, str], ...
    ]  # (old, new) pairs, each ``old`` found exactly once in TARGET
    expect: str  # text of the failing assertion message
    constraint: bool = False  # the kill is a schema CHECK error, not an assertion


M = [
    PgMutant(
        "P1 day counter replaced instead of added",
        ((DAY_UPSERT, "DO UPDATE SET usd = EXCLUDED.usd RETURNING usd"),),
        "the day total of two charges on one day did not add up",
    ),
    PgMutant(
        "P2 month counter replaced instead of added",
        ((MONTH_UPSERT, "DO UPDATE SET usd = EXCLUDED.usd"),),
        "the month total of two charges did not add up",
    ),
    PgMutant(
        "P3 add_spend books the month one month early (a valid first-of-month date, so the CHECK passes)",
        ((MONTH_KEY, MONTH_KEY_EARLY),),
        "read at",
    ),
    PgMutant(
        "P3b add_spend keys the month counter by the day (killed by the schema CHECK, an error, not an assertion)",
        ((MONTH_KEY, "month = day\n        with self._lock, self._db.transaction():"),),
        "CheckViolation",
        constraint=True,
    ),
    PgMutant(
        "P4 spend_totals reads the month counter by the day",
        ((MONTH_READ_KEY, "(agent_id, day),"),),
        "read at",
    ),
    PgMutant(
        "P5 spend_totals reads the day counter of any agent",
        (
            (
                '"SELECT usd FROM spend WHERE agent_id = %s AND day = %s", (agent_id, day)',
                '"SELECT usd FROM spend WHERE %s::text IS NOT NULL AND day = %s ORDER BY usd DESC LIMIT 1", (agent_id, day)',
            ),
        ),
        "spend_totals showed this agent's spend to another agent",
    ),
    PgMutant(
        "P6 spend_totals reads the month counter of any agent",
        (
            (
                '"SELECT usd FROM spend_month WHERE agent_id = %s AND month = %s",',
                '"SELECT usd FROM spend_month WHERE %s::text IS NOT NULL AND month = %s ORDER BY usd DESC LIMIT 1",',
            ),
        ),
        "spend_totals showed this agent's spend to another agent",
    ),
    PgMutant(
        "P7 the day counter ignores every charge after the first",
        ((DAY_UPSERT, "DO UPDATE SET usd = spend.usd RETURNING usd"),),
        "the day total of two charges on one day did not add up",
    ),
    PgMutant(
        "P8 the month counter ignores every charge after the first",
        ((MONTH_UPSERT, "DO UPDATE SET usd = spend_month.usd"),),
        "the month total of two charges did not add up",
    ),
    PgMutant(
        "P9 the year is dropped from the month key (add_spend and spend_totals)",
        (
            (MONTH_KEY, MONTH_KEY_NO_YEAR),
            (MONTH_READ_KEY, "(agent_id, day.replace(year=2000, day=1)),"),
        ),
        "a March of another year was added to the March of 2026",
    ),
    PgMutant(
        "P10 the day is taken from the database server's clock, not from the caller",
        ((DAY_INSERT, DAY_INSERT_SERVER_DATE),),
        "a charge on a past date is not on that date",
    ),
    PgMutant(
        "P11 the day counter rounds a charge to cents",
        (("(agent_id, day, usd),", "(agent_id, day, round(usd, 2)),"),),
        "the first tiny charge was rounded",
    ),
    PgMutant(
        "P12 the month counter is never written (every charge adds 0 to it)",
        (("(agent_id, month, usd),", "(agent_id, month, 0),"),),
        "the month total of two charges did not add up",
    ),
]


async def _run_pytest(cmd: list[str], cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    """One pytest child with a time limit; on a timeout the child is killed and the run fails loudly."""
    proc = await asyncio.create_subprocess_exec(
        *cmd, cwd=cwd, env=env, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), TIMEOUT_S)
    except TimeoutError:
        proc.kill()
        await proc.wait()
        raise
    return proc.returncode if proc.returncode is not None else -1, out.decode("utf-8", "replace")


def run(root: Path, mutant: PgMutant | None) -> tuple[int, str]:
    tmp = Path(tempfile.mkdtemp(prefix="pgmut_"))
    try:
        for d in ("src", "tests", "tools"):
            shutil.copytree(
                root / d, tmp / d, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache")
            )
        shutil.copy(root / "pyproject.toml", tmp)
        if mutant:
            target = tmp / TARGET
            text = target.read_text(encoding="utf-8")
            for old, new in mutant.changes:
                if text.count(old) != 1:
                    raise SystemExit(
                        f"{mutant.name}: the old text is found {text.count(old)} times, not once"
                    )
                text = text.replace(old, new)
            target.write_text(text, encoding="utf-8")
        env = {k: os.environ[k] for k in KEEP_ENV if k in os.environ}
        env["PYTHONPATH"] = os.pathsep.join([str(tmp / "src"), str(tmp)])
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            *TESTS,
            "-q",
            "-k",
            "postgres",
            "-p",
            "no:cacheprovider",
            "-p",
            "no:randomly",
            "--tb=line",
            "-rf",
        ]
        return asyncio.run(_run_pytest(cmd, tmp, env))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def judge(mutant: PgMutant, rc: int, stdout: str) -> tuple[bool, str]:
    failing = [
        ln for ln in stdout.splitlines() if ".py:" in ln and ("Error" in ln or "Violation" in ln)
    ]
    if rc != 1:
        return (
            False,
            f"pytest exit code {rc}, not 1 (a failing test); last line: {stdout.strip().splitlines()[-1:]}",
        )
    kind = "CheckViolation" if mutant.constraint else "AssertionError"
    hit = [ln for ln in failing if kind in ln and mutant.expect in ln]
    if not hit:
        return False, f"no {kind} line holds {mutant.expect!r}; first failing lines: {failing[:2]}"
    fails = [ln for ln in stdout.splitlines() if ln.startswith("FAILED ")]
    pick = next((ln for ln in fails if mutant.expect in ln), fails[0] if fails else "")
    test = pick.split("::")[-1].split(" ")[0] if pick else ""
    return True, (f"[{test}] " if test else "") + hit[0].strip()[-160:]


def main(argv: list[str]) -> int:
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print(
            "HADAVIN_TEST_PG_DSN is not set: the postgres cases would be skipped and prove nothing",
            file=sys.stderr,
        )
        return 2
    only = argv[1:]
    chosen = [x for x in M if not only or any(o in x.name for o in only)]
    if not chosen:
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        return 2
    try:
        rc, out = run(ROOT, None)
    except TimeoutError:
        print(f"baseline: pytest ran longer than {TIMEOUT_S:.0f} s and was killed", file=sys.stderr)
        return 1
    last = out.strip().splitlines()[-1] if out.strip() else "(no output)"
    print(f"baseline rc={rc} :: {last}", flush=True)
    if (
        rc != 0 or "skipped" in last
    ):  # a failing or skipped baseline proves nothing about any mutant
        print(
            "the unmutated copy must pass with no skipped case; no mutant was run", file=sys.stderr
        )
        return 1
    bad = False
    killed = 0
    for x in chosen:
        try:
            result = run(ROOT, x)
        except TimeoutError:
            print(
                f"BAD {x.name}\n      pytest ran longer than {TIMEOUT_S:.0f} s and was killed",
                flush=True,
            )
            bad = True
            continue
        good, why = judge(x, *result)
        print(f"{'ok ' if good else 'BAD'} {x.name}\n      {why}", flush=True)
        killed += good
        bad |= not good
    print(
        f"{killed} of {len(chosen)} mutants killed as described; {'PROBLEMS' if bad else 'no problems'}"
    )
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
