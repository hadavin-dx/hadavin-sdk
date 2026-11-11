"""Mutants of the migrate wiring: `store/migrate.py`, `store/migration_numbers.py`, the CHANGELOG runbook and
two test helpers. Not collected by pytest.

Each mutant plants ONE wrong line in a COPY of the repository (the working tree is never touched) and runs the tests
named in `killer`; the mutant is KILLED when pytest exits with code 1 AND a test of a named killer is among the failures
AND no output line shows that the planted line was simply broken (`NameError`, `SyntaxError`, `IndentationError`,
`ImportError`: that is BROKEN, not a kill). Exit code 0 means SURVIVED; any other code (collection error, timeout) is
ERROR and counts as not killed, so a syntax error cannot pass as a kill. An id on the command line that no mutant has is
refused (the run stops with exit code 2 and starts nothing). A
baseline run of every killer on the untouched copy must pass first. The mutants started as a reconstruction of an earlier
runner that was lost (what was known of it: names, one-line descriptions and killers; the planted text was
rewritten and proven by running) and were extended for the trigger read-back, the role check and the allow list.

Run from the repository root (needs the Postgres tests' variable HADAVIN_TEST_PG_DSN pointing at a scratch server whose
login may create schemas and roles; about 10 minutes):

    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py            # all; exit 1 if any is not killed
    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py M88,R4      # only these ids (comma-separated)

Each killer id runs on its own (no -x) so a killer that does not fail shows; only the failing ones are printed. The last line is `N of N killed`; the lines before it count the three kinds. A cheap check that runs with the ordinary tests,
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
T_K2 = "tests/test_k2_migrations.py"
T_NUM = "tests/test_migration_numbers.py"
T_GUARDS = "tests/test_migration_numbers_guards.py"
T_NAMES = "tests/test_migration_names.py"
T_CMP = "tests/test_migration_compare.py"
T_VERIFY = "tests/test_migration_verify.py"
T_STEPS = "tests/test_migration_steps.py"


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
SKIPS = k(T_RULES, "test_no_migration_test_skips_silently")
MEMBER = k(T_RULES, "test_role_membership_is_refused_whatever_the_comments_and_names_hold") + "[-]"
BLOCK_PG = k(T_PG, "test_runbook_case_b_renames_the_old_notes_row_back_and_migrate_accepts_it")
RUNBOOK = k(T_RULES, "test_the_runbook_carries_the_real_lock_the_command_and_every_case")
CMP_OLD = "        if old != new\n"
PAIR_FUNC = "def _table_body(text: str, start: int) -> str:"
LEX_CALL = "        text, lexer_problem = lex(raw, keep_quoted=True)\n"
SAVE_READ = (
    "                    if pending:\n"
    "                        saved = _read_back(db, schema, named)\n"
    "                        _refuse_unusual_strings(saved)\n"
    "                    for path in pending:  # step 3\n"
    '                        step[0] = f"applying {path.name}"\n'
    "                        db.execute(texts[path])  # the text that was scanned, never a second read\n"
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
    "                        saved = _check_read_back(\n"
    "                            db,\n"
    "                            saved,\n"
    "                            path.name,\n"
    "                            frozenset(c for c in allowed_changes if c.migration == path.stem),\n"
    "                            named,\n"
    "                            schema=schema,\n"
    "                        )\n"
)
RECHECK = (
    "                        with pinned_read(db, RECIPE_TIMEOUTS):\n"
    "                            _recheck_roles(db, named, path.name)\n"
)
INSERT = (
    "                        db.execute(\n"
    '                            "INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,)\n'
    "                        )\n"
)


# Batch 2 of the four mutant batches (ticket P3a-2, 5.5 and 7.10): the mutants re-pointed, re-checked or newly checked
# because their planted text sits in code that ticket P3a-2 edits. Ids that a later commit retires are taken out in that
# commit; `test_batch_2_names_only_real_mutants` fails until they are.
BATCH_2_IDS: frozenset[str] = frozenset(
    {
        # re-pointed (the rule lives on; the planted line moves)
        *("AC1", "AC2", "AC3", "AC4", "AC5", "SD1", "SD2", "SD6", "SD7", "SD8"),
        *("DP1", "DP2", "DP3", "DP4", "DP5", "DP6", "DP7", "DP8", "DP9"),
        *("SC8", "SC9", "SC12", "SC13", "SC14", "GO4", "GO5", "GO6", "RO1", "RO3", "RO4", "RO5"),
        *(
            "RA2",
            "RA4",
            "IM1",
            "RK1",
            "RK2",
            "RF5",
            "OW5",
            "OW6",
            "OW9",
            "MC2",
            "PDO2",
        ),
        *("R23", "SH1"),
        # re-checked, killer changes (the mutant text stays)
        *(
            "MW1",
            "S2",
            "S3",
            "S4",
            "S5",
            "B1",
            "SU1",
            "PA1",
            "RC2",
            "RF1",
            "R7",
            "CL1",
            "CL2",
            "GM1",
            "MC1",
            "OA4",
        ),
        # re-checked, planted inside code that moves
        *("M102", "LV1", "LV2", "LV3", "LV4", "LW4", "N15", "MW2", "MW3", "MW4", "MW5", "MW6"),
        *("M61", "M64", "M67", "M95", "T13", "RC1", "S1", "O1", "R6"),
        *("LW1", "LW2", "LW3", "LW5", "LW6", "MW8", "LW7", "LW8", "P8"),
    }
)


def cmp_mutant(name: str, item: str, desc: str, killer_item: str) -> Mutant:
    return Mutant(
        name,
        desc,
        MIG,
        CMP_OLD,
        f'        if old != new and item != "{item}"\n',
        f"{WIRING_VAL}[{killer_item}]",
    )


FILTER2 = '                        if not p.repaired_by_run and p.kind != "missing_schema_usage"\n'
STEP6_CALL = (
    "                        schema_owner=schema_owner,\n"
    "                    ):\n"
    "                        raise ConfigError(\n"
    '                            "after the migration files and the grants'
)
STEP8_TAIL = "                schema_owner=schema_owner,\n            )\n    except Exception as e:"


def S_(name: str) -> str:
    return k(T_STEPS, name)


S2_REFUSES = S_("test_a_right_found_at_step_2_refuses_the_run_before_any_file")
S2_EXCUSES = S_("test_step_2_does_not_refuse_what_step_4_repairs")
S4_REVOKE = S_("test_step_4_takes_everyones_execute_off_the_functions_the_files_name")
S6_REFUSES = S_("test_a_right_found_at_step_6_refuses_the_run_and_keeps_nothing")
S7_REFUSED = S_("test_a_commit_the_server_refuses_is_a_refusal_and_step_8_does_not_run")
S7_UNKNOWN = S_("test_a_commit_that_may_or_may_not_have_happened_is_applied_not_verified")
S8_SNAPSHOT = S_("test_step_8_reads_on_a_new_connection_in_one_snapshot_that_cannot_write")
S8_FOUND = S_("test_a_right_found_after_the_commit_is_applied_not_verified_with_the_statements")
PINNED = k(T_VERIFY, "test_every_runner_catalog_read_is_pinned")
OWNER_SAME = S_("test_a_schema_owned_by_the_same_role_as_at_the_start_is_not_a_problem")
OWNER_MOVED = S_("test_a_schema_that_changed_owner_during_the_run_is_still_a_problem")
OWNER_ONLY = k(
    T_STEPS, "test_only_the_schema_of_the_run_is_excused_not_another_object_with_the_same_owner"
)

# The eight steps of `migrate()` (ticket P3a-2, 3b): planted text inside the new body, each killed by a test of
# `tests/test_migration_steps.py` (or a real-server test).
STEP_MUTANTS: list[Mutant] = [
    Mutant(
        "E1",
        "step 2 refuses nothing",
        MIG,
        FILTER2,
        "                        if False\n",
        S2_REFUSES,
    ),
    Mutant(
        "E2",
        "step 2 also refuses what step 4 repairs itself",
        MIG,
        FILTER2,
        '                        if p.kind != "missing_schema_usage"\n',
        S2_EXCUSES,
    ),
    Mutant(
        "E3",
        "step 2 also refuses a missing USAGE that step 4 gives",
        MIG,
        FILTER2,
        "                        if not p.repaired_by_run\n",
        S2_EXCUSES,
    ),
    Mutant(
        "E4",
        "step 4 does not take everyone's EXECUTE off the new functions",
        MIG,
        "                    _revoke_default_execute(db, schema, me, login, texts.values())\n",
        "                    pass\n",
        S4_REVOKE,
    ),
    Mutant(
        "E5",
        "step 4 writes an aggregate with no arguments with empty brackets",
        MIG,
        'signature = args if args or kind != "a" else "*"\n        db.execute(',
        "signature = args\n        db.execute(",
        S4_REVOKE,
    ),
    Mutant(
        "E6",
        "step 4 revokes from the migration role instead of everyone",
        MIG,
        '"REVOKE ALL ON ROUTINE {}({}) FROM PUBLIC"',
        '"REVOKE ALL ON ROUTINE {}({}) FROM CURRENT_USER"',
        S4_REVOKE,
    ),
    Mutant(
        "E7",
        "step 5 does not run the deferred checks",
        MIG,
        '                        db.execute("SET CONSTRAINTS ALL IMMEDIATE")\n',
        "                        pass\n",
        (
            S_("test_step_5_runs_the_deferred_checks_before_the_commit"),
            S_("test_a_deferred_check_that_fails_at_step_5_is_a_refusal_with_its_reason"),
        ),
    ),
    Mutant(
        "E8",
        "step 6 never refuses for what the state check finds",
        MIG,
        STEP6_CALL,
        STEP6_CALL.replace("                    ):\n", "                    ) and False:\n", 1),
        S6_REFUSES,
    ),
    Mutant(
        "E9",
        "step 6 does not compare the session values once more",
        MIG,
        "                        _check_read_back(db, saved, END_OF_RUN, frozenset(), named, schema=schema)\n",
        "                        pass\n",
        S_("test_a_value_that_changed_only_after_the_grants_is_refused_at_step_6"),
    ),
    Mutant(
        "E10",
        "step 6 does not ask the role questions once more",
        MIG,
        "                            _recheck_roles(db, named, END_OF_RUN)\n",
        "                            pass\n",
        S_("test_a_role_that_became_privileged_after_the_grants_is_refused_at_step_6"),
    ),
    Mutant(
        "E11",
        "a refused commit is raised as the driver's own error",
        MIG,
        "                    reached_commit = True\n",
        "                    reached_commit = False\n",
        S7_REFUSED,
    ),
    Mutant(
        "E12",
        "every commit error is taken as unknown",
        MIG,
        '                if _commit_outcome(e, db) == "refused":\n',
        "                if False:\n",
        S7_REFUSED,
    ),
    Mutant(
        "E13",
        "an unknown commit is not marked unknown",
        MIG,
        "raise _after_commit(applied, [], commit_unknown=True) from e",
        "raise _after_commit(applied, [], commit_unknown=False) from e",
        S7_UNKNOWN,
    ),
    Mutant(
        "E14",
        "step 8 may write",
        MIG,
        "            after.read_only = True\n",
        "            pass\n",
        S8_SNAPSHOT,
    ),
    Mutant(
        "E15",
        "step 8 reads in more than one snapshot",
        MIG,
        "after.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ",
        "after.isolation_level = psycopg.IsolationLevel.READ_COMMITTED",
        S8_SNAPSHOT,
    ),
    Mutant(
        "E16",
        "an error of step 8 other than a driver error is raised as it is",
        MIG,
        "    except Exception as e:  # any error at all: the commit happened and the check did not finish\n",
        "    except psycopg.OperationalError as e:  # any error at all: the commit happened and the check did not finish\n",
        S_("test_a_check_that_cannot_run_after_the_commit_is_applied_not_verified") + "[verify]",
    ),
    Mutant(
        "E17",
        "step 8 does not report what it finds",
        MIG,
        "    if problems:\n        raise _after_commit(applied, problems)\n",
        "    if False:\n        raise _after_commit(applied, problems)\n",
        S8_FOUND,
    ),
    Mutant(
        "E18",
        "step 8 does not get the schema owner of step 1",
        MIG,
        STEP8_TAIL,
        STEP8_TAIL.replace("schema_owner=schema_owner", 'schema_owner=""'),
        S_("test_every_step_reads_the_same_names_and_the_schema_owner_read_at_step_1"),
    ),
    Mutant(
        "E19",
        "the schema owner is not read at step 1",
        MIG,
        '                    schema_owner = owner_row[0] if owner_row else ""\n',
        '                    schema_owner = ""\n',
        S_("test_every_step_reads_the_same_names_and_the_schema_owner_read_at_step_1"),
    ),
    Mutant(
        "E20",
        "a schema owned by a database administrator is a problem again",
        MIG,
        '            p.kind == "foreign_owner"\n',
        '            False and p.kind == "foreign_owner"\n',
        OWNER_SAME,
    ),
    Mutant(
        "E21",
        "a schema that changed owner is excused too",
        MIG,
        "            and p.owner == schema_owner\n",
        "            and True\n",
        OWNER_MOVED,
    ),
    Mutant(
        "E22",
        "every owner problem of the kind schema is excused, whatever the schema",
        MIG,
        "            and p.obj == schema\n",
        "            and True\n",
        OWNER_ONLY + "[other2]",
    ),
    Mutant(
        "E24",
        "the ownership read of step 1 runs outside pinned_read",
        MIG,
        "                    with pinned_read(db, RECIPE_TIMEOUTS):\n                        _refuse_foreign_owned(db, schema, texts.values())\n",
        "                    if True:\n                        _refuse_foreign_owned(db, schema, texts.values())\n",
        PINNED,
    ),
    Mutant(
        "E25",
        "the step-4 read runs outside pinned_read",
        MIG,
        "    with pinned_read(db, RECIPE_TIMEOUTS):\n        rows = db.execute(\n            STEP4_SQL",
        "    if True:\n        rows = db.execute(\n            STEP4_SQL",
        PINNED,
    ),
    Mutant(
        "E26",
        "the catalog reads of the read-back run outside pinned_read",
        MIG,
        "    with pinned_read(db, RECIPE_TIMEOUTS):\n        trigger_rows = db.execute(",
        "    if True:\n        trigger_rows = db.execute(",
        PINNED,
    ),
    Mutant(
        "E27",
        "a read after a file ended the transaction is still pinned (the driver asserts)",
        MIG,
        "    if if_ended is not None and db.info.transaction_status == TransactionStatus.IDLE:\n",
        "    if False:\n",
        (
            k(
                T_STEPS,
                "test_a_read_after_a_file_ended_the_transaction_is_not_pinned_and_keeps_the_saved_catalog_parts",
            ),
            k(T_PG, "test_a_hidden_commit_is_found_by_the_transaction_backstop"),
        ),
    ),
    Mutant(
        "E23",
        "every owner problem is excused, whatever the object kind",
        MIG,
        '            and p.word == "schema"\n',
        "            and True\n",
        OWNER_ONLY + "[other1]",
    ),
]


FX_ = "tests/fixtures/migration_role.py"
R = "test_a_right_for_a_role_the_run_does_not_name_is_refused"
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
        CALL + RECHECK + INSERT,
        INSERT + CALL + RECHECK,
        READS_BEFORE,
    ),
    Mutant(
        "M67",
        "read-back only after the last file",
        MIG,
        CALL,
        "                        if path is pending[-1]:\n"
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
        "                    saved = None\n"
        "                    for path in pending:  # step 3\n"
        '                        step[0] = f"applying {path.name}"\n'
        "                        db.execute(texts[path])  # the text that was scanned, never a second read\n"
        "                        if saved is None:\n"
        "                            saved = _read_back(db, schema, named)\n"
        "                            _refuse_unusual_strings(saved)\n",
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
        '"WHERE NOT t.tgisinternal AND n.nspname = %s"',
        '"WHERE NOT t.tgisinternal AND true"',
        k(T_WIRING, "test_trigger_query_reads_only_the_migration_schema"),
    ),
    # --- the commit outcome (commit 3a, ticket P3a-2 4.1 step 7) ---
    Mutant(
        "CO1",
        "a commit error is called refused whatever the transaction state",
        MIG,
        '    if db.info.transaction_status != TransactionStatus.IDLE:\n        return "unknown"\n',
        "",
        k(
            T_VERIFY,
            "test_commit_outcome_classes_unknown_without_a_code_a_closed_connection_or_a_transaction_state",
        ),
    ),
    Mutant(
        "CO2",
        "a commit error on a closed connection is called refused",
        MIG,
        'if not state or getattr(db, "closed", True):',
        "if not state:",
        k(
            T_VERIFY,
            "test_commit_outcome_classes_unknown_without_a_code_a_closed_connection_or_a_transaction_state",
        ),
    ),
    Mutant(
        "CO3",
        "the connection-loss class 08 is called refused",
        MIG,
        '_COMMIT_REFUSED_CLASSES = ("22", "23", "40", "42", "44", "P0")',
        '_COMMIT_REFUSED_CLASSES = ("08", "22", "23", "40", "42", "44", "P0")',
        k(T_VERIFY, "test_commit_outcome_classes_unknown_by_code") + "[08006]",
    ),
    Mutant(
        "CO4",
        "a refusing class is called unknown (23 left out)",
        MIG,
        '_COMMIT_REFUSED_CLASSES = ("22", "23", "40", "42", "44", "P0")',
        '_COMMIT_REFUSED_CLASSES = ("22", "40", "42", "44", "P0")',
        k(T_VERIFY, "test_commit_outcome_classes_refused") + "[23503]",
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
        '    if not DSN:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"hadavin_test_',
        '    if True:\n        pytest.skip("HADAVIN_TEST_PG_DSN not set")\n    schema = f"hadavin_test_',
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
        "three settings that change how SQL text is read",
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
    Mutant(
        "T3",
        "function text not compared",
        MIG,
        '"p.prosrc, p.prosecdef,',
        "\"'', p.prosecdef,",
        TRIG_CHANGED,
    ),
    Mutant(
        "T4",
        "function security mode not compared",
        MIG,
        "p.prosrc, p.prosecdef, pg_get_userbyid",
        "p.prosrc, false, pg_get_userbyid",
        TRIG_CHANGED,
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
        '        elif after[0] != before[0] and after[0] in ("D", "R") and after[0] != entry.state:\n',
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
        '        elif after[0] != before[0] and after[0] in ("D", "R") and after[0] != entry.state:\n',
        '        elif after[0] != before[0] and after[0] == "D" and after[0] != entry.state:\n',
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
        "members = frozenset(tuple(r) for r in member_rows)",
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
        "settings = frozenset(tuple(r) for r in setting_rows)",
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
        "held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]",
        'held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows) and flag != "rolsuper"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S3",
        "the flag rolcreaterole is not read",
        MIG,
        "held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]",
        'held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows) and flag != "rolcreaterole"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S4",
        "the flag rolcreatedb is not read",
        MIG,
        "held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]",
        'held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows) and flag != "rolcreatedb"]',
        ROLE_REFUSED,
    ),
    Mutant(
        "S5",
        "the flag rolbypassrls is not read",
        MIG,
        "held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows)]",
        'held = [flag for i, flag in enumerate(_ROLE_FLAGS) if any(row[i] for row in rows) and flag != "rolbypassrls"]',
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
        "AND r.rolname NOT IN (current_user, session_user) \"\n    \"AND (pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER')) \"",
        'AND r.rolname NOT IN (current_user, session_user) "\n    "AND false "',
        (
            k(
                T_PG,
                "test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server",
            ),
            k(
                T_WIRING,
                "test_the_membership_check_reads_both_user_names_all_five_flags_and_the_built_in_roles",
            ),
        ),
    ),
    Mutant(
        "B3",
        "the test helper takes over any schema, public included",
        "tests/fixtures/migration_role.py",
        "                if not _is_scratch(schema):\n",
        "                if False:\n",
        k(T_PG, "test_the_test_helper_refuses_to_take_over_a_schema_that_is_not_a_scratch_one"),
    ),
    Mutant(
        "O1",
        "the check for objects another role owns is not called",
        MIG,
        "            _refuse_foreign_owned(db, schema, texts.values())\n",
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
    # --- session user, built-in roles, parameter grants, grant option, ownership refusal ---
    Mutant(
        "SU1",
        "the flags are read for the current user only, not the session user",
        MIG,
        '"WHERE rolname IN (current_user, session_user)"',
        '"WHERE rolname IN (current_user)"',
        (
            k(T_PG, "test_a_superuser_login_that_switches_to_a_plain_role_is_refused"),
            k(T_WIRING, "test_the_role_flags_are_read_for_the_current_user_and_the_session_user"),
            k(
                T_WIRING,
                "test_a_privileged_session_user_is_refused_even_when_the_current_user_is_plain",
            ),
        ),
    ),
    Mutant(
        "SU2",
        "membership of a privileged role is checked for the current user only",
        MIG,
        "AND (pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER')) ",
        "AND (pg_has_role(current_user, r.oid, 'MEMBER') OR false) ",
        k(T_PG, "test_the_session_user_is_checked_for_membership_too"),
    ),
    Mutant(
        "PD1",
        "built-in server roles are not treated as privileged",
        MIG,
        "OR (left(r.rolname, 3) = 'pg_' AND r.rolname <> 'pg_database_owner')) ",
        "OR false) ",
        k(T_PG, "test_a_member_of_a_built_in_server_role_is_refused_by_a_real_server"),
    ),
    Mutant(
        "PA1",
        "a grant on a server setting is not looked for",
        MIG,
        "    if row and row[0] and (params := [",
        "    if False and (params := [",
        (
            k(T_PG, "test_a_parameter_grant_is_refused_by_a_real_server"),
            k(T_WIRING, "test_a_parameter_grant_is_refused_before_any_file_runs"),
        ),
    ),
    Mutant(
        "GO1",
        "the printed role SQL leaves out the grant option",
        MIG,
        "TO migration_role WITH GRANT OPTION;",
        "TO migration_role;",
        k(
            T_PG,
            "test_a_role_made_with_the_printed_sql_only_can_pass_usage_on_to_the_runtime_and_portal_roles",
        ),
    ),
    Mutant(
        "FO1",
        "a procedure or an aggregate is printed as a function",
        MIG,
        "{_FUNCTION_WORD.get(kind, 'FUNCTION')}",
        "FUNCTION",
        k(T_PG, "test_a_procedure_and_an_aggregate_get_their_own_words_and_the_printed_lines_run"),
    ),
    Mutant(
        "FO2",
        "a partition (its parent is in the way) owned by another role is not listed",
        MIG,
        "AND (c.relkind <> 'S' OR NOT EXISTS",
        "AND (false OR NOT EXISTS",
        k(T_PG, "test_a_partition_owned_by_another_role_is_listed"),
    ),
    Mutant(
        "FO3",
        "a name with a control character is copied into a printed statement",
        MIG,
        "        plain = all(escape_name(x) == x for x in (name, args, schema, me))\n",
        "        plain = True\n",
        k(T_PG, "test_a_name_with_a_newline_is_never_copied_into_a_printed_statement"),
    ),
    Mutant(
        "FO4",
        "only the shown names get a printed statement",
        MIG,
        "    for what, kind, name, owner, args in rows:\n",
        "    for what, kind, name, owner, args in rows[:_FOREIGN_OWNED_SHOWN]:\n",
        k(T_PG, "test_every_statement_is_printed_when_more_than_the_shown_names_are_foreign"),
    ),
    Mutant(
        "OW1",
        "an owner the role belongs to counts as safe without inheriting its rights",
        MIG,
        "c.relowner, 'USAGE') ",
        "c.relowner, 'MEMBER') ",
        k(T_PG, "test_an_owner_the_migration_role_belongs_to_is_safe_only_when_it_inherits"),
    ),
    Mutant(
        "OW2",
        "functions that another role owns are not looked for",
        MIG,
        "AND NOT pg_has_role(current_user, p.proowner, 'USAGE') ",
        "AND false ",
        k(T_PG, "test_the_function_half_of_the_ownership_check_finds_a_function_alone"),
    ),
    Mutant(
        "EX1",
        "functions of an installed extension are listed",
        MIG,
        "AND d.deptype = 'e') ORDER BY 1, 3, 5",
        "AND false) ORDER BY 1, 3, 5",
        k(T_PG, "test_objects_of_an_installed_extension_are_not_listed"),
    ),
    Mutant(
        "EX2",
        "tables and views of an installed extension are listed",
        MIG,
        '"AND d.deptype = \'e\') "\n    "AND (c.relkind',
        '"AND false) "\n    "AND (c.relkind',
        k(T_PG, "test_objects_of_an_installed_extension_are_not_listed"),
    ),
    # --- scoped read-back, managed names, parameter grants through memberships, test helper ---
    Mutant(
        "SC1",
        "the members query reads every role of the server",
        MIG,
        "WHERE m.member IN (SELECT oid FROM scope WHERE own OR via_membership) OR m.roleid IN (SELECT oid FROM scope WHERE own)",
        "WHERE true",
        k(T_PG, "test_another_session_changing_unrelated_roles_does_not_stop_the_run"),
    ),
    Mutant(
        "SC2",
        "the saved-settings query reads every role of the server",
        MIG,
        "AND (s.setrole = 0 OR s.setrole IN (SELECT oid FROM scope WHERE own OR via_membership))",
        "AND true",
        k(T_PG, "test_another_session_changing_unrelated_roles_does_not_stop_the_run"),
    ),
    Mutant(
        "SC3",
        "the migration user's own memberships are not compared",
        MIG,
        "WHERE m.member IN (SELECT oid FROM scope WHERE own OR via_membership)",
        "WHERE m.member IN (SELECT oid FROM scope WHERE false)",
        k(T_PG, "test_another_session_changing_the_migration_users_own_roles_stops_the_run"),
    ),
    Mutant(
        "SC3b",
        "the roles the migration user belongs to are not in the compared set",
        MIG,
        "\"(pg_has_role(current_user, r.oid, 'MEMBER') OR pg_has_role(session_user, r.oid, 'MEMBER') \"\n"
        "    \"OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS via_membership \"\n"
        '    "FROM pg_roles r) "\n'
        '    "SELECT m.roleid',
        '"false AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        MEMBERS,
    ),
    Mutant(
        "SC4",
        "a membership change is reported with the old wording",
        MIG,
        '"a role membership changed while the file ran (it may be another session; run migrate again): "',
        '"left the database session changed: "',
        k(T_WIRING, "test_the_membership_message_says_it_may_be_another_session"),
    ),
    Mutant(
        "SC5",
        "the named roles are not passed to the scoped queries",
        MIG,
        "    scope = (list(named),)\n",
        "    scope = ([],)\n",
        k(T_WIRING, "test_the_named_roles_reach_the_two_scoped_read_back_queries"),
    ),
    Mutant(
        "RC1",
        "the role questions are not asked again after a file",
        MIG,
        RECHECK,
        "                        pass\n",
        k(T_WIRING, "test_the_roles_are_asked_again_after_every_file"),
    ),
    Mutant(
        "RC2",
        "the named roles are not checked against each other after a file",
        MIG,
        "        _refuse_privileged_role(db)\n        if _members_of_each_other(db, named):\n",
        "        _refuse_privileged_role(db)\n        if False:\n",
        k(T_WIRING, "test_the_named_roles_are_checked_against_each_other_after_every_file"),
    ),
    Mutant(
        "OA1",
        "the table half of the ownership check lists every relation of the schema",
        MIG,
        "AND c.relname = ANY(%s::text[]) ",
        "AND (c.relname = ANY(%s::text[]) OR true) ",
        k(
            T_PG,
            "test_tables_and_functions_of_another_application_in_the_schema_are_never_refused_or_listed",
        ),
    ),
    Mutant(
        "OA2",
        "the function half of the ownership check lists every function of the schema",
        MIG,
        "AND p.proname = ANY(%s::text[]) ",
        "AND (p.proname = ANY(%s::text[]) OR true) ",
        k(
            T_PG,
            "test_tables_and_functions_of_another_application_in_the_schema_are_never_refused_or_listed",
        ),
    ),
    Mutant(
        "OA3",
        "the functions the files create are not managed names",
        MIG,
        "        for m in _FUNCTION_CREATE.finditer(text):\n",
        "        for m in ():\n",
        (
            k(
                T_WIRING,
                "test_the_managed_names_are_the_grant_map_the_ledger_and_the_functions_the_files_create",
            ),
            k(T_PG, "test_a_function_a_migration_file_creates_counts_as_managed"),
        ),
    ),
    Mutant(
        "OA4",
        "the managed names are not given to the function half of the query",
        MIG,
        "db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, managed_fn))",
        "db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, []))",
        k(
            T_CMP,
            "test_the_ownership_check_before_the_files_gets_the_relation_names_and_the_function_names_apart",
        ),
    ),
    Mutant(
        "OA5",
        "the ledger table is not a managed name",
        MIG,
        'relations = set(GRANTS) | {"schema_migrations"}',
        "relations = set(GRANTS)",
        (
            k(
                T_WIRING,
                "test_the_managed_names_are_the_grant_map_the_ledger_and_the_functions_the_files_create",
            ),
            k(
                T_PG,
                "test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over",
            ),
        ),
    ),
    Mutant(
        "MT1",
        "the MAINTAIN privilege is never asked about",
        MIG,
        '+ (("MAINTAIN",) if row and row[0] >= _MAINTAIN_FROM else ())',
        "+ ()",
        k(T_WIRING, "test_the_maintain_privilege_is_asked_about_from_postgresql_17_only"),
    ),
    Mutant(
        "MT2",
        "the MAINTAIN privilege is asked about on every version",
        MIG,
        "_MAINTAIN_FROM = 170000",
        "_MAINTAIN_FROM = 0",
        k(T_WIRING, "test_the_maintain_privilege_is_asked_about_from_postgresql_17_only"),
    ),
    Mutant(
        "PA2",
        "the ALTER SYSTEM parameter right is not asked about",
        MIG,
        "OR has_parameter_privilege(r.oid, a.parname, 'ALTER SYSTEM')) ",
        "OR false) ",
        k(T_PG, "test_a_parameter_grant_is_refused_however_the_migration_user_holds_it"),
    ),
    Mutant(
        "PA3",
        "the session user is not asked about parameter rights",
        MIG,
        "\"WHERE (r.rolname IN (current_user, session_user) OR pg_has_role(current_user, r.oid, 'MEMBER') \"\n"
        "    \"OR pg_has_role(session_user, r.oid, 'MEMBER')) \"",
        "\"WHERE (r.rolname IN (current_user) OR pg_has_role(current_user, r.oid, 'MEMBER') \"\n"
        '    "OR false) "',
        k(T_PG, "test_a_parameter_grant_is_refused_however_the_migration_user_holds_it"),
    ),
    Mutant(
        "PA4",
        "parameter rights are asked about for the user itself only, not the roles it belongs to",
        MIG,
        "\"WHERE (r.rolname IN (current_user, session_user) OR pg_has_role(current_user, r.oid, 'MEMBER') \"\n"
        "    \"OR pg_has_role(session_user, r.oid, 'MEMBER')) \"",
        '"WHERE (r.rolname IN (current_user, session_user) "\n    "OR false) "',
        k(T_PG, "test_a_parameter_grant_is_refused_however_the_migration_user_holds_it"),
    ),
    Mutant(
        "DO1",
        "the owner of the database (pg_database_owner) is refused like any built-in role",
        MIG,
        "AND r.rolname <> 'pg_database_owner'",
        "AND true",
        k(T_PG, "test_the_owner_of_a_database_belongs_to_pg_database_owner_and_is_not_refused"),
    ),
    Mutant(
        "FO5",
        "an aggregate with no arguments is printed with the star of ALTER AGGREGATE",
        "src/hadavin_sdk/store/migration_verify.py",
        'args = "" if sub == "*" else sub',
        "args = sub",
        k(T_PG, "test_an_aggregate_with_no_arguments_is_revoked_with_empty_brackets"),
    ),
    Mutant(
        "OS1",
        "a sequence that belongs to a table column is listed on its own",
        MIG,
        "AND d.deptype IN ('a','i'))) ",
        "AND false)) ",
        k(T_PG, "test_a_sequence_that_belongs_to_a_table_column_is_not_listed_on_its_own"),
    ),
    Mutant(
        "PR1",
        "the printed role SQL gives CREATE with the grant option",
        MIG,
        '"GRANT CREATE ON SCHEMA <schema> TO migration_role; "',
        '"GRANT CREATE ON SCHEMA <schema> TO migration_role WITH GRANT OPTION; "',
        k(T_PG, "test_the_printed_role_may_pass_usage_on_but_not_create"),
    ),
    Mutant(
        "TR1",
        "the exit hook does not drop the test role",
        "tests/fixtures/migration_role.py",
        'db.execute(sql.SQL("DROP ROLE IF EXISTS {}").format(sql.Identifier(PLAIN_ROLE)))',
        "pass",
        k(T_PG, "test_the_plain_test_role_and_what_it_owns_are_dropped_when_the_process_exits"),
    ),
    Mutant(
        "TR1b",
        "the exit hook drops what the role owns without CASCADE",
        "tests/fixtures/migration_role.py",
        'DROP OWNED BY {} CASCADE").format(sql.Identifier(PLAIN_ROLE))',
        'DROP OWNED BY {}").format(sql.Identifier(PLAIN_ROLE))',
        k(T_PG, "test_the_plain_test_role_and_what_it_owns_are_dropped_when_the_process_exits"),
    ),
    Mutant(
        "TR2",
        "the test role is created without looking in pg_roles first",
        "tests/fixtures/migration_role.py",
        'if db.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (PLAIN_ROLE,)).fetchone():\n        return\n',
        "if False:\n        return\n",
        k(T_WIRING, "test_the_test_role_is_looked_up_first_and_not_made_a_second_time"),
    ),
    Mutant(
        "TR3",
        "the raw test-role password is sent to the server",
        "tests/fixtures/migration_role.py",
        "sql.Literal(scram_hash(db, role, password))",
        "sql.Literal(password)",
        k(T_WIRING, "test_the_test_role_password_is_sent_only_as_a_hash"),
    ),
    Mutant(
        "TR4",
        "a schema named t_... counts as a scratch schema",
        "tests/fixtures/migration_role.py",
        'SCRATCH_PREFIXES = (\n    "hadavin_test_",\n)',
        'SCRATCH_PREFIXES = (\n    "hadavin_test_",\n    "t_",\n)',
        k(T_WIRING, "test_only_a_schema_with_the_test_prefix_is_a_scratch_schema"),
    ),
    Mutant(
        "RN1",
        "the mutant runner accepts an id that no mutant has",
        "tests/migrate_mutants.py",
        '    return [n for n in only.split(",") if n and n not in known]\n',
        "    return []\n",
        k(T_RULES, "test_the_mutant_runner_refuses_an_unknown_id"),
    ),
    Mutant(
        "RN2",
        "the mutant runner counts a NameError as a kill",
        "tests/migrate_mutants.py",
        "and only_test_failures(out):\n",
        "and True:\n",
        k(T_RULES, "test_the_mutant_runner_does_not_count_a_broken_line_as_a_kill"),
    ),
    Mutant(
        "TN1",
        "a trigger name with a control character is accepted in the allow list",
        MIG,
        '        if escape_name(entry["trigger"]) != entry["trigger"]:\n',
        "        if False:\n",
        k(T_WIRING, "test_a_trigger_name_that_is_not_plain_is_refused_in_the_list"),
    ),
    Mutant(
        "NR1",
        "the roles a named role belongs to are not in the compared memberships",
        MIG,
        "\"OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS via_membership \"\n"
        '    "FROM pg_roles r) "\n'
        '    "SELECT m.roleid',
        '"OR false) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        k(
            T_PG,
            "test_another_session_changing_a_role_that_a_named_role_belongs_to_stops_the_run",
        ),
    ),
    Mutant(
        "NR2",
        "the roles a named role belongs to are not in the compared saved settings",
        MIG,
        "\"OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, 'MEMBER'))) AS via_membership \"\n"
        '    "FROM pg_roles r) "\n'
        '    "SELECT coalesce',
        '"OR false) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT coalesce',
        k(
            T_PG,
            "test_another_session_changing_a_role_that_a_named_role_belongs_to_stops_the_run",
        ),
    ),
    Mutant(
        "MN1",
        "a plain function name is not folded to lower case",
        MIG,
        "return _fold(plain) if plain is not None else None",
        "return plain",
        (
            k(
                T_WIRING,
                "test_a_plain_function_name_is_folded_to_lower_case_and_a_quoted_one_is_read_whole",
            ),
            k(T_PG, "test_functions_with_capitals_or_a_space_in_the_name_count_as_managed"),
        ),
    ),
    Mutant(
        "MN2",
        "a quoted function name is cut at its first space",
        MIG,
        '_QUOTED_NAME_BODY = r\'"((?:[^"]|"")+)"\'',
        '_QUOTED_NAME_BODY = r\'"([^" ]+)"\'',
        (
            k(
                T_WIRING,
                "test_a_plain_function_name_is_folded_to_lower_case_and_a_quoted_one_is_read_whole",
            ),
            k(T_PG, "test_functions_with_capitals_or_a_space_in_the_name_count_as_managed"),
        ),
    ),
    Mutant(
        "DD1",
        "the search path stays in the server entry, so each scratch schema is one more entry",
        "tests/fixtures/migration_role.py",
        '    parts.pop("options", None)\n',
        "    pass\n",
        k(T_PG, "test_one_connection_target_is_one_entry_whatever_the_search_path"),
    ),
    Mutant(
        "SW1",
        "the stale roles are not swept when the test role is made",
        "tests/fixtures/migration_role.py",
        "    _mark_the_role(db)\n    sweep_stale_roles(db)\n",
        "    _mark_the_role(db)\n",
        k(
            T_WIRING,
            "test_making_the_test_role_first_sweeps_the_stale_roles_of_killed_processes",
        ),
    ),
    Mutant(
        "SW2",
        "a stale test role with an open session is dropped",
        "tests/fixtures/migration_role.py",
        'WHERE a.usename = r.rolname "\n        "OR a.application_name = r.rolname) "',
        'WHERE a.application_name = r.rolname) "',
        k(T_PG, "test_a_test_role_left_by_a_killed_process_is_swept_and_a_live_one_is_not"),
    ),
    Mutant(
        "SW3",
        "a test role whose process lock is held is dropped",
        "tests/fixtures/migration_role.py",
        '        if not db.execute("SELECT pg_try_advisory_lock(%s)", (key,)).fetchone()[0]:\n',
        "        if False:\n",
        k(T_PG, "test_a_test_role_left_by_a_killed_process_is_swept_and_a_live_one_is_not"),
    ),
    Mutant(
        "RN3",
        "the mutant runner's allow list takes any exception as a kill",
        "tests/migrate_mutants.py",
        "    return bool(heads) and all(_KILL_HEAD.match(h) for h in heads)\n",
        "    return bool(heads)\n",
        k(T_RULES, "test_the_mutant_runner_does_not_count_a_broken_line_as_a_kill"),
    ),
    Mutant(
        "RN4",
        "the mutant runner's allow list takes any dotted name, so a server error counts as a kill",
        "tests/migrate_mutants.py",
        "(?:assert\\b|AssertionError\\b|Failed:|",
        "(?:[\\w.]+|assert\\b|AssertionError\\b|Failed:|",
        k(T_RULES, "test_the_mutant_runner_does_not_count_a_broken_line_as_a_kill"),
    ),
    Mutant(
        "RN5",
        "the mutant runner counts a test that could not start as a kill",
        "tests/migrate_mutants.py",
        "(?!.*TEST SETUP PROBLEM)(?:assert\\b",
        "(?:assert\\b",
        k(T_RULES, "test_the_mutant_runner_does_not_count_a_broken_line_as_a_kill"),
    ),
    Mutant(
        "FQ1",
        "a plain function name is folded with Python's lower(), which also changes capitals of other scripts",
        MIG,
        'c.lower() if "A" <= c <= "Z" else c',
        "c.lower()",
        k(
            T_WIRING,
            "test_a_name_is_folded_as_the_server_folds_it_and_is_read_only_at_the_start_of_a_statement",
        ),
    ),
    Mutant(
        "PL1",
        "a dollar sign ends a plain function name",
        MIG,
        '_PLAIN_NAME = r"\\w[\\w$]*"',
        '_PLAIN_NAME = r"\\w+"',
        k(
            T_WIRING,
            "test_a_name_is_folded_as_the_server_folds_it_and_is_read_only_at_the_start_of_a_statement",
        ),
    ),
    Mutant(
        "ST1",
        "a function is read from anywhere in a statement, not only at its start",
        MIG,
        "(?:\\A|;)\\s*CREATE\\s+(?:OR\\s+REPLACE\\s+)?FUNCTION",
        "CREATE\\s+(?:OR\\s+REPLACE\\s+)?FUNCTION",
        k(
            T_WIRING,
            "test_a_name_is_folded_as_the_server_folds_it_and_is_read_only_at_the_start_of_a_statement",
        ),
    ),
    Mutant(
        "NM1",
        "the named roles are not 'own' in the members read-back, so a new member of one is not seen",
        MIG,
        'OR r.oid IN (SELECT oid FROM named)) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        'OR false) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        k(T_PG, "test_a_new_member_of_a_named_role_stops_the_run"),
    ),
    Mutant(
        "NS1",
        "a superuser among the named roles is not left out of the compared set (members read-back)",
        MIG,
        'rolname = ANY(%s::text[]) AND NOT rolsuper), "\n    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        'rolname = ANY(%s::text[])), "\n    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT m.roleid',
        k(T_PG, "test_a_superuser_among_the_named_roles_does_not_widen_the_read_back"),
    ),
    Mutant(
        "SW4",
        "the live-process lock is never taken when the test role is made",
        "tests/fixtures/migration_role.py",
        "    _mark_the_role(db)\n",
        "",
        k(
            T_WIRING,
            "test_the_live_process_lock_is_taken_on_the_connection_target_that_makes_the_role",
        ),
    ),
    Mutant(
        "SW5",
        "the live-process lock is taken on a fixed local server, not on the server that makes the role",
        "tests/fixtures/migration_role.py",
        "    mark = psycopg.connect(\n        make_conninfo(db.info.dsn, password=db.info.password or None, application_name=PLAIN_ROLE),\n        autocommit=True,\n    )\n",
        '    mark = psycopg.connect("host=localhost", autocommit=True)\n',
        k(
            T_WIRING,
            "test_the_live_process_lock_is_taken_on_the_connection_target_that_makes_the_role",
        ),
    ),
    Mutant(
        "SW6",
        "a test-role token is read by int(x, 16) alone, so signs and spaces pass",
        "tests/fixtures/migration_role.py",
        '    if not re.fullmatch(r"[0-9a-f]{8}", token):\n',
        "    if False:\n",
        k(T_WIRING, "test_only_eight_lower_case_hex_digits_are_a_token"),
    ),
    Mutant(
        "SW7",
        "the sweep does not look at the name of the connections, so a role held from another database is dropped",
        "tests/fixtures/migration_role.py",
        'a.usename = r.rolname "\n        "OR a.application_name = r.rolname) "',
        'a.usename = r.rolname) "',
        k(
            T_PG,
            "test_a_role_held_from_one_database_is_not_swept_from_another_database_of_the_server",
        ),
    ),
    Mutant(
        "SW8",
        "the marking connection is not named like the role",
        "tests/fixtures/migration_role.py",
        "password=db.info.password or None, application_name=PLAIN_ROLE),",
        "password=db.info.password or None),",
        (
            k(
                T_WIRING,
                "test_the_live_process_lock_is_taken_on_the_connection_target_that_makes_the_role",
            ),
            k(
                T_PG,
                "test_a_role_held_from_one_database_is_not_swept_from_another_database_of_the_server",
            ),
        ),
    ),
    Mutant(
        "SW9",
        "the marking connection is left open when the lock cannot be taken",
        "tests/fixtures/migration_role.py",
        "    except BaseException:\n        mark.close()\n        raise\n",
        "    except BaseException:\n        raise\n",
        k(T_WIRING, "test_the_marking_connection_is_closed_when_the_lock_cannot_be_taken"),
    ),
    Mutant(
        "NS2",
        "a superuser among the named roles is not left out of the compared set (settings read-back)",
        MIG,
        'rolname = ANY(%s::text[]) AND NOT rolsuper), "\n    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT coalesce(d.datname',
        'rolname = ANY(%s::text[])), "\n    "scope AS (SELECT r.oid, (r.rolname IN (current_user, session_user) OR r.oid IN (SELECT oid FROM named)) AS own, "\n    "(pg_has_role(current_user, r.oid, \'MEMBER\') OR pg_has_role(session_user, r.oid, \'MEMBER\') "\n    "OR EXISTS (SELECT 1 FROM named n WHERE pg_has_role(n.oid, r.oid, \'MEMBER\'))) AS via_membership "\n    "FROM pg_roles r) "\n    "SELECT coalesce(d.datname',
        k(T_PG, "test_a_superuser_among_the_named_roles_does_not_widen_the_read_back")
        + "[settings]",
    ),
    Mutant(
        "SQ1",
        "a function written with another schema before the dot is read as a managed name of this schema",
        MIG,
        "if where is None or where == schema:",
        "if True:",
        k(T_WIRING, "test_a_function_of_another_schema_is_not_a_managed_name"),
    ),
    Mutant(
        "SQ2",
        "a function written with this schema before the dot is not read as a managed name",
        MIG,
        "if where is None or where == schema:",
        "if where is None:",
        k(T_WIRING, "test_a_function_of_another_schema_is_not_a_managed_name"),
    ),
    Mutant(
        "SW10",
        "the marking connection is not given the password of the connection",
        "tests/fixtures/migration_role.py",
        "make_conninfo(db.info.dsn, password=db.info.password or None, application_name=PLAIN_ROLE),",
        "make_conninfo(db.info.dsn, application_name=PLAIN_ROLE),",
        k(T_WIRING, "test_the_marking_connection_is_given_the_password_of_the_connection"),
    ),
    Mutant(
        "SW11",
        "the sweep does not ask whether the login can see the sessions of other users",
        "tests/fixtures/migration_role.py",
        "    if not seen or not seen[0]:\n",
        "    if False:\n",
        (
            k(T_WIRING, "test_a_login_that_cannot_see_other_sessions_sweeps_nothing"),
            k(
                T_PG,
                "test_a_login_that_cannot_see_other_sessions_sweeps_nothing_on_a_real_server",
            ),
        ),
    ),
    Mutant(
        "SW12",
        "the unlock after a sweep is not guarded against a broken connection",
        "tests/fixtures/migration_role.py",
        '            try:\n                db.execute("SELECT pg_advisory_unlock(%s)", (key,))\n            except psycopg.Error:\n                pass  # a broken connection must not fail the setup of a test\n',
        '            db.execute("SELECT pg_advisory_unlock(%s)", (key,))\n',
        k(T_WIRING, "test_a_failed_unlock_does_not_fail_the_setup"),
    ),
    Mutant(
        "SW13",
        "the sweep drops a role that owns a schema that is not a scratch schema",
        "tests/fixtures/migration_role.py",
        "AND NOT (n.nspname LIKE ANY(%s)))",
        "AND %s::text[] IS NULL)",
        k(T_PG, "test_a_role_that_owns_a_schema_that_is_not_a_scratch_schema_is_not_swept"),
    ),
    Mutant(
        "SW14",
        "the message of a role that could not be dropped does not name the databases",
        "tests/fixtures/migration_role.py",
        'where = ", ".join(_databases_that_still_hold(db, name)) or "none found"',
        'where = "none found"',
        k(
            T_PG,
            "test_a_stale_role_that_owns_objects_in_another_database_is_left_and_the_databases_are_named",
        ),
    ),
    Mutant(
        "SW15",
        "the exit hook cleans only the first database before it drops the role",
        "tests/fixtures/migration_role.py",
        "            for dsn in dsns:\n",
        "            for dsn in dsns[:1]:\n",
        k(
            T_PG,
            "test_the_exit_hook_drops_what_the_role_owns_in_every_used_database_and_then_the_role",
        ),
    ),
    Mutant(
        "TD1",
        "a function name with a database part (db.schema.name) is read as schema db and name schema",
        MIG,
        '_SCHEMA_DOT = rf"{_DATABASE_DOT}(?:',
        '_SCHEMA_DOT = rf"(?:',
        k(T_WIRING, "test_a_function_of_another_schema_is_not_a_managed_name"),
    ),
    Mutant(
        "ML1",
        "the refusal for objects of another role does not say that nothing was changed",
        MIG,
        'unchanged = "Nothing was changed."',
        'unchanged = ""',
        k(
            T_PG,
            "test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over",
        ),
    ),
    Mutant(
        "GM1",
        "the words after a refusal of the portal role do not say what the grant map is",
        MIG,
        "for the portal role SELECT only)",
        "the one right it may have on each)",
        k(T_PG, "test_the_portal_role_is_refused_what_the_other_roles_are_refused"),
    ),
    Mutant(
        "GD1",
        "one test login loses its password",
        "tests/test_migration_postgres.py",
        "make_conninfo(DSN, user=live, password=passwords[live])",
        "make_conninfo(DSN, user=live)",
        k(T_RULES, "test_no_test_logs_in_as_a_role_without_passing_its_password"),
    ),
    Mutant(
        "RP1",
        "the test role is made without NOREPLICATION",
        "tests/fixtures/migration_role.py",
        "NOBYPASSRLS NOREPLICATION PASSWORD",
        "NOBYPASSRLS PASSWORD",
        k(T_WIRING, "test_the_test_role_is_made_without_the_replication_flag"),
    ),
    Mutant(
        "AC1",
        "the rights on tables, views and sequences are not read back",
        MIG,
        "CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE ((",
        "CROSS JOIN LATERAL aclexplode(c.relacl) a WHERE false AND ((",
        k(T_PG, R),
    ),
    Mutant(
        "AC2",
        "the rights on single columns are not read back",
        MIG,
        "CROSS JOIN LATERAL aclexplode(t.attacl) a WHERE ((",
        "CROSS JOIN LATERAL aclexplode(t.attacl) a WHERE false AND ((",
        k(T_PG, R),
    ),
    Mutant(
        "AC3",
        "the rights on functions are not read back",
        MIG,
        "        elif who is not None and not is_owner:\n            if who not in allowed:",
        "        elif False:\n            if who not in allowed:",
        k(T_PG, R),
    ),
    Mutant(
        "AC4",
        "PUBLIC (everyone) is allowed to hold a right",
        MIG,
        "    allowed = set(named)\n    keys = {",
        '    allowed = set(named) | {"PUBLIC"}\n    keys = {',
        k(T_PG, R),
    ),
    Mutant(
        "AC5",
        "the default 'everyone may call it' of a function is not removed",
        MIG,
        "    for ident in revoke:",
        "    for ident in []:",
        k(
            T_PG,
            "test_the_named_roles_and_the_owner_may_hold_rights_and_a_function_loses_the_default_for_everyone",
        ),
    ),
    Mutant(
        "SD1",
        "a SECURITY DEFINER function is not looked at",
        MIG,
        "        if definer and name not in REVIEWED_DEFINER_FUNCTIONS:",
        "        if False and name not in REVIEWED_DEFINER_FUNCTIONS:",
        k(T_PG, "test_a_security_definer_function_is_refused_unless_a_reviewer_listed_it"),
    ),
    Mutant(
        "SD2",
        "the reviewed list of SECURITY DEFINER functions is not read",
        MIG,
        "name not in REVIEWED_DEFINER_FUNCTIONS:",
        "name not in ():",
        k(T_PG, "test_a_security_definer_function_is_refused_unless_a_reviewer_listed_it"),
    ),
    Mutant(
        "LW1",
        "the wait for the migration lock is not limited",
        MIG,
        "    db.execute(\n        f\"SET LOCAL lock_timeout = '{int(wait_seconds) * 1000}ms'; SET LOCAL statement_timeout = 0;\"\n    )\n",
        "",
        k(T_WIRING, "test_the_wait_for_the_lock_is_limited_by_the_argument"),
    ),
    Mutant(
        "LW2",
        "a run that gives up does not name the session that holds the lock",
        MIG,
        "        row = db.execute(_LOCK_HOLDER_SQL, (MIGRATE_LOCK,)).fetchone()",
        "        row = None",
        k(T_PG, "test_a_run_that_cannot_get_the_migration_lock_gives_up_and_names_the_holder"),
    ),
    Mutant(
        "LW3",
        "the wait is the constant, not the argument",
        MIG,
        "int(wait_seconds) * 1000",
        "MIGRATE_LOCK_WAIT_SECONDS * 1000",
        k(T_WIRING, "test_the_wait_for_the_lock_is_limited_by_the_argument"),
    ),
    Mutant(
        "SW16",
        "the sweep that cannot see other sessions says nothing",
        FX_,
        '"stale test roles were not looked for: this login is neither a superuser nor a member of pg_read_all_stats, "',
        '"x "',
        k(T_WIRING, "test_a_login_that_cannot_see_other_sessions_sweeps_nothing"),
    ),
    Mutant(
        "SW17",
        "a dead marking connection is kept",
        FX_,
        '        try:\n            if not mark.closed:\n                mark.execute("SELECT 1")\n                return\n        except psycopg.Error:\n            pass\n',
        "        return\n",
        k(T_PG, "test_a_marking_connection_that_died_is_opened_again_and_the_role_is_not_swept"),
    ),
    Mutant(
        "SG1",
        "the sweep does not look at tables and views the role owns",
        FX_,
        '"UNION ALL SELECT relnamespace FROM pg_class WHERE relowner = r.oid "',
        '""',
        k(
            T_PG,
            "test_a_role_that_owns_a_table_function_or_type_outside_a_scratch_schema_is_not_swept",
        ),
    ),
    Mutant(
        "SG2",
        "the sweep does not look at functions the role owns",
        FX_,
        '"UNION ALL SELECT pronamespace FROM pg_proc WHERE proowner = r.oid "',
        '""',
        k(
            T_PG,
            "test_a_role_that_owns_a_table_function_or_type_outside_a_scratch_schema_is_not_swept",
        ),
    ),
    Mutant(
        "SG3",
        "the sweep does not look at types the role owns",
        FX_,
        '"UNION ALL SELECT typnamespace FROM pg_type WHERE typowner = r.oid) o JOIN pg_namespace n ON n.oid = o.ns "',
        '") o JOIN pg_namespace n ON n.oid = o.ns "',
        k(
            T_PG,
            "test_a_role_that_owns_a_table_function_or_type_outside_a_scratch_schema_is_not_swept",
        ),
    ),
    Mutant(
        "GD2",
        "any ** expansion counts as a password in the login guard",
        T_RULES,
        "        if k.arg is None and any(",
        "        if k.arg is None or any(",
        k(T_RULES, "test_the_password_scan_reads_the_star_star_forms"),
    ),
    Mutant(
        "SD4",
        "only the schema of the run is read for functions (a function in another schema escapes)",
        MIG,
        '"FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE "\n    "@NOT_SYSTEM_P@"',
        '"FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace WHERE n.nspname = current_schema() AND "\n    "@NOT_SYSTEM_P@"',
        (
            k(T_PG, "test_a_security_definer_function_written_with_another_schema_is_refused"),
            k(T_PG, "test_a_plain_function_in_another_schema_loses_the_default_right_for_everyone"),
        ),
    ),
    Mutant(
        "SD5",
        "only new ids are looked at, not the state of an object that existed before (a replaced function, a table whose rights changed)",
        MIG,
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st",
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and i not in before",
        (
            k(T_PG, "test_a_function_replaced_with_the_same_id_and_made_security_definer_is_found"),
            k(T_PG, "test_a_right_given_on_a_table_that_existed_before_the_run_is_refused")
            + "[table]",
            k(T_PG, "test_an_owner_handed_over_in_the_run_schema_is_refused"),
            k(
                T_PG,
                "test_with_the_printed_role_an_owner_handed_over_is_the_one_cause_of_the_refusal",
            ),
        ),
    ),
    Mutant(
        "RN6",
        "relations that changed during the run are not read",
        MIG,
        "        _changed_ids(before.relations, after.relations),",
        "        frozenset(),",
        k(T_PG, "test_a_table_made_by_dynamic_sql_and_opened_to_everyone_is_refused"),
    ),
    Mutant(
        "DP1",
        "the default rights are not read",
        MIG,
        "    for kind, where, who, priv, for_role in db.execute(_ACL_DEFAULT_SQL).fetchall():",
        "    for kind, where, who, priv, for_role in []:",
        k(
            T_PG,
            "test_a_default_right_that_an_administrator_set_is_refused_and_the_message_says_so",
        ),
    ),
    Mutant(
        "SC8",
        "the rights on the schemas are not read",
        MIG,
        "    for sname, who, priv, grantable, is_owner in db.execute(_ACL_SCHEMA_SQL, keys).fetchall():",
        "    for sname, who, priv, grantable, is_owner in []:",
        k(
            T_PG,
            "test_a_role_that_may_create_in_the_schema_is_refused_but_one_that_may_only_look_is_not",
        ),
    ),
    Mutant(
        "SC9",
        "a role that may only use the schema is refused too",
        MIG,
        '        elif priv != "USAGE":  # USAGE only lets a role look a name up',
        "        else:  # USAGE only lets a role look a name up",
        k(
            T_PG,
            "test_a_role_that_may_create_in_the_schema_is_refused_but_one_that_may_only_look_is_not",
        ),
    ),
    Mutant(
        "OW4",
        "any owner is accepted (an owner a file handed an object to too)",
        MIG,
        "        i for i, st in after.items() if i in before and before[i][_OWNER] == st[_OWNER]",
        "        i for i, st in after.items() if True",
        k(
            T_PG,
            "test_an_owner_a_file_handed_an_object_to_is_refused_even_when_the_migration_role_belongs_to_it",
        ),
    ),
    Mutant(
        "OW3",
        "a relation that kept the owner it had before the files is refused for that owner",
        MIG,
        "        _kept_owner_ids(before.relations, after.relations),",
        "        frozenset(),",
        k(T_PG, "test_an_owner_the_migration_role_belongs_to_is_safe_only_when_it_inherits")
        + "[TRUE]",
    ),
    Mutant(
        "WD1",
        "the refusal blames the file when an earlier run gave the right",
        MIG,
        "(2) If no file did, an earlier run or a database administrator did",
        "(2) If no file did, somebody did",
        k(T_PG, "test_a_right_that_an_earlier_run_gave_is_named_as_such_in_the_refusal"),
    ),
    Mutant(
        "GO4",
        "a function right that may be passed on is accepted",
        MIG,
        '            if grantable:\n                problems.append(\n                    f"{_label(who)} may pass {priv} on {shown} on to others',
        '            if False:\n                problems.append(\n                    f"{_label(who)} may pass {priv} on {shown} on to others',
        (
            k(T_PG, "test_a_named_role_may_not_pass_a_function_right_on"),
            k(T_PG, "test_a_named_role_that_may_pass_a_function_right_on_is_refused"),
        ),
    ),
    Mutant(
        "LW4",
        "the lock wait has no upper bound",
        MIG,
        "        or not 1 <= lock_wait_seconds <= MAX_LOCK_WAIT_SECONDS",
        "        or not 1 <= lock_wait_seconds",
        k(T_PG, "test_the_lock_wait_has_an_upper_bound_that_the_server_accepts"),
    ),
    Mutant(
        "LW5",
        "an activity field that the login cannot see is printed as None",
        MIG,
        '    return "not visible to this login" if value is None else str(value)',
        "    return str(value)",
        (
            k(T_PG, "test_a_null_column_of_the_activity_view_is_worded_for_a_reader"),
            k(T_PG, "test_a_lock_holder_that_this_login_cannot_look_into_is_named_in_plain_words"),
        ),
    ),
    Mutant(
        "LW6",
        "a saved statement limit is not switched off for the lock wait",
        MIG,
        "ms'; SET LOCAL statement_timeout = 0;",
        "ms';",
        k(T_PG, "test_a_statement_limit_saved_for_the_migration_role_does_not_end_the_lock_wait"),
    ),
    Mutant(
        "LW7",
        "the holder is found without comparing objsubid (a look-alike lock is named)",
        MIG,
        "\"JOIN pg_stat_activity a ON a.pid = l.pid WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 \"",
        "\"JOIN pg_stat_activity a ON a.pid = l.pid WHERE l.locktype = 'advisory' AND l.granted \"",
        k(
            T_PG,
            "test_the_holder_named_is_the_one_that_holds_the_real_lock_not_one_with_the_same_two_words",
        ),
    ),
    Mutant(
        "GT1",
        "a right on a schema, database or type is not refused by the text rule",
        MN,
        "        elif m := _GRANT_TARGET.match(s):\n",
        "        elif False:\n",
        k(
            T_RULES,
            "test_a_right_anywhere_but_on_a_table_view_sequence_column_or_function_is_refused",
        )
        + "[GRANT USAGE ON SCHEMA s TO r]",
    ),
    Mutant(
        "GT2",
        "ALTER DEFAULT PRIVILEGES and ALTER PUBLICATION are not refused by the text rule",
        MN,
        '    rf"|alter{_W}default{_W}privileges|alter{_W}publication)\\b",',
        '    rf")\\b",',
        k(
            T_RULES,
            "test_a_right_anywhere_but_on_a_table_view_sequence_column_or_function_is_refused",
        )
        + "[ALTER DEFAULT PRIVILEGES GRANT SELECT ON TABLES TO PUBLIC]",
    ),
    Mutant(
        "GT3",
        "`GRANT ... ON ALL ... IN SCHEMA` is not refused by the text rule",
        MN,
        "|tablespace|parameter|all|procedure){_NAME_END}",
        "|tablespace|parameter|procedure){_NAME_END}",
        k(
            T_RULES,
            "test_a_right_anywhere_but_on_a_table_view_sequence_column_or_function_is_refused",
        )
        + "[GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA s TO r]",
    ),
    Mutant(
        "CL1",
        "the command line drops --lock-wait-seconds",
        "src/hadavin_sdk/cli.py",
        "cfg, args.runtime_role, args.portal_role, args.purge_role, args.lock_wait_seconds",
        "cfg, args.runtime_role, args.portal_role, args.purge_role, None",
        k(T_K2, "test_cli_migrate_passes_the_portal_role"),
    ),
    Mutant(
        "SW18",
        "the read of pg_shdepend in the sweep report is not guarded",
        FX_,
        '                except psycopg.Error:\n                    where = "not known',
        '                except ZeroDivisionError:\n                    where = "not known',
        k(
            T_PG,
            "test_a_login_that_cannot_read_which_databases_hold_a_role_does_not_fail_the_sweep",
        ),
    ),
    Mutant(
        "SW19",
        "the marking connection gives up at the first miss",
        FX_,
        "    deadline = time.monotonic() + _MARK_WAIT_SECONDS\n",
        "    deadline = time.monotonic()\n",
        k(
            T_PG,
            "test_a_marking_connection_that_cannot_get_its_lock_ends_with_a_plain_error_not_a_hang",
        ),
    ),
    Mutant(
        "RA1",
        "the rights of a table are not part of its state (a right given later is not seen)",
        MIG,
        '(SELECT @ITEM@ AS x FROM aclexplode(c.relacl) a "',
        '(SELECT @ITEM@ AS x FROM aclexplode(NULL::aclitem[]) a "',
        k(T_PG, "test_a_right_given_on_a_table_that_existed_before_the_run_is_refused") + "[table]",
    ),
    Mutant(
        "RA1b",
        "what a right on a column says is not part of the state, only which columns have one",
        MIG,
        "(SELECT t.attnum::text || ' ' || @ITEM@ AS x \"",
        '(SELECT DISTINCT t.attnum::text AS x "',
        k(T_PG, "test_a_second_right_on_a_column_that_already_had_one_is_refused"),
    ),
    Mutant(
        "RA2",
        "only the relations of the schema of the run are read back (for the table rights)",
        MIG,
        'aclexplode(c.relacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "\n    "OR (c.oid = ANY(',
        'aclexplode(c.relacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "\n    "OR (false AND c.oid = ANY(',
        k(T_PG, "test_a_right_given_on_a_table_of_another_schema_is_refused"),
    ),
    Mutant(
        "RK1",
        "a foreign table is not read back (the kind 'f' is left out)",
        MIG,
        "\"@RELKINDS@\": \"('r','p','v','m','S','f')\",",
        "\"@RELKINDS@\": \"('r','p','v','m','S')\",",
        k(T_PG, "test_a_foreign_table_that_a_file_opens_to_everyone_is_refused"),
    ),
    Mutant(
        "OW5",
        "the owner of a function is not read",
        MIG,
        '"AND p.proowner <> @ME@ AND p.oid <> ALL(%(kept_fn)s::oid[]) AND "',
        '"AND false AND "',
        k(T_PG, "test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind")
        + "[function-function]",
    ),
    Mutant(
        "OW6",
        "the owner of a view or a sequence is not read",
        MIG,
        '"AND c.relowner <> @ME@ AND c.oid <> ALL(%(kept_rel)s::oid[]) AND "',
        "\"AND c.relowner <> @ME@ AND c.relkind IN ('r', 'p') AND c.oid <> ALL(%(kept_rel)s::oid[]) AND \"",
        (
            k(T_PG, "test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind")
            + "[sequence-sequence]",
            k(T_PG, "test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind")
            + "[view-view]",
        ),
    ),
    Mutant(
        "OW7",
        "a function that kept its owner is refused for that owner",
        MIG,
        "        _kept_owner_ids(before.functions, after.functions),",
        "        frozenset(),",
        (
            k(T_PG, "test_a_function_that_kept_a_foreign_owner_is_not_refused_for_that_owner"),
            k(T_CMP, "test_the_ids_that_kept_their_owner_are_one_set_per_catalog"),
        ),
    ),
    Mutant(
        "FB1",
        "the text body of a function is not part of its state",
        MIG,
        '"p.prosrc, pg_get_function_sqlbody',
        "\"''::text, pg_get_function_sqlbody",
        (
            k(T_PG, "test_a_function_whose_body_a_file_replaced_is_treated_as_changed"),
            k(
                T_PG,
                "test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function",
            )
            + "[text_body]",
        ),
    ),
    Mutant(
        "SC10",
        "a schema that a file changed is not read back unless it is the schema of the run",
        MIG,
        '"WHERE n.nspname = %(schema)s OR (n.oid = ANY(%(changed_schema)s::oid[]) "',
        '"WHERE n.nspname = %(schema)s OR (false AND n.oid = ANY(%(changed_schema)s::oid[]) "',
        k(T_PG, "test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is") + "[acl]",
    ),
    Mutant(
        "SC11",
        "the owner of a changed schema is not read",
        MIG,
        '"WHERE n.oid = ANY(%(changed_schema)s::oid[]) AND n.nspowner <> @ME@',
        '"WHERE false AND n.nspowner <> @ME@',
        k(T_PG, "test_a_schema_that_a_file_changed_is_read_back_whatever_schema_it_is") + "[owner]",
    ),
    Mutant(
        "GO5",
        "the grant option on a table or column right is ignored",
        MIG,
        '        elif grantable:\n            problems.append(\n                f"{_label(who)} may pass {priv} on {where} on to others (WITH GRANT OPTION)"',
        '        elif False:\n            problems.append(\n                f"{_label(who)} may pass {priv} on {where} on to others (WITH GRANT OPTION)"',
        (
            k(
                T_PG,
                "test_a_right_that_a_named_role_may_pass_on_is_refused_on_a_table_of_the_grant_map",
            )
            + "[table]",
            k(
                T_PG,
                "test_a_right_that_a_named_role_may_pass_on_is_refused_on_a_table_of_the_grant_map",
            )
            + "[column]",
        ),
    ),
    Mutant(
        "GO6",
        "the grant option on a schema right is ignored",
        MIG,
        '        if grantable:\n            problems.append(\n                f"{_label(who)} may pass {priv} on the schema',
        '        if False:\n            problems.append(\n                f"{_label(who)} may pass {priv} on the schema',
        k(T_PG, "test_a_named_role_that_may_pass_the_schema_right_on_is_refused"),
    ),
    Mutant(
        "RO1",
        "a named role may have any right on a relation that is not in the grant map",
        MIG,
        "        elif not is_managed:\n            problems.append(",
        "        elif False:\n            problems.append(",
        (
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map") + "[insert]",
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
            + "[sequence_update]",
            k(T_CMP, "test_the_relation_loop_refuses_each_kind_of_right_with_its_own_words"),
        ),
    ),
    Mutant(
        "DP2",
        "default rights are read only for the schema of the run and for all schemas",
        MIG,
        "\"WHERE (d.defaclrole = @ME@ OR pg_has_role(current_user, d.defaclrole, 'MEMBER')) \"",
        "\"WHERE (d.defaclrole = @ME@ OR pg_has_role(current_user, d.defaclrole, 'MEMBER')) AND (n.nspname IS NULL OR n.nspname = current_schema()) \"",
        k(
            T_PG,
            "test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to",
        )
        + "[other_schema]",
    ),
    Mutant(
        "DP3",
        "default rights are read only for the migration role itself, not for the roles it belongs to",
        MIG,
        "\"WHERE (d.defaclrole = @ME@ OR pg_has_role(current_user, d.defaclrole, 'MEMBER')) \"",
        '"WHERE (d.defaclrole = @ME@) "',
        k(
            T_PG,
            "test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to",
        )
        + "[member_role]",
    ),
    Mutant(
        "DP4",
        "a named role may have a default right",
        MIG,
        '        if where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:',
        '        if who in allowed or (where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT):',
        (
            k(
                T_PG,
                "test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to",
            )
            + "[named_delete]",
            k(
                T_PG,
                "test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to",
            )
            + "[named_select]",
            k(
                T_PG,
                "test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types",
            )
            + "[named_sequences_in_a_schema]",
        ),
    ),
    Mutant(
        "DP5",
        "the default rights of the role they are set for are read as rights of a stranger",
        MIG,
        '"AND a.grantee <> d.defaclrole AND a.grantee <> @ME@ ORDER BY 1, 2, 3, 4, 5"',
        '"AND a.grantee <> @ME@ ORDER BY 1, 2, 3, 4, 5"',
        k(
            T_PG,
            "test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers",
        )
        + "[only_the_groups_own_row]",
    ),
    Mutant(
        "SW20",
        "the read of pg_shdepend in the sweep is not in a savepoint",
        FX_,
        "                    with db.transaction():\n                        where =",
        "                    if True:\n                        where =",
        k(T_PG, "test_a_refused_read_in_the_sweep_does_not_abort_the_transaction_of_the_caller"),
    ),
    Mutant(
        "LV1",
        "a lock wait of 0 seconds is accepted",
        MIG,
        "        or not 1 <= lock_wait_seconds <= MAX_LOCK_WAIT_SECONDS",
        "        or not 0 <= lock_wait_seconds <= MAX_LOCK_WAIT_SECONDS",
        k(
            T_K2,
            "test_a_lock_wait_that_is_not_a_whole_number_of_seconds_from_1_up_is_refused_before_anything_is_done",
        )
        + "[0]",
    ),
    Mutant(
        "LV2",
        "a bool is accepted as a number of seconds",
        MIG,
        "        isinstance(lock_wait_seconds, bool)\n        or not isinstance(lock_wait_seconds, int)",
        "        False\n        or not isinstance(lock_wait_seconds, int)",
        k(
            T_K2,
            "test_a_lock_wait_that_is_not_a_whole_number_of_seconds_from_1_up_is_refused_before_anything_is_done",
        )
        + "[True]",
    ),
    Mutant(
        "LV3",
        "a string or a fraction is accepted as a number of seconds",
        MIG,
        "        or not isinstance(lock_wait_seconds, int)\n        or not 1",
        "        or not 1",
        k(
            T_K2,
            "test_a_lock_wait_that_is_not_a_whole_number_of_seconds_from_1_up_is_refused_before_anything_is_done",
        )
        + "[1.5]",
    ),
    Mutant(
        "LV4",
        "one above the largest wait is accepted",
        MIG,
        "<= MAX_LOCK_WAIT_SECONDS\n    ):",
        "<= MAX_LOCK_WAIT_SECONDS + 1\n    ):",
        k(
            T_K2,
            "test_a_lock_wait_that_is_not_a_whole_number_of_seconds_from_1_up_is_refused_before_anything_is_done",
        )
        + "[2147484]",
    ),
    Mutant(
        "CL2",
        "the command line always passes a wait (None when none was given)",
        "src/hadavin_sdk/cli.py",
        'wait = {} if lock_wait_seconds is None else {"lock_wait_seconds": lock_wait_seconds}',
        'wait = {"lock_wait_seconds": lock_wait_seconds}',
        k(T_K2, "test_cli_migrate_passes_the_portal_role"),
    ),
    Mutant(
        "OT1",
        "the text rule for ALTER ... OWNER TO is off",
        MN,
        "        elif _hands_over(s):",
        "        elif False:",
        (
            k(T_RULES, "test_handing_an_object_to_another_role_is_refused_by_the_text_rule")
            + "[ALTER TABLE t OWNER TO r]",
            k(T_RULES, "test_the_owner_refusal_holds_under_noise") + "[-]",
        ),
    ),
    Mutant(
        "OT2",
        "every ALTER statement that has the word owner is taken for an owner change",
        MN,
        '_OWNER_TO = re.compile(rf"{_NAME_START}owner{_W}to{_NAME_END}", re.IGNORECASE)',
        '_OWNER_TO = re.compile(r"owner", re.IGNORECASE)',
        k(T_RULES, "test_a_column_or_a_text_that_says_owner_is_not_taken_for_an_owner_change")
        + "[ALTER TABLE t ADD COLUMN owner_id int]",
    ),
    Mutant(
        "RF1",
        "the flag rolreplication is not one of the flags that are refused",
        MIG,
        '_ROLE_FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls", "rolreplication")',
        '_ROLE_FLAGS = ("rolsuper", "rolcreaterole", "rolcreatedb", "rolbypassrls")',
        (
            k(T_WIRING, "test_a_privileged_migration_role_is_refused_before_any_file_runs")
            + "[rolreplication]",
            k(T_WIRING, "test_the_replication_flag_is_read_again_after_every_file"),
        ),
    ),
    Mutant(
        "RF2",
        "the flag rolreplication is not read from the server",
        MIG,
        '"SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication FROM pg_roles "\n    "WHERE rolname IN',
        '"SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, false FROM pg_roles "\n    "WHERE rolname IN',
        (
            k(T_PG, "test_a_migration_role_with_a_privilege_flag_is_refused_by_a_real_server")
            + "[REPLICATION]",
            k(T_WIRING, "test_the_role_flags_are_read_for_the_current_user_and_the_session_user"),
        ),
    ),
    Mutant(
        "RF3",
        "a member of a role with the replication flag is not refused",
        MIG,
        'OR r.rolbypassrls OR r.rolreplication "',
        'OR r.rolbypassrls "',
        (
            k(
                T_PG,
                "test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server",
            )
            + "[TRUE-REPLICATION]",
            k(
                T_PG,
                "test_a_plain_role_that_is_a_member_of_a_privileged_role_is_refused_by_a_real_server",
            )
            + "[FALSE-REPLICATION]",
        ),
    ),
    Mutant(
        "RF5",
        "the replication flag of a named role is not read",
        MIG,
        '"SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, rolreplication FROM pg_roles WHERE rolname = %s",',
        '"SELECT rolsuper, rolcreaterole, rolcreatedb, rolbypassrls, false FROM pg_roles WHERE rolname = %s",',
        k(T_PG, "test_a_named_role_with_the_replication_flag_is_refused"),
    ),
    Mutant(
        "GD3",
        "a `**dict(password=...)` is not read as a password",
        T_RULES,
        '    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict":',
        "    if False:",
        k(T_RULES, "test_the_password_scan_reads_the_star_star_forms"),
    ),
    Mutant(
        "GD4",
        '`**{"password": None}` counts as a password',
        T_RULES,
        "not _is_none(v) for v in _password_keys_in(k.value)",
        "True for v in _password_keys_in(k.value)",
        k(T_RULES, "test_the_password_scan_reads_the_star_star_forms"),
    ),
    # --- round 12 ---
    Mutant(
        "PDO2",
        "the pseudo-role pg_database_owner is accepted on a schema it does not own",
        MIG,
        '        if is_owner:\n            continue\n        if grantable:\n            problems.append(\n                f"{_label(who)} may pass {priv} on the schema',
        '        if is_owner or who == "pg_database_owner":\n            continue\n        if grantable:\n            problems.append(\n                f"{_label(who)} may pass {priv} on the schema',
        (
            k(T_PG, "test_the_database_owner_pseudo_role_is_refused_on_a_schema_it_does_not_own"),
            k(
                T_CMP,
                "test_the_schema_loop_lets_any_role_look_a_name_up_and_refuses_everything_else",
            ),
        ),
    ),
    Mutant(
        "RO3",
        "a named role may SELECT a relation that is not in the grant map (the rule of round 11)",
        MIG,
        "        elif not is_managed:",
        '        elif not is_managed and priv != "SELECT":',
        (
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map") + "[select]",
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
            + "[view_select]",
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
            + "[column_select]",
        ),
    ),
    Mutant(
        "RO5",
        "a named role may use a sequence that is not in the grant map (the rule of round 11)",
        MIG,
        "        elif not is_managed:",
        '        elif not is_managed and not (relkind == "S" and priv == "USAGE"):',
        k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
        + "[sequence_usage]",
    ),
    Mutant(
        "RO4",
        "a named role may have a right on a function",
        MIG,
        '            else:\n                problems.append(f"{_label(who)} has {priv} on {shown} ({_NO_RIGHT_OUTSIDE})")',
        "            else:\n                pass",
        (
            k(T_PG, "test_a_named_role_gets_no_right_on_a_function"),
            k(
                T_CMP,
                "test_the_function_loop_refuses_rights_and_security_definer_and_removes_the_default_for_everyone",
            ),
        ),
    ),
    Mutant(
        "DP6",
        "a default right for the migration role itself is read as a right of a stranger",
        MIG,
        '"AND a.grantee <> d.defaclrole AND a.grantee <> @ME@ ORDER BY 1, 2, 3, 4, 5"',
        '"AND a.grantee <> d.defaclrole ORDER BY 1, 2, 3, 4, 5"',
        (
            k(
                T_PG,
                "test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers",
            )
            + "[tables_in_the_run_schema]",
            k(
                T_PG,
                "test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers",
            )
            + "[sequences_everywhere]",
        ),
    ),
    Mutant(
        "DP7",
        "the server's own default for functions and types is refused",
        MIG,
        '        if where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:',
        "        if False:",
        (
            k(
                T_PG,
                "test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers",
            )
            + "[functions_everywhere]",
            k(
                T_PG,
                "test_a_default_right_for_the_migration_role_itself_and_the_servers_own_default_are_not_a_strangers",
            )
            + "[types_everywhere]",
        ),
    ),
    Mutant(
        "DP8",
        "a right for everyone on new functions is also skipped when it was set for one schema",
        MIG,
        '        if where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:',
        '        if who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:',
        (
            k(
                T_PG,
                "test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types",
            )
            + "[everyone_functions_in_a_schema]",
            k(
                T_CMP,
                "test_the_default_right_loop_skips_only_the_servers_own_default_for_every_schema",
            ),
        ),
    ),
    Mutant(
        "DP9",
        "every default right for everyone that is set for all schemas is skipped",
        MIG,
        '        if where is None and who == "PUBLIC" and (kind, priv) in _BUILT_IN_DEFAULT:',
        '        if where is None and who == "PUBLIC":',
        (
            k(
                T_PG,
                "test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types",
            )
            + "[everyone_sequences_everywhere]",
            k(
                T_CMP,
                "test_the_default_right_loop_skips_only_the_servers_own_default_for_every_schema",
            ),
        ),
    ),
    Mutant(
        "OT3",
        "any word rename before owner lets an owner change pass (the rule of 8382bdd)",
        MN,
        "    exempt = _RENAME_OWNER.match(statement)",
        '    exempt = re.match(r"(?is).*?rename.*?owner[ \\t\\n]+to", statement)',
        (
            k(T_RULES, "test_handing_an_object_to_another_role_is_refused_by_the_text_rule")
            + "[ALTER TYPE rename OWNER TO r]",
            k(T_RULES, "test_handing_an_object_to_another_role_is_refused_by_the_text_rule")
            + "[ALTER TABLE t ADD COLUMN rename int, OWNER TO r]",
            k(T_RULES, "test_handing_an_object_to_another_role_is_refused_by_the_text_rule")
            + "[ALTER TABLE a$rename OWNER TO r]",
        ),
    ),
    Mutant(
        "OT4",
        "the rename of a column called owner is taken for an owner change",
        MN,
        "    exempt = _RENAME_OWNER.match(statement)",
        "    exempt = None",
        k(T_RULES, "test_a_column_or_a_text_that_says_owner_is_not_taken_for_an_owner_change")
        + "[ALTER TABLE t RENAME COLUMN owner TO owner_name]",
    ),
    Mutant(
        "SO1",
        "every function of the database is in scope (another session's function is compared)",
        MIG,
        '"SELECT p.oid, (p.proowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(p.proacl) a WHERE a.grantor IN @MINE@)), "',
        '"SELECT p.oid, true, "',
        k(T_PG, "test_what_another_session_commits_during_the_run_does_not_stop_the_run"),
    ),
    Mutant(
        "SO2",
        "every relation of the database is in scope (another session's table is compared)",
        MIG,
        '"SELECT c.oid, (c.relowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(c.relacl) a WHERE a.grantor IN @MINE@) "',
        '"SELECT c.oid, (true OR EXISTS (SELECT 1 FROM aclexplode(c.relacl) a WHERE a.grantor IN @MINE@) "',
        k(T_PG, "test_what_another_session_commits_during_the_run_does_not_stop_the_run"),
    ),
    Mutant(
        "SO3",
        "every schema of the database is in scope (another session's schema is compared)",
        MIG,
        '"SELECT n.oid, (n.nspowner IN @MINE@ OR EXISTS (SELECT 1 FROM aclexplode(n.nspacl) a WHERE a.grantor IN @MINE@)), "',
        '"SELECT n.oid, true, "',
        k(T_PG, "test_what_another_session_commits_during_the_run_does_not_stop_the_run"),
    ),
    Mutant(
        "CS1",
        "only a new owner makes an object changed",
        MIG,
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st",
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and (i not in before or before[i][_OWNER] != st[_OWNER])",
        (
            k(T_CMP, "test_a_difference_in_any_one_field_of_an_object_in_scope_makes_it_changed")
            + "[functions-4]",
            k(T_CMP, "test_a_difference_in_any_one_field_of_an_object_in_scope_makes_it_changed")
            + "[relations-2]",
            k(T_CMP, "test_a_difference_in_any_one_field_of_an_object_in_scope_makes_it_changed")
            + "[schemas-2]",
        ),
    ),
    Mutant(
        "CS2",
        "the scope is not asked: every difference in the database is a change",
        MIG,
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st",
        "        if before.get(i) != st",
        (
            k(T_CMP, "test_an_object_that_is_out_of_scope_before_and_after_is_never_changed")
            + "[relations]",
            k(T_PG, "test_what_another_session_commits_during_the_run_does_not_stop_the_run"),
        ),
    ),
    Mutant(
        "CS4",
        "only the scope after the files counts",
        MIG,
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st",
        "        if st[_IN_SCOPE] and before.get(i) != st",
        k(T_CMP, "test_an_object_in_scope_only_before_or_only_after_is_compared") + "[relations]",
    ),
    Mutant(
        "CS5",
        "only the scope before the files counts",
        MIG,
        "        if (st[_IN_SCOPE] or (i in before and before[i][_IN_SCOPE])) and before.get(i) != st",
        "        if (i in before and before[i][_IN_SCOPE]) and before.get(i) != st",
        (
            k(T_CMP, "test_an_object_in_scope_only_before_or_only_after_is_compared")
            + "[functions]",
            k(T_PG, "test_a_table_made_by_dynamic_sql_and_opened_to_everyone_is_refused"),
        ),
    ),
    Mutant(
        "KC1",
        "the relations take the kept ids of the functions (one mixed set)",
        MIG,
        "        _kept_owner_ids(before.relations, after.relations),",
        "        _kept_owner_ids(before.functions, after.functions),",
        k(T_CMP, "test_the_ids_that_kept_their_owner_are_one_set_per_catalog"),
    ),
    Mutant(
        "KC2",
        "the schemas take the kept ids of the functions (one mixed set)",
        MIG,
        "        _kept_owner_ids(before.schemas, after.schemas),",
        "        _kept_owner_ids(before.functions, after.functions),",
        k(T_CMP, "test_the_ids_that_kept_their_owner_are_one_set_per_catalog"),
    ),
    Mutant(
        "KC3",
        "the relation queries get the kept ids of the functions",
        MIG,
        '        "kept_rel": sorted(changed.kept_relations),',
        '        "kept_rel": sorted(changed.kept_functions),',
        k(
            T_CMP,
            "test_nothing_found_means_no_refusal_and_the_queries_get_one_set_of_ids_per_catalog",
        ),
    ),
    Mutant(
        "OW8",
        "a schema that kept the owner it had before the files is refused for that owner",
        MIG,
        "        _kept_owner_ids(before.schemas, after.schemas),",
        "        frozenset(),",
        k(
            T_PG,
            "test_a_schema_that_a_file_changed_and_that_kept_its_owner_is_not_taken_for_handed_over",
        ),
    ),
    Mutant(
        "OW9",
        "every relation is called a table in the owner message",
        MIG,
        "            thing = f\"the {_OWNER_WORD.get(kind, 'relation').lower()} {_label(obj_schema, name)}\"",
        '            thing = f"the table {_label(obj_schema, name)}"',
        (
            k(T_CMP, "test_the_owner_loop_says_what_the_object_is_and_names_it_with_its_schema"),
            k(T_PG, "test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind")
            + "[view-view]",
        ),
    ),
    Mutant(
        "MC1",
        "the function half of the ownership check gets the relation names",
        MIG,
        "db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, managed_fn))",
        "db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, managed_rel + managed_fn))",
        (
            k(
                T_CMP,
                "test_the_ownership_check_before_the_files_gets_the_relation_names_and_the_function_names_apart",
            ),
            k(
                T_PG,
                "test_a_function_that_is_called_like_a_table_of_the_grant_map_is_not_this_packages",
            )
            + "[another_role]",
        ),
    ),
    Mutant(
        "MC2",
        "the rights check takes a relation name for a function name",
        MIG,
        "    managed_rel, managed_fn = _managed_names(texts, schema)\n    allowed = set(named)",
        "    managed_rel, managed_fn = _managed_names(texts, schema)\n    managed_fn = managed_rel + managed_fn\n    allowed = set(named)",
        (
            k(
                T_CMP,
                "test_nothing_found_means_no_refusal_and_the_queries_get_one_set_of_ids_per_catalog",
            ),
            k(
                T_PG,
                "test_a_function_that_is_called_like_a_table_of_the_grant_map_is_not_this_packages",
            )
            + "[the_migration_role]",
        ),
    ),
    Mutant(
        "OA6",
        "the relation half of the ownership check gets no names",
        MIG,
        "db.execute(_FOREIGN_OWNED_SQL, (schema, managed_rel, schema, managed_fn))",
        "db.execute(_FOREIGN_OWNED_SQL, (schema, [], schema, managed_fn))",
        k(T_WIRING, "test_the_ownership_query_gets_the_managed_names"),
    ),
    Mutant(
        "SD6",
        "a SECURITY DEFINER function of the migration role that no file touched is not looked at (the rule of round 11)",
        MIG,
        '"OR (n.nspname = %(schema)s AND p.prosecdef AND p.proowner IN @MINE@)) AND "',
        '"OR false) AND "',
        (
            k(
                T_PG,
                "test_a_security_definer_function_of_the_migration_role_that_no_file_made_is_refused",
            )
            + "[the_migration_role]",
            k(
                T_PG,
                "test_a_security_definer_function_of_the_migration_role_that_no_file_made_is_refused",
            )
            + "[a_role_it_belongs_to]",
        ),
    ),
    Mutant(
        "SD7",
        "every untouched SECURITY DEFINER function of the run schema is refused, whoever owns it",
        MIG,
        '"OR (n.nspname = %(schema)s AND p.prosecdef AND p.proowner IN @MINE@)) AND "',
        '"OR (n.nspname = %(schema)s AND p.prosecdef)) AND "',
        k(
            T_PG,
            "test_a_security_definer_function_that_is_not_the_migration_roles_or_not_in_the_run_schema_is_left_alone",
        )
        + "[another_owner]",
    ),
    Mutant(
        "SD8",
        "the untouched SECURITY DEFINER functions of every schema are refused",
        MIG,
        '"OR (n.nspname = %(schema)s AND p.prosecdef AND p.proowner IN @MINE@)) AND "',
        '"OR (p.prosecdef AND p.proowner IN @MINE@)) AND "',
        k(
            T_PG,
            "test_a_security_definer_function_that_is_not_the_migration_roles_or_not_in_the_run_schema_is_left_alone",
        )
        + "[another_schema]",
    ),
    Mutant(
        "SD9",
        "the rights of a function that is listed only for its SECURITY DEFINER flag are read",
        MIG,
        "        if not judged:\n            continue",
        "        if False:\n            continue",
        k(
            T_CMP,
            "test_the_function_loop_refuses_rights_and_security_definer_and_removes_the_default_for_everyone",
        ),
    ),
    Mutant(
        "FB2",
        "the SQL-standard body of a function (RETURN ...) is not part of its state",
        MIG,
        "pg_get_function_sqlbody(p.oid), p.probin",
        "NULL::text, p.probin",
        k(T_PG, "test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function")
        + "[sql_standard_body]",
    ),
    Mutant(
        "FB3",
        "the saved settings of a function are not part of its state",
        MIG,
        'p.prolang::bigint, p.proconfig::text "',
        'p.prolang::bigint, NULL::text "',
        k(T_PG, "test_every_part_of_a_function_that_a_file_can_change_makes_it_a_changed_function")
        + "[saved_settings]",
    ),
    Mutant(
        "RA4",
        "only the relations of the schema of the run are read back (for the column rights)",
        MIG,
        'aclexplode(t.attacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "\n    "OR (c.oid = ANY(',
        'aclexplode(t.attacl) a WHERE ((n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)) "\n    "OR (false AND c.oid = ANY(',
        (
            k(T_PG, "test_a_right_given_on_a_table_that_existed_before_the_run_is_refused")
            + "[column]",
            k(T_PG, "test_a_second_right_on_a_column_that_already_had_one_is_refused"),
        ),
    ),
    Mutant(
        "IM1",
        "no relation counts as one of the grant map in the rights check (is_managed is always false)",
        MIG,
        '"a.is_grantable, (n.nspname = %(schema)s AND c.relname = ANY(%(managed_rel)s)), c.relkind::text "\n    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "\n    "CROSS JOIN LATERAL',
        '"a.is_grantable, false, c.relkind::text "\n    "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "\n    "CROSS JOIN LATERAL',
        k(
            T_PG,
            "test_the_named_roles_and_the_owner_may_hold_rights_and_a_function_loses_the_default_for_everyone",
        ),
    ),
    Mutant(
        "RK2",
        "a foreign table is not read by the check of what a named role can do",
        MIG,
        "c.relkind IN ('r','p','v','m','S','f')\",",
        "c.relkind IN ('r','p','v','m','S')\",",
        k(T_PG, "test_a_named_role_that_can_read_a_foreign_table_in_the_run_schema_is_refused"),
    ),
    Mutant(
        "SC12",
        "the migration role's own right on a schema it does not own is read as a right of a stranger",
        MIG,
        '"a.is_grantable, a.grantee = n.nspowner OR a.grantee = @ME@ FROM pg_namespace n "',
        '"a.is_grantable, a.grantee = n.nspowner FROM pg_namespace n "',
        k(
            T_PG,
            "test_a_role_made_with_the_printed_sql_only_can_pass_usage_on_to_the_runtime_and_portal_roles",
        ),
    ),
    Mutant(
        "SC13",
        "the owner's right on a schema is read as a right of a stranger",
        MIG,
        '"a.is_grantable, a.grantee = n.nspowner OR a.grantee = @ME@ FROM pg_namespace n "',
        '"a.is_grantable, a.grantee = @ME@ FROM pg_namespace n "',
        k(T_PG, "test_the_printed_role_runs_in_a_schema_that_the_database_owner_role_owns"),
    ),
    Mutant(
        "SC14",
        "a named role may create in a schema",
        MIG,
        '        elif priv != "USAGE":  # USAGE only lets a role look a name up',
        '        elif priv != "USAGE" and who not in allowed:  # USAGE only lets a role look a name up',
        k(T_CMP, "test_the_schema_loop_lets_any_role_look_a_name_up_and_refuses_everything_else"),
    ),
    Mutant(
        "SH1",
        "a long list is cut without saying how many items were left out",
        MIG,
        '    return joiner.join(items[:limit]) + (f"{joiner}and {more} more" if more > 0 else "")',
        "    return joiner.join(items[:limit])",
        k(T_CMP, "test_a_long_list_is_cut_with_a_count_of_what_was_left_out"),
    ),
    Mutant(
        "LW8",
        "a lock that no session holds (a prepared transaction) is not looked for",
        MIG,
        "        if row is None and (db.execute(_LOCK_PREPARED_SQL, (MIGRATE_LOCK,)).fetchone() or (0,))[0]:",
        "        if False:",
        (
            k(T_CMP, "test_a_lock_held_by_a_prepared_transaction_is_said_so_with_what_finishes_it"),
            k(T_PG, "test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one"),
        ),
    ),
]
M.extend(STEP_MUTANTS)


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


def kind_of(m: Mutant) -> str:
    """behaviour (a line of the package), prose (the CHANGELOG runbook) or test-helper (a line of the tests)."""
    return "behaviour" if m.file.startswith("src/") else "prose" if m.file == CL else "test-helper"


def killers_of(m: Mutant) -> list[str]:
    return [m.killer] if isinstance(m.killer, str) else list(m.killer)


# An allow list, not a list of known crashes: a failure counts as a kill only when the FIRST `E` line of its block in the
# pytest output (the exception that ended the test) is one a test raises on purpose: a failed `assert`, an
# `AssertionError` (which also covers "Regex pattern did not match"), `Failed:` (also "DID NOT RAISE") or a `ConfigError`
# (the refusal that a test did not expect). Anything else (a NameError, a KeyError, a server error such as
# `psycopg.errors.UndefinedTable`, an error that is not named yet) is a mutant that only broke the code.
_BLOCK = re.compile(r"^_+ \S.* _+$", re.MULTILINE)  # pytest pads the title with one or more "_"
_FIRST_E = re.compile(r"^E\s+(.*)$", re.MULTILINE)
# A test that cannot start (no CREATEDB right, a slow machine, a timeout of its own wait) says so with this phrase, and
# that is never a kill: the same failure happens with no mutant planted.
SETUP_PROBLEM = "TEST SETUP PROBLEM"
_KILL_HEAD = re.compile(
    r"^(?!.*TEST SETUP PROBLEM)(?:assert\b|AssertionError\b|Failed:|(?:[A-Za-z_][\w]*\.)*ConfigError\b)",
)


def failure_heads(out: str) -> list[str]:
    """The first `E` line of each failure block of the pytest output (the head of the exception)."""
    blocks = _BLOCK.split(out)[1:]
    heads = []
    for block in blocks:
        first = _FIRST_E.search(block)
        heads.append(first.group(1) if first else "")
    return heads


def only_test_failures(out: str) -> bool:
    """True when there is at least one failure block and every block ends in an exception a test raises on purpose."""
    heads = failure_heads(out)
    return bool(heads) and all(_KILL_HEAD.match(h) for h in heads)


def unknown_ids(only: str) -> list[str]:
    """The ids in the comma list that no mutant has (an empty list: all are known)."""
    known = {m.name for m in M}
    return [n for n in only.split(",") if n and n not in known]


def status_of(m: Mutant, runs: list[tuple[object, str]]) -> str:
    """`runs` = (exit code, pytest output) of each killer of `m`, each run on its own with the mutant planted.
    KILLED: some killer failed with exit code 1, a test of that very killer is in its FAILED lines, and every failure
    ended in an exception a test raises on purpose (`only_test_failures`: an allow list; a mutant that only broke the
    code proves nothing). BROKEN: it
    failed but only like that. SURVIVED: every killer passed. ERROR: any other exit code."""
    codes = [rc for rc, _ in runs]
    if all(rc == 0 for rc in codes):
        return "SURVIVED"
    if not all(rc in (0, 1) for rc in codes):
        return f"ERROR(rc={codes})"
    for killer, (rc, out) in zip(killers_of(m), runs, strict=True):
        named = killer.split("[")[0]
        failed = [f.split("[")[0] for f in re.findall(r"^FAILED (\S+)", out, re.MULTILINE)]
        if rc == 1 and named in failed and only_test_failures(out):
            return "KILLED"
    return "BROKEN"


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
    if unknown := unknown_ids(only):
        print(f"STOP: no mutant has the id {', '.join(unknown)} (several: comma-separated)")
        return 2
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
    base = ["-p", "no:cacheprovider", "-q", "--no-header", "--tb=short"]
    if unknown := unknown_ids(only):
        print(f"STOP: no mutant has the id {', '.join(unknown)} (several: comma-separated)")
        return 2
    wanted = {n for n in only.split(",") if n}
    selected = [m for m in M if not wanted or m.name in wanted]
    if not selected:
        print(f"STOP: no mutant has the id {only!r} (several: comma-separated)")
        return 2
    killers = sorted({kid for m in selected for kid in killers_of(m)})
    rc, out, dt = run([py, "-m", "pytest", *base, "-x", *killers], copy, env, timeout)
    print(f"BASELINE rc={rc} {summary_line(out)} ({dt:.1f}s, {len(killers)} killer ids)")
    if rc != 0:
        print(out[-3000:])
        print("STOP: baseline not green")
        return 2
    raw_dir = os.environ.get("MIGRATE_MUTANTS_RAW_DIR")
    if raw_dir:
        Path(raw_dir).mkdir(parents=True, exist_ok=True)
    print(
        "name | kind | description | result | failing killers (only the ones that fail) | seconds"
    )
    results = []
    for m in selected:
        path = copy / m.file
        original = path.read_bytes()
        failing, runs, spent = [], [], 0.0
        try:
            path.write_bytes(original.decode("utf-8").replace(m.old, m.new, 1).encode("utf-8"))
            for killer in killers_of(
                m
            ):  # each killer on its own, without -x, so a silent one shows
                rc, out, dt = run([py, "-m", "pytest", *base, "-rf", killer], copy, env, timeout)
                spent += dt
                runs.append((rc, out))
                failing += re.findall(r"^FAILED (\S+)", out, re.MULTILINE)
        finally:
            path.write_bytes(original)
        status = status_of(m, runs)
        results.append((m, status))
        if (
            raw_dir
        ):  # the whole pytest output of each killer, to read afterwards (what each kill really was)
            Path(raw_dir, f"{m.name}.txt").write_text(
                "".join(
                    f"### {k} rc={rc}\n{out}\n"
                    for k, (rc, out) in zip(killers_of(m), runs, strict=True)
                ),
                encoding="utf-8",
            )
        print(
            f"{m.name} | {kind_of(m)} | {m.desc} | {status} | {', '.join(failing) or '-'} | {spent:.1f}s",
            flush=True,
        )
    for kind in ("behaviour", "prose", "test-helper"):
        part = [(m, s) for m, s in results if kind_of(m) == kind]
        print(f"{kind}: {sum(1 for _, s in part if s == 'KILLED')} of {len(part)} killed")
    killed = sum(1 for _, s in results if s == "KILLED")
    bad = [f"{m.name}:{s}" for m, s in results if s != "KILLED"]
    print(f"not killed: {bad}")
    print(f"{killed} of {len(results)} killed")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
