"""Mutants of the stop state (step B). Each reverts ONE guard; the pinned test of ``tests/test_stop_state_roles.py``
must fail, and its output must hold ``expect``. Not collected by pytest.

Same file format as the other mutant lists (``Mutant`` of ``tools/mutation_runner.py``), with one difference in how
they are run. The runner gives a mutant run no DSN and no conftest (by design: the child sees no secret of the
caller), and every killer here needs a real PostgreSQL and the ``cfg_dir`` fixtures. So the list ``M`` (mutants the
runner can run) is empty and all mutants are in ``HAND``. They are applied one at a time to THIS working tree, the
killer is run with the caller's HADAVIN_TEST_PG_DSN, and the file is put back byte for byte:

    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/stop_state_mutants.py --hand
    HADAVIN_TEST_PG_DSN=<dsn> uv run --all-extras --group test python tests/stop_state_mutants.py --hand flag
    uv run --all-extras --group test python tests/stop_state_mutants.py        # lists the mutants, runs nothing

``--hand`` refuses to start when a target file has uncommitted changes, runs the killer on the clean tree first (it
must pass, or the kill means nothing), and restores the file in a ``finally``. Exit 1 if any mutant is not KILLED.

A mutant of the migration file also breaks the released-manifest sha check
(``tests/test_migration_numbers_guards.py``); that does not count as the kill. The behaviour test named here does.

``PENDING`` names the ticket's mutants whose guard is not in the source at the commit these tests were written
against (the stop id was still a serial number and the loop hunk was not taken). Their killers exist and fail
there. Move them to ``HAND`` once the guard exists."""

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
TEST = "tests/test_stop_state_roles.py"
PIN = "tests/test_stop_state_roles::"
LIM = "src/hadavin_sdk/limits.py"
MIG = "src/hadavin_sdk/store/migrate.py"
PG = "src/hadavin_sdk/store/postgres.py"
CLI = "src/hadavin_sdk/cli.py"
SQL = "src/hadavin_sdk/store/migrations/0006_stop_state.sql"
LOOP = "src/hadavin_sdk/runtime/agent_loop.py"

DENIED = "test_runtime_login_is_denied_and_the_switch_stays_on"
N2 = "test_n2_a_reset_by_the_reset_login_reads_off"
N3 = "test_n3_cli_round_trip_in_pilot_with_only_the_reset_dsn_for_the_reset"
OWNER = "test_the_owner_is_refused_by_the_append_only_trigger"
RESET_BODY = (
    '        self.audit.write_intent(self._event(False, by, "reset"))\n'
    "        try:\n"
    "            self.store.set_kill_switch(KillSwitch(on=False, by=by))\n"
    "        except Exception:\n"
    '            self.audit.write_outcome(self._event(True, by, "reset_failed"))\n'
    "            raise\n"
)
CLEAR_FIRST = (
    "        self.store.set_kill_switch(KillSwitch(on=False, by=by))\n"
    '        self.audit.write_intent(self._event(False, by, "reset"))\n'
)
TRIGGERS = (
    "CREATE OR REPLACE TRIGGER kill_switch_stops_append_only BEFORE UPDATE OR DELETE ON kill_switch_stops\n"
    "    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();\n"
    "CREATE OR REPLACE TRIGGER kill_switch_stops_no_truncate BEFORE TRUNCATE ON kill_switch_stops\n"
    "    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();\n"
    "CREATE OR REPLACE TRIGGER kill_switch_clears_append_only BEFORE UPDATE OR DELETE ON kill_switch_clears\n"
    "    FOR EACH ROW EXECUTE FUNCTION hadavin_audit_append_only();\n"
    "CREATE OR REPLACE TRIGGER kill_switch_clears_no_truncate BEFORE TRUNCATE ON kill_switch_clears\n"
    "    FOR EACH STATEMENT EXECUTE FUNCTION hadavin_audit_append_only();\n"
)


def mutant(name, file, old, new, killer, expect):
    return Mutant(
        name, file, old, new, expect, test_file=TEST, only_test=killer, pinned=PIN + killer
    )


M: list[Mutant] = []  # nothing the runner can run without a database (see the module docstring)

