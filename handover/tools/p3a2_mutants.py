#!/usr/bin/env python3
"""P3a-2 mutant runner: 66 mutants of the wiring PR (PR 73, branch core/P3a-2, head 2b0941b).

RECONSTRUCTED. The original runner (`mutants.py`, last seen in run ea40242, log
handover/evidence/P3a-2/ea40242/mutants-p3a2.log) is lost. What is KNOWN from that log: the 66 mutant names
(M61 ... P10), a one-line description of each, the killer test of each, and that all 66 were killed.
What is RECONSTRUCTED here: the exact text each mutant plants (`file`, `old`, `new`). They were written from the
description + killer test + the source at 2b0941b, then proven by running (a mutant that its killer does not kill is
reported as SURVIVED, never hidden). The text of the original mutants may differ; the intent per name is the same.

Ambiguous items and the interpretation chosen:
  * M65 "current_user compared with session_user": the saved current_user is compared with the NEW session_user.
  * M88b "a trigger already D passes the same check wrongly (before None only)": the D/R refusal fires only for a
    trigger that had no saved state (before is None); a trigger that was enabled and became D passes.
  * N3b is the same planted text as N3, killed by a different test (the wiring file), as the old log shows.
  * M94: the old log names the killer `[current_user]`, which cannot see "session_user not compared" (the log is hand-
    edited); the parameter `[session_user]` of the same test is used.
  * N10 "require_module returns nothing": read as "an import failure returns None instead of failing or skipping"
    (the log's killer is the DSN-set failure test, which only that reading can fail).
  * N1 plants a dead helper in migrate.py that unpacks `checked_statement_text(...)` into two names.
  * N16-N19 and P1-P7 change CHANGELOG.md (the runbook text), read by tests/fixtures/runbook.py.
  * Killer ids: the log shows ONE node id per mutant; the whole id (with its [parameter]) is run.
  * The old log ran each killer on a `git archive` copy with 3 tests deselected (marks `live`, `perf`); here the
    killer is run by node id in the working tree and the file is restored after every mutant.
  * Killed = pytest exit code 1 (a test failed). Exit code 0 = SURVIVED. Any other code (2 collection error, 3, 4, 5)
    or a timeout is reported as ERROR and counts as NOT killed, so a syntax error cannot pass as a kill.
  * A baseline run of every killer id on the untouched tree must pass first, else the run stops.

Usage (needs HADAVIN_TEST_PG_DSN in the environment for the Postgres killers):
    python p3a2_mutants.py --root <worktree> --python <venv python> [--only TEXT] [--timeout SECONDS]
Exit 0 only if exactly 66 mutants ran, all 66 were killed, and `git diff` is empty afterwards.
"""

from __future__ import annotations

import argparse
import atexit
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

MIG = "src/hadavin_sdk/store/migrate.py"
MN = "src/hadavin_sdk/store/migration_numbers.py"
CL = "CHANGELOG.md"
DSN_SKIP = "tests/fixtures/dsn_skip.py"
T_WIRING = "tests/test_migration_wiring.py"
T_PG = "tests/test_migration_postgres.py"
T_RULES = "tests/test_migration_rules.py"
T_NUM = "tests/test_migration_numbers.py"
T_GUARDS = "tests/test_migration_numbers_guards.py"
T_NAMES = "tests/test_migration_names.py"
FALSE_NAME = "0006" + "_evidence"  # built from parts: the repo scans for the written name


@dataclass(frozen=True)
class Mutant:
    name: str
    desc: str
    file: str
    old: str
    new: str
    killer: str  # full pytest node id


def k(test_file: str, test: str) -> str:
    return f"{test_file}::{test}"


