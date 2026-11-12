"""The mutants of the inbound ledger (AK-G2-a: keys, receiving, the store methods in memory and in PostgreSQL, the migration, the role grants),
run by the P1m runner (``tools/mutation_runner.py``), in the style of ``tests/stage_mutants.py``.

Each mutant reverts or bends ONE guard in a temp copy of the package. The test in ``killer`` (of ``test_file``) must fail, and its
first failing line must hold ``expect`` (a fragment of the assertion message). Mutants of the message routing (dispatch, classify,
start of a run) are NOT here: they wait for AK1-a (see the pull request body). Not collected by pytest. Needs a PostgreSQL for the
database mutants (HADAVIN_TEST_PG_DSN, a login that can create roles); without it a database killer would be SKIPPED and so look
like a surviving mutant, which is why the script refuses to run without the variable. Run from the repo root:

    HADAVIN_TEST_PG_DSN=postgresql://... python tests/inbound_ledger_mutants.py          # all; exit 1 if any is not good
    HADAVIN_TEST_PG_DSN=... python tests/inbound_ledger_mutants.py L3                    # only names holding the text
"""

import os
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1])
)  # the repo root: tools.* is not installed

import tools.mutation_runner as runner
from tools.mutation_runner import Mutant, run_mutants

ROOT = Path(__file__).resolve().parents[1]
# The runner passes only the variables in CHILD_ENV to the test child (never the caller's secrets). The database killers need ONE
# more: the test database address. When the runner grows a per-call ``pass_env`` argument this line is replaced by it.
runner.CHILD_ENV = (*runner.CHILD_ENV, "HADAVIN_TEST_PG_DSN")

LEDGER_T = "tests/test_inbound_ledger.py"
CONTRACT_T = "tests/contracts/test_store_inbound.py"
PG_T = "tests/test_inbound_postgres.py"
LEDGER = "src/hadavin_sdk/triggers/ledger.py"
MEM = "src/hadavin_sdk/store/memory.py"
PG = "src/hadavin_sdk/store/postgres.py"
SQL = "src/hadavin_sdk/store/migrations/0006_inbound.sql"
MIG = "src/hadavin_sdk/store/migrate.py"

_PIN_PREFIX = {
    LEDGER_T: "tests/test_inbound_ledger::",
    CONTRACT_T: "tests/contracts/test_store_inbound::",
    PG_T: "tests/test_inbound_postgres::",
}


def mu(name, file, old, new, test_file, killer, expect, pin_suffix=""):
    """One mutant: `killer` is the test function that must be the first failing one; `pin_suffix` is the parameter id when the killer is parametrized (``[postgres]``)."""
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test_file,
        only_test=killer,
        pinned=_PIN_PREFIX[test_file] + killer + pin_suffix,
    )