HAND = [
    mutant("grants: the runtime may append to kill_switch_clears", MIG,
        '"kill_switch_clears": Grant("table", "SELECT", reset=_APPEND)',
        '"kill_switch_clears": Grant("table", _APPEND, reset=_APPEND)',
        DENIED, "DID NOT RAISE"),
    mutant("grants: the runtime is read-write on kill_switch again", MIG,
        '"kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE")',
        '"kill_switch": Grant("table", _RW, reset="SELECT, UPDATE")',
        DENIED, "DID NOT RAISE"),
    mutant("grants: the reset role may not append to audit_entries", MIG,
        '"audit_entries": Grant("table", _APPEND, portal=True, reset=_APPEND)',
        '"audit_entries": Grant("table", _APPEND, portal=True, reset="SELECT")',
        N3, "assert 3 == 0"),
    mutant("migrate: the reset block is skipped", MIG,
        "        if reset_role:\n            _apply_grants(db, reset_role, lambda g: g.reset)",
        "        if False:\n            _apply_grants(db, reset_role, lambda g: g.reset)",
        N2, "psycopg.errors."),
    mutant("migrate: effective_problems is not run for the reset role", MIG,
        'if bad := effective_problems(db, reset_role, lambda g: g.reset if g else ""):',
        "if bad := []:",
        "test_migrate_refuses_a_public_right_the_reset_role_would_inherit", "DID NOT RAISE"),
    mutant("migrate: reset_role is left out of the named roles", MIG,
        "    named = [r for r in roles if r is not None]",
        "    named = [r for r in roles[:3] if r is not None]",
        "test_migrate_refuses_a_reset_role_that_is_the_runtime_role", "DID NOT RAISE"),
    mutant("migrate: the forbidden role names are not checked", MIG,
        " or role in _FORBIDDEN_ROLES", "",
        "test_h4_a_role_name_that_is_not_one_plain_role_is_refused_before_any_connection", "ConfigError"),
    mutant("read: the NOT EXISTS is dropped (a cleared stop still counts)", PG,
        '\'SELECT s."by", s.ts FROM kill_switch_stops s WHERE NOT EXISTS \'\n'
        '                "(SELECT 1 FROM kill_switch_clears c WHERE c.stop_id = s.id) ORDER BY',
        '\'SELECT s."by", s.ts FROM kill_switch_stops s \'\n                " ORDER BY',
        N2, "assert True is False"),
    mutant("read: open stops are ignored", PG,
        "        if stop is not None:\n", "        if False:\n",
        "test_n1_a_stop_by_the_runtime_login_reads_on_from_a_second_connection", "assert (False"),
    mutant("read: a flag that is ON reads OFF", PG,
        "        if found[0].on:\n            return found[0]\n",
        '        if found[0].on:\n            return found[0].model_copy(update={"on": False})\n',
        "test_e5_a_flag_set_on_by_the_owner_reads_on_and_a_reset_turns_it_off", "assert (False"),
    mutant("read: a missing flag row reads OFF", PG,
        'return KillSwitch(on=True, by="system:kill_switch_row_missing")',
        'return KillSwitch(on=False, by="system:kill_switch_row_missing")',
        "test_e6_a_deleted_flag_row_reads_on_and_stays_on_after_a_reset", "assert False is True"),
    mutant("reset: ON CONFLICT is removed", PG,
        '                "ON CONFLICT (stop_id) DO NOTHING",\n', '                "",\n',
        "test_e2_a_reset_that_overlaps_an_uncommitted_reset_succeeds", "UniqueViolation"),
    mutant("reset: the flag update and the clears are not one transaction", PG,
        "        with self._lock, self._db.transaction():\n            self._exec(\n"
        "                'UPDATE kill_switch SET",
        "        with self._lock:\n            self._exec(\n                'UPDATE kill_switch SET",
        "test_e8_a_refused_clear_leaves_the_flag_on", "assert False is True"),
    mutant("limits: the reset clears before the intent is written", LIM,
        RESET_BODY, CLEAR_FIRST,
        "test_e8_cli_reset_with_the_audit_down_exits_3_and_clears_nothing", "assert"),
    mutant("limits: reset_failed is not written", LIM,
        '            self.audit.write_outcome(self._event(True, by, "reset_failed"))\n', "",
        "test_cli_reset_on_the_runtime_dsn_exits_2_stays_on_and_audits_reset_failed", "limits.reset_failed"),
    mutant("migration 0006: the append-only triggers are removed", SQL,
        TRIGGERS, "",
        OWNER, "DID NOT RAISE"),
    mutant("cli: the reset ignores reset_credential_ref", CLI,
        "        if reset_ref:\n            # The reset role's own login",
        "        if False:\n            # The reset role's own login",
        N3, "assert 2 == 0"),
    mutant("cli: the pilot and prod refusal is removed", CLI,
        "        if not reset_ref and is_live(cfg.environment):", "        if False:",
        "test_e10_reset_without_the_ref_is_refused_before_any_connection", "assert 3 == 2"),
]  # fmt: skip