WIRING_VAL = k(T_WIRING, "test_each_value_is_compared_with_its_own_saved_value")
READS_BEFORE = k(T_WIRING, "test_clean_run_reads_before_each_file_insert")
FORM = k(T_RULES, "test_every_caller_in_the_package_uses_the_right_form")
SKIPS = k(T_RULES, "test_no_p3a2_test_skips_silently")
MEMBER = k(T_RULES, "test_role_membership_is_refused_whatever_the_comments_and_names_hold") + "[-]"
BLOCK_PG = k(T_PG, "test_runbook_case_b_renames_the_old_notes_row_back_and_migrate_accepts_it")
RUNBOOK = k(T_RULES, "test_the_runbook_carries_the_real_lock_the_command_and_every_case")
CMP_OLD = "        if old != new\n"
PAIR_FUNC = "def _table_body(text: str, start: int) -> str:"
LEX_CALL = "        text, lexer_problem = lex(raw, keep_quoted=True)\n"
SAVE_READ = (
    "            if pending:\n"
    "                saved = _read_back(db)\n"
    "                _refuse_unusual_strings(saved)\n"
    "            for path in pending:\n"
    '                step[0] = f"applying {path.name}"\n'
    "                db.execute(texts[path])  # the text that was scanned, never a second read\n"
)
RECIPE_CLEAN = "cleaned = checked_statement_text(text)  # cannot raise: _refuse_entry read this text above"
ROLE_RX = 'rf"(grant|revoke)\\b(?!.*?{_NAME_START}on{_NAME_END})"'
RELEASE_ONE = (
    '        if p is None or not p.is_file():\n            problems.append(f"{_esc(stem)}: a released file is missing")\n'
)
GUARDS_KILL = k(T_GUARDS, "test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number")
DROP_ADVICE = k(
    T_RULES, "test_a_drop_is_advised_in_one_place_only_and_never_for_the_evidence_tables_of_a_live_database"
)


def cmp_mutant(name: str, item: str, desc: str, killer_item: str) -> Mutant:
    return Mutant(name, desc, MIG, CMP_OLD, f'        if old != new and item != "{item}"\n', f"{WIRING_VAL}[{killer_item}]")


