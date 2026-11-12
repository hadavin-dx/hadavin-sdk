"""Mutants of the kill switch stop state (P2a-1). Each reverts ONE guard in a temp copy of the package; the pinned
test must fail with a line holding ``expect``. Run from the repo root with HADAVIN_TEST_PG_DSN set (the database
killers need it):

    uv run python tests/stop_state_mutants.py            # all; exit 1 if any mutant is not good
    uv run python tests/stop_state_mutants.py stale      # only mutants whose name contains the text

Not collected by pytest. Uses the runner of ``tools/mutation_runner.py``."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
LIM = "src/hadavin_sdk/limits.py"
MIG = "src/hadavin_sdk/store/migrate.py"
PG = "src/hadavin_sdk/store/postgres.py"
LOOP = "src/hadavin_sdk/runtime/agent_loop.py"
CLI = "src/hadavin_sdk/cli.py"
STOP = "src/hadavin_sdk/runtime/stop_state.py"


def mutant(name, file, old, new, test_file, killer, expect, **kw):
    stem = test_file.removesuffix(".py")
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        **{"pinned": f"{stem}::{killer}", **kw},
    )


DB = "tests/test_stop_state_db.py"
LIMT = "tests/test_stop_state_limits.py"
PRB = "tests/test_stop_state_probe.py"
CL = "tests/test_stop_state_cli.py"
LP = "tests/test_stop_state_loop.py"

M = [
    mutant("limits: demo is accepted as a stage", LIM,
        "        if environment not in _STAGES:", "        if False:",
        LIMT, "test_only_dev_pilot_prod_are_stages_and_demo_is_not_an_alias_of_dev", "Regex pattern did not match", pinned="tests/test_stop_state_limits::test_only_dev_pilot_prod_are_stages_and_demo_is_not_an_alias_of_dev[demo]"),
    mutant("limits: a busy stop is not tried again", LIM,
        "        except StoreBusy:\n", "        except ZeroDivisionError:\n",
        LIMT, "test_a_busy_stop_is_tried_once_more_then_works", "StoreBusy", allow_crash=True, crash_type="StoreBusy"),
    mutant("cli: a pilot stop without a key name is a traceback", CLI,
        '    elif cfg.environment != "demo":', "    elif False:",
        CL, "test_stop_on_pilot_without_a_label_key_name_works_not_a_traceback", "label key is required",
        allow_crash=True, crash_type="ValueError"),
    mutant("probe: a busy database is read as a finding", STOP,
        "        return ProbeResult(INCONCLUSIVE)", "        return ProbeResult(FAILED, ('busy',))",
        LIMT, "test_probe_verdicts", "assert"),
]  # fmt: skip

# Database and app killers: the runner gives a mutant run no DSN and no conftest (by design), so these are run by
# hand against a local database (see the builder report). They are listed so the plan is complete.
HAND = [
    mutant("migrate: the lock bound is not put back after a file", MIG,
        "            _set_lock_timeout(db, lock_timeout_ms)\n            db.execute(\"INSERT INTO schema_migrations",
        "            db.execute(\"INSERT INTO schema_migrations",
        DB, "test_a_migration_file_cannot_lengthen_the_table_lock_bound", "assert"),
    mutant("reset: the version is not compared (stale pair)", MIG,
        "IF p_expected_version IS NULL OR v <> p_expected_version THEN",
        "IF p_expected_version IS NULL THEN",
        DB, "test_a_stale_pair_from_before_another_reset_cannot_clear_a_newer_stop", "assert"),
    mutant("reset: the open count is not compared", MIG,
        "IF p_expected_open IS NULL OR n <> p_expected_open OR (n = 0 AND NOT was_on) THEN",
        "IF p_expected_open IS NULL OR (n = 0 AND NOT was_on) THEN",
        DB, "test_a_stale_pair_is_refused_with_hd003_and_the_switch_stays_on", "assert"),
    mutant("probe: the group check matches a substring", PG,
        "SELECT strpos(%s, quote_literal(%s) || '::text') > 0",
        "SELECT strpos(%s, %s) > 0",
        PRB, "test_the_group_check_is_exact_not_a_substring", "assert"),
    mutant("loop: the recheck does not guard an unreadable limits store", LOOP,
        '            return "recheck.limits_unavailable"', "            raise",
        LP, "test_unreadable_limits_at_the_recheck_needs_a_person_and_nothing_runs", "limits store down",
        allow_crash=True, crash_type="RuntimeError"),
]  # fmt: skip

if __name__ == "__main__":
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:60]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:150], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [LIMT, CL],
        extra_dirs=("tests", "tools", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
