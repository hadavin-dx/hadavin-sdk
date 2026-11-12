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
login may create schemas and roles; the whole list takes 30 minutes or more, so the final head runs it in four batches):

    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py            # all; exit 1 if any is not killed
    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py M88,R4      # only these ids (comma-separated)
    uv run python tests/migrate_mutants.py --list-batch 1                                   # the ids of batch 1 to 4 (comma-separated, needs no server)
    HADAVIN_TEST_PG_DSN=postgresql://... uv run python tests/migrate_mutants.py $(uv run python tests/migrate_mutants.py --list-batch 1)

Each killer id runs on its own (no -x) so a killer that does not fail shows; only the failing ones are printed. The last line is `N of N killed`; the lines before it count the three kinds. A cheap check that runs with the ordinary tests,
`test_every_migrate_mutant_still_applies_to_the_source` (tests/test_migration_rules.py), fails when a mutant's `old`
text is no longer in its file exactly once, so the list cannot rot between two runs.
"""

from __future__ import annotations

import ast
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
T_MX = "tests/test_migration_matrix.py"
T_VERIFY = "tests/test_migration_verify.py"
T_STEPS = "tests/test_migration_steps.py"
T_VERIFY_PG = "tests/test_migration_verify_pg.py"
VERIFY = "src/hadavin_sdk/store/migration_verify.py"
AUTH = "src/hadavin_sdk/store/auth_aws.py"
PGS = "src/hadavin_sdk/store/postgres.py"
T_SIGN = "tests/test_sign_in_channels.py"
T_CHAN = "tests/test_driver_error_channels.py"


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
    "                        running_a_file = True\n"
    "                        db.execute(texts[path])  # the text that was scanned, never a second read\n"
    "                        running_a_file = False\n"
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
    "                    if problems:\n"
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
        STEP6_CALL.replace("if problems:", "if problems and False:", 1),
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
        "            and p.schema == schema\n",
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
        (PINNED, S_("test_step_4_asks_for_the_functions_of_this_run_and_this_schema")),
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
        "                        saved = saved\n",
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
        "                        running_a_file = True\n"
        "                        db.execute(texts[path])  # the text that was scanned, never a second read\n"
        "                        running_a_file = False\n"
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
        "memberships, saved settings and triggers it saved before",
        "memberships, three session settings and triggers it saved before",
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
        k(
            T_PG,
            "test_the_owner_check_leaves_a_managed_function_of_an_extension_to_the_state_check",
        ),
    ),
    Mutant(
        "EX2",
        "tables and views of an installed extension are listed",
        MIG,
        '"AND d.deptype = \'e\') "\n    "AND (c.relkind',
        '"AND false) "\n    "AND (c.relkind',
        k(T_PG, "test_the_owner_check_leaves_a_managed_table_of_an_extension_to_the_state_check"),
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
        "        for m in _FUNCTION_CREATE.finditer(text):\n            where = _name_of(m.group(1), m.group(2))\n            # no schema written",
        "        for m in ():\n            where = _name_of(m.group(1), m.group(2))\n            # no schema written",
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
        'unchanged = "Nothing was changed. No file ran."',
        'unchanged = ""',
        k(
            T_PG,
            "test_tables_owned_by_another_role_are_refused_with_the_sql_that_hands_them_over",
        ),
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
        "the rights on tables, views and sequences are not judged",
        VERIFY,
        "        in_run = (not it.system) and it.schema == schema\n",
        '        in_run = (not it.system) and it.schema == schema\n        if it.kind in ("table", "view", "sequence"):\n            continue\n',
        k(T_PG, R),
    ),
    Mutant(
        "AC2",
        "the rights on single columns are not judged",
        VERIFY,
        "        in_run = (not it.system) and it.schema == schema\n",
        '        in_run = (not it.system) and it.schema == schema\n        if it.kind == "column":\n            continue\n',
        k(T_PG, R),
    ),
    Mutant(
        "AC3",
        "the rights on functions are not judged",
        VERIFY,
        "        in_run = (not it.system) and it.schema == schema\n",
        "        in_run = (not it.system) and it.schema == schema\n        if it.kind in _FUNCTION_KINDS:\n            continue\n",
        k(T_PG, R),
    ),
    Mutant(
        "AC4",
        "a right held by everyone (PUBLIC) is not judged",
        VERIFY,
        "        if it.grantee is None:\n            kind, right = it.kind, it.privilege_type\n",
        "        if it.grantee is None:\n            continue\n            kind, right = it.kind, it.privilege_type\n",
        k(T_PG, R),
    ),
    Mutant(
        "AC5",
        "the default 'everyone may call it' of a function is not removed at step 4",
        MIG,
        "    for _shown_name, where, name, args, _kind in rows:\n",
        "    for _shown_name, where, name, args, _kind in []:\n",
        k(
            T_PG,
            "test_the_named_roles_and_the_owner_may_hold_rights_and_a_function_loses_the_default_for_everyone",
        ),
    ),
    Mutant(
        "SD1",
        "a SECURITY DEFINER function is not seen as one (the query says false)",
        VERIFY,
        "pg_catalog.pg_get_function_identity_arguments(p.oid), p.proowner, p.prosecdef, false,",
        "pg_catalog.pg_get_function_identity_arguments(p.oid), p.proowner, false, false,",
        k(T_PG, "test_a_security_definer_function_is_refused_unless_a_reviewer_listed_it"),
    ),
    Mutant(
        "SD2",
        "the reviewed list of SECURITY DEFINER functions is not read",
        VERIFY,
        '    migration_role = family[0] if family else ""\n',
        '    migration_role = family[0] if family else ""\n    reviewed_definers = frozenset()\n',
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
        "DP1",
        "the default rights are not judged",
        VERIFY,
        "    for d in rows.defaults:\n",
        "    for d in ():\n",
        k(
            T_PG,
            "test_a_default_right_that_an_administrator_set_is_refused_and_the_message_says_so",
        ),
    ),
    Mutant(
        "SC8",
        "the rights on the schemas are not judged",
        VERIFY,
        "        in_run = (not it.system) and it.schema == schema\n",
        '        in_run = (not it.system) and it.schema == schema\n        if it.kind == "schema":\n            continue\n',
        k(
            T_PG,
            "test_a_role_that_may_create_in_the_schema_is_refused_but_one_that_may_only_look_is_not",
        ),
    ),
    Mutant(
        "SC9",
        "a role that may only use the schema is refused too",
        VERIFY,
        '    if it.kind == "schema":\n        return it.privilege_type == "USAGE"\n',
        '    if it.kind == "schema":\n        return False\n',
        k(T_VERIFY, "test_a_named_role_may_use_the_schema_but_not_create_in_it") + "[USAGE-False]",
    ),
    Mutant(
        "GO4",
        "a function right that may be passed on is accepted",
        VERIFY,
        '            if it.is_grantable:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        '            if it.is_grantable and it.kind not in _FUNCTION_KINDS:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
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
        "RA2",
        "only the schema of the run is judged on the subject side (table rights)",
        VERIFY,
        "        if it.grantee is not None and it.grantee_is_subject:\n",
        '        if it.grantee is not None and it.grantee_is_subject:\n            if not in_run and it.kind in ("table", "view", "sequence"):\n                continue\n',
        k(T_VERIFY, "test_the_grant_map_is_what_a_named_role_may_hold"),
    ),
    Mutant(
        "RK1",
        "a foreign table is not judged",
        VERIFY,
        "        in_run = (not it.system) and it.schema == schema\n",
        '        in_run = (not it.system) and it.schema == schema\n        if it.kind == "foreign table":\n            continue\n',
        k(T_PG, "test_a_foreign_table_that_a_file_opens_to_everyone_is_refused"),
    ),
    Mutant(
        "OW5",
        "the owner of a function is not read (step 1)",
        MIG,
        "\"AND p.proname = ANY(%s::text[]) AND NOT pg_has_role(current_user, p.proowner, 'USAGE') \"",
        '"AND p.proname = ANY(%s::text[]) AND false "',
        k(
            T_VERIFY_PG,
            "test_a_name_the_package_manages_that_a_third_role_owns_is_refused_at_step_2",
        )
        + "[function]",
    ),
    Mutant(
        "OW6",
        "the owner of a sequence is not read (step 1)",
        MIG,
        "\"AND c.relkind IN ('r','p','v','m','S','f') AND c.relname = ANY(%s::text[]) \"",
        "\"AND c.relkind IN ('r','p','v','m','f') AND c.relname = ANY(%s::text[]) \"",
        k(
            T_VERIFY_PG,
            "test_a_name_the_package_manages_that_a_third_role_owns_is_refused_at_step_2",
        )
        + "[sequence]",
    ),
    Mutant(
        "GO5",
        "the grant option on a table or column right is ignored",
        VERIFY,
        '            if it.is_grantable:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        '            if it.is_grantable and (it.kind in _FUNCTION_KINDS or it.kind == "schema"):\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
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
        VERIFY,
        '            if it.is_grantable:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        '            if it.is_grantable and it.kind != "schema":\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        k(T_PG, "test_a_named_role_that_may_pass_the_schema_right_on_is_refused"),
    ),
    Mutant(
        "RO1",
        "a named role may have any right on a relation that is not in the grant map",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n",
        '    if it.schema != schema or it.name not in grant_map:\n        return it.kind in ("table", "view", "sequence")\n',
        (
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map") + "[insert]",
            k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
            + "[sequence_update]",
        ),
    ),
    Mutant(
        "DP2",
        "default rights are read only for the current schema and for all schemas",
        VERIFY,
        "WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)\n",
        "WHERE (a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)) AND (n.nspname IS NULL OR n.nspname = pg_catalog.current_schema())\n",
        k(
            T_PG,
            "test_default_rights_are_read_for_every_schema_and_for_the_roles_the_migration_role_belongs_to",
        )
        + "[other_schema]",
    ),
    Mutant(
        "DP3",
        "default rights are read only for the migration role itself, not for the roles it belongs to",
        VERIFY,
        "WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole IN (SELECT role FROM fam)\n",
        "WHERE a.grantee IN (SELECT role FROM subj) OR a.grantee = 0 OR d.defaclrole = (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname = current_user)\n",
        k(
            T_PG,
            "test_a_default_right_that_a_group_of_the_migration_role_sets_for_a_third_role_is_refused",
        ),
    ),
    Mutant(
        "DP4",
        "a named role may have a default right",
        VERIFY,
        "            if d.grantee == d.set_for:\n                continue\n",
        "            if d.grantee == d.set_for or d.grantee in named_roles:\n                continue\n",
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
        "the default rights of the role they are set for are judged as rights of a stranger",
        VERIFY,
        "d.set_for_family and d.grantee != d.set_for and d.grantee != migration_role",
        "d.set_for_family and d.grantee != migration_role",
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
        "the replication flag of a named role is not judged",
        VERIFY,
        '    ("rolreplication", "REPLICATION"),\n',
        "",
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
        "the pseudo-role pg_database_owner is not added to what a named role reaches",
        VERIFY,
        '        if rows.database_owner in closure[n] and "pg_database_owner" not in closure[n]:\n',
        '        if False and rows.database_owner in closure[n] and "pg_database_owner" not in closure[n]:\n',
        k(T_VERIFY, "test_the_database_owner_reaches_pg_database_owner_and_gets_no_statement"),
    ),
    Mutant(
        "RO3",
        "a named role may SELECT a relation that is not in the grant map",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n",
        '    if it.schema != schema or it.name not in grant_map:\n        return it.privilege_type == "SELECT" and it.kind in ("table", "view", "sequence")\n',
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
        "a named role may use a sequence that is not in the grant map",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n",
        '    if it.schema != schema or it.name not in grant_map:\n        return it.kind == "sequence" and it.privilege_type == "USAGE"\n',
        k(T_PG, "test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map")
        + "[sequence_usage]",
    ),
    Mutant(
        "RO4",
        "a named role may have a right on a function",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n",
        "    if it.schema != schema or it.name not in grant_map:\n        return it.kind in _FUNCTION_KINDS\n",
        (k(T_PG, "test_a_named_role_gets_no_right_on_a_function"),),
    ),
    Mutant(
        "DP6",
        "a default right for the migration role itself is judged as a right of a stranger",
        VERIFY,
        "d.set_for_family and d.grantee != d.set_for and d.grantee != migration_role",
        "d.set_for_family and d.grantee != d.set_for",
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
        VERIFY,
        '            built_in = d.kind in "fT" and not d.schema and (d.kind, right) in _BUILT_IN_DEFAULT\n',
        "            built_in = False\n",
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
        VERIFY,
        '            built_in = d.kind in "fT" and not d.schema and (d.kind, right) in _BUILT_IN_DEFAULT\n',
        '            built_in = d.kind in "fT" and (d.kind, right) in _BUILT_IN_DEFAULT\n',
        (
            k(
                T_PG,
                "test_a_default_right_for_a_named_role_or_for_everyone_is_refused_for_functions_sequences_and_types",
            )
            + "[everyone_functions_in_a_schema]",
        ),
    ),
    Mutant(
        "DP9",
        "every default right for everyone that is set for all schemas is skipped",
        VERIFY,
        '            built_in = d.kind in "fT" and not d.schema and (d.kind, right) in _BUILT_IN_DEFAULT\n',
        '            built_in = d.kind in "fT" and not d.schema\n',
        k(
            T_VERIFY,
            "test_a_default_right_for_everyone_is_skipped_only_when_it_is_the_servers_own_pair",
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
        "a relation name of the grant map is taken for a function name",
        VERIFY,
        "    managed_rel, managed_fn = set(managed_relations), set(managed_functions)\n",
        "    managed_rel, managed_fn = set(managed_relations), set(managed_functions)\n    managed_fn = managed_rel | managed_fn\n",
        (
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
        "a SECURITY DEFINER function of the migration role that no file names is not judged",
        VERIFY,
        "            and it.definer\n            and (it.schema, it.name, it.sub) not in reviewed_definers\n",
        "            and it.definer\n            and it.name in managed_fn\n            and (it.schema, it.name, it.sub) not in reviewed_definers\n",
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
        "every SECURITY DEFINER function of the run schema is refused, whoever owns it (rule S7)",
        VERIFY,
        "            and fam_owned\n            and it.definer\n",
        "            and it.definer\n",
        k(T_VERIFY_PG, "test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments"),
    ),
    Mutant(
        "SD8",
        "the SECURITY DEFINER functions of every schema are refused (rule S7 is read in the schema of the run only)",
        VERIFY,
        "        if it.system or it.schema != schema:\n            continue\n        fam_owned",
        "        if it.system:\n            continue\n        fam_owned",
        k(T_VERIFY_PG, "test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments"),
    ),
    Mutant(
        "RA4",
        "only the schema of the run is judged on the subject side (column rights)",
        VERIFY,
        "        if it.grantee is not None and it.grantee_is_subject:\n",
        '        if it.grantee is not None and it.grantee_is_subject:\n            if not in_run and it.kind == "column":\n                continue\n',
        k(T_VERIFY, "test_a_right_of_a_named_role_on_a_column_of_another_schema_is_refused"),
    ),
    Mutant(
        "IM1",
        "no relation counts as one of the grant map (the name is never found)",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n",
        "    if True:\n        return False\n",
        k(
            T_PG,
            "test_the_named_roles_and_the_owner_may_hold_rights_and_a_function_loses_the_default_for_everyone",
        ),
    ),
    Mutant(
        "RK2",
        "a foreign table is not judged for what a named role can do",
        VERIFY,
        "        if it.grantee is not None and it.grantee_is_subject:\n",
        '        if it.grantee is not None and it.grantee_is_subject:\n            if it.kind == "foreign table":\n                continue\n',
        k(T_PG, "test_a_named_role_that_can_read_a_foreign_table_in_the_run_schema_is_refused"),
    ),
    Mutant(
        "SC12",
        "the migration role's own right on a schema it does not own is judged as a right of a stranger",
        VERIFY,
        "        if not in_run or it.owner_item or it.grantee == migration_role:\n",
        "        if not in_run or it.owner_item:\n",
        k(
            T_PG,
            "test_a_role_made_with_the_printed_sql_only_can_pass_usage_on_to_the_runtime_and_portal_roles",
        ),
    ),
    Mutant(
        "SC13",
        "the owner's right on a schema is judged as a right of a stranger",
        VERIFY,
        "        if not in_run or it.owner_item or it.grantee == migration_role:\n",
        "        if not in_run or it.grantee == migration_role:\n",
        k(T_PG, "test_the_printed_role_runs_in_a_schema_that_the_database_owner_role_owns"),
    ),
    Mutant(
        "SC14",
        "a named role may create in a schema",
        VERIFY,
        '    if it.kind == "schema":\n        return it.privilege_type == "USAGE"\n',
        '    if it.kind == "schema":\n        return True\n',
        k(T_VERIFY, "test_a_named_role_may_use_the_schema_but_not_create_in_it") + "[CREATE-True]",
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
        "                and (db.execute(_LOCK_PREPARED_SQL, (MIGRATE_LOCK,)).fetchone() or (0,))[0]\n",
        "                and False\n",
        (
            k(T_CMP, "test_a_lock_held_by_a_prepared_transaction_is_said_so_with_what_finishes_it"),
            k(T_PG, "test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one"),
        ),
    ),
    # --- ticket P3a-2, commit 3c: one mutant per clause of `_judge` and of the steps (V01 to V60) ---
    Mutant(
        "V01",
        "S1: the five flags are not read",
        VERIFY,
        "            for word in flags.get(role, ()):\n",
        "            for word in ():\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[flag]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V02",
        "S2: a built-in server role is not refused",
        VERIFY,
        '            if role.startswith("pg_"):\n',
        "            if False:\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[built_in_role]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V03",
        "S3: a role of the migration role family is not refused",
        VERIFY,
        "            elif role in fam_roles:\n",
        "            elif False:\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[can_act_as_family]",
    ),
    Mutant(
        "V04",
        "S3: two named roles that reach each other are not refused",
        VERIFY,
        "            elif role != n and role in named_roles:\n",
        "            elif False:\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[named_roles_overlap]",
    ),
    Mutant(
        "V05",
        "S4: an object owned by a named role is not refused",
        VERIFY,
        '        if r.deptype == "o" and not r.temporary:\n',
        "        if False:\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[owns]",
            "tests/test_migration_verify_pg.py::test_a_left_over_object_owned_by_a_named_role_is_found",
        ),
    ),
    Mutant(
        "V06",
        "S5: a right that the grant map does not give is accepted",
        VERIFY,
        "                if _allowed_for(named_roles[n], it, schema, grant_map):\n                    continue\n",
        "                if True:\n                    continue\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[right]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V07",
        "S5: a right reached through a group is not refused",
        VERIFY,
        '                    p = make("right", n, it.privilege_type, fix=mfix or None, via=it.grantee)\n                    out.append(p)\n',
        "                    pass\n",
        "tests/test_migration_verify.py::test_a_group_reached_by_two_named_roles_is_judged_for_each",
    ),
    Mutant(
        "V08",
        "S6: a grant option held by a named role is not refused",
        VERIFY,
        '            if it.is_grantable:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        '            if False:\n                out.append(make("grant_option", it.grantee, it.privilege_type, option=True))\n',
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[grant_option]",
    ),
    Mutant(
        "V09",
        "S8: a right named in a catalog that is not read is not refused",
        VERIFY,
        '        elif r.deptype == "a" and not r.role.startswith("pg_") and r.catalog not in _READ_CATALOGS:\n',
        "        elif False:\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[unread_catalog]",
    ),
    Mutant(
        "V10",
        "O2: a function of the family that everyone may call is not refused",
        VERIFY,
        '                if in_run and fam_owned:\n                    out.append(make("everyone", EVERYONE, right, rep=managed_here))\n',
        '                if False:\n                    out.append(make("everyone", EVERYONE, right, rep=managed_here))\n',
        "tests/test_migration_postgres.py::test_an_aggregate_with_no_arguments_is_revoked_with_empty_brackets",
    ),
    Mutant(
        "V11",
        "O2: USAGE on a plain type for everyone is not refused (the test is turned round)",
        VERIFY,
        "                if in_run and fam_owned and not it.row_type:\n",
        "                if in_run and fam_owned and it.row_type:\n",
        (
            "tests/test_migration_verify.py::test_a_row_type_may_be_used_by_everyone_and_a_plain_type_may_not",
            "tests/test_migration_verify_pg.py::test_message_safety_names_with_newline_and_escape",
        ),
    ),
    Mutant(
        "V12",
        "O2: USAGE on a language of the family for everyone is not refused",
        VERIFY,
        '            if kind == "language":\n                if in_run and fam_owned:\n',
        '            if kind == "language":\n                if False:\n',
        "tests/test_migration_verify.py::test_usage_on_a_language_is_refused_for_everyone_only_when_the_migration_family_owns_it",
    ),
    Mutant(
        "V13",
        "O7: a schema right beyond USAGE for everyone is not refused",
        VERIFY,
        '                    out.append(make("schema_right" if in_run else "everyone", EVERYONE, right))\n',
        "                    pass\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[schema_right]",
            "tests/test_migration_verify_pg.py::test_create_for_everyone_on_public_is_refused",
        ),
    ),
    Mutant(
        "V14",
        "O2: CREATE on the database for everyone is not refused",
        VERIFY,
        '                if right not in ("CONNECT", "TEMPORARY"):\n',
        "                if False:\n",
        "tests/test_migration_verify.py::test_a_right_of_everyone_on_the_database_is_refused_only_beyond_connect_and_temporary[CREATE-True]",
    ),
    Mutant(
        "V15",
        "Q2 change (d): a relation of an unread kind is not refused",
        VERIFY,
        '                out.append(make("unread_relation_kind", EVERYONE, right, detail=it.relkind, fix=""))\n',
        "                pass\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[unread_relation_kind]",
    ),
    Mutant(
        "V16",
        "O2: a right for everyone where everyone holds nothing by default is not refused",
        VERIFY,
        '            if kind in _NOTHING_BY_DEFAULT:\n                out.append(make("everyone", EVERYONE, right))\n',
        '            if False:\n                out.append(make("everyone", EVERYONE, right))\n',
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[everyone]",
            "tests/test_migration_verify_pg.py::test_message_safety_names_with_newline_and_escape",
        ),
    ),
    Mutant(
        "V17",
        "O7: a schema right for a third role is not refused",
        VERIFY,
        '        elif it.kind == "schema":\n            out.append(\n                make(\n                    "schema_right" if it.privilege_type != "USAGE" else "other_grantee",',
        '        elif it.kind == "schema" and False:\n            out.append(\n                make(\n                    "schema_right" if it.privilege_type != "USAGE" else "other_grantee",',
        "tests/test_migration_postgres.py::test_a_role_that_may_create_in_the_schema_is_refused_but_one_that_may_only_look_is_not[CREATE]",
    ),
    Mutant(
        "V18",
        "O1: a right for a third role on an object of the family is not refused",
        VERIFY,
        '        elif fam_owned:\n            out.append(make("other_grantee", it.grantee, it.privilege_type))\n',
        '        elif False:\n            out.append(make("other_grantee", it.grantee, it.privilege_type))\n',
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[other_grantee]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V19",
        "O3: a grant option held by a third role is not refused",
        VERIFY,
        '            out.append(make("other_grantee", it.grantee, it.privilege_type))\n            if it.is_grantable:\n',
        '            out.append(make("other_grantee", it.grantee, it.privilege_type))\n            if False:\n',
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[object_grant_option]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V20",
        "O4: a SECURITY DEFINER function nobody reviewed is not refused",
        VERIFY,
        "            and fam_owned\n            and it.definer\n            and (it.schema, it.name, it.sub) not in reviewed_definers\n",
        "            and fam_owned\n            and False\n            and (it.schema, it.name, it.sub) not in reviewed_definers\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[definer_unreviewed]",
            "tests/test_migration_verify_pg.py::test_a_reviewed_definer_is_excused_only_in_its_schema_with_its_arguments",
        ),
    ),
    Mutant(
        "V21",
        "O8: a package object whose owner is outside the family is not refused",
        VERIFY,
        "        if managed and not fam_owned:\n",
        "        if False:\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[foreign_owner]",
    ),
    Mutant(
        "V22",
        "S7: a SECURITY DEFINER function that everyone may call is not refused",
        VERIFY,
        '            if in_fn and it.definer and right == "EXECUTE" and not ext:\n',
        "            if False:\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[definer_callable]",
    ),
    Mutant(
        "V23",
        "E1: an object of an extension is given a statement",
        VERIFY,
        '        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        outside = (not in_run) or not fam_owned\n',
        '        ext = ""\n        outside = (not in_run) or not fam_owned\n',
        "tests/test_migration_verify.py::test_an_extension_member_is_refused_with_no_statement",
    ),
    Mutant(
        "V24",
        "O8: the split between the package and other applications is lost",
        VERIFY,
        "        outside = (not in_run) or not fam_owned\n",
        "        outside = False\n",
        "tests/test_migration_postgres.py::test_a_named_role_gets_no_right_on_what_is_not_in_the_grant_map[select]",
    ),
    Mutant(
        "V25",
        "D4: a default right of an unknown kind is not refused",
        VERIFY,
        '            out.append(_default("default_unknown_kind", d, "", ""))\n',
        "            pass\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[default_unknown_kind]",
    ),
    Mutant(
        "V26",
        "D1: a default right for a named role is not refused",
        VERIFY,
        '            out.append(_default("default_for_named", d, right, d.grantee))\n',
        "            pass\n",
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[default_for_named]",
    ),
    Mutant(
        "V27",
        "D2: a default right for everyone is not refused",
        VERIFY,
        '            if not built_in:\n                out.append(_default("default_for_everyone", d, right, EVERYONE))\n',
        '            if False:\n                out.append(_default("default_for_everyone", d, right, EVERYONE))\n',
        "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[default_for_everyone]",
    ),
    Mutant(
        "V28",
        "D3: a default right for another role on what the family makes is not refused",
        VERIFY,
        "        elif d.set_for_family and d.grantee != d.set_for and d.grantee != migration_role:\n",
        "        elif False:\n",
        (
            "tests/test_migration_verify.py::test_judge_makes_the_problem_kind[default_for_other]",
            "tests/test_migration_verify_pg.py::test_printed_statements_remove_every_problem_for_every_grantor_form",
        ),
    ),
    Mutant(
        "V29",
        "the map is keyed by name only: the schema is not compared",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:\n        return False\n    g = grant_map[it.name]\n",
        "    if it.name not in grant_map:\n        return False\n    g = grant_map[it.name]\n",
        "tests/test_migration_verify.py::test_the_grant_map_is_what_a_named_role_may_hold",
    ),
    Mutant(
        "V30",
        "the map is keyed by kind only: the name is not compared",
        VERIFY,
        "    g = grant_map[it.name]\n",
        "    g = next(iter(grant_map.values()))\n",
        "tests/test_migration_verify_pg.py::test_upgrade_from_mains_state_is_repaired",
    ),
    Mutant(
        "V31",
        "the map is not keyed by kind: a view is judged as a table",
        VERIFY,
        "    if wanted != g.kind:\n        return False\n",
        "    if False:\n        return False\n",
        "tests/test_migration_verify.py::test_a_shipped_table_name_does_not_make_a_view_of_that_name_allowed",
    ),
    Mutant(
        "V32",
        "the row-type exception is widened to every type",
        VERIFY,
        "                if in_run and fam_owned and not it.row_type:\n",
        "                if False:\n",
        (
            "tests/test_migration_verify.py::test_a_row_type_may_be_used_by_everyone_and_a_plain_type_may_not",
            "tests/test_migration_verify_pg.py::test_row_types_of_six_relation_kinds_pass_and_a_standalone_composite_type_does_not",
        ),
    ),
    Mutant(
        "V33",
        "the rule for what everyone holds on the system schemas is dropped",
        VERIFY,
        "    OR (NOT i.system AND i.grantee = 0\n",
        "    OR (i.grantee = 0\n",
        "tests/test_migration_verify_pg.py::test_the_running_server_is_16_or_later_and_accepted",
    ),
    Mutant(
        "V34",
        "repaired_by_run is set for every problem",
        VERIFY,
        "                by_hand,\n                rep,\n",
        "                by_hand,\n                True,\n",
        (
            "tests/test_migration_verify.py::test_the_rights_on_a_map_table_before_the_run_are_repaired_by_the_run_only_for_the_migration_roles_grants",
            "tests/test_migration_verify_pg.py::test_create_for_everyone_on_public_is_refused",
        ),
    ),
    Mutant(
        "V35",
        "the closure follows memberships that do not inherit",
        VERIFY,
        "        closure.setdefault(r.start_role, {})[r.member_of] = bool(r.uses_rights_at_once)\n",
        "        closure.setdefault(r.start_role, {})[r.member_of] = True\n",
        "tests/test_migration_verify.py::test_usage_on_the_schema_through_a_group_that_does_not_inherit_is_not_usage",
    ),
    Mutant(
        "V36",
        "pg_database_owner is not counted as the family's when the database owner is in the family",
        VERIFY,
        "    fam_has_db_owner = rows.database_owner in fam_roles\n",
        "    fam_has_db_owner = False\n",
        "tests/test_migration_verify.py::test_an_object_of_pg_database_owner_is_the_familys_when_the_database_owner_is_in_the_family",
    ),
    Mutant(
        "V37",
        "the temporary-object exception is widened to every object",
        VERIFY,
        "  (d.classid = 'pg_catalog.pg_class'::pg_catalog.regclass AND EXISTS (\n",
        "  (true OR d.classid = 'pg_catalog.pg_class'::pg_catalog.regclass AND EXISTS (\n",
        "tests/test_migration_verify_pg.py::test_a_left_over_object_owned_by_a_named_role_is_found",
    ),
    Mutant(
        "V38",
        "the pinned path is removed from verify",
        VERIFY,
        "    with pinned_read(db, limits):\n        rows = _read(\n",
        "    if True:\n        rows = _read(\n",
        "tests/test_migration_verify_pg.py::test_step_8_reads_one_snapshot",
    ),
    Mutant(
        "V39",
        "the version refusal is removed",
        VERIFY,
        "    version, owner = _fetch(db, V2_SQL, named=False)[0]\n    check_version(version)\n",
        "    version, owner = _fetch(db, V2_SQL, named=False)[0]\n",
        "tests/test_migration_verify.py::test_the_read_refuses_an_old_server_before_it_runs_a_query_that_needs_16",
    ),
    Mutant(
        "V40",
        "the self-check of the access-list columns is removed",
        VERIFY,
        "    acl_columns = tuple(r[0] for r in _fetch(db, Q0, named=False))\n    check_acl_columns(acl_columns)\n",
        "    acl_columns = tuple(r[0] for r in _fetch(db, Q0, named=False))\n",
        "tests/test_migration_verify.py::test_the_read_runs_the_self_check_before_the_queries_that_use_the_columns",
    ),
    Mutant(
        "V41",
        "the self-check does not refuse a column this package does not know",
        VERIFY,
        "    if unknown:\n        raise ConfigError(",
        "    if False:\n        raise ConfigError(",
        (
            "tests/test_migration_verify.py::test_the_self_check_names_an_unknown_and_a_missing_column",
            "tests/test_migration_verify_pg.py::test_the_self_check_stops_verify_when_the_server_has_a_column_the_package_does_not_know",
        ),
    ),
    Mutant(
        "V42",
        "the self-check does not refuse a column this server lacks",
        VERIFY,
        "    if missing:\n        raise ConfigError(",
        "    if False:\n        raise ConfigError(",
        "tests/test_migration_verify.py::test_the_self_check_names_an_unknown_and_a_missing_column",
    ),
    Mutant(
        "V43",
        "the built-in-grantee filter is removed from S5",
        VERIFY,
        '            if it.grantee.startswith("pg_") or it.owner_item:\n',
        "            if it.owner_item:\n",
        "tests/test_migration_verify.py::test_a_right_for_a_built_in_role_is_not_counted_a_second_time_as_a_right",
    ),
    Mutant(
        "V44",
        "a statement is printed for a system object",
        VERIFY,
        '            if it.system:\n                fix, by_hand = "", "system"\n',
        '            if False:\n                fix, by_hand = "", "system"\n',
        "tests/test_migration_verify.py::test_no_statement_is_printed_for_a_right_on_a_system_object",
    ),
    Mutant(
        "V45",
        "the REVOKE of an object right ignores the grantor",
        VERIFY,
        '    if not grantor_is_owner:\n        text = f"SET ROLE',
        '    if False:\n        text = f"SET ROLE',
        "tests/test_migration_verify.py::test_the_revoke_of_a_right_that_another_role_granted_acts_as_that_role",
    ),
    Mutant(
        "V46",
        "the membership fix has no GRANTED BY",
        VERIFY,
        'GRANTED BY {_s(_ident(grantor))};"',
        '{_s(_ident(grantor))[:0]};"',
        (
            "tests/test_migration_verify.py::test_a_group_reached_by_two_named_roles_is_judged_for_each",
            "tests/test_migration_verify_pg.py::test_a_named_role_in_pg_monitor_prints_exactly_one_statement",
        ),
    ),
    Mutant(
        "V47",
        "repaired_by_run ignores the grantor",
        VERIFY,
        "                        and it.grantor == migration_role\n",
        "                        and True\n",
        (
            "tests/test_migration_verify.py::test_the_rights_on_a_map_table_before_the_run_are_repaired_by_the_run_only_for_the_migration_roles_grants",
            "tests/test_migration_verify_pg.py::test_verify_cost_on_a_large_catalog",
        ),
    ),
    Mutant(
        "V48",
        "the two time limits are not run inside verify",
        VERIFY,
        "        for line in limits:\n            db.execute(line)\n",
        "        for line in ():\n            db.execute(line)\n",
        (
            "tests/test_migration_verify.py::test_pinned_read_sets_the_two_limits_and_the_path_before_any_read_and_always_rolls_back",
            "tests/test_migration_verify_pg.py::test_verify_gets_through_a_one_millisecond_statement_timeout_that_cancels_its_own_query",
        ),
    ),
    Mutant(
        "V49",
        "Q1 joins its closure with UNION ALL",
        VERIFY,
        "  UNION\n  SELECT c.root, m.roleid, c.at_once AND m.inherit_option\n",
        "  UNION ALL\n  SELECT c.root, m.roleid, c.at_once AND m.inherit_option\n",
        "tests/test_migration_verify_pg.py::test_verify_cost_on_a_large_catalog",
    ),
    Mutant(
        "V50",
        "the check before the first file is removed",
        MIG,
        "                    if before:\n                        raise ConfigError(",
        "                    if False:\n                        raise ConfigError(",
        "tests/test_migration_matrix.py::test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O01-select-other/C12-by-hand-then-migrate/no-roles]",
    ),
    Mutant(
        "V51",
        "the check before the commit is removed",
        MIG,
        STEP6_CALL,
        STEP6_CALL.replace("if problems:", "if False:", 1),
        "tests/test_migration_matrix.py::test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O01-select-other/C1-plain-file/no-roles]",
    ),
    Mutant(
        "V52",
        "the check after the commit is removed",
        MIG,
        "    if problems:\n        raise _after_commit(applied, problems)\n    return applied",
        "    return applied",
        "tests/test_migration_verify_pg.py::test_after_commit_a_grant_gives_exit_5_and_the_statements_repair_it",
    ),
    Mutant(
        "V53",
        "a check that cannot run after the commit is raised as a refusal",
        MIG,
        "        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e",
        '        raise ConfigError("check failed") from e',
        "tests/test_migration_verify_pg.py::test_step_8_that_cannot_connect_gives_exit_5",
    ),
    Mutant(
        "V54",
        "a failed check after the commit returns as applied",
        MIG,
        "        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e",
        "        return applied",
        "tests/test_migration_verify_pg.py::test_step_8_that_cannot_connect_gives_exit_5",
    ),
    Mutant(
        "V55",
        "step 8 is not one snapshot",
        MIG,
        "            after.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ\n",
        "            pass\n",
        "tests/test_migration_verify_pg.py::test_step_8_reads_one_snapshot",
    ),
    Mutant(
        "V56",
        "the step-8 try catches connection errors only",
        MIG,
        "    except Exception as e:  # any error at all: the commit happened and the check did not finish",
        "    except psycopg.OperationalError as e:  # any error at all: the commit happened and the check did not finish",
        "tests/test_migration_verify_pg.py::test_any_error_inside_step_8_gives_exit_5_not_exit_2[old_version]",
    ),
    Mutant(
        "V57",
        "a commit the server refused is classed as unknown",
        MIG,
        '        return "refused"\n    return "unknown"\n',
        '        return "unknown"\n    return "unknown"\n',
        (
            "tests/test_migration_verify.py::test_commit_outcome_classes_refused[22001]",
            "tests/test_migration_verify_pg.py::test_a_commit_refused_by_the_server_gives_exit_2_and_keeps_nothing",
        ),
    ),
    Mutant(
        "V58",
        "a lost connection at the commit is classed as refused",
        MIG,
        '    if not state or getattr(db, "closed", True):\n        return "unknown"\n',
        '    if not state or getattr(db, "closed", True):\n        return "refused"\n',
        (
            "tests/test_migration_verify.py::test_commit_outcome_classes_unknown_without_a_code_a_closed_connection_or_a_transaction_state",
            "tests/test_migration_verify_pg.py::test_a_lost_connection_at_commit_gives_exit_5",
        ),
    ),
    Mutant(
        "V59",
        "a transaction that is not idle is classed as refused",
        MIG,
        '    if db.info.transaction_status != TransactionStatus.IDLE:\n        return "unknown"\n',
        '    if False:\n        return "unknown"\n',
        (
            "tests/test_migration_verify.py::test_commit_outcome_classes_unknown_without_a_code_a_closed_connection_or_a_transaction_state",
            "tests/test_migration_steps.py::test_a_refused_error_on_a_closed_connection_is_unknown",
        ),
    ),
    Mutant(
        "V60",
        "the REVOKE of a function default skips a function with no arguments (the empty signature)",
        MIG,
        "        signature = args  # an aggregate",
        "        if not args:\n            continue\n        signature = args  # an aggregate",
        (
            "tests/test_migration_verify_pg.py::test_step_4_revokes_an_aggregate_with_no_arguments_that_has_the_name_of_a_files_function",
            "tests/test_migration_steps.py::test_step_4_takes_everyones_execute_off_the_functions_the_files_name",
        ),
    ),
    Mutant(
        "V61",
        "a right word is accepted when it is the start of one of the map's rights (a prefix test)",
        VERIFY,
        "    return it.privilege_type in _rights_for(role_kind, g) and not it.is_grantable\n",
        '    return any(r.startswith(it.privilege_type or "?") for r in _rights_for(role_kind, g)) and not it.is_grantable\n',
        (
            "tests/test_migration_verify.py::test_an_unknown_right_word_is_refused_whole_never_by_prefix",
        ),
    ),
    Mutant(
        "V62",
        "an object with an empty access list (a row with no right) is judged as if it had a right",
        VERIFY,
        "        if it.privilege_type is None:\n            continue\n",
        "        if False:\n            continue\n",
        (
            "tests/test_migration_verify.py::test_an_item_with_no_right_is_never_read_as_a_right_for_everyone",
        ),
    ),
    Mutant(
        "V63",
        "the promise table of the docstring says its first row is NOT BUILT YET (the CHANGELOG still names the test)",
        MIG,
        "is caught before release by a test that runs the shipped files",
        "is NOT BUILT YET (planned for commit 5 of this package) and would run the shipped files",
        "tests/test_migration_verify.py::test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog",
    ),
    Mutant(
        "V64",
        "the promise table of the CHANGELOG says its first row is NOT BUILT YET (the docstring still names the test)",
        CL,
        "is caught before release by a test that runs the shipped files",
        "is NOT BUILT YET (planned for commit 5 of this package) and would run the shipped files",
        "tests/test_migration_verify.py::test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog",
    ),
    Mutant(
        "V65",
        "SQLSTATE 40003 (statement completion unknown) at the commit is classed with the refused class 40",
        MIG,
        '    if state in _COMMIT_UNKNOWN_STATES:\n        return "unknown"\n',
        '    if False:\n        return "unknown"\n',
        "tests/test_migration_verify.py::test_commit_outcome_classes_unknown_by_code",
    ),
    Mutant(
        "V66",
        "step 4 skips a function whose name has a character outside ASCII (it keeps EXECUTE for everyone)",
        MIG,
        '        db.execute(\n            pg.sql_template(\n                "REVOKE ALL ON ROUTINE {}({}) FROM PUBLIC",',
        '        if not name.isascii():\n            continue\n        db.execute(\n            pg.sql_template(\n                "REVOKE ALL ON ROUTINE {}({}) FROM PUBLIC",',
        (
            "tests/test_migration_steps.py::test_step_4_writes_every_function_name_through_identifier_quoting",
            "tests/test_migration_verify_pg.py::test_step_4_takes_everyones_execute_off_functions_with_awkward_names",
        ),
    ),
    Mutant(
        "V67",
        "a driver error raised by the check at step 2 is not mapped to a refusal (it escapes as exit 3)",
        MIG,
        "                    with _check_could_not_run(step[0]):\n                        found = _state_problems(",
        "                    if True:\n                        found = _state_problems(",
        (
            "tests/test_migration_steps.py::test_a_driver_error_raised_by_the_check_before_the_commit_is_a_refusal_that_keeps_nothing",
            "tests/test_migration_verify_pg.py::test_a_connection_lost_while_the_check_runs_before_the_commit_gives_exit_2",
        ),
    ),
    Mutant(
        "V68",
        "a driver error raised by the check at step 6 is not mapped to a refusal (it escapes as exit 3)",
        MIG,
        "                    with _check_could_not_run(step[0]):\n                        problems = _state_problems(",
        "                    if True:\n                        problems = _state_problems(",
        (
            "tests/test_migration_steps.py::test_a_driver_error_raised_by_the_check_before_the_commit_is_a_refusal_that_keeps_nothing",
            "tests/test_migration_verify_pg.py::test_a_connection_lost_while_the_check_runs_before_the_commit_gives_exit_2",
        ),
    ),
    Mutant(
        "V69",
        "an error at the commit is always taken as refused, without asking which kind it is",
        MIG,
        '                if _commit_outcome(e, db) == "refused":',
        "                if True:",
        "tests/test_migration_verify_pg.py::test_a_lost_connection_at_commit_gives_exit_5",
    ),
    Mutant(
        "V70",
        "Q2 drops an object whose access list is empty (a CROSS JOIN instead of a LEFT JOIN)",
        VERIFY,
        "FROM obj o LEFT JOIN LATERAL pg_catalog.aclexplode(o.acl) a ON true)",
        "FROM obj o CROSS JOIN LATERAL pg_catalog.aclexplode(o.acl) a)",
        "tests/test_migration_verify_pg.py::test_an_object_whose_access_list_is_empty_is_still_judged_for_owner_and_definer",
    ),
    # --- ticket P3a-2, commit 4: the lock message (6.1, 6.2) ---
    Mutant(
        "V71",
        "6.1: the prepared transactions are listed the old way (every one of the database) and not joined to the lock",
        MIG,
        "    \"JOIN pg_catalog.pg_locks t ON t.locktype = 'transactionid' AND t.pid IS NULL AND t.granted \"\n"
        '    "AND t.virtualtransaction = l.virtualtransaction "\n'
        '    "JOIN pg_catalog.pg_prepared_xacts x ON x.transaction = t.transactionid "\n',
        "    \"JOIN pg_catalog.pg_locks t ON l.locktype = 'advisory' \"\n"
        "    \"JOIN pg_catalog.pg_prepared_xacts x ON t.locktype = 'advisory' \"\n",
        (
            k(T_PG, "test_a_prepared_transaction_that_holds_the_migration_lock_is_named_as_one"),
            k(T_VERIFY_PG, "test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction"),
        ),
    ),
    Mutant(
        "V72",
        "6.1: the count of lock rows without a session also counts the lock of a live session (`l.pid IS NULL` left out)",
        MIG,
        "    \"SELECT count(*) FROM pg_locks l WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 AND l.pid IS NULL \"",
        "    \"SELECT count(*) FROM pg_locks l WHERE l.locktype = 'advisory' AND l.granted AND l.objsubid = 1 \"",
        k(T_VERIFY_PG, "test_the_lock_queries_tell_a_live_session_from_a_prepared_transaction"),
    ),
    Mutant(
        "V73",
        "6.2: a driver error while the holder of the lock is read is not caught",
        MIG,
        "        except psycopg.Error as exc:\n            # Ticket 6.2",
        "        except ZeroDivisionError as exc:\n            # Ticket 6.2",
        (
            k(T_CMP, "test_an_unreadable_lock_view_is_a_plain_config_error_whichever_query_fails"),
            k(T_VERIFY_PG, "test_an_unreadable_lock_view_is_a_plain_config_error"),
        ),
    ),
    Mutant(
        "V74",
        "6.2: the user name of the session that holds the lock is written without the escape of control characters",
        MIG,
        '            f"the session of {_label(_seen(row[1]))} (process',
        '            f"the session of {_seen(row[1])} (process',
        k(
            T_CMP,
            "test_the_name_of_the_session_that_holds_the_lock_is_written_without_control_characters",
        ),
    ),
    Mutant(
        "V75",
        "6.1: a list of several prepared transactions is not named",
        MIG,
        '            elif named:\n                finish = (\n                    f"One of these',
        '            elif False:\n                finish = (\n                    f"One of these',
        k(
            T_CMP,
            "test_two_prepared_transactions_that_could_hold_the_lock_are_all_named_and_none_is_picked",
        ),
    ),
    Mutant(
        "V76",
        "7.7: the runtime role gets nothing in step 4 (the shipped files give it no right)",
        MIG,
        "                    if runtime_role:\n                        _apply_grants(db, schema, runtime_role, lambda g: g.runtime)",
        "                    if False:\n                        _apply_grants(db, schema, runtime_role, lambda g: g.runtime)",
        k(T_MX, "test_the_shipped_files_give_each_role_exactly_the_map"),
    ),
    Mutant(
        "V77",
        "7.7: the purge role gets its table rights but no column to read (its DELETE cannot name a row)",
        MIG,
        "db, schema, purge_role, lambda g: g.purge, lambda g: g.purge_cols\n",
        "db, schema, purge_role, lambda g: g.purge, None\n",
        k(T_MX, "test_the_shipped_files_give_each_role_exactly_the_map"),
    ),
    Mutant(
        "V78",
        "7.5: the deferred checks and triggers are not run early (a deferred trigger acts after the check)",
        MIG,
        '                        db.execute("SET CONSTRAINTS ALL IMMEDIATE")\n',
        "                        pass\n",
        k(
            T_MX,
            "test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O01-select-other/C6-deferred-ledger-trigger/no-roles]",
        ),
    ),
    Mutant(
        "V79",
        "7.5: the check before the commit is removed (a composition of effects is then found only after the commit)",
        MIG,
        STEP6_CALL,
        STEP6_CALL.replace("if problems:", "if False:", 1),
        k(T_MX, "test_every_composition_of_effects_is_refused_and_keeps_nothing[comp000]"),
    ),
    Mutant(
        "V80",
        "Issue 2 of 3d: a driver error before the commit that is not a file's own is raised as the raw error (exit 3)",
        MIG,
        "\n                    raise _driver_error_before_commit(e, step[0]) from e\n",
        "\n                    raise\n",
        (
            k(
                T_VERIFY_PG,
                "test_a_connection_lost_at_any_step_before_the_commit_gives_exit_2_and_keeps_nothing[_take_the_lock]",
            ),
            k(
                T_VERIFY_PG,
                "test_a_connection_lost_at_any_step_before_the_commit_gives_exit_2_and_keeps_nothing[_apply_grants]",
            ),
        ),
    ),
    Mutant(
        "V81",
        "Issue 2 of 3d: every driver error while a file runs is taken as the file's own (a lost connection stays raw)",
        MIG,
        "                    if running_a_file and _is_a_files_own_error(e, db):\n",
        "                    if running_a_file:\n",
        k(T_VERIFY_PG, "test_a_connection_lost_while_a_file_runs_is_refused_with_exit_2"),
    ),
    Mutant(
        "V82",
        "Issue 2 of 3d: a file's own error is turned into the refusal of a driver error (the file text is lost)",
        MIG,
        "                    if running_a_file and _is_a_files_own_error(e, db):\n",
        "                    if False:\n",
        k(T_VERIFY_PG, "test_a_files_own_error_is_raised_as_it_is"),
    ),
    Mutant(
        "V83",
        "Issue 5 of 3d: the identity arguments are left out of the REVOKE of step 4 (a function with an odd argument is not found)",
        MIG,
        "                pg.sql_words(signature),\n",
        '                pg.sql_words(""),\n',
        k(
            T_VERIFY_PG,
            "test_step_4_takes_everyones_execute_off_a_function_whose_argument_has_an_odd_name_and_type",
        ),
    ),
    Mutant(
        "V84",
        'Issue 1 of 3d: the code writes "holds" where the CHANGELOG quotes "has" (the message words are stale)',
        VERIFY,
        '                    else f"has {self.right}"\n',
        '                    else f"holds {self.right}"\n',
        (
            k(
                T_VERIFY,
                "test_every_sentence_form_the_changelog_quotes_is_in_the_code_and_is_what_a_line_says",
            ),
        ),
    ),
    Mutant(
        "V85",
        "B6 of 3e: the refusal of a package object that another role owns does not say that no file ran",
        MIG,
        '    unchanged = "Nothing was changed. No file ran."\n',
        '    unchanged = "Nothing was changed."\n',
        k(
            T_MX,
            "test_a_state_made_before_the_run_is_refused_and_no_file_runs[X28-named-role-owns-a-table/with-roles]",
        ),
    ),
    Mutant(
        "V86",
        "B4 of batch 3e: the all-schema oracle leaves one schema out, so a right on an object of another schema is not seen",
        "tests/fixtures/oracle.py",
        "        for schema in self.schemas():\n            one = self.can(role, schema, **merged)\n",
        '        for schema in [s for s in self.schemas() if s != "s"]:\n            one = self.can(role, schema, **merged)\n',
        (
            k(
                T_MX,
                "test_direction_2_sees_an_extra_right_on_an_object_outside_the_schema_of_the_run",
            ),
        ),
    ),
    Mutant(
        "V87",
        "C8 of batch 3e: an object that is a member of an extension is skipped by the check",
        VERIFY,
        '        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        outside =',
        '        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        if it.extension:\n            continue\n        outside =',
        (
            k(
                T_MX,
                "test_c8_an_object_that_is_an_extension_member_is_still_judged[O01-select-other/C8/no-roles]",
            ),
            k(
                T_MX,
                "test_c8_an_object_that_is_an_extension_member_is_still_judged[O01-select-other/C8/with-roles]",
            ),
        ),
    ),
    Mutant(
        "V88",
        "Issue 1 of batch 4: the two session-ending codes of class 25 (25P03, 25P04) are taken as a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CODES = ("25P03", "25P04")\n',
        "_NOT_A_FILES_OWN_CODES = ()\n",
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[25P03-False]",
            ),
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[25P04-False]",
            ),
        ),
    ),
    Mutant(
        "V89",
        "Issue 1 of batch 4: the usable-connection check is left out of the classifier (a dead session with a file-like code is the file's own)",
        MIG,
        "    return bool(code) and not code.startswith(_NOT_A_FILES_OWN_ERROR) and _connection_is_usable(db)\n",
        "    return bool(code) and not code.startswith(_NOT_A_FILES_OWN_ERROR)\n",
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[closed]",
            ),
            k(
                T_VERIFY_PG,
                "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[broken]",
            ),
            k(
                T_VERIFY_PG,
                "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[unknown_status]",
            ),
            k(
                T_VERIFY_PG,
                "test_a_real_files_own_error_leaves_the_connection_usable_and_is_the_files_own",
            ),
        ),
    ),
    Mutant(
        "V90",
        "Issue 7 of batch 4: a lost connection at step 5 gets the wording of a failed deferred check",
        MIG,
        "                        if not _is_a_files_own_error(e, db):\n",
        "                        if False:\n",
        (
            k(
                T_VERIFY_PG,
                "test_a_connection_lost_at_a_statement_the_runner_sends_itself_gives_exit_2_and_keeps_nothing[SET CONSTRAINTS ALL IMMEDIATE]",
            ),
        ),
    ),
    Mutant(
        "V91",
        'Issue 7 of batch 4: the flag "a file is running" is not cleared after the file (a later error with a file-like code stays raw)',
        MIG,
        "                        running_a_file = False\n",
        "                        pass\n",
        (
            k(
                T_VERIFY_PG,
                "test_an_error_of_the_runner_after_the_last_file_is_never_taken_as_the_files_own",
            ),
        ),
    ),
    Mutant(
        "V92",
        "Issue 7 of batch 4: SQLSTATE class 08 is left out of the classes that are never a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58", "XX")\n',
        '_NOT_A_FILES_OWN_CLASSES = ("53", "57", "58", "XX")\n',
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[08006-False]",
            ),
        ),
    ),
    Mutant(
        "V93",
        "Issue 7 of batch 4: SQLSTATE class 53 is left out of the classes that are never a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58", "XX")\n',
        '_NOT_A_FILES_OWN_CLASSES = ("08", "57", "58", "XX")\n',
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[53300-False]",
            ),
        ),
    ),
    Mutant(
        "V94",
        "Issue 7 of batch 4: SQLSTATE class 57 is left out of the classes that are never a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58", "XX")\n',
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "58", "XX")\n',
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[57P01-False]",
            ),
        ),
    ),
    Mutant(
        "V95",
        "Issue 7 of batch 4: SQLSTATE class 58 is left out of the classes that are never a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58", "XX")\n',
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "XX")\n',
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[58030-False]",
            ),
        ),
    ),
    Mutant(
        "V96",
        "Issue 7 of batch 4: SQLSTATE class XX is left out of the classes that are never a file's own error",
        MIG,
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58", "XX")\n',
        '_NOT_A_FILES_OWN_CLASSES = ("08", "53", "57", "58")\n',
        (
            k(
                T_VERIFY_PG,
                "test_the_classifier_knows_which_sqlstates_are_not_a_files_own[XX000-False]",
            ),
        ),
    ),
    Mutant(
        "V97",
        "Issue 1 of batch 4: a connection whose transaction state is UNKNOWN counts as usable",
        MIG,
        " and db.info.transaction_status != TransactionStatus.UNKNOWN\n",
        " and True\n",
        k(
            T_VERIFY_PG,
            "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[unknown_status]",
        ),
    ),
    Mutant(
        "V98",
        "Issue 1 of batch 4: a closed connection counts as usable",
        MIG,
        "        not db.closed and not db.broken and",
        "        True and not db.broken and",
        k(
            T_VERIFY_PG,
            "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[closed]",
        ),
    ),
    Mutant(
        "V99",
        "Issue 1 of batch 4: a broken connection counts as usable",
        MIG,
        "not db.closed and not db.broken and",
        "not db.closed and True and",
        k(
            T_VERIFY_PG,
            "test_the_classifier_never_calls_an_error_on_a_dead_connection_the_files_own[broken]",
        ),
    ),
    Mutant(
        "V100",
        "Issue 4 of batch 4: a finding names the schema where the object's name belongs (the finding names the wrong object)",
        VERIFY,
        "            return Problem(\n                kind,\n                it.schema,\n                it.name,\n                sub,\n                role,",
        "            return Problem(\n                kind,\n                it.schema,\n                it.schema,\n                sub,\n                role,",
        k(
            T_MX,
            "test_c6b_a_trigger_that_defers_itself_again_is_applied_and_reported[O01-select-other/C6b/with-roles]",
        ),
    ),
    Mutant(
        "V101",
        "Issue 2 of batch 4: the strict reading of rule O8 is ON by default (a schema owned outside the family at the start is refused)",
        MIG,
        "ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = False",
        "ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START = True",
        k(
            T_VERIFY,
            "test_the_strict_reading_of_rule_o8_is_off_by_default",
        ),
    ),
    Mutant(
        "V102",
        "Issue 2 of batch 4: the switch is ignored (a schema owner that changed during the run is dropped when the strict reading is off)",
        MIG,
        "        if ENFORCE_O8_FOR_THE_SCHEMA_OWNED_OUTSIDE_THE_FAMILY_AT_THE_START\n        or not (",
        "        if not (",
        (
            k(
                T_VERIFY,
                "test_the_owner_of_the_schema_of_the_run_must_not_change_and_the_strict_reading_is_a_named_switch[admin_x-admin_x-None-True]",
            ),
            k(
                T_MX,
                "test_o8_a_schema_owned_outside_the_family_at_the_start_is_refused_only_with_the_switch_on[switch-on]",
            ),
        ),
    ),
    Mutant(
        "V103",
        "Issue 8 of batch 4: the code writes a longer sentence only where the short form 'has {right}' is quoted (the checker must see it)",
        VERIFY,
        '                    else f"has {self.right}"\n',
        '                    else f"has now {self.right}"\n',
        (
            k(
                T_VERIFY,
                "test_a_sentence_the_changelog_quotes_but_the_code_does_not_write_is_found",
            ),
            k(
                T_VERIFY,
                "test_every_sentence_form_the_changelog_quotes_is_in_the_code_and_is_what_a_line_says",
            ),
        ),
    ),
    # --- round 15 (batch 5): one mutant for each new family of cells, each killed by the real-server test that is named ---
    Mutant(
        "V104",
        "Issue 6 of batch 5: a right of a third role on a table the family owns is no longer refused (rule O1, third-role refusal removed)",
        VERIFY,
        '        elif fam_owned:\n            out.append(make("other_grantee", it.grantee, it.privilege_type))',
        '        elif False:\n            out.append(make("other_grantee", it.grantee, it.privilege_type))',
        k(
            T_MX,
            "test_a_third_role_right_on_a_table_the_family_owns_is_refused_with_no_role_argument",
        ),
    ),
    Mutant(
        "V105",
        "Issue 6 of batch 5: the grant map is matched by name only, so a map table moved to another schema counts as the map table (carrier C13)",
        VERIFY,
        "    if it.schema != schema or it.name not in grant_map:",
        "    if it.name not in grant_map:",
        k(
            T_MX,
            "test_c13_a_map_table_moved_or_renamed_and_made_again_is_refused_and_nothing_is_kept[move-to-another-schema-with-roles]",
        ),
    ),
    Mutant(
        "V106",
        "Issue 6 of batch 5: the rows of an object that is an extension member are skipped (the planted skip; carrier C8 says a member is judged like any object)",
        VERIFY,
        '        in_run = (not it.system) and it.schema == schema\n        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        outside',
        '        in_run = (not it.system) and it.schema == schema\n        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        if it.extension:\n            continue\n        outside',
        k(
            T_MX,
            "test_c8_an_object_that_is_an_extension_member_is_still_judged[O04-sequence-other/C8/with-roles]",
        ),
    ),
    Mutant(
        "V107",
        "Issue 6 of batch 5: the login that differs from the role is not part of the migration role family (carrier C9)",
        VERIFY,
        "        [login_role] if login_role and login_role != migration_role else []",
        "        []",
        k(
            T_MX,
            "test_c9_a_table_owned_by_the_login_is_the_familys_own_so_a_third_role_right_on_it_is_refused",
        ),
    ),
    Mutant(
        "V108",
        "Issue 6 of batch 5: a database owned by a role of the family is not seen as family-owned (variant O)",
        VERIFY,
        "    fam_has_db_owner = rows.database_owner in fam_roles",
        "    fam_has_db_owner = False",
        k(
            T_MX,
            "test_o8_switch_on_the_public_schema_is_family_owned_only_when_the_database_owner_is_the_migration_role",
        ),
    ),
    Mutant(
        "V109",
        "Issue 4 of batch 5: a right for everyone on ANOTHER schema than the schema of the run is not judged (carrier C10, effect O15)",
        VERIFY,
        '            if kind == "schema":\n                if right != "USAGE":',
        '            if kind == "schema":\n                if right != "USAGE" and in_run:',
        k(
            T_MX,
            "test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O15-create-on-schema-everyone/C10-another-schema/no-roles]",
        ),
    ),
    Mutant(
        "V110",
        "Issue 4 of batch 5: a named role may hold any right on a schema (carrier C10, effect O13)",
        VERIFY,
        '    if it.kind == "schema":\n        return it.privilege_type == "USAGE"',
        '    if it.kind == "schema":\n        return True',
        k(
            T_MX,
            "test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O13-create-on-schema-other/C10-another-schema/with-roles]",
        ),
    ),
    Mutant(
        "V111",
        "Issue 4 of batch 5: a default right set for a named role is not refused (carrier C10, effect O16)",
        VERIFY,
        '            out.append(_default("default_for_named", d, right, d.grantee))',
        "            pass",
        k(
            T_MX,
            "test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O16-default-right-named/C10-another-schema/with-roles]",
        ),
    ),
    Mutant(
        "V112",
        "Issue 3 of batch 5: `connect` runs a second setup statement outside every wrapper (the exit-2 promise would start later than the CHANGELOG says)",
        "src/hadavin_sdk/store/postgres.py",
        "        raise\n    return conn",
        '        raise\n    conn.execute("SELECT 1")\n    return conn',
        k(
            T_VERIFY,
            "test_connect_runs_exactly_one_statement_so_the_exit_2_promise_starts_after_it",
        ),
    ),
    Mutant(
        "V118",
        "Issue 4 of batch 6: `connect` sends a second setup statement through a cursor (the form V112 does not plant)",
        "src/hadavin_sdk/store/postgres.py",
        "    try:\n        conn.execute(\"SET TIME ZONE 'UTC'\")\n    except BaseException:",
        '    try:\n        conn.execute("SET TIME ZONE \'UTC\'")\n        conn.cursor().execute("SELECT 1")\n    except BaseException:',
        k(
            T_VERIFY,
            "test_on_a_real_server_connect_sends_exactly_one_statement_through_any_driver_path",
        ),
    ),
    Mutant(
        "V119",
        "Issue 4 of batch 6: `connect` sets a server variable through the connection options",
        "src/hadavin_sdk/store/postgres.py",
        "    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10, **extra)",
        '    extra["options"] = "-c statement_timeout=0"\n    conn = psycopg.connect(dsn, autocommit=True, connect_timeout=10, **extra)',
        k(T_VERIFY, "test_connect_opens_no_cursor_and_sends_no_connection_option"),
    ),
    Mutant(
        "V120",
        "Issue 4 of batch 6: the sign-in branch of IAM adds a connection option",
        "src/hadavin_sdk/store/postgres.py",
        '            extra["password"] = password_source(',
        '            extra["options"] = "-c statement_timeout=0"\n            extra["password"] = password_source(',
        k(
            T_VERIFY,
            "test_connect_with_the_iam_sign_in_runs_one_statement_and_adds_only_the_password",
        ),
    ),
    Mutant(
        "V121",
        "Issue 2 of batch 6: a right of a named role on a sequence is not judged (carrier C13, a sequence that moved out of the map, effect O04)",
        VERIFY,
        "                if _allowed_for(named_roles[n], it, schema, grant_map):\n                    continue",
        '                if _allowed_for(named_roles[n], it, schema, grant_map) or it.kind == "sequence":\n                    continue',
        k(
            T_MX,
            "test_c13_a_sequence_or_function_moved_out_of_the_map_is_judged_like_one_outside_the_map[O04-sequence-other-with-roles]",
        ),
    ),
    Mutant(
        "V116",
        "Issue 3 of batch 6: an error while the connection of the run is made is not turned into the refusal (exit 3 again)",
        MIG,
        "        refusal = _driver_error_before_commit(e, _CONNECTING)\n",
        "        raise\n",
        k(
            T_VERIFY_PG,
            "test_a_setup_statement_that_fails_on_the_first_connection_is_refused_with_exit_2_and_closed",
        ),
    ),
    Mutant(
        "V117",
        "Issue 3 of batch 6: a connection whose setup statement failed is left open",
        "src/hadavin_sdk/store/postgres.py",
        "        with suppress(Exception):  # any error of `close` (r18 group 4), not only the driver's own\n            conn.close()\n",
        "        pass\n",
        k(
            T_VERIFY_PG,
            "test_a_setup_statement_that_fails_on_the_first_connection_is_refused_with_exit_2_and_closed",
        ),
    ),
    Mutant(
        "V113",
        "Issue 1 of batch 6: a default right for everyone that is limited to one schema is not refused (carrier C10, effect O17)",
        VERIFY,
        '            if not built_in:\n                out.append(_default("default_for_everyone", d, right, EVERYONE))',
        '            if not built_in and not d.schema:\n                out.append(_default("default_for_everyone", d, right, EVERYONE))',
        k(
            T_MX,
            "test_every_matrix_cell_ends_in_one_of_the_three_outcomes[O17-default-right-everyone/C10-another-schema/no-roles]",
        ),
    ),
    Mutant(
        "V114",
        "Issue 2 of batch 6: a schema that is an extension member is skipped (carrier C8, effects O13 to O15)",
        VERIFY,
        '        in_run = (not it.system) and it.schema == schema\n        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        outside',
        '        in_run = (not it.system) and it.schema == schema\n        ext = it.extension if (it.extension and not it.extension_family_owned) else ""\n        if it.extension and it.kind == "schema":\n            continue\n        outside',
        k(
            T_MX,
            "test_c8_the_schema_of_the_run_as_an_extension_member_is_still_judged[O13-create-on-schema-other/C8/migration-role-owns-the-schema/no-roles]",
        ),
    ),
    Mutant(
        "V115",
        "Issue 2 of batch 6: a right for everyone on a sequence is not judged (carrier C13, a sequence that moved with its table, effect O11)",
        VERIFY,
        '            if kind in _NOTHING_BY_DEFAULT:\n                out.append(make("everyone", EVERYONE, right))',
        '            if kind in _NOTHING_BY_DEFAULT and kind != "sequence":\n                out.append(make("everyone", EVERYONE, right))',
        k(
            T_MX,
            "test_c13_a_sequence_or_function_moved_out_of_the_map_is_judged_like_one_outside_the_map[O11-everyone-setval-no-roles]",
        ),
    ),
    Mutant(
        "V122",
        "Round 17 group 3: the refusal for a failed cloud sign-in (token step) prints the SDK's own words",
        "src/hadavin_sdk/store/auth_aws.py",
        "            failed = type(exc).__name__\n            transient = is_transient(exc)\n",
        "            failed = str(exc)\n            transient = is_transient(exc)\n",
        (
            k(
                T_VERIFY,
                "test_a_failed_cloud_sign_in_is_a_plain_refusal_that_prints_none_of_the_sdks_words[no-credentials]",
            ),
            k(
                T_VERIFY,
                "test_a_failed_cloud_sign_in_is_a_plain_refusal_that_prints_none_of_the_sdks_words[refused-request]",
            ),
            k(
                T_VERIFY_PG,
                "test_a_failed_cloud_sign_in_at_the_start_is_refused_with_exit_2_and_keeps_nothing",
            ),
        ),
    ),
    Mutant(
        "V123",
        "Round 17 group 3: a refused connection is worded as a rollback (the sentence for the connection step is dropped)",
        MIG,
        "    if step == _CONNECTING:\n        # r17 group 3 (c)",
        "    if False:\n        # r17 group 3 (c)",
        k(
            T_VERIFY_PG,
            "test_an_address_that_cannot_be_reached_is_refused_with_exit_2_with_a_real_driver_error",
        ),
    ),
    Mutant(
        "V124",
        "Round 17 group 4: the refusal prints the class name of the driver error instead of its SQLSTATE",
        MIG,
        '    code = getattr(e, "sqlstate", None) or type(e).__name__\n    if step == _CONNECTING:',
        "    code = type(e).__name__\n    if step == _CONNECTING:",
        (
            k(T_VERIFY_PG, "test_the_refusal_names_the_sqlstate_of_a_session_ending_error[25P03]"),
            k(T_VERIFY_PG, "test_the_refusal_names_the_sqlstate_of_a_session_ending_error[25P04]"),
        ),
    ),
    Mutant(
        "V125",
        "Round 17 group 6: a failing close of the half-made connection hides the first error",
        "src/hadavin_sdk/store/postgres.py",
        "        with suppress(Exception):  # any error of `close` (r18 group 4), not only the driver's own\n            conn.close()\n",
        "        conn.close()\n",
        k(
            T_VERIFY,
            "test_a_close_that_fails_after_a_failed_setup_statement_does_not_hide_the_first_error",
        ),
    ),
    Mutant(
        "V126",
        "Round 17 group 5: the window of the PostgreSQL 17 wording check is cut to nothing",
        T_RULES,
        '    rf"{_PG17_RESULT}\\b[^.;]{{0,40}}?{_PG17_VERSION_RX}|{_PG17_VERSION_RX}[^.;]{{0,40}}?\\b{_PG17_RESULT}\\b",',
        '    rf"{_PG17_RESULT}\\b[^.;]{{0,0}}?{_PG17_VERSION_RX}|{_PG17_VERSION_RX}[^.;]{{0,0}}?\\b{_PG17_RESULT}\\b",',
        (
            k(
                T_RULES,
                "test_the_postgresql_17_wording_check_finds_each_new_form_of_a_result_claim[The suite is green on 17.10.]",
            ),
            k(
                T_RULES,
                "test_the_postgresql_17_wording_check_finds_each_new_form_of_a_result_claim[The case was seen passing on 17.10.]",
            ),
        ),
    ),
    Mutant(
        "V127",
        "Round 17 group 1: the reason of an empty pair is built with another SQLSTATE than its probe's",
        T_MX,
        '    return f"measured on PostgreSQL {MEASURED_ON}: ERROR {probe.state} {probe.shown}"',
        '    return f"measured on PostgreSQL {MEASURED_ON}: ERROR 42000 {probe.shown}"',
        k(
            T_MX,
            "test_every_empty_pair_has_a_probe_and_its_reason_carries_the_state_text_and_version_of_it",
        ),
    ),
    Mutant(
        "V128",
        "Round 17 group 1: the SQLSTATE of the probe for the map objects is edited to a wrong fact",
        T_MX,
        '_NO_REL = ("42P01", "does not exist",',
        '_NO_REL = ("42P05", "does not exist",',
        k(T_MX, "test_every_empty_reason_is_the_answer_of_a_real_server"),
    ),
    Mutant(
        "V129",
        "Round 17 group 5: the old O8 wording condition (the change-of-owner half alone) is accepted again",
        T_RULES,
        "    return _O8_SWITCH in sentence\n",
        '    return _O8_SWITCH in sentence or ("must not change owner" in sentence and "during the run" in sentence)\n',
        k(
            T_RULES,
            "test_the_o8_wording_check_finds_each_sentence_that_keeps_only_part_of_the_condition[The schema must be owned by a family role at the start and must not change owner during the run.]",
        ),
    ),
    Mutant(
        "V130",
        "Round 18 group 1: the token step raises the refusal inside its except block again (the SDK error stays on __context__)",
        AUTH,
        "        except Exception as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n            failed = type(exc).__name__\n",
        "        except Exception as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n            raise _refused(type(exc).__name__) from None\n",
        (
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[runtime-error-token-is-asked-for]",
            ),
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[client-error-token-is-asked-for]",
            ),
            k(
                T_SIGN,
                "test_the_choke_points_raise_no_new_error_inside_an_except_block[src/hadavin_sdk/store/auth_aws.py]",
            ),
        ),
    ),
    Mutant(
        "V131",
        "Round 18 group 1: the client step raises the refusal inside its except block again",
        AUTH,
        "    except Exception as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n        failed = type(exc).__name__\n",
        "    except Exception as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n        raise _refused(type(exc).__name__) from None\n",
        (
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[runtime-error-client-is-built]",
            ),
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[client-error-client-is-built]",
            ),
        ),
    ),
    Mutant(
        "V132",
        "Round 18 group 1: the refusal for a failed sign-in is raised inside the except block of the runner (the sign-in error stays on __context__)",
        MIG,
        '        refusal = ConfigError(\n            f"migrate stopped and kept nothing: while {_CONNECTING}, {e} Nothing was started."',
        '        raise ConfigError(\n            f"migrate stopped and kept nothing: while {_CONNECTING}, {e} Nothing was started."',
        (
            k(
                T_VERIFY_PG,
                "test_a_failed_cloud_sign_in_at_the_start_is_refused_with_exit_2_and_keeps_nothing",
            ),
        ),
    ),
    Mutant(
        "V133",
        "Round 18 group 1: the refusal for a refused connection keeps the driver error as its cause again",
        MIG,
        "        refusal = _driver_error_before_commit(e, _CONNECTING)\n",
        "        raise _driver_error_before_commit(e, _CONNECTING) from e\n",
        (k(T_VERIFY_PG, "test_a_refused_connection_keeps_no_driver_error_on_either_channel"),),
    ),
    Mutant(
        "V134",
        "Round 18 group 1: the store raises its unavailable error inside the except block (the driver error stays on __context__)",
        PGS,
        "        unavailable = exc.__class__.__name__\n",
        '        raise StoreUnavailable(f"store postgres: cannot connect ({exc.__class__.__name__})") from None\n',
        (
            k(
                T_SIGN,
                "test_a_store_that_cannot_connect_names_only_the_class_and_keeps_no_driver_error",
            ),
            k(
                T_SIGN,
                "test_the_choke_points_raise_no_new_error_inside_an_except_block[src/hadavin_sdk/store/postgres.py]",
            ),
        ),
    ),
    Mutant(
        "V135",
        "Round 18 group 4: the close of a half-made connection ignores the driver's errors only",
        PGS,
        "        with suppress(Exception):  # any error of `close` (r18 group 4), not only the driver's own\n",
        "        with suppress(psycopg.Error):  # any error of `close` (r18 group 4), not only the driver's own\n",
        (
            k(
                T_SIGN,
                "test_a_close_that_fails_with_any_error_does_not_hide_the_first_error[OSError]",
            ),
            k(
                T_SIGN,
                "test_a_close_that_fails_with_any_error_does_not_hide_the_first_error[BrokenPipeError]",
            ),
        ),
    ),
    Mutant(
        "V136",
        "Round 18 group 2: the token step converts only OSError (any other error of the sign-in comes out raw)",
        AUTH,
        "        except Exception as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n",
        "        except OSError as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n",
        (
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[runtime-error-token-is-asked-for]",
            ),
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[client-error-token-is-asked-for]",
            ),
        ),
    ),
    Mutant(
        "V137",
        "Round 18 group 2: the client step converts only OSError",
        AUTH,
        "    except Exception as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n",
        "    except OSError as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n",
        (
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[runtime-error-client-is-built]",
            ),
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[boto3-error-client-is-built]",
            ),
        ),
    ),
    Mutant(
        "V138",
        "Round 18 group 2: the token step converts an interrupt too (Exception widened to BaseException)",
        AUTH,
        "        except Exception as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n",
        "        except BaseException as exc:  # noqa: BLE001 - same as above; KeyboardInterrupt and SystemExit are not `Exception` and pass\n",
        (
            k(
                T_SIGN,
                "test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal[KeyboardInterrupt-token-is-asked-for]",
            ),
            k(
                T_SIGN,
                "test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal[SystemExit-token-is-asked-for]",
            ),
        ),
    ),
    Mutant(
        "V139",
        "Round 18 group 2: the client step converts an interrupt too",
        AUTH,
        "    except Exception as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n",
        "    except BaseException as exc:  # noqa: BLE001 - any failure of the sign-in step, not two library types (round 18 group 2); only the class name is kept\n",
        (
            k(
                T_SIGN,
                "test_an_interrupt_during_the_sign_in_is_not_turned_into_a_refusal[KeyboardInterrupt-client-is-built]",
            ),
        ),
    ),
    Mutant(
        "V140",
        "Round 18 group 3: the port range is not checked (only the digits)",
        PGS,
        '    return re.fullmatch(r"[0-9]{1,5}", text) is not None and 1 <= int(text) <= 65535\n',
        '    return re.fullmatch(r"[0-9]{1,5}", text) is not None\n',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[port-0]",
            ),
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[port-65536]",
            ),
        ),
    ),
    Mutant(
        "V141",
        "Round 18 group 3: the port may be written with the digits of another script",
        PGS,
        'r"[0-9]{1,5}"',
        'r"\\d{1,5}"',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[port-other-script]",
            ),
        ),
    ),
    Mutant(
        "V142",
        "Round 18 group 3: a list of hosts is not refused",
        PGS,
        '("more than one host", "," not in host),',
        '("more than one host", True),',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[two-hosts]",
            ),
        ),
    ),
    Mutant(
        "V143",
        "Round 18 group 3: a missing user is not refused",
        PGS,
        '("no user", bool(user)),',
        '("no user", True),',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[no-user]",
            ),
        ),
    ),
    Mutant(
        "V144",
        "Round 18 group 3: a missing host is not refused",
        PGS,
        '("no host", bool(host)),',
        '("no host", True),',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[no-host]",
            ),
        ),
    ),
    Mutant(
        "V145",
        "Round 18 group 3: the refusal of a bad address is never raised (the guard branch is dead)",
        PGS,
        "            if lacking:\n",
        "            if False:\n",
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[port-abc]",
            ),
        ),
    ),
    Mutant(
        "V146",
        "Round 18 group 3: the runner does not turn a failed sign-in into its refusal (the clause for SignInError is dropped)",
        MIG,
        "    except SignInError as e:  # r17 group 3 (b)",
        "    except KeyError as e:  # r17 group 3 (b)",
        (
            k(
                T_VERIFY_PG,
                "test_a_failed_cloud_sign_in_at_the_start_is_refused_with_exit_2_and_keeps_nothing",
            ),
        ),
    ),
    Mutant(
        "V147",
        "Round 18 group 4: the refusal for a bad address names the Python error class again",
        PGS,
        '                    "the sign-in for the database connection cannot start: the address has "\n',
        '                    "the sign-in for the database connection cannot start (KeyError): the address has "\n',
        (
            k(
                T_SIGN,
                "test_an_iam_address_the_sign_in_cannot_be_asked_for_is_refused_by_name_before_any_connection[no-user]",
            ),
        ),
    ),
    Mutant(
        "V148",
        "Round 17 group 3: the refusal for a failed cloud sign-in (client step) prints the SDK's own words",
        AUTH,
        "        failed = type(exc).__name__\n    if failed:\n",
        "        failed = str(exc)\n    if failed:\n",
        (
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[runtime-error-client-is-built]",
            ),
            k(
                T_SIGN,
                "test_a_failed_sign_in_of_any_kind_leaves_no_trace_of_the_sdk_error[client-error-client-is-built]",
            ),
        ),
    ),
    Mutant(
        "V149",
        "Round 19 group 1: the refusal of a failed connection in step 8 is raised inside the except block with from e (the driver error stays on __cause__)",
        MIG,
        "        could_not_connect = type(e).__name__\n",
        "        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e\n",
        (
            k(
                T_STEPS,
                "test_a_connection_that_cannot_be_made_in_step_8_keeps_no_error_on_either_channel",
            ),
            k(T_STEPS, "test_a_sign_in_that_fails_in_step_8_keeps_no_error_on_either_channel"),
            k(
                T_VERIFY_PG,
                "test_a_connection_refused_in_step_8_on_a_real_server_keeps_no_driver_error_on_either_channel",
            ),
        ),
    ),
    Mutant(
        "V150",
        "Round 19 group 1: the refusal of a failed connection in step 8 is raised inside the except block with no from (the driver error stays on __context__)",
        MIG,
        "        could_not_connect = type(e).__name__\n",
        "        raise _after_commit(applied, [], could_not_run=type(e).__name__)\n",
        (
            k(
                T_STEPS,
                "test_a_connection_that_cannot_be_made_in_step_8_keeps_no_error_on_either_channel",
            ),
            k(T_STEPS, "test_a_sign_in_that_fails_in_step_8_keeps_no_error_on_either_channel"),
            k(
                T_VERIFY_PG,
                "test_a_connection_refused_in_step_8_on_a_real_server_keeps_no_driver_error_on_either_channel",
            ),
        ),
    ),
    Mutant(
        "V151",
        "Round 19 group 1: the refusal of a failed connection in step 8 prints the driver's own words",
        MIG,
        "        could_not_connect = type(e).__name__\n",
        "        could_not_connect = str(e)\n",
        (
            k(
                T_STEPS,
                "test_a_connection_that_cannot_be_made_in_step_8_keeps_no_error_on_either_channel",
            ),
            k(T_STEPS, "test_a_sign_in_that_fails_in_step_8_keeps_no_error_on_either_channel"),
            k(
                T_VERIFY_PG,
                "test_a_connection_refused_in_step_8_on_a_real_server_keeps_no_driver_error_on_either_channel",
            ),
        ),
    ),
    Mutant(
        "V152",
        "Round 19 group 1: an error of the check of step 8 (the connection is in place) is no longer turned into the failure report",
        MIG,
        "    except Exception as e:  # any error at all: the commit happened and the check did not finish\n        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e\n",
        "    except KeyError as e:  # any error at all: the commit happened and the check did not finish\n        raise _after_commit(applied, [], could_not_run=type(e).__name__) from e\n",
        (
            k(
                T_STEPS,
                "test_a_check_that_fails_in_step_8_with_the_connection_in_place_is_applied_not_verified",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-8-check]",
            ),
        ),
    ),
    Mutant(
        "V153",
        "Round 19 group 2: `migrate` is not guarded (the one exit of the rule is not applied)",
        MIG,
        "@_keeps_no_driver_error\ndef migrate(\n",
        "def migrate(\n",
        (
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-4-statement]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-5-deferred-check]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-7-commit-refused]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-8-check]",
            ),
            k(T_CHAN, "test_migrate_is_wrapped_and_keeps_its_signature_and_its_text"),
        ),
    ),
    Mutant(
        "V154",
        "Round 19 group 2: the guard leaves __context__ in place",
        MIG,
        "                err.__context__ = None\n",
        "",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-implicit-config]",
            ),
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-nested-config]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-5-session-ended]",
            ),
        ),
    ),
    Mutant(
        "V155",
        "Round 19 group 2: the guard leaves __cause__ in place",
        MIG,
        "                err.__cause__ = None\n",
        "",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-from-e-config]",
            ),
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-from-e-applied-not-verified]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-4-statement]",
            ),
        ),
    ),
    Mutant(
        "V156",
        "Round 19 group 2: the guard hides the chain from the printed traceback only (__suppress_context__ stays True)",
        MIG,
        "                err.__suppress_context__ = False\n",
        "                err.__suppress_context__ = True\n",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-from-e-config]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-6-check-could-not-run]",
            ),
        ),
    ),
    Mutant(
        "V157",
        "Round 19 group 2: the guard handles a ConfigError only (a failure report is not guarded)",
        MIG,
        "        except Exception as err:\n",
        "        except ConfigError as err:\n",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-from-e-applied-not-verified]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-7-commit-unknown]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-8-check]",
            ),
        ),
    ),
    Mutant(
        "V158",
        "Round 19 group 2: the search for a driver error looks at the first links only (not behind another refusal)",
        MIG,
        "        todo += [e.__cause__, e.__context__]\n    return False",
        "        pass\n    return False",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[operational-nested-config]",
            ),
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[unique-violation-nested-applied-not-verified]",
            ),
        ),
    ),
    Mutant(
        "V159",
        "Round 19 group 2: only one class of driver error is recognised (not every psycopg.Error)",
        MIG,
        "        if isinstance(e, psycopg.Error) and not _is_a_limit_error(e):",
        "        if isinstance(e, pg_errors.OperationalError) and not _is_a_limit_error(e):",
        (
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[unique-violation-from-e-config]",
            ),
            k(
                T_CHAN,
                "test_a_refusal_made_from_a_driver_error_keeps_it_on_no_channel[check-violation-implicit-config]",
            ),
            k(
                T_STEPS,
                "test_no_refusal_of_migrate_keeps_a_driver_error_on_either_channel[step-5-deferred-check]",
            ),
        ),
    ),
    Mutant(
        "V160",
        "Round 19 group 2: the guard drops the cause of any refusal (also one that is not a driver error)",
        MIG,
        "            if not isinstance(err, psycopg.Error) and _driver_error_in_chain(err):",
        "            if not isinstance(err, psycopg.Error):",
        (k(T_CHAN, "test_an_error_that_is_not_a_driver_error_keeps_its_cause"),),
    ),
    Mutant(
        "V161",
        "Round 19 group 2: the guard also clears the chain of the driver's own error (a migration file's failure)",
        MIG,
        "            if not isinstance(err, psycopg.Error) and _driver_error_in_chain(err):",
        "            if _driver_error_in_chain(err):",
        (k(T_CHAN, "test_a_raw_driver_error_of_a_migration_file_passes_through_unchanged"),),
    ),
    Mutant(
        "V162",
        "Round 19 group 2: a lock wait or a statement limit is not recognised (its cause is dropped too)",
        MIG,
        "    return isinstance(e, pg_errors.LockNotAvailable | pg_errors.QueryCanceled)\n",
        "    return False\n",
        (
            k(
                T_CHAN,
                "test_a_lock_wait_or_a_statement_limit_is_still_kept_as_the_cause[LockNotAvailable]",
            ),
            k(
                T_CHAN,
                "test_a_lock_wait_or_a_statement_limit_is_still_kept_as_the_cause[QueryCanceled]",
            ),
        ),
    ),
    Mutant(
        "V163",
        "Round 19 group 2: only a lock wait is recognised as a limit (a statement limit is dropped)",
        MIG,
        "    return isinstance(e, pg_errors.LockNotAvailable | pg_errors.QueryCanceled)\n",
        "    return isinstance(e, pg_errors.LockNotAvailable)\n",
        (
            k(
                T_CHAN,
                "test_a_lock_wait_or_a_statement_limit_is_still_kept_as_the_cause[QueryCanceled]",
            ),
        ),
    ),
    Mutant(
        "V164",
        "Round 19 group 2: a limit error next to a row-value error is kept (the check stops at the first limit error)",
        MIG,
        "        if isinstance(e, psycopg.Error) and not _is_a_limit_error(e):\n            return True\n",
        "        if isinstance(e, psycopg.Error):\n            return not _is_a_limit_error(e)\n",
        (
            k(
                T_CHAN,
                "test_a_chain_that_holds_a_limit_error_and_another_driver_error_keeps_neither",
            ),
        ),
    ),
    Mutant(
        "V165",
        "Round 19 group 2: a new `raise ... from e` is added to a function that is not on the written list",
        MIG,
        "        if (plain := _limit_error(e, step)) is not None:\n            raise plain from e\n",
        "        if (plain := _limit_error(e, step)) is not None:\n            raise plain from e\n        if False:\n            raise plain from e\n",
        (
            k(
                T_CHAN,
                "test_every_raise_from_of_migrate_is_on_the_written_list_or_is_one_of_the_guarded_driver_sites",
            ),
        ),
    ),
    Mutant(
        "V166",
        "Round 19 group 3: a timeout or a lost network is not transient",
        AUTH,
        "        OSError\n        | botocore_errors.ConnectionError\n",
        "        botocore_errors.ConnectionError\n",
        (
            k(
                T_CHAN,
                "test_the_classifier_calls_a_timeout_a_lost_network_or_a_throttle_transient[os-error]",
            ),
            k(
                T_CHAN,
                "test_the_classifier_calls_a_timeout_a_lost_network_or_a_throttle_transient[timeout]",
            ),
        ),
    ),
    Mutant(
        "V167",
        "Round 19 group 3: a throttling code is read the wrong way round",
        AUTH,
        "in THROTTLING_CODES",
        "not in THROTTLING_CODES",
        (
            k(
                T_CHAN,
                "test_the_classifier_calls_a_timeout_a_lost_network_or_a_throttle_transient[throttled]",
            ),
            k(
                T_CHAN,
                "test_the_classifier_does_not_call_a_missing_login_or_a_refusal_transient[unknown-code]",
            ),
        ),
    ),
    Mutant(
        "V168",
        "Round 19 group 3: the token step does not pass the transient flag on",
        AUTH,
        "        raise _refused(failed, transient)\n",
        "        raise _refused(failed)\n",
        (
            k(
                T_CHAN,
                "test_a_transient_sign_in_failure_while_the_store_is_built_is_store_unavailable_by_class_name[timeout]",
            ),
            k(
                T_CHAN,
                "test_a_transient_sign_in_failure_while_the_store_is_built_is_store_unavailable_by_class_name[throttled]",
            ),
        ),
    ),
    Mutant(
        "V169",
        "Round 19 group 3: every failure of the token step is called transient",
        AUTH,
        "            transient = is_transient(exc)\n",
        "            transient = True\n",
        (
            k(
                T_CHAN,
                "test_a_sign_in_failure_that_a_second_try_cannot_cure_stays_the_refusal_of_exit_2[runtime-error]",
            ),
            k(
                T_CHAN,
                "test_a_sign_in_failure_that_a_second_try_cannot_cure_stays_the_refusal_of_exit_2[access-denied]",
            ),
        ),
    ),
    Mutant(
        "V170",
        "Round 19 group 3: the store build does not turn a transient sign-in failure into StoreUnavailable (the clause is dropped)",
        PGS,
        "    except SignInError as exc:\n        # r19 group 3",
        "    except KeyError as exc:\n        # r19 group 3",
        (
            k(
                T_CHAN,
                "test_a_transient_sign_in_failure_while_the_store_is_built_is_store_unavailable_by_class_name[os-error]",
            ),
            k(
                T_CHAN,
                "test_the_kill_switch_says_not_set_run_again_exit_4_for_a_transient_sign_in_failure[stop-os-error]",
            ),
        ),
    ),
    Mutant(
        "V171",
        "Round 19 group 3: the store build turns every sign-in failure into StoreUnavailable",
        PGS,
        "        if not exc.transient:\n            raise\n",
        "        if False:\n            raise\n",
        (
            k(
                T_CHAN,
                "test_a_sign_in_failure_that_a_second_try_cannot_cure_stays_the_refusal_of_exit_2[runtime-error]",
            ),
            k(
                T_CHAN,
                "test_the_kill_switch_keeps_exit_2_for_a_sign_in_failure_that_is_not_transient[stop]",
            ),
        ),
    ),
    Mutant(
        "V172",
        "Round 19 group 3: the store unavailable message holds the sign-in error's own text",
        PGS,
        '        unavailable = exc.kind or "SignInError"\n',
        "        unavailable = str(exc)\n",
        (
            k(
                T_CHAN,
                "test_a_transient_sign_in_failure_while_the_store_is_built_is_store_unavailable_by_class_name[timeout]",
            ),
        ),
    ),
    Mutant(
        "V173",
        "Round 19 group 8: the refusal for an unreadable DSN prints the driver's own words",
        PGS,
        '        failed = type(exc).__name__\n    raise ConfigError(\n        f"store postgres: the database address',
        '        failed = str(exc)\n    raise ConfigError(\n        f"store postgres: the database address',
        (
            k(
                T_CHAN,
                "test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path[word-without-equals]",
            ),
        ),
    ),
    Mutant(
        "V174",
        "Round 19 group 8: the refusal for an unreadable DSN is raised inside the except block (the driver error stays on __context__)",
        PGS,
        '        failed = type(exc).__name__\n    raise ConfigError(\n        f"store postgres: the database address',
        '        raise ConfigError("store postgres: the database address (the DSN) is not a valid connection string (" + type(exc).__name__ + "); the words of the driver\'s error are not shown because they can quote part of the address.")\n    raise ConfigError(\n        f"store postgres: the database address',
        (
            k(
                T_CHAN,
                "test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path[word-without-equals]",
            ),
        ),
    ),
    Mutant(
        "V175",
        "Round 19 group 8: `tls_mode` reads the DSN with the driver directly",
        PGS,
        "    return _tls_mode_of(dsn_parts(dsn), iam_auth",
        "    return _tls_mode_of(conninfo_to_dict(dsn), iam_auth",
        (
            k(
                T_CHAN,
                "test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path[word-without-equals]",
            ),
        ),
    ),
    Mutant(
        "V176",
        "Round 19 group 8: `connect` reads the DSN with the driver directly",
        PGS,
        "    parts = dsn_parts(\n        dsn\n    )  # read once (r19 group 8): an address that cannot be read is refused before anything else\n",
        "    parts = conninfo_to_dict(dsn)\n",
        (
            k(
                T_CHAN,
                "test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path[word-without-equals]",
            ),
        ),
    ),
    Mutant(
        "V177",
        "Round 19 group 8: the store build (IAM) reads the DSN with the driver directly",
        PGS,
        'settings.iam_auth and dsn_parts(dsn).get("password")',
        'settings.iam_auth and conninfo_to_dict(dsn).get("password")',
        (
            k(
                T_CHAN,
                "test_a_dsn_that_cannot_be_read_is_a_plain_refusal_by_class_name_on_every_path[word-without-equals]",
            ),
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
    problems += _stale_ids(root, {m.name for m in M})
    return problems


# A mutant id in a test docstring ("Killed by: mutant X", "mutants X and Y") or a part of the parametrize id of a killer
# that no mutant has any more is a stale claim: the cheap check finds it (ticket P3a-2, round 2 of commit 3c, Issue 17).
_DOC_CLAIM = re.compile(r"(?:Killed by|killed by|mutants?)\b(.{0,300}?)(?:\.\s|\.$|$)", re.DOTALL)
_ID_WORD = re.compile(r"\b([A-Z]{1,4}\d{1,3}[a-z]?)\b")


def _stale_ids(root: Path, known: set[str]) -> list[str]:
    problems = []
    files = {k.partition("::")[0] for m in M for k in killers_of(m)}
    for path in sorted(files):
        full = root / path
        if not full.is_file():
            continue
        text = full.read_text(encoding="utf-8")
        for fn in ast.walk(ast.parse(text)):
            if not isinstance(fn, ast.FunctionDef) or not fn.name.startswith("test_"):
                continue
            doc = ast.get_docstring(fn) or ""
            for claim in _DOC_CLAIM.finditer(doc):
                for word in _ID_WORD.findall(claim.group(1)):
                    if word not in known:
                        problems.append(
                            f"{path}::{fn.name}: the docstring names the mutant {word}, which is not in the list"
                        )
        for m in M:
            for killer in killers_of(m):
                kpath, _, test = killer.partition("::")
                if kpath != path or "[" not in test:
                    continue
                inside = test.split("[", 1)[1].rstrip("]")
                if "matrix" in kpath:
                    continue  # the ids of the matrix are made from its cells (checked by the matrix test itself)
                for part in inside.split("-"):
                    if re.fullmatch(r"-?\d+|[a-z]+\d+", part):
                        continue  # a number or an id that pytest made itself (`other2`)
                    if part not in text:
                        problems.append(
                            f"{m.name}: the parametrize id part '{part}' of {killer} is not in {kpath}"
                        )
    return problems


_V_ID = re.compile(r"V[0-9]+")


def batches() -> list[list[str]]:
    """The whole list of mutant ids in four disjoint batches that together cover it (ticket P3a-2, 7.10), so the four runs
    of the final head can follow one another and each stays under the time limit of a heavy slot. Batch 1: the `V` mutants
    of the new check (`V01` and on). Batch 2: `BATCH_2_IDS` (the re-pointed and re-checked ones) that are not in batch 1.
    Batches 3 and 4: every other id, in the order of the list, the first half and the second half."""
    names = [m.name for m in M]
    first = [n for n in names if _V_ID.fullmatch(n)]
    second = [n for n in names if n in BATCH_2_IDS and n not in first]
    rest = [n for n in names if n not in first and n not in second]
    half = (len(rest) + 1) // 2
    return [first, second, rest[:half], rest[half:]]


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--list-batch":
        if len(argv) != 2 or argv[1] not in {"1", "2", "3", "4"}:
            print("STOP: --list-batch needs one number from 1 to 4")
            return 2
        print(",".join(batches()[int(argv[1]) - 1]))
        return 0
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