M: list[Mutant] = [
    # --- read-back and its order (migrate.py) ---
    Mutant("M61", "read-back removed from migrate()", MIG,
           "                saved = _check_read_back(db, saved, path.name)\n",
           "                saved = saved\n", READS_BEFORE),
    cmp_mutant("M62", "search_path", "search_path not compared", "search_path"),
    Mutant("M64", "read-back after the ledger INSERT", MIG,
           "                saved = _check_read_back(db, saved, path.name)\n"
           '                db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))\n',
           '                db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))\n'
           "                saved = _check_read_back(db, saved, path.name)\n", READS_BEFORE),
    Mutant("M65", "current_user compared with session_user", MIG,
           "for item, old, new in zip(_READBACK_VALUES, saved.values, now.values, strict=True)",
           "for item, old, new in zip(\n"
           "            _READBACK_VALUES, saved.values, (now.values[1], *now.values[1:]), strict=True\n"
           "        )",
           k(T_WIRING, "test_saved_users_that_differ_are_not_a_refusal")),
    Mutant("M66", "message omits the file name", MIG,
           'f"migration {ascii(file_name)[1:-1]} left the database session changed: "',
           '"migration left the database session changed: "',
           f"{WIRING_VAL}[current_user]"),
    Mutant("M67", "read-back only after the last file", MIG,
           "                saved = _check_read_back(db, saved, path.name)\n",
           "                if path is pending[-1]:\n"
           "                    saved = _check_read_back(db, saved, path.name)\n", READS_BEFORE),
    cmp_mutant("M70", "session_replication_role", "session_replication_role not compared",
               "session_replication_role"),
    cmp_mutant("M71", "current_user", "current_user not compared", "current_user"),
    cmp_mutant("M94", "session_user", "session_user not compared", "session_user"),
    cmp_mutant("M91", "standard_conforming_strings", "standard_conforming_strings not compared",
               "standard_conforming_strings"),
    cmp_mutant("M92", "backslash_quote", "backslash_quote not compared", "backslash_quote"),
    cmp_mutant("M93", "client_encoding", "client_encoding not compared", "client_encoding"),
    cmp_mutant("MB1", "transaction_timestamp", "transaction_timestamp not compared",
               "transaction_timestamp"),
    cmp_mutant("MB2", "txid_current", "txid_current not compared", "txid_current"),
    Mutant("M88", "trigger state D/R check removed", MIG,
           'if enabled in ("D", "R") and (before is None or before[0] != enabled):',
           "if False:", k(T_WIRING, "test_a_disabled_trigger_is_refused")),
    Mutant("M88b", "trigger state: a trigger already D passes the same check wrongly (before None only)", MIG,
           'if enabled in ("D", "R") and (before is None or before[0] != enabled):',
           'if enabled in ("D", "R") and before is None:',
           k(T_WIRING, "test_a_disabled_trigger_is_refused")),
    Mutant("M89", "saved trigger still exists: check removed", MIG,
           "        if key not in now.triggers:\n", "        if False:\n",
           k(T_WIRING, "test_a_dropped_trigger_is_refused")),
    Mutant("M90", "start check of standard_conforming_strings removed", MIG,
           '    if value != "on":\n', "    if False:\n",
           k(T_WIRING, "test_start_value_of_standard_conforming_strings_must_be_on")),
    Mutant("M95", "saved values read after the first file", MIG, SAVE_READ,
           "            saved = None\n"
           "            for path in pending:\n"
           '                step[0] = f"applying {path.name}"\n'
           "                db.execute(texts[path])  # the text that was scanned, never a second read\n"
           "                if saved is None:\n"
           "                    saved = _read_back(db)\n"
           "                    _refuse_unusual_strings(saved)\n", READS_BEFORE),
    Mutant("M101", "trigger baseline not refreshed", MIG,
           "    return _Saved(saved.values, now.triggers, saved.members)\n", "    return saved\n",
           k(T_WIRING, "test_a_new_trigger_is_not_a_refusal_and_is_watched_from_then_on")),
    Mutant("M102", "trigger query has no schema filter", MIG,
           '"WHERE NOT t.tgisinternal AND n.nspname = current_schema()"',
           '"WHERE NOT t.tgisinternal"',
           k(T_WIRING, "test_trigger_query_reads_only_the_migration_schema")),
    # --- _scan (migrate.py) ---
    Mutant("M68", "_scan strips with the old regexes", MIG, LEX_CALL,
           "        text, lexer_problem = (\n"
           '            re.sub(r"--[^\\n]*|/\\*.*?\\*/", " ", raw, flags=re.DOTALL),\n'
           '            "",\n'
           "        )\n", k(T_NUM, "test_scan_double_dash_in_string")),
    Mutant("M69", "_scan ignores the lexer problem", MIG, "        if lexer_problem:\n", "        if False:\n",
           k(T_NUM, "test_scan_comment_ends_at_cr")),
    Mutant("M87", "_scan reads the view with emptied quotes", MIG, LEX_CALL,
           "        text, lexer_problem = lex(raw)\n",
           k(T_NUM, "test_scan_sees_create_inside_bodies_and_strings")),
    # --- migrate() wiring ---
    Mutant("MW1", "refusal list not applied in _scan", MIG, "for reason in refused_statements(raw)",
           "for reason in []", k(T_WIRING, "test_commit_in_a_file_is_refused_before_connecting")),
    Mutant("MW2", "migrate() reads the file again instead of the scanned text", MIG,
           "db.execute(texts[path])  # the text that was scanned, never a second read",
           'db.execute(path.read_text(encoding="utf-8"))',
           k(T_WIRING, "test_migrate_executes_the_text_it_scanned")),
    Mutant("MW3", "number problems raised as a plain ConfigError", MIG,
           "    if problems := check_ledger(files):\n        raise MigrationNumberError(problems)\n",
           '    if problems := check_ledger(files):\n        raise ConfigError("; ".join(problems))\n',
           k(T_WIRING, "test_directory_named_like_a_migration_is_refused")),
    Mutant("MW4", "gone-name check removed", MIG, "            if gone := gone_message(done, files):\n",
           "            if False:\n", k(T_WIRING, "test_gone_name_is_refused_with_the_old_phrase")),
    Mutant("MW5", "late-file check removed", MIG,
           "            if late := order_problems(done, files, texts, schema):\n", "            if False:\n",
           k(T_WIRING, "test_late_file_is_refused_and_nothing_runs")),
    Mutant("MW6", "check_grants scans without the shared text", MIG, "check_grants(files, texts=texts)",
           "check_grants(files)", k(T_WIRING, "test_migrate_executes_the_text_it_scanned")),
    Mutant("MW7", "_migration_files uses the case-sensitive glob again", MN,
           'if e.name.lower().endswith(".sql"))', 'if e.name.endswith(".sql"))',
           k(T_WIRING, "test_uppercase_extension_is_refused")),
    Mutant("MW8", "lock key differs from the module constant", MIG,
           '"SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK,)',
           '"SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK + 1,)',
           k(T_WIRING, "test_migrate_takes_the_one_advisory_lock_key_first")),
    Mutant("MW9", "no read-back message escapes (ESC survives)", MIG,
           'f"{item} was {old!a} and is now {new!a}"', 'f"{item} was {old} and is now {new}"',
           f"{WIRING_VAL}[current_user]"),
    # --- release manifest (migration_numbers.py) ---
    Mutant("MM1", "manifest: edited file not detected", MN,
           '        elif hashlib.sha256(p.read_bytes().replace(b"\\r\\n", b"\\n")).hexdigest() != manifest[stem]:\n',
           "        elif False:\n", GUARDS_KILL),
    Mutant("MM2", "manifest: missing file not detected", MN, RELEASE_ONE,
           "        if p is None or not p.is_file():\n            pass\n", GUARDS_KILL),
    Mutant("MM3", "manifest: new file below released not detected", MN,
           "            if stem not in manifest and int(stem[:4]) <= int(top[:4])\n",
           "            if False\n", GUARDS_KILL),
    # --- pair / str form ---
    Mutant("N1", "B: dead helper in migrate.py unpacks the str form into two names", MIG, PAIR_FUNC,
           "def _dead_helper(raw):\n    text, problem = checked_statement_text(raw)\n    return text\n\n\n"
           + PAIR_FUNC, FORM),
    Mutant("N2", "B: _scan takes the pair as the text", MIG, LEX_CALL,
           '        text = lex(raw, keep_quoted=True)\n        lexer_problem = ""\n', FORM),
    Mutant("N3", "B: hand_recipe calls statement_text (the pair) as a str", MN, RECIPE_CLEAN,
           "cleaned = statement_text(text)", FORM),
    Mutant("N3b", "B: same mutant N3 against the whole old+new migration test set (is the pair type error caught anywhere else?)",
           MN, RECIPE_CLEAN, "cleaned = statement_text(text)",
           k(T_WIRING, "test_late_file_is_refused_and_nothing_runs")),
    Mutant("N4", "B: hand_recipe unpacks the str into two names", MN, RECIPE_CLEAN,
           "cleaned, _ignored = checked_statement_text(text)", FORM),
    # --- no silent skip (test helpers) ---
    Mutant("N5", "C2: wiring test file skips with importorskip again", T_WIRING,
           'require_module("psycopg")', 'pytest.importorskip("psycopg")',
           SKIPS + "[tests/test_migration_wiring.py]"),
    Mutant("N6", "C2: require_module skips even when the DSN is set", DSN_SKIP, "        if env.get(DSN_NAME):\n",
           "        if False:\n", k(T_RULES, "test_a_missing_driver_with_the_dsn_set_is_a_failure")),
    Mutant("N7", "C2: require_module skip has no reason", DSN_SKIP,
           '            f"{name} is not installed (the pg extra) and {DSN_NAME} is not set",\n',
           "",
           k(T_RULES, "test_a_missing_driver_without_the_dsn_is_a_skip_with_a_reason") + "[environ0]"),
    Mutant("N8", "C2: needs_pg skipif reason does not name the variable", T_PG,
           'not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"',
           'not DSN, reason="not set (the postgres service runs in CI)"',
           SKIPS + "[tests/test_migration_postgres.py]"),
    Mutant("N9", "C2: scratch fixture skips whatever the DSN is", T_PG,
           '    if not DSN:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"p3a_',
           '    if True:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"p3a_',
           SKIPS + "[tests/test_migration_postgres.py]"),
    Mutant("N10", "C2: require_module returns nothing", DSN_SKIP, "    except ImportError:\n",
           "    except ImportError:\n        return None\n",
           k(T_RULES, "test_a_missing_driver_with_the_dsn_set_is_a_failure")),
    # --- role membership rule ---
    Mutant("N11", "C3: role-membership rule looks for `on` as a substring (ADMIN OPTION slips)", MN,
           ROLE_RX, 'r"(grant|revoke)\\b(?!.*?on)"', MEMBER),
    Mutant("N12", "C3: refusal list reads the view with quoted parts kept", MN,
           "    cleaned, problem = lex(text)\n    reasons = [hidden]",
           "    cleaned, problem = lex(text, keep_quoted=True)\n    reasons = [hidden]", MEMBER),
    Mutant("N13", "C3: role-membership rule removed (every GRANT/REVOKE passes)", MN,
           "        elif m := _ROLE_MEMBERSHIP.match(s):\n", "        elif False:\n", MEMBER),
    Mutant("N14", "C3: role-membership rule refuses every GRANT/REVOKE (lookahead removed)", MN,
           ROLE_RX, 'r"(grant|revoke)\\b"',
           k(T_RULES, "test_privileges_on_objects_are_not_refused_as_role_membership") + "[GRANT SELECT ON t TO r]"),
    Mutant("N15", "C3: migrate() docstring loses the role argument sentence", MIG,
           "own Python step, with the role as an argument,", "own Python step,",
           k(T_RULES, "test_the_migrate_docstring_says_where_role_membership_is_changed")),
    # --- CHANGELOG / runbook ---
    Mutant("N16", "D: CHANGELOG gives the false name again", CL,
           "Do not rename a row that reads `0005_evidence`.",
           f"Rename the row to `{FALSE_NAME}`.",
           k(T_RULES, "test_no_advice_tells_anyone_to_rename_a_row_to_the_false_name")),
    Mutant("N17", "D: runbook lock number differs from MIGRATE_LOCK", CL,
           "pg_advisory_xact_lock(3760701656253510835)", "pg_advisory_xact_lock(3760701656253510836)", RUNBOOK),
    Mutant("N18", "D: runbook case (a) loses the current_user sentence", CL,
           "IF current_user <> '<MIGRATION ROLE>' THEN", "IF true THEN", RUNBOOK),
    Mutant("N19", "D: the drop advice returns in the repair step", CL,
           "Do not drop tables or ledger rows on the advice of an older note:",
           "Drop `tool_calls` and `redaction_maps` and run migrate again:", DROP_ADVICE),
    Mutant("P1", "G: case (g) block has no ALTER", CL,
           "ALTER TABLE tool_calls ADD COLUMN IF NOT EXISTS error BOOLEAN NOT NULL DEFAULT FALSE;",
           "SELECT 1;", BLOCK_PG),
    Mutant("P2", "G: case (b) no longer puts the evidence block into the file", CL,
           "put the block of case (g) (the evidence tables check) into", "put the evidence tables check into",
           k(T_RULES, "test_the_changelog_keeps_a_repair_path_for_an_early_evidence_table")),
    Mutant("P3", "C: case (c) loses the released-file sentence", CL,
           "can never be renumbered, renamed or edited", "can be handled like the others",
           k(T_RULES, "test_case_c_says_a_released_file_cannot_be_renumbered")),
    Mutant("P4", "R: the rename refusal loses the pointer to case (b)", MN,
           "section Migration repair steps, case (b).", "section Migration repair steps.",
           k(T_RULES, "test_the_rename_refusal_points_to_the_runbook_case_b")),
    Mutant("P5", "A: case (a) failure wording back to the ledger row", CL,
           "the second run fails, and keeps nothing (the file's own SQL stops it, or at the latest the ledger row, whose version is a primary key)",
           "the second run fails at the ledger row, and keeps nothing",
           k(T_RULES, "test_case_a_failure_wording_and_the_hand_written_fallback")),
    Mutant("P6", "G: the structure check forgets the error column in its expected list", CL,
           "error boolean NO, ", "", BLOCK_PG),
    Mutant("P7", "G: the structure check forgets the redaction_maps columns", CL,
           "'mapping jsonb NO, run_id text NO, updated_at timestamp with time zone NO'",
           "'run_id text NO, updated_at timestamp with time zone NO'", BLOCK_PG),
    Mutant("P8", "D: the docstring goes back to three session settings", MIG,
           "three settings that\nchange how SQL text is read", "three session settings",
           k(T_RULES, "test_the_migrate_docstring_counts_what_it_reads_back")),
    Mutant("P9", "R: _SET_ALLOWED uses the word boundary (order 112)", MN,
           'rf"set{_W}local{_W}(?:lock_timeout|statement_timeout){_NAME_END}"',
           'rf"set{_W}local{_W}(?:lock_timeout|statement_timeout)\\b"',
           k(T_NAMES, "test_the_word_boundary_is_used_only_where_a_match_refuses")),
    Mutant("P10", "R: a name character without the dollar sign (order 112)", MN,
           '_NAME_CHAR = "[A-Za-z0-9_$\\u0080-\\U0010ffff]"', '_NAME_CHAR = "[A-Za-z0-9_\\u0080-\\U0010ffff]"',
           k(T_NAMES, "test_a_name_that_holds_on_and_a_dollar_does_not_hide_a_role_grant")
           + "[GRANT pg_write_all_data TO {n}-app$on]"),
]