M = [
    # --- keys and the sender id (triggers/ledger.py): memory only, no database ------------------------------------------
    mu(
        "L1 tenant_key drops its length prefix",
        LEDGER,
        "f\"{len(p.encode('utf-8'))}:{p}\"",
        'f"{p}"',
        LEDGER_T,
        "test_property_the_delivery_key_separates_every_tenant_source_id_triple",
        "XXXX",
    ),
    mu(
        "L2 the key-derivation label changes",
        LEDGER,
        'b"hadavin-inbound-key-v1"',
        'b"hadavin-inbound-key-v2"',
        LEDGER_T,
        "test_l19_golden_literals",
        "XXXX",
    ),
    mu(
        "L3 a given key is ignored (plain hash)",
        LEDGER,
        "    if key:\n        return hmac.new",
        "    if False:\n        return hmac.new",
        LEDGER_T,
        "test_l19_golden_literals",
        "XXXX",
    ),
    mu(
        "L4 the run id's generation part is 3 characters",
        LEDGER,
        'format(generation, "04x")',
        'format(generation, "03x")',
        LEDGER_T,
        "test_l19_golden_literals",
        "XXXX",
    ),
    mu(
        "L5 the key check is 12 characters",
        LEDGER,
        "_h(key, _CHECK_LABEL)[:16]",
        "_h(key, _CHECK_LABEL)[:12]",
        LEDGER_T,
        "test_l19_golden_literals",
        "XXXX",
    ),
    mu(
        "L6 a subclass of str is accepted as a sender id",
        LEDGER,
        "type(x) is not str",
        "not isinstance(x, str)",
        LEDGER_T,
        "test_l18_a_bad_sender_id_is_refused_before_any_store_call",
        "XXXX",
    ),
    mu(
        "L7 an empty sender id is accepted",
        LEDGER,
        "not 1 <= len(x) <=",
        "not 0 <= len(x) <=",
        LEDGER_T,
        "test_l18_a_bad_sender_id_is_refused_before_any_store_call",
        "XXXX",
    ),
    mu(
        "L8 invisible characters are accepted in a sender id",
        LEDGER,
        'startswith("C")',
        'startswith("Cc")',
        LEDGER_T,
        "test_l18_a_bad_sender_id_is_refused_before_any_store_call",
        "XXXX",
    ),
    mu(
        "L9 the sender id is not checked before the store call",
        LEDGER,
        "        check_sender_id(sender_id)  # the choke point: before any store call\n",
        "",
        LEDGER_T,
        "test_l18_a_bad_sender_id_is_refused_before_any_store_call",
        "XXXX",
    ),
    mu(
        "L10 a changed key is not reported on the first call",
        LEDGER,
        'if result == "key_changed":',
        'if result == "never":',
        LEDGER_T,
        "test_a_changed_key_refuses_the_receive_and_the_message_names_no_key",
        "XXXX",
    ),
    mu(
        "L11 id reuse at the cap is reported as plain id reuse",
        LEDGER,
        '"id_reuse_capped" if again == "conflict_capped" else "id_reuse"',
        '"id_reuse"',
        CONTRACT_T,
        "test_l3_id_reuse_keeps_the_first_and_caps_at_eight",
        "XXXX",
    ),
    # --- memory store ----------------------------------------------------------------------------------------------
    mu(
        "L12 memory: a new receipt may carry a later update time",
        MEM,
        "            or rec.updated_at != rec.received_at\n",
        "",
        CONTRACT_T,
        "test_l22_every_written_time_is_the_injected_time",
        "XXXX",
    ),
    mu(
        "L13 memory: a changed key check is not refused",
        MEM,
        "if stored != rec.key_check:",
        "if False:",
        CONTRACT_T,
        "test_l20_key_change_writes_nothing_and_only_dispatch_changes_the_check",
        "XXXX",
    ),
    mu(
        "L14 memory: same id with other text is a duplicate",
        MEM,
        'return "duplicate" if found.body_sha256 == rec.body_sha256 else "conflict"',
        'return "duplicate"',
        CONTRACT_T,
        "test_l3_id_reuse_keeps_the_first_and_caps_at_eight",
        "XXXX",
    ),
    mu(
        "L15 memory: the reuse cap lets a ninth row in",
        MEM,
        "if reuse_rows >= max_reuse:",
        "if reuse_rows > max_reuse:",
        CONTRACT_T,
        "test_l3_id_reuse_keeps_the_first_and_caps_at_eight",
        "XXXX",
    ),
    mu(
        "L16 memory: the open cap lets one more in",
        MEM,
        "if open_rows >= max_open:",
        "if open_rows > max_open:",
        CONTRACT_T,
        "test_l11_busy_counts_open_receipts_of_this_address_only",
        "XXXX",
    ),
    mu(
        "L17 memory: a claimed receipt does not count as open",
        MEM,
        "and r.state in INBOUND_OPEN_STATES\n",
        'and r.state == "received"\n',
        CONTRACT_T,
        "test_l11_busy_counts_open_receipts_of_this_address_only",
        "XXXX",
    ),
    mu(
        "L18 memory: a claim whose lease ends right now is not reclaimed late",
        MEM,
        "and r.lease_until < now\n",
        "and r.lease_until < now - timedelta(seconds=1)\n",
        CONTRACT_T,
        "test_l6_lease_expiry_reclaims_and_counts_one_try",
        "XXXX",
    ),
    mu(
        "L19 memory: a reclaim after lease expiry does not count a try",
        MEM,
        '"attempts": r.attempts + (1 if r.state == "claimed" else 0),',
        '"attempts": r.attempts,',
        CONTRACT_T,
        "test_l6_lease_expiry_reclaims_and_counts_one_try",
        "XXXX",
    ),
    mu(
        "L20 memory: claim takes the newest first",
        MEM,
        "key=lambda r: (r.received_at, r.delivery_key),",
        "key=lambda r: (-r.received_at.timestamp(), r.delivery_key),",
        CONTRACT_T,
        "test_l6_lease_expiry_reclaims_and_counts_one_try",
        "XXXX",
    ),
    mu(
        "L21 memory: finish ignores the claim token",
        MEM,
        'if r.state != "claimed" or r.claim_token != token:',
        'if r.state != "claimed":',
        CONTRACT_T,
        "test_l7_finish_is_a_compare_and_set",
        "XXXX",
    ),
    mu(
        "L22 memory: finish accepts any reason",
        MEM,
        "if state not in INBOUND_FINAL_STATES or not inbound_reason_allowed(state, reason):",
        "if state not in INBOUND_FINAL_STATES:",
        CONTRACT_T,
        "test_l9_finish_refuses_a_bad_state_or_reason_and_writes_nothing",
        "XXXX",
    ),
    mu(
        "L23 memory: audit_unavailable counts a try as well",
        MEM,
        '"attempts": r.attempts + (1 if reason == "step_error" else 0),',
        '"attempts": r.attempts + 1,',
        CONTRACT_T,
        "test_l9_release_counts_step_error_but_not_audit_unavailable",
        "XXXX",
    ),
    mu(
        "L24 memory: release accepts any reason",
        MEM,
        'if reason not in INBOUND_RETRY_REASONS:\n            raise ValueError("inbound release',
        'if False:\n            raise ValueError("inbound release',
        CONTRACT_T,
        "test_l9_release_counts_step_error_but_not_audit_unavailable",
        "XXXX",
    ),
    mu(
        "L25 memory: the owner's re-run ignores an open run",
        MEM,
        "if run is not None and run.state in OPEN_STATES:",
        "if False:",
        CONTRACT_T,
        "test_l16_reopen_through_the_owner_raises_the_generation_and_gives_a_new_run_id",
        "XXXX",
    ),
    mu(
        "L26 memory: purge drops texts only when they are past the ceiling",
        MEM,
        "if r.updated_at < ceiling or aged:",
        "if aged:",
        CONTRACT_T,
        "test_l13_purge_rules",
        "XXXX",
    ),
    mu(
        "L27 memory: purge forgets that a person-waiting run keeps the text",
        MEM,
        "held = OPEN_STATES | {RunState.NEEDS_PERSON, RunState.STOPPED}",
        "held = OPEN_STATES",
        CONTRACT_T,
        "test_l13_purge_rules",
        "XXXX",
    ),
    mu(
        "L28 memory: purge may delete the text of an open receipt",
        MEM,
        "if r is None or r.state not in INBOUND_FINAL_STATES:\n                    continue",
        "if r is None:\n                    continue",
        CONTRACT_T,
        "test_l13_purge_rules",
        "XXXX",
    ),
    mu(
        "L29 memory: the key check moves without the old value",
        MEM,
        "if stored != old:\n                raise StaleState",
        "if False:\n                raise StaleState",
        CONTRACT_T,
        "test_l20_key_change_writes_nothing_and_only_dispatch_changes_the_check",
        "XXXX",
    ),
    # --- PostgreSQL store (store/postgres.py) -----------------------------------------------------------------------
    mu(
        "P1 pg: a claimed receipt does not count as open",
        PG,
        "\"AND state IN ('received', 'claimed')\",",
        "\"AND state IN ('received')\",",
        CONTRACT_T,
        "test_l11_busy_counts_open_receipts_of_this_address_only",
        "XXXX",
    ),
    mu(
        "P2 pg: the reuse cap lets a ninth row in",
        PG,
        "if n >= max_reuse:",
        "if n > max_reuse:",
        CONTRACT_T,
        "test_l3_id_reuse_keeps_the_first_and_caps_at_eight",
        "XXXX",
    ),
    mu(
        "P3 pg: claim does not lock the row it picks",
        PG,
        "ORDER BY received_at, delivery_key LIMIT 1 FOR UPDATE SKIP LOCKED)",
        "ORDER BY received_at, delivery_key LIMIT 1)",
        PG_T,
        "test_l5_every_receipt_is_claimed_exactly_once_by_8_processes",
        "XXXX",
    ),
    mu(
        "P4 pg: a reclaim after lease expiry does not count a try",
        PG,
        "attempts = r.attempts + CASE WHEN r.state = 'claimed' THEN 1 ELSE 0 END",
        "attempts = r.attempts",
        CONTRACT_T,
        "test_l6_lease_expiry_reclaims_and_counts_one_try",
        "XXXX",
    ),
    mu(
        "P5 pg: finish ignores the claim token",
        PG,
        '"claim_token = NULL, updated_at = %(now)s WHERE tenant = %(tenant)s AND source = %(source)s "\n                "AND delivery_key = %(delivery_key)s AND state = \'claimed\' AND claim_token = %(token)s "',
        '"claim_token = NULL, updated_at = %(now)s WHERE tenant = %(tenant)s AND source = %(source)s "\n                "AND delivery_key = %(delivery_key)s AND state = \'claimed\' "',
        CONTRACT_T,
        "test_l7_finish_is_a_compare_and_set",
        "XXXX",
    ),
    mu(
        "P6 pg: audit_unavailable counts a try as well",
        PG,
        'THEN 1 ELSE 0 END, "\n                "updated_at = %(now)s WHERE',
        'THEN 1 ELSE 1 END, "\n                "updated_at = %(now)s WHERE',
        CONTRACT_T,
        "test_l9_release_counts_step_error_but_not_audit_unavailable",
        "XXXX",
    ),
    mu(
        "P7 pg: purge may delete the text of an open receipt",
        PG,
        "AND r.state IN ('done', 'needs_person', 'refused') ",
        "AND r.state IN ('done', 'needs_person', 'refused', 'received') ",
        CONTRACT_T,
        "test_l13_purge_rules",
        "XXXX",
    ),
    mu(
        "P8 pg: purge forgets that a person-waiting run keeps the text",
        PG,
        "'NEEDS_PERSON', 'STOPPED'))))))",
        "'NEEDS_PERSON'))))))",
        CONTRACT_T,
        "test_l13_purge_rules",
        "XXXX",
    ),
    mu(
        "P9 pg: a key change between the read and the insert is an error, not key_changed",
        PG,
        'if exc.diag.message_primary == "inbound_key_changed":',
        'if exc.diag.message_primary == "never":',
        PG_T,
        "test_l25_iv_a_key_change_between_the_read_and_the_insert_is_key_changed_and_writes_nothing",
        "XXXX",
    ),
    mu(
        "P10 pg: the first receive may overwrite the key check",
        PG,
        '"ON CONFLICT (tenant, source) DO NOTHING",',
        '"ON CONFLICT (tenant, source) DO UPDATE SET key_check = EXCLUDED.key_check",',
        CONTRACT_T,
        "test_l20_key_change_writes_nothing_and_only_dispatch_changes_the_check",
        "XXXX",
    ),
    mu(
        "P11 pg: a changed key check is not refused by the read",
        PG,
        'if stored is None or stored["key_check"] != rec.key_check:',
        "if stored is None:",
        PG_T,
        "test_l25_iv_a_key_change_between_the_read_and_the_insert_is_key_changed_and_writes_nothing",
        "XXXX",
    ),
    mu(
        "P12 pg: a missing receipt is reported as a stale claim",
        PG,
        "return StaleState(stale) if exists else NotFound(delivery_key)",
        "return StaleState(stale)",
        CONTRACT_T,
        "test_l7_finish_is_a_compare_and_set",
        "XXXX",
    ),
    mu(
        "P13 pg: the re-run refusal is not mapped",
        PG,
        'raise RerunRefused("rerun_owner_only") from None',
        "raise",
        PG_T,
        "test_l15_a_the_reopen_move_is_refused_to_dispatch_door_and_runtime_and_the_row_is_unchanged",
        "XXXX",
    ),
    # --- migration 0006 (the database rules) -------------------------------------------------------------------------
    mu(
        "S1 sql: the key check of a receipt may change",
        SQL,
        "       OR NEW.key_check IS DISTINCT FROM OLD.key_check OR NEW.readers IS DISTINCT FROM OLD.readers\n",
        "       OR NEW.readers IS DISTINCT FROM OLD.readers\n",
        PG_T,
        "test_l15_h_an_immutable_column_cannot_change_even_for_the_migrator",
        "XXXX",
    ),
    mu(
        "S2 sql: the text hash of a receipt may change",
        SQL,
        "OR NEW.body_sha256 IS DISTINCT FROM OLD.body_sha256",
        "",
        PG_T,
        "test_l15_h_an_immutable_column_cannot_change_even_for_the_migrator",
        "XXXX",
    ),
    mu(
        "S3 sql: any login may re-run a message",
        SQL,
        "IF owner_name IS NULL OR current_user <> owner_name THEN",
        "IF FALSE THEN",
        PG_T,
        "test_l15_a_the_reopen_move_is_refused_to_dispatch_door_and_runtime_and_the_row_is_unchanged",
        "XXXX",
    ),
    mu(
        "S4 sql: a re-run is allowed while the run is open",
        SQL,
        "IF EXISTS (SELECT 1 FROM runs WHERE run_id = OLD.run_id AND state IN",
        "IF FALSE AND EXISTS (SELECT 1 FROM runs WHERE run_id = OLD.run_id AND state IN",
        PG_T,
        "test_l15_b_the_owner_is_refused_while_the_run_is_in_any_open_state",
        "XXXX",
    ),
    mu(
        "S5 sql: a re-run keeps the old try count",
        SQL,
        "OR NEW.attempts <> 0 OR NEW.reason IS NOT NULL OR NEW.last_reason IS NOT NULL\n",
        "OR NEW.reason IS NOT NULL OR NEW.last_reason IS NOT NULL\n",
        PG_T,
        "test_l15_h_a_reopen_must_raise_the_generation_by_one_and_spell_the_new_run_id",
        "XXXX",
    ),
    mu(
        "S6 sql: the try count may go down",
        SQL,
        "IF NEW.attempts < OLD.attempts THEN",
        "IF FALSE THEN",
        PG_T,
        "test_l15_h_attempts_cannot_go_down",
        "XXXX",
    ),
    mu(
        "S7 sql: a received receipt may jump to done",
        SQL,
        "(OLD.state = 'received' AND NEW.state = 'claimed')",
        "(OLD.state = 'received' AND NEW.state IN ('claimed', 'done'))",
        LEDGER_T,
        "test_the_memory_state_map_equals_the_migration_trigger_move_list",
        "XXXX",
    ),
    mu(
        "S8 sql: an insert with another key check is accepted",
        SQL,
        "IF stored IS NULL OR NEW.key_check <> stored THEN",
        "IF stored IS NULL THEN",
        PG_T,
        "test_l25_iv_a_key_change_between_the_read_and_the_insert_is_key_changed_and_writes_nothing",
        "XXXX",
    ),
    mu(
        "S9 sql: an insert may carry a later update time",
        SQL,
        " OR NEW.updated_at <> NEW.received_at THEN",
        " THEN",
        PG_T,
        "test_l24_door_the_two_legal_shapes_succeed_and_a_first_non_hex_check_is_refused",
        "XXXX",
    ),
    mu(
        "S10 sql: a new receipt may carry any run id",
        SQL,
        "\n       AND NEW.run_id = 'run-' || substr(NEW.delivery_key, 1, 28) || '0000' THEN\n        RETURN NEW;",
        " THEN\n        RETURN NEW;",
        PG_T,
        "test_l24_door_the_two_legal_shapes_succeed_and_a_first_non_hex_check_is_refused",
        "XXXX",
    ),
    mu(
        "S11 sql: a text may be added to a receipt that is not new",
        SQL,
        "AND r.state = 'received' AND r.reuse_of IS NULL AND r.readers = NEW.readers) THEN",
        "AND r.reuse_of IS NULL AND r.readers = NEW.readers) THEN",
        PG_T,
        "test_l24_door_bodies_only_for_a_new_receipt",
        "XXXX",
    ),
    mu(
        "S12 sql: the receipt update rule is switched off for replicas-style sessions",
        SQL,
        "ALTER TABLE inbound_receipts ENABLE ALWAYS TRIGGER inbound_receipts_update;",
        "ALTER TABLE inbound_receipts ENABLE TRIGGER inbound_receipts_update;",
        PG_T,
        "test_l24_the_receipts_key_check_check_alone_refuses_a_non_hex_value",
        "XXXX",
    ),
    mu(
        "S13 sql: a claim needs a lease but no token",
        SQL,
        "(lease_until IS NOT NULL AND claim_token IS NOT NULL)",
        "(lease_until IS NOT NULL)",
        PG_T,
        "test_l24_door_inserts_outside_the_two_legal_shapes_are_refused_and_nothing_is_written",
        "XXXX",
    ),
    mu(
        "S14 sql: a reuse row may carry a run id",
        SQL,
        "CHECK ((reuse_of IS NULL) = (run_id IS NOT NULL))",
        "CHECK (TRUE)",
        PG_T,
        "test_l24_door_inserts_outside_the_two_legal_shapes_are_refused_and_nothing_is_written",
        "XXXX",
    ),
    mu(
        "S15 sql: the reuse index leaves out the reuse column",
        SQL,
        "ON inbound_receipts (tenant, source, reuse_of) WHERE reuse_of IS NOT NULL",
        "ON inbound_receipts (tenant, source) WHERE reuse_of IS NOT NULL",
        PG_T,
        "test_l21_no_statement_of_the_ledger_needs_a_sequential_scan_of_the_receipts",
        "XXXX",
    ),
    mu(
        "S16 sql: the waiting index does not cover the claim order",
        SQL,
        "ON inbound_receipts (tenant, source, state, lease_until)",
        "ON inbound_receipts (tenant, state)",
        PG_T,
        "test_l21_no_statement_of_the_ledger_needs_a_sequential_scan_of_the_receipts",
        "XXXX",
    ),
    # --- role grants and the migrate command (store/migrate.py) -------------------------------------------------------
    mu(
        "G1 grants: dispatch may update the generation",
        MIG,
        '        dispatch_update_cols=(\n            "state",\n            "attempts",',
        '        dispatch_update_cols=(\n            "generation",\n            "state",\n            "attempts",',
        PG_T,
        "test_l24_each_login_holds_exactly_its_rights_on_the_four_inbound_tables",
        "XXXX",
        "[dispatch]",
    ),
    mu(
        "G2 grants: the door may read the claim token",
        MIG,
        '            "body_sha256",\n            "reuse_of",\n            "state",\n            "readers",\n        ),',
        '            "body_sha256",\n            "reuse_of",\n            "state",\n            "readers",\n            "claim_token",\n        ),',
        PG_T,
        "test_l24_each_login_holds_exactly_its_rights_on_the_four_inbound_tables",
        "XXXX",
        "[door]",
    ),
    mu(
        "G3 grants: purge may read the text",
        MIG,
        '        purge="DELETE",\n        purge_cols=("tenant", "source", "delivery_key"),',
        '        purge="DELETE",\n        purge_cols=("tenant", "source", "delivery_key", "body"),',
        PG_T,
        "test_l24_each_login_holds_exactly_its_rights_on_the_four_inbound_tables",
        "XXXX",
        "[purge]",
    ),
    mu(
        "G4 grants: dispatch may read who the re-run owner is",
        MIG,
        '"inbound_rerun_owner": Grant("table", "", rerun="SELECT")',
        '"inbound_rerun_owner": Grant("table", "", rerun="SELECT", dispatch="SELECT")',
        PG_T,
        "test_l24_each_login_holds_exactly_its_rights_on_the_four_inbound_tables",
        "XXXX",
        "[dispatch]",
    ),
    mu(
        "G5 migrate: a second holder of UPDATE on generation is not refused",
        MIG,
        "    if others or [r[0] for r in rows] != [role_name]:",
        "    if False:",
        PG_T,
        "test_l24_a_stray_holder_of_update_generation_makes_migrate_refuse_and_roll_back",
        "XXXX",
    ),
    mu(
        "G6 migrate: a re-run owner that can log in is accepted",
        MIG,
        "if can_login is None or can_login[0]:",
        "if can_login is None:",
        PG_T,
        "test_l28_every_login_passes_the_effective_problems_check",
        "XXXX",
    ),
    mu(
        "G7 migrate: two roles with the same name are accepted",
        MIG,
        "    if len(set(named)) != len(named):",
        "    if False:",
        LEDGER_T,
        "test_l26_the_six_roles_must_differ",
        "XXXX",
    ),
    mu(
        "G8 migrate: a partial set of inbound roles is accepted",
        MIG,
        "if 0 < sum(v is not None for v in inbound.values()) < len(inbound):",
        "if False:",
        LEDGER_T,
        "test_l26_a_partial_set_of_inbound_roles_is_refused_before_connecting",
        "XXXX",
    ),
    mu(
        "G9 migrate: the trigger functions are not pinned to a schema",
        MIG,
        "        _pin_inbound_functions(db)\n    return applied",
        "    return applied",
        PG_T,
        "test_l15_h_each_function_is_pinned_to_the_schema_and_pg_temp",
        "XXXX",
    ),
    mu(
        "G10 migrate: a renamed re-run owner keeps its rights",
        MIG,
        '        _apply_grants(db, old[0], lambda g: "")',
        "        pass",
        PG_T,
        "test_l24_a_renamed_rerun_owner_leaves_the_old_one_with_no_right_on_any_granted_relation",
        "XXXX",
    ),
    mu(
        "G11 migrate: the re-run owner check is skipped",
        MIG,
        "            _check_rerun_holders(db, rerun_owner_role)\n        if portal_role:",
        "        if portal_role:",
        PG_T,
        "test_l24_a_stray_holder_of_update_generation_makes_migrate_refuse_and_roll_back",
        "XXXX",
    ),
]


if __name__ == "__main__":
    if not os.environ.get("HADAVIN_TEST_PG_DSN"):
        print(
            "HADAVIN_TEST_PG_DSN is not set: the database killers would be skipped and look like survivors",
            file=sys.stderr,
        )
        sys.exit(2)
    only = sys.argv[1:]
    if only and not any(o in m.name for m in M for o in only):
        print(f"no mutant name contains any of {only}; nothing was run", file=sys.stderr)
        sys.exit(2)
    first_lines: dict[str, str] = {}

    def show(row):
        name, v, test_id, good = row
        print(
            f"{'ok ' if good else 'BAD'} {v:12} {name}  [{test_id.split('::')[-1][:70]}]",
            flush=True,
        )
        if not good:
            print("      first line:", first_lines.get(name, "")[:170], flush=True)

    res = run_mutants(
        ROOT,
        M,
        [LEDGER_T, CONTRACT_T, PG_T],
        extra_dirs=("tests", "tools", "demos", "docs"),
        only=only,
        on_result=show,
        first_lines=first_lines,
    )
    bad = [n for n, _, _, g in res if not g]
    print(f"{len(res) - len(bad)} of {len(res)} good; problems: {bad}")
    sys.exit(1 if bad else 0)