# Guards the ticket asks for that the source did not hold when this list was written; (name, file, killer).
PENDING = [
    ("migration 0006: the stop id is a serial number again (BIGSERIAL)", SQL,
        "test_h2_the_runtime_login_cannot_make_a_later_stop_fail"),
    ("loop: the limits_unavailable hunk is removed (first check)", LOOP,
        "test_e9_an_unreadable_stop_state_at_the_first_check_means_no_model_call"),
    ("loop: the limits_unavailable hunk is removed (recheck)", LOOP,
        "test_e9_an_unreadable_stop_state_at_the_recheck_means_no_action"),
]  # fmt: skip


def _killer(name: str) -> tuple[int, str]:
    done = subprocess.run(  # noqa: S603 - this interpreter, a fixed test id
        [sys.executable, "-m", "pytest", f"{TEST}::{name}", "-q", "-x", "-p", "no:cacheprovider"],
        cwd=ROOT, capture_output=True, text=True, timeout=900, check=False,
    )  # fmt: skip
    return done.returncode, done.stdout + done.stderr


def run_by_hand(only: list[str]) -> int:
    """Apply each HAND mutant to the working tree, run its killer, restore. Returns the number not killed."""
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print("HADAVIN_TEST_PG_DSN is not set: the killers would be skipped, nothing was run")
        return 1
    chosen = [m for m in HAND if not only or any(text in m.name for text in only)]
    dirty = subprocess.run(  # noqa: S603 - fixed arguments
        ["git", "status", "--porcelain", "--", *sorted({m.file for m in chosen})],  # noqa: S607 - git from PATH
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if dirty.strip():
        print("refused: a target file has uncommitted changes:\n" + dirty)
        return 1
    bad, clean = 0, {}
    for m in chosen:
        path = ROOT / m.file
        before = path.read_bytes()
        text = before.decode("utf-8")
        if m.only_test not in clean:
            clean[m.only_test] = _killer(m.only_test)[0] == 0
        if not clean[m.only_test]:
            verdict = "BASELINE FAILS (the killer fails on the clean tree)"
        elif m.old not in text:
            verdict = "NOT APPLIED (the old text is not in the file)"
        else:
            try:
                path.write_bytes(text.replace(m.old, m.new).encode("utf-8"))
                code, out = _killer(m.only_test)
            finally:
                path.write_bytes(before)
            if code == 0:
                verdict = "SURVIVED"
            elif m.expect not in out:
                verdict = f"FAILED FOR ANOTHER REASON (no {m.expect!r} in the output)"
            else:
                verdict = "KILLED"
        bad += verdict != "KILLED"
        print(f"{verdict:8} | {m.name} | {m.file} | {m.only_test}", flush=True)
    return bad


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--hand"]:
        sys.exit(1 if run_by_hand(args[1:]) else 0)
    results = run_mutants(ROOT, M, [TEST], only=args) if M else []
    for name, verdict, first, good in results:
        print(f"{'ok ' if good else 'BAD'} {verdict.value:10} {name}  [{first}]")
    for m in HAND:
        print(f"by hand (--hand): {m.name} -> {m.only_test}")
    for name, _file, killer in PENDING:
        print(f"pending (guard not in the source yet): {name} -> {killer}")
    sys.exit(0 if all(good for *_, good in results) else 1)