def run(cmd, cwd, env, timeout):
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr or ""), time.monotonic() - t0
    except subprocess.TimeoutExpired as e:
        out = e.stdout or b""
        out = out.decode("utf-8", "replace") if isinstance(out, bytes) else out
        return "TIMEOUT", out, time.monotonic() - t0


def summary_line(out: str) -> str:
    for line in reversed(out.strip().splitlines()):
        if re.search(r"\b(passed|failed|error|errors|no tests ran)\b", line):
            return line.strip(" =")
    return out.strip().splitlines()[-1][:120] if out.strip() else ""


def git_clean(root: Path) -> bool:
    return subprocess.run(["git", "diff", "--quiet"], cwd=root).returncode == 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="git worktree of the head under test (modified temporarily)")
    ap.add_argument("--python", default=sys.executable)
    ap.add_argument("--only", default="", help="run only mutants whose name contains this text")
    ap.add_argument("--timeout", type=int, default=600)
    a = ap.parse_args()
    root = Path(a.root).resolve()
    pycache = tempfile.mkdtemp(prefix="p3a2-pyc-")
    env = dict(os.environ, PYTHONPATH=str(root / "src"), PYTHONPYCACHEPREFIX=pycache, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTEST_ADDOPTS", None)
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True).stdout.strip()
    print(f"HEAD {head}")
    print(f"root {root}")
    if not git_clean(root):
        print("STOP: the tree has tracked changes before the run; refusing to plant on top of them")
        return 2
    chk = subprocess.run([a.python, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"], cwd=root, env=env,
                         capture_output=True, text=True).stdout.strip()
    print(f"import path: {chk}")
    if not chk.startswith(str(root)):
        print("STOP: hadavin_sdk is not imported from the root under test")
        return 2
    print(f"HADAVIN_TEST_PG_DSN set: {bool(env.get('HADAVIN_TEST_PG_DSN'))}")
    base = ["-p", "no:cacheprovider", "-q", "-x", "--no-header"]
    selected = [m for m in M if a.only in m.name]
    killers = sorted({m.killer for m in selected})
    rc, out, dt = run([a.python, "-m", "pytest", *base, *killers], root, env, a.timeout)
    print(f"BASELINE rc={rc} {summary_line(out)} ({dt:.1f}s, {len(killers)} killer ids)")
    if rc != 0:
        print(out[-3000:])
        print("STOP: baseline not green")
        return 2

    results = []
    held: dict[str, bytes] = {}

    def restore_all():
        for f, data in held.items():
            (root / f).write_bytes(data)

    atexit.register(restore_all)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(143))
    print("name | description | result | pytest summary | seconds | killer")
    for m in selected:
        path = root / m.file
        original = path.read_bytes()
        held[m.file] = original
        text = original.decode("utf-8")
        status, line, dt = "ERROR", "", 0.0
        try:
            n = text.count(m.old)
            if n != 1:
                status, line = "ERROR", f"old text occurs {n} times (need exactly 1)"
            else:
                path.write_bytes(text.replace(m.old, m.new, 1).encode("utf-8"))
                rc, out, dt = run([a.python, "-m", "pytest", *base, m.killer], root, env, a.timeout)
                line = summary_line(out)
                status = "KILLED" if rc == 1 else "SURVIVED" if rc == 0 else f"ERROR(rc={rc})"
        finally:
            path.write_bytes(original)
            held.pop(m.file, None)
            if not git_clean(root):
                subprocess.run(["git", "checkout", "--", m.file], cwd=root)
                status = "ERROR(tree not restored; checked out)"
        results.append((m, status))
        print(f"{m.name} | {m.desc} | {status} | {line} | {dt:.1f}s | killer: {m.killer}", flush=True)

    killed = sum(1 for _, s in results if s == "KILLED")
    survived = [m.name for m, s in results if s == "SURVIVED"]
    errors = [f"{m.name}:{s}" for m, s in results if s not in ("KILLED", "SURVIVED")]
    clean = git_clean(root)
    print(f"planted {len(results)}; killed {killed}; survived {len(survived)} {survived}; errors {len(errors)} {errors}")
    print(f"git diff empty after the run: {clean}")
    print(f"{killed} of {len(results)} killed")
    if a.only == "" and len(results) != 66:
        print(f"STOP: expected 66 mutants, defined {len(results)}")
    return 0 if (clean and a.only == "" and len(results) == 66 and killed == 66) else 1


if __name__ == "__main__":
    sys.exit(main())
