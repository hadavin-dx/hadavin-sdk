"""Mutants of the migrate wiring: `store/migrate.py`, `store/migration_numbers.py`, the CHANGELOG runbook and
two test helpers. Not collected by pytest.

Each mutant plants ONE wrong line in a COPY of the repository (the working tree is never touched) and runs the tests
named in `killer`; the mutant is KILLED when pytest exits with code 1 (a test failed). Exit code 0 means SURVIVED; any
other code (collection error, timeout) is ERROR and counts as not killed, so a syntax error cannot pass as a kill. A
baseline run of every killer on the untouched copy must pass first. The mutants started as a reconstruction of an earlier
runner that was lost (what was known of it: names, one-line descriptions and killers; the planted text was
rewritten and proven by running) and were extended for the trigger read-back, the role check and the allow list.

Run from the repository root (needs the Postgres tests' variable HADAVIN_TEST_PG_DSN pointing at a scratch server whose
login may create schemas and roles; about 10 minutes):

    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py            # all; exit 1 if any is not killed
    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py M88         # only names that hold the text

The last line is `N of N killed`. A cheap check that runs with the ordinary tests,
`test_every_migrate_mutant_still_applies_to_the_source` (tests/test_migration_rules.py), fails when a mutant's `old`
text is no longer in its file exactly once, so the list cannot rot between two runs.
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FALSE_NAME = "0006" + "_evidence"  # built from parts: the repo scans for the written name
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


@dataclass(frozen=True)
class Mutant:
    name: str
    desc: str
    file: str
    old: str
    new: str
    killer: str | tuple  # full pytest node id, or several (all are run together)


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
RECIPE_CLEAN = (
    "cleaned = checked_statement_text(text)  # cannot raise: _refuse_entry read this text above"
)
ROLE_RX = 'rf"(grant|revoke)\\b(?!.*?{_NAME_START}on{_NAME_END})"'
RELEASE_ONE = '        if p is None or not p.is_file():\n            problems.append(f"{escape_name(stem)}: a released file is missing")\n'
GUARDS_KILL = k(T_GUARDS, "test_released_problems_catches_an_edit_a_deletion_and_a_low_new_number")
DROP_ADVICE = k(
    T_RULES,
    "test_a_drop_is_advised_in_one_place_only_and_never_for_the_evidence_tables_of_a_live_database",
)


TRIG_CHANGED = (
    k(T_WIRING, "test_a_trigger_recreated_with_another_definition_or_function_is_refused"),
    k(T_WIRING, "test_the_trigger_query_reads_definition_function_text_and_security_mode"),
    k(T_PG, "test_h11_the_read_back_refuses_a_planted_file"),
    k(T_PG, "test_h11_a_function_owner_change_is_refused"),
)
ALLOWED = k(T_WIRING, "test_an_allowed_trigger_change_passes_only_for_that_file_table_and_trigger")
STATE_LISTED = k(
    T_WIRING,
    "test_a_listed_trigger_may_not_be_left_disabled_or_replica_only_unless_the_entry_says_so",
)
SCHEMA_LISTED = k(T_WIRING, "test_an_entry_that_names_another_schema_does_not_allow_the_change")
ALLOWED_PG = k(T_PG, "test_h11_a_listed_trigger_change_passes_for_that_file_and_trigger_only")
MEMBERS = (
    k(T_WIRING, "test_a_new_role_membership_after_a_file_is_refused"),
    k(T_WIRING, "test_the_membership_is_read_after_every_file_and_before_its_ledger_row"),
    k(T_PG, "test_h11_a_role_grant_hidden_in_a_function_body_is_refused"),
)
SETTINGS = k(T_WIRING, "test_a_new_saved_setting_for_a_role_is_refused")
ROLE_REFUSED = k(T_WIRING, "test_a_privileged_migration_role_is_refused_before_any_file_runs")


CALL = (
    "                saved = _check_read_back(\n"
    "                    db,\n"
    "                    saved,\n"
    "                    path.name,\n"
    "                    frozenset(c for c in allowed_changes if c.migration == path.stem),\n"
    "                )\n"
)
INSERT = '                db.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))\n'


def cmp_mutant(name: str, item: str, desc: str, killer_item: str) -> Mutant:
    return Mutant(
        name,
        desc,
        MIG,
        CMP_OLD,
        f'        if old != new and item != "{item}"\n',
        f"{WIRING_VAL}[{killer_item}]",
    )


M: list[Mutant] = [
    # --- read-back and its order (migrate.py) ---
    Mutant(
        "M61",
        "read-back removed from migrate()",
        MIG,
        CALL,
        "                saved = saved\n",
        READS_BEFORE,
    ),
    cmp_mutant("M62", "search_path", "search_path not compared", "search_path"),
    Mutant(
        "M64",
        "read-back after the ledger INSERT",
        MIG,
        CALL + INSERT,
        INSERT + CALL,
        READS_BEFORE,
    ),
    Mutant(
        "M67",
        "read-back only after the last file",
        MIG,
        CALL,
        "                if path is pending[-1]:\n"
        + "".join("    " + line for line in CALL.splitlines(True)),
        READS_BEFORE,
    ),
    cmp_mutant(
        "M70",
        "session_replication_role",
        "session_replication_role not compared",
        "session_replication_role",
    ),
    cmp_mutant("M71", "current_user", "current_user not compared", "current_user"),
    Mutant(
        "M65",
        "the saved current_user is compared with the new session_user",
        MIG,
        "for item, old, new in zip(_READBACK_VALUES, saved.values, now.values, strict=True)",
        "for item, old, new in zip(\n"
        "            _READBACK_VALUES, saved.values, (now.values[1], *now.values[1:]), strict=True\n"
        "        )",
        k(T_WIRING, "test_saved_users_that_differ_are_not_a_refusal"),
    ),
    cmp_mutant("M94", "session_user", "session_user not compared", "session_user"),
    cmp_mutant(
        "M91",
        "standard_conforming_strings",
        "standard_conforming_strings not compared",
        "standard_conforming_strings",
    ),
    cmp_mutant("M92", "backslash_quote", "backslash_quote not compared", "backslash_quote"),
    cmp_mutant("M93", "client_encoding", "client_encoding not compared", "client_encoding"),
    cmp_mutant(
        "MB1",
        "transaction_timestamp",
        "transaction_timestamp not compared",
        "transaction_timestamp",
    ),
    cmp_mutant("MB2", "txid_current", "txid_current not compared", "txid_current"),
    Mutant(
        "M88",
        "a trigger created disabled or replica-only is not refused",
        MIG,
        'if key not in saved.triggers and enabled in ("D", "R"):',
        "if False:",
        k(T_WIRING, "test_a_trigger_created_disabled_is_refused_and_one_created_enabled_is_not"),
    ),
    Mutant(
        "M90",
        "start check of standard_conforming_strings removed",
        MIG,
        '    if value != "on":\n',
        "    if False:\n",
        k(T_WIRING, "test_start_value_of_standard_conforming_strings_must_be_on"),
    ),
    Mutant(
        "M95",
        "saved values read after the first file",
        MIG,
        SAVE_READ,
        "            saved = None\n"
        "            for path in pending:\n"
        '                step[0] = f"applying {path.name}"\n'
        "                db.execute(texts[path])  # the text that was scanned, never a second read\n"
        "                if saved is None:\n"
        "                    saved = _read_back(db)\n"
        "                    _refuse_unusual_strings(saved)\n",
        READS_BEFORE,
    ),
    Mutant(
        "M101",
        "trigger baseline not refreshed",
        MIG,
        "    return _Saved(saved.values, now.triggers, saved.members, saved.settings, now.relids)\n",
        "    return saved\n",
        k(T_WIRING, "test_a_new_trigger_is_not_a_refusal_and_is_watched_from_then_on"),
    ),
    Mutant(
        "M102",
        "trigger query has no schema filter",
        MIG,
        '"WHERE NOT t.tgisinternal AND n.nspname = current_schema()"',
        '"WHERE NOT t.tgisinternal"',
        k(T_WIRING, "test_trigger_query_reads_only_the_migration_schema"),
    ),
    # --- _scan (migrate.py) ---
    Mutant(
        "M68",
        "_scan strips with the old regexes",
        MIG,
        LEX_CALL,
        "        text, lexer_problem = (\n"
        '            re.sub(r"--[^\\n]*|/\\*.*?\\*/", " ", raw, flags=re.DOTALL),\n'
        '            "",\n'
        "        )\n",
        k(T_NUM, "test_scan_double_dash_in_string"),
    ),
    Mutant(
        "M69",
        "_scan ignores the lexer problem",
        MIG,
        "        if lexer_problem:\n",
        "        if False:\n",
        k(T_NUM, "test_scan_comment_ends_at_cr"),
    ),
    Mutant(
        "M87",
        "_scan reads the view with emptied quotes",
        MIG,
        LEX_CALL,
        "        text, lexer_problem = lex(raw)\n",
        k(T_NUM, "test_scan_sees_create_inside_bodies_and_strings"),
    ),
    # --- migrate() wiring ---
    Mutant(
        "MW1",
        "refusal list not applied in _scan",
        MIG,
        "for reason in refused_statements(raw)",
        "for reason in []",
        k(T_WIRING, "test_commit_in_a_file_is_refused_before_connecting"),
    ),
    Mutant(
        "MW2",
        "migrate() reads the file again instead of the scanned text",
        MIG,
        "db.execute(texts[path])  # the text that was scanned, never a second read",
        'db.execute(path.read_text(encoding="utf-8"))',
        k(T_WIRING, "test_migrate_executes_the_text_it_scanned"),
    ),
    Mutant(
        "MW3",
        "number problems raised as a plain ConfigError",
        MIG,
        "    if problems := check_ledger(files):\n        raise MigrationNumberError(problems)\n",
        '    if problems := check_ledger(files):\n        raise ConfigError("; ".join(problems))\n',
        k(T_WIRING, "test_directory_named_like_a_migration_is_refused"),
    ),
    Mutant(
        "MW4",
        "gone-name check removed",
        MIG,
        "            if gone := gone_message(done, files):\n",
        "            if False:\n",
        k(T_WIRING, "test_gone_name_is_refused_with_the_old_phrase"),
    ),
    Mutant(
        "MW5",
        "late-file check removed",
        MIG,
        "            if late := order_problems(done, files, texts, schema):\n",
        "            if False:\n",
        k(T_WIRING, "test_late_file_is_refused_and_nothing_runs"),
    ),
    Mutant(
        "MW6",
        "check_grants scans without the shared text",
        MIG,
        "check_grants(files, texts=texts)",
        "check_grants(files)",
        k(T_WIRING, "test_migrate_executes_the_text_it_scanned"),
    ),
    Mutant(
        "MW7",
        "_migration_files uses the case-sensitive glob again",
        MN,
        'if e.name.lower().endswith(".sql"))',
        'if e.name.endswith(".sql"))',
        k(T_WIRING, "test_uppercase_extension_is_refused"),
    ),
    Mutant(
        "MW8",
        "lock key differs from the module constant",
        MIG,
        '"SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK,)',
        '"SELECT pg_advisory_xact_lock(%s)", (MIGRATE_LOCK + 1,)',
        k(T_WIRING, "test_migrate_takes_the_one_advisory_lock_key_first"),
    ),
    Mutant(
        "MW9",
        "no read-back message escapes (ESC survives)",
        MIG,
        'f"{item} was {old!a} and is now {new!a}"',
        'f"{item} was {old} and is now {new}"',
        f"{WIRING_VAL}[current_user]",
    ),
    # --- release manifest (migration_numbers.py) ---
    Mutant(
        "MM1",
        "manifest: edited file not detected",
        MN,
        "        elif _digest(p, texts) != manifest[stem]:\n",
        "        elif False:\n",
        GUARDS_KILL,
    ),
    Mutant(
        "MM2",
        "manifest: missing file not detected",
        MN,
        RELEASE_ONE,
        "        if p is None or not p.is_file():\n            pass\n",
        GUARDS_KILL,
    ),
    Mutant(
        "MM3",
        "manifest: new file below released not detected",
        MN,
        "            if stem not in manifest and int(stem[:4]) <= int(top[:4])\n",
        "            if False\n",
        GUARDS_KILL,
    ),
    # --- pair / str form ---
    Mutant(
        "N1",
        "B: dead helper in migrate.py unpacks the str form into two names",
        MIG,
        PAIR_FUNC,
        "def _dead_helper(raw):\n    text, problem = checked_statement_text(raw)\n    return text\n\n\n"
        + PAIR_FUNC,
        FORM,
    ),
    Mutant(
        "N2",
        "B: _scan takes the pair as the text",
        MIG,
        LEX_CALL,
        '        text = lex(raw, keep_quoted=True)\n        lexer_problem = ""\n',
        FORM,
    ),
    Mutant(
        "N3",
        "B: hand_recipe calls statement_text (the pair) as a str",
        MN,
        RECIPE_CLEAN,
        "cleaned = statement_text(text)",
        FORM,
    ),
    Mutant(
        "N3b",
        "B: same mutant N3 against the whole old+new migration test set (is the pair type error caught anywhere else?)",
        MN,
        RECIPE_CLEAN,
        "cleaned = statement_text(text)",
        k(T_WIRING, "test_late_file_is_refused_and_nothing_runs"),
    ),
    Mutant(
        "N4",
        "B: hand_recipe unpacks the str into two names",
        MN,
        RECIPE_CLEAN,
        "cleaned, _ignored = checked_statement_text(text)",
        FORM,
    ),
    # --- no silent skip (test helpers) ---
    Mutant(
        "N5",
        "C2: wiring test file skips with importorskip again",
        T_WIRING,
        'require_module("psycopg")',
        'pytest.importorskip("psycopg")',
        SKIPS + "[tests/test_migration_wiring.py]",
    ),
    Mutant(
        "N6",
        "C2: require_module skips even when the DSN is set",
        DSN_SKIP,
        "        if env.get(DSN_NAME):\n",
        "        if False:\n",
        k(T_RULES, "test_a_missing_driver_with_the_dsn_set_is_a_failure"),
    ),
    Mutant(
        "N7",
        "C2: require_module skip has no reason",
        DSN_SKIP,
        '            f"{name} is not installed (the pg extra) and {DSN_NAME} is not set",\n',
        "",
        k(T_RULES, "test_a_missing_driver_without_the_dsn_is_a_skip_with_a_reason") + "[environ0]",
    ),
    Mutant(
        "N8",
        "C2: needs_pg skipif reason does not name the variable",
        T_PG,
        'not DSN, reason="HADAVIN_TEST_PG_DSN not set (the postgres service runs in CI)"',
        'not DSN, reason="not set (the postgres service runs in CI)"',
        SKIPS + "[tests/test_migration_postgres.py]",
    ),
    Mutant(
        "N9",
        "C2: scratch fixture skips whatever the DSN is",
        T_PG,
        '    if not DSN:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"p3a_',
        '    if True:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"p3a_',
        SKIPS + "[tests/test_migration_postgres.py]",
    ),
    Mutant(
        "N10",
        "C2: require_module returns nothing",
        DSN_SKIP,
        "        return importer(name)\n    except ImportError:\n",
        "        return importer(name)\n    except ImportError:\n        return None\n",
        k(T_RULES, "test_a_missing_driver_with_the_dsn_set_is_a_failure"),
    ),
    # --- role membership rule ---
    Mutant(
        "N11",
        "C3: role-membership rule looks for `on` as a substring (ADMIN OPTION slips)",
        MN,
        ROLE_RX,
        'r"(grant|revoke)\\b(?!.*?on)"',
        MEMBER,
    ),
    Mutant(
        "N12",
        "C3: refusal list reads the view with quoted parts kept",
        MN,
        "    cleaned, problem = lex(text)\n    reasons = [hidden]",
        "    cleaned, problem = lex(text, keep_quoted=True)\n    reasons = [hidden]",
        MEMBER,
    ),
    Mutant(
        "N13",
        "C3: role-membership rule removed (every GRANT/REVOKE passes)",
        MN,
        "        elif m := _ROLE_MEMBERSHIP.match(s):\n",
        "        elif False:\n",
        MEMBER,
    ),
    Mutant(
        "N14",
        "C3: role-membership rule refuses every GRANT/REVOKE (lookahead removed)",
        MN,
        ROLE_RX,
        'r"(grant|revoke)\\b"',
        k(T_RULES, "test_privileges_on_objects_are_not_refused_as_role_membership")
        + "[GRANT SELECT ON t TO r]",
    ),
    Mutant(
        "N15",
        "C3: migrate() docstring loses the role argument sentence",
        MIG,
        "own Python step, with the role as an argument,",
        "own Python step,",
        k(T_RULES, "test_the_migrate_docstring_says_where_role_membership_is_changed"),
    ),
    # --- CHANGELOG / runbook ---
    Mutant(
        "N16",
        "D: CHANGELOG gives the false name again",
        CL,
        "Do not rename a row that reads `0005_evidence`.",
        f"Rename the row to `{FALSE_NAME}`.",
        k(T_RULES, "test_no_advice_tells_anyone_to_rename_a_row_to_the_false_name"),
    ),
    Mutant(
        "N17",
        "D: runbook lock number differs from MIGRATE_LOCK",
        CL,
        "pg_advisory_xact_lock(3760701656253510835)",
        "pg_advisory_xact_lock(3760701656253510836)",
        RUNBOOK,
    ),
    Mutant(
        "N18",
        "D: runbook case (a) loses the current_user sentence",
        CL,
        "IF current_user <> '<MIGRATION ROLE>' THEN",
        "IF true THEN",
        RUNBOOK,
    ),
    Mutant(
        "N19",
        "D: the drop advice returns in the repair step",
        CL,
        "Do not drop tables or ledger rows on the advice of an older note:",
        "Drop `tool_calls` and `redaction_maps` and run migrate again:",
        DROP_ADVICE,
    ),
    Mutant(
        "P1",
        "G: case (g) block has no ALTER",
        CL,
        "ALTER TABLE tool_calls ADD COLUMN IF NOT EXISTS error BOOLEAN NOT NULL DEFAULT FALSE;",
        "SELECT 1;",
        BLOCK_PG,
    ),
    Mutant(
        "P2",
        "G: case (b) no longer puts the evidence block into the file",
        CL,
        "put the block of case (g) (the evidence tables check) into",
        "put the evidence tables check into",
        k(T_RULES, "test_the_changelog_keeps_a_repair_path_for_an_early_evidence_table"),
    ),
    Mutant(
        "P3",
        "C: case (c) loses the released-file sentence",
        CL,
        "can never be renumbered, renamed or edited",
        "can be handled like the others",
        k(T_RULES, "test_case_c_says_a_released_file_cannot_be_renumbered"),
    ),
    Mutant(
        "P4",
        "R: the rename refusal loses the pointer to case (b)",
        MN,
        "section Migration repair steps, case (b).",
        "section Migration repair steps.",
        k(T_RULES, "test_the_rename_refusal_points_to_the_runbook_case_b"),
    ),
    Mutant(
        "P5",
        "A: case (a) failure wording back to the ledger row",
        CL,
        "the second run fails, and keeps nothing (the file's own SQL stops it, or at the latest the ledger row, whose version is a primary key)",
        "the second run fails at the ledger row, and keeps nothing",
        k(T_RULES, "test_case_a_failure_wording_and_the_hand_written_fallback"),
    ),
    Mutant(
        "P6",
        "G: the structure check forgets the error column in its expected list",
        CL,
        "error boolean NO, ",
        "",
        BLOCK_PG,
    ),
    Mutant(
        "P7",
        "G: the structure check forgets the redaction_maps columns",
        CL,
        "'mapping jsonb NO, run_id text NO, updated_at timestamp with time zone NO'",
        "'run_id text NO, updated_at timestamp with time zone NO'",
        BLOCK_PG,
    ),
    Mutant(
        "P8",
        "D: the docstring goes back to three session settings",
        MIG,
        "three settings that\nchange how SQL text is read",
        "three session settings",
        k(T_RULES, "test_the_migrate_docstring_counts_what_it_reads_back"),
    ),
    Mutant(
        "P10",
        "R: a name character without the dollar sign",
        MN,
        '_NAME_CHAR = "[A-Za-z0-9_$\\u0080-\\U0010ffff]"',
        '_NAME_CHAR = "[A-Za-z0-9_\\u0080-\\U0010ffff]"',
        k(T_NAMES, "test_a_name_that_holds_on_and_a_dollar_does_not_hide_a_role_grant")
        + "[GRANT pg_write_all_data TO {n}-app$on]",
    ),
    Mutant(
        "M89",
        "a vanished trigger is not reported",
        MIG,
        'triggers.append(f"trigger {label} no longer exists")',
        "pass",
        k(T_WIRING, "test_a_dropped_trigger_is_refused"),
    ),
    Mutant(
        "M66",
        "the refusal does not name the file",
        MIG,
        'raise ConfigError(f"migration {escape_name(file_name)} " + ". It also ".join(parts))',
        'raise ConfigError("migration " + ". It also ".join(parts))',
        f"{WIRING_VAL}[current_user]",
    ),
    Mutant(
        "L1",
        "the two time limits are not in the read-back",
        MIG,
        CMP_OLD,
        '        if old != new and item not in ("lock_timeout", "statement_timeout")\n',
        k(T_WIRING, "test_a_file_that_changes_a_time_limit_is_refused"),
    ),
    # --- trigger read-back and the reviewed list of allowed changes ---
    Mutant(
        "T1",
        "a changed trigger is no longer refused (only D/R states are)",
        MIG,
        "        elif after != before and not allowed:\n",
        "        elif False:\n",
        TRIG_CHANGED,
    ),
    Mutant(
        "T2",
        "trigger definition not compared",
        MIG,
        "pg_get_triggerdef(t.oid), ",
        "'', ",
        TRIG_CHANGED,
    ),
    Mutant("T3", "function text not compared", MIG, "md5(p.prosrc)", "''", TRIG_CHANGED),
    Mutant(
        "T4", "function security mode not compared", MIG, "p.prosecdef,", "false,", TRIG_CHANGED
    ),
    Mutant(
        "T5",
        "function settings not compared",
        MIG,
        "p.proconfig::text FROM pg_trigger t",
        "NULL FROM pg_trigger t",
        TRIG_CHANGED,
    ),
    Mutant(
        "T7",
        "function owner not compared",
        MIG,
        "p.prosecdef, pg_get_userbyid(p.proowner)",
        "p.prosecdef, ''",
        TRIG_CHANGED,
    ),
    Mutant(
        "T8",
        "a trigger change is reported as a changed session",
        MIG,
        "triggers.append(f\"trigger {label} changed: {', '.join(changed)}\")",
        "session.append(f\"trigger {label} changed: {', '.join(changed)}\")",
        k(T_WIRING, "test_a_trigger_change_is_not_reported_as_a_changed_session"),
    ),
    Mutant(
        "T9",
        "a renamed table reads as a vanished trigger",
        MIG,
        "            if new_home is None:\n",
        "            if True:\n",
        k(T_WIRING, "test_a_renamed_table_with_a_trigger_is_reported_as_a_renamed_table"),
    ),
    Mutant(
        "T10",
        "any trigger is allowed once any entry exists",
        MIG,
        "        entry = _listed(allowed_triggers, key)\n        allowed = entry is not None\n",
        "        entry = next(iter(allowed_triggers), None)\n        allowed = entry is not None\n",
        ALLOWED,
    ),
    Mutant(
        "T11",
        "a disappearance is allowed",
        MIG,
        "            if new_home is None:\n",
        "            if new_home is None and not allowed:\n",
        ALLOWED,
    ),
    Mutant(
        "T12",
        "the list of allowed changes ignores a bad shape",
        MIG,
        "            not isinstance(entry, dict)\n            or not required <= set(entry)\n"
        '            or set(entry) - required - {"enabled_state"}\n',
        "            False\n",
        k(T_WIRING, "test_the_list_of_allowed_trigger_changes_is_empty_today_and_strictly_read"),
    ),
    Mutant(
        "T13",
        "the allowed list is not passed to the read-back",
        MIG,
        "                    frozenset(c for c in allowed_changes if c.migration == path.stem),\n",
        "                    frozenset(),\n",
        ALLOWED_PG,
    ),
    Mutant(
        "T14",
        "a listed trigger may be left disabled or replica-only",
        MIG,
        '        elif after != before and after[0] in ("D", "R") and after[0] != entry.state:\n',
        "        elif False:\n",
        STATE_LISTED,
    ),
    Mutant(
        "T15",
        "the table is not part of the key of a list entry",
        MIG,
        "            if c.table == key[1] and c.trigger == key[2] and c.schema in (None, key[0])\n",
        "            if c.trigger == key[2] and c.schema in (None, key[0])\n",
        ALLOWED,
    ),
    Mutant(
        "T16",
        "the schema of a list entry is not compared",
        MIG,
        "c.table == key[1] and c.trigger == key[2] and c.schema in (None, key[0])\n",
        "c.table == key[1] and c.trigger == key[2]\n",
        SCHEMA_LISTED,
    ),
    Mutant(
        "T17",
        "a listed trigger left replica-only passes (only D is refused)",
        MIG,
        '        elif after != before and after[0] in ("D", "R") and after[0] != entry.state:\n',
        '        elif after != before and after[0] == "D" and after[0] != entry.state:\n',
        STATE_LISTED,
    ),
    # --- role memberships and saved settings ---
    Mutant(
        "R1",
        "a new role membership is not reported",
        MIG,
        "for role, member, rest in sorted(now.members - saved.members)",
        "for role, member, rest in []",
        MEMBERS,
    ),
    Mutant(
        "R2",
        "the memberships are not read",
        MIG,
        "members = frozenset(tuple(r) for r in db.execute(_READBACK_MEMBERS_SQL).fetchall())",
        "members = frozenset()",
        MEMBERS,
    ),
    Mutant(
        "R3",
        "a removed role membership is not reported",
        MIG,
        "for role, member, rest in sorted(saved.members - now.members)",
        "for role, member, rest in []",
        k(T_WIRING, "test_a_removed_role_membership_is_refused"),
    ),
    Mutant(
        "R4",
        "only role and member are compared, not the other columns",
        MIG,
        "(to_jsonb(m) - 'oid' - 'roleid' - 'member')::text FROM pg_auth_members m",
        "''::text FROM pg_auth_members m",
        (
            k(T_WIRING, "test_a_changed_grant_option_of_a_membership_is_refused"),
            k(T_WIRING, "test_the_membership_query_reads_names_and_every_other_column"),
            k(T_PG, "test_h11_a_changed_grant_option_of_an_existing_membership_is_refused"),
        ),
    ),
    Mutant(
        "PS1",
        "the saved per-role settings are not read",
        MIG,
        "settings = frozenset(tuple(r) for r in db.execute(_READBACK_SETTINGS_SQL).fetchall())",
        "settings = frozenset()",
        SETTINGS,
    ),
    Mutant(
        "PS2",
        "a new saved setting is not compared",
        MIG,
        "for db_name, role, conf in sorted(now.settings - saved.settings)",
        "for db_name, role, conf in []",
        SETTINGS,
    ),
    # --- the plain migration role ---
    Mutant(
        "S1",
        "the migration-role check is not called",
        MIG,
        "            _refuse_privileged_role(db)\n",
        "            pass\n",
        ROLE_REFUSED,
    ),
    Mutant(
        "S2",
        "the flag rolsuper is not read",
        MIG,
        "held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value]",
        'held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value and flag != "rolsuper"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S3",
        "the flag rolcreaterole is not read",
        MIG,
        "held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value]",
        'held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value and flag != "rolcreaterole"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S4",
        "the flag rolcreatedb is not read",
        MIG,
        "held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value]",
        'held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value and flag != "rolcreatedb"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S5",
        "the flag rolbypassrls is not read",
        MIG,
        "held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value]",
        'held = [flag for flag, value in zip(_ROLE_FLAGS, row, strict=True) if value and flag != "rolbypassrls"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "B1",
        "a membership in a privileged role is not checked",
        MIG,
        "    if borrowed := [r[0] for r in db.execute(_BORROWED_ROLES_SQL).fetchall()]:\n",
        "    if False:\n",
        (
            k(
                T_WIRING,
                "test_a_role_that_is_a_member_of_a_privileged_role_is_refused_before_any_file_runs",
            ),
            k(
                T_PG,
                "test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server",
            ),
        ),
    ),
    Mutant(
        "B2",
        "the membership query matches no role",
        MIG,
        "AND r.rolname <> current_user AND pg_has_role(current_user, r.oid, 'MEMBER') ORDER BY r.rolname",
        "AND false ORDER BY r.rolname",
        (
            k(
                T_PG,
                "test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server",
            ),
            k(T_WIRING, "test_the_membership_check_reads_the_current_user_and_all_four_flags"),
        ),
    ),
    Mutant(
        "B3",
        "the test helper takes over any schema, public included",
        "tests/fixtures/migration_role.py",
        "                    if not _is_scratch(schema):\n",
        "                    if False:\n",
        k(T_PG, "test_the_test_helper_refuses_to_take_over_a_schema_that_is_not_a_scratch_one"),
    ),
    Mutant(
        "O1",
        "the check for objects another role owns is not called",
        MIG,
        "            _refuse_foreign_owned(db)\n",
        "            pass\n",
        (
            k(
                T_PG,
                "test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over",
            ),
            k(
                T_PG,
                "test_one_table_owned_by_another_role_is_enough_to_refuse_and_a_function_is_named",
            ),
        ),
    ),
    Mutant(
        "O2",
        "an object that another role owns is not looked for",
        MIG,
        "AND NOT pg_has_role(current_user, c.relowner, 'USAGE') ",
        "AND false ",
        k(T_PG, "test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over"),
    ),
    Mutant(
        "R6",
        "released_problems is not called by migrate()",
        MIG,
        "    if problems := released_problems(MIGRATIONS, _released_manifest(), texts, files):\n",
        "    if False:\n",
        k(T_WIRING, "test_migrate_refuses_a_changed_released_file_before_it_connects"),
    ),
    Mutant(
        "R7",
        "the released check lists the folder, not the files migrate runs",
        MN,
        "    listed = list_migration_files(folder) if files is None else files\n",
        "    listed = list_migration_files(folder)\n",
        k(T_WIRING, "test_the_released_check_looks_at_the_files_migrate_runs_not_at_the_folder"),
    ),
    Mutant(
        "R23",
        "the CHANGELOG sentence on what migrate checks goes",
        CL,
        "refuses, before it connects, a released file that was edited or deleted",
        "refuses a released file",
        k(T_RULES, "test_the_upgrade_bullet_says_what_migrate_checks_and_does_not_overclaim"),
    ),
]


async def _run_async(cmd, cwd, env, timeout):
    """Start one child process (no shell), wait at most `timeout` seconds, kill it on timeout."""
    t0 = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=cwd,
        env=env,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout)
    except TimeoutError:
        proc.kill()
        out, _ = await proc.communicate()
        return "TIMEOUT", out.decode("utf-8", "replace"), time.monotonic() - t0
    return proc.returncode, out.decode("utf-8", "replace"), time.monotonic() - t0


def run(cmd, cwd, env, timeout):
    return asyncio.run(_run_async(cmd, cwd, env, timeout))


def summary_line(out: str) -> str:
    for line in reversed(out.strip().splitlines()):
        if re.search(r"\b(passed|failed|error|errors|no tests ran)\b", line):
            return line.strip(" =")
    return out.strip().splitlines()[-1][:120] if out.strip() else ""


def killers_of(m: Mutant) -> list[str]:
    return [m.killer] if isinstance(m.killer, str) else list(m.killer)


def problems_with_the_list(root: Path = ROOT) -> list[str]:
    """Cheap check (no database): every `old` text is in its file exactly once, every killer file and test exists, and
    the names are unique."""
    problems = []
    names = [m.name for m in M]
    problems += [f"name used twice: {n}" for n in sorted({n for n in names if names.count(n) > 1})]
    for m in M:
        text = (root / m.file).read_text(encoding="utf-8")
        if text.count(m.old) != 1:
            problems.append(
                f"{m.name}: the old text is in {m.file} {text.count(m.old)} times (need exactly 1)"
            )
        for killer in killers_of(m):
            path, _, test = killer.partition("::")
            test = test.split("[")[0]
            if not (root / path).is_file() or f"def {test}(" not in (root / path).read_text(
                encoding="utf-8"
            ):
                problems.append(f"{m.name}: killer {killer} does not exist")
    return problems


def main(argv: list[str]) -> int:
    only = argv[0] if argv else ""
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print("STOP: HADAVIN_TEST_PG_DSN is not set (the Postgres killers need a scratch server)")
        return 2
    if problems := problems_with_the_list():
        print("STOP: the list of mutants is out of date:\n  " + "\n  ".join(problems))
        return 2
    work = Path(tempfile.mkdtemp(prefix="migrate-mutants-"))
    try:
        return _run_all(only, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _run_all(only: str, work: Path) -> int:
    timeout = 900
    copy = work / "repo"
    shutil.copytree(
        ROOT,
        copy,
        ignore=shutil.ignore_patterns(
            ".venv", ".git", "__pycache__", ".pytest_cache", "handover", "dist", ".env*"
        ),
    )
    env = dict(
        os.environ,
        PYTHONPATH=str(copy / "src"),
        PYTHONPYCACHEPREFIX=str(work / "pyc"),
        PYTHONDONTWRITEBYTECODE="1",
    )
    env.pop("PYTEST_ADDOPTS", None)
    py = sys.executable
    chk = run([py, "-c", "import hadavin_sdk;print(hadavin_sdk.__file__)"], copy, env, 60)[
        1
    ].strip()
    print(f"copy of the repository: {copy}\nimport path: {chk}")
    if not chk.startswith(str(copy)):
        print("STOP: hadavin_sdk is not imported from the copy under test")
        return 2
    base = ["-p", "no:cacheprovider", "-q", "-x", "--no-header"]
    selected = [m for m in M if not only or m.name == only]
    if not selected:
        print(f"STOP: no mutant has the id {only!r}")
        return 2
    killers = sorted({kid for m in selected for kid in killers_of(m)})
    rc, out, dt = run([py, "-m", "pytest", *base, *killers], copy, env, timeout)
    print(f"BASELINE rc={rc} {summary_line(out)} ({dt:.1f}s, {len(killers)} killer ids)")
    if rc != 0:
        print(out[-3000:])
        print("STOP: baseline not green")
        return 2
    print("name | description | result | pytest summary | seconds | killers")
    results = []
    for m in selected:
        path = copy / m.file
        original = path.read_bytes()
        try:
            path.write_bytes(original.decode("utf-8").replace(m.old, m.new, 1).encode("utf-8"))
            rc, out, dt = run([py, "-m", "pytest", *base, *killers_of(m)], copy, env, timeout)
        finally:
            path.write_bytes(original)
        status = "KILLED" if rc == 1 else "SURVIVED" if rc == 0 else f"ERROR(rc={rc})"
        results.append((m, status))
        print(
            f"{m.name} | {m.desc} | {status} | {summary_line(out)} | {dt:.1f}s | {', '.join(killers_of(m))}",
            flush=True,
        )
    killed = sum(1 for _, s in results if s == "KILLED")
    bad = [f"{m.name}:{s}" for m, s in results if s != "KILLED"]
    print(f"not killed: {bad}")
    print(f"{killed} of {len(results)} killed")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
