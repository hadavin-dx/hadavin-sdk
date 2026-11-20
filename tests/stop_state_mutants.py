"""Mutants of the stop state (step B). Each reverts ONE guard; the pinned test of ``tests/test_stop_state_roles.py``
must fail, and its output must hold ``expect``. Not collected by pytest. Re-anchored after fix rounds 2 and 3.

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

A mutant that needs a second file changed to be honest (the serial stop id needs its sequence row in the grant
map, or ``migrate`` refuses the mutant before any test runs) names the further edits in ``ALSO``; they are applied
and put back with the mutant. ``EQUIVALENT`` lists mutants that no test can kill, with the reason; they are printed,
never run."""

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
E6 = "test_e6_a_deleted_flag_row_reads_on_and_a_reset_fails_loudly_and_stays_on"
S1 = "test_s1_temporary_tables_on_the_runtime_connection_do_not_hide_an_open_stop"
S2 = "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear"
LOOP_RETURN = '            return self._to(run, S.NEEDS_PERSON, "limits_unavailable")\n'
LOOP_FIRST = (
    "        except Exception:  # noqa: BLE001\n"
    + LOOP_RETURN
    + '        if "kill_switch" in blocked:\n'
)
LOOP_PLAN = (
    "        except Exception:  # noqa: BLE001\n"
    + LOOP_RETURN
    + "        try:\n            decision = authorize(\n"
)
# Since fix round 3 a runtime role that could clear is refused by migrate itself (who_else_can_clear), so the two
# grant mutants die in the fixture's migrate, before the statement of the killer runs.
WHO_ELSE = "roles other than the reset role could clear a stop"
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
        DENIED, WHO_ELSE),
    mutant("grants: the runtime is read-write on kill_switch again", MIG,
        '"kill_switch": Grant("table", "SELECT", reset="SELECT, UPDATE")',
        '"kill_switch": Grant("table", _RW, reset="SELECT, UPDATE")',
        DENIED, WHO_ELSE),
    mutant("grants: the reset role may not append to audit_entries", MIG,
        '"audit_entries": Grant("table", _APPEND, portal=True, reset=_APPEND)',
        '"audit_entries": Grant("table", _APPEND, portal=True, reset="SELECT")',
        N3, "assert 3 == 0"),
    mutant("migrate: the reset block is skipped", MIG,
        "        if reset_role:\n            _apply_grants(db, reset_role, lambda g: g.reset)",
        "        if False:\n            _apply_grants(db, reset_role, lambda g: g.reset)",
        N2, "the search_path names no schema that exists"),
    mutant("migrate: effective_problems is not run for the reset role", MIG,
        'if bad := effective_problems(db, reset_role, lambda g: g.reset if g else ""):',
        "if bad := []:",
        "test_migrate_refuses_a_public_right_the_reset_role_would_inherit", "DID NOT RAISE"),
    mutant("migrate: reset_role is left out of the named roles", MIG,
        "    named = [r for r in roles if r is not None]",
        "    named = [r for r in roles[:3] if r is not None]",
        "test_migrate_refuses_a_reset_role_that_is_the_runtime_role", "Regex pattern did not match"),
    mutant("migrate: the forbidden role names are not checked", MIG,
        " or role in _FORBIDDEN_ROLES", "",
        "test_h4_a_role_name_that_is_not_one_plain_role_is_refused_before_any_connection", "ConfigError"),
    mutant("read: the NOT EXISTS is dropped (a cleared stop still counts)", PG,
        '\'SELECT s."by", s.ts FROM {stops} s WHERE NOT EXISTS \'\n'
        '                    "(SELECT 1 FROM {clears} c WHERE c.stop_id = s.id) ORDER BY',
        '\'SELECT s."by", s.ts FROM {stops} s \'\n                    "ORDER BY',
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
        E6, "assert False is True"),
    mutant("reset: ON CONFLICT is removed", PG,
        '                    "ON CONFLICT (stop_id) DO NOTHING"\n', '                    ""\n',
        "test_s6_a_reset_that_meets_an_uncommitted_clear_of_the_same_stop_succeeds", "UniqueViolation"),
    mutant("reset: the flag update and the clears are not one transaction", PG,
        "        with self._lock, self._db.transaction():\n            flag = self._exec(\n",
        "        with self._lock:\n            flag = self._exec(\n",
        "test_e8_a_refused_clear_leaves_the_flag_on", "assert False is True"),
    mutant("reset: not one transaction (through the command line)", PG,
        "        with self._lock, self._db.transaction():\n            flag = self._exec(\n",
        "        with self._lock:\n            flag = self._exec(\n",
        "test_s6_cli_reset_whose_clear_insert_is_refused_leaves_the_flag_on", "(False, 'user:op')"),
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
    # ---- fix round 3 ----
    mutant("S1: the stops table is not schema-qualified (read)", PG,
        '"stops": sql.SQL("{}.kill_switch_stops").format(s),', '"stops": sql.SQL("kill_switch_stops"),',
        S1, "assert False is True"),
    mutant("S1: the stops table is not schema-qualified (a stop lands in the temporary table)", PG,
        '"stops": sql.SQL("{}.kill_switch_stops").format(s),', '"stops": sql.SQL("kill_switch_stops"),',
        "test_s1_temporary_tables_made_before_any_stop_do_not_swallow_the_stop",
        "the stop went into the temporary table"),
    mutant("S1: the clears table is not schema-qualified", PG,
        '"clears": sql.SQL("{}.kill_switch_clears").format(s),', '"clears": sql.SQL("kill_switch_clears"),',
        S1, "assert False is True"),
    mutant("S1: the flag table is not schema-qualified (read)", PG,
        '"flag": sql.SQL("{}.kill_switch").format(s),', '"flag": sql.SQL("kill_switch"),',
        "test_s1_a_temporary_flag_table_does_not_hide_a_real_flag_that_is_on", "assert False is True"),
    # One edit cannot un-qualify all three names. With only the flag un-qualified, a reset by the runtime login
    # through its temporary tables is still refused at the real kill_switch_clears, so
    # test_s1_the_runtime_login_cannot_reset_through_its_temporary_tables does not see that mutant; the read test
    # above does.
    mutant("S2: who_else_can_clear is not called", MIG,
        "        if named and (others := who_else_can_clear(db, reset_role, accepted)):",
        "        if named and (others := []):",
        S2, "DID NOT RAISE"),
    mutant("S2: a column-level privilege is not counted", MIG,
        "    WHERE att.attnum > 0 AND NOT att.attisdropped AND a.privilege_type = rel.priv",
        "    WHERE FALSE",
        S2, "DID NOT RAISE"),
    mutant("S2: membership without inheritance is not counted", MIG,
        '"(m.inherit_option OR m.set_option OR m.admin_option)" if new', '"m.inherit_option" if new',
        "test_s2_migrate_refuses_a_member_of_the_reset_role", "DID NOT RAISE"),
    mutant("S2: membership of a grantee ignored (the group a role can SET ROLE to)", MIG,
        "JOIN can ON m.roleid = can.oid", "JOIN can ON FALSE",
        "test_s2_migrate_refuses_the_runtime_role_as_a_noinherit_member_of_a_group_that_can_clear",
        "is not named in"),
    mutant("S2: membership of a grantee ignored (a member and a member of a member)", MIG,
        "JOIN can ON m.roleid = can.oid", "JOIN can ON FALSE",
        "test_s2_a_member_of_a_role_that_holds_the_right_is_listed_with_it", "assert ["),
    mutant("S2: PUBLIC grant ignored", MIG,
        "WHERE EXISTS (SELECT 1 FROM acl WHERE grantee = 0)", "WHERE FALSE",
        "test_s2_a_grant_to_public_is_listed_as_public", "== ['PUBLIC']"),
    mutant("S2: the check reads every schema of the database, not this one", MIG,
        "    WHERE n.nspname = pg_catalog.current_schema()\n)",
        "    WHERE TRUE\n)",
        "test_s2_a_second_schema_with_its_own_stop_tables_and_roles_does_not_change_this_schemas_answer",
        "could clear a stop"),
    mutant("S2: a member of the owner is followed", MIG,
        "    SELECT relowner AS oid FROM rel UNION SELECT r.oid",
        "    SELECT r.oid",
        "test_s2_a_member_of_an_owner_that_is_not_a_superuser_is_not_listed", "could clear a stop"),
    mutant("S2: a membership with the ADMIN option only is not counted (the creator of the reset role)", MIG,
        '"(m.inherit_option OR m.set_option OR m.admin_option)" if new', '"(m.inherit_option OR m.set_option)" if new',
        "test_s2_the_creator_of_the_reset_role_with_the_admin_option_only_is_listed", "DID NOT RAISE"),
    mutant("S2: a membership with the ADMIN option only is not counted (a role that holds the right)", MIG,
        '"(m.inherit_option OR m.set_option OR m.admin_option)" if new', '"(m.inherit_option OR m.set_option)" if new',
        "test_s2_a_member_of_a_role_that_holds_a_right_with_the_admin_option_only_is_listed", "assert ["),
    mutant("S2: below 16 a membership is not counted", MIG,
        '" if new else "TRUE"', '" if new else "FALSE"',
        "test_s2_migrate_refuses_a_member_of_the_reset_role", "DID NOT RAISE"),
    mutant("S2: below 16 a CREATEROLE login is not listed", MIG,
        'creators = "FALSE" if new else _CREATORS', 'creators = "FALSE"',
        "test_s2_below_16_a_createrole_login_that_is_not_a_superuser_is_listed", "assert [] == ["),
    mutant("S2: from 16 a CREATEROLE login with no membership is listed", MIG,
        'creators = "FALSE" if new else _CREATORS', 'creators = "r.rolcreaterole"',
        "test_s2_from_16_a_createrole_login_with_no_membership_is_not_listed", "sb_cq_"),
    mutant("S2: the reset role is not a base row", MIG,
        "WHERE r.rolname = %(reset)s\n                       UNION", "WHERE FALSE\n                       UNION",
        "test_s2_members_of_the_reset_role_are_listed_even_when_it_holds_no_right_yet", "== ['sb_n8_"),
    mutant("S2: a dropped column is counted", MIG,
        "AND NOT att.attisdropped AND a.privilege_type", "AND a.privilege_type",
        "test_s2_a_dropped_column_keeps_no_grant", "assert ['sb_dc_"),
    mutant("S2: a superuser is not excluded", MIG,
        "UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolsuper", "UNION SELECT r.oid FROM pg_catalog.pg_roles r WHERE FALSE",
        "test_s2_a_superuser_with_a_right_or_a_membership_is_not_listed", "assert ["),
    mutant("S2: the update right is read on the clears, not the insert right", MIG,
        "('kill_switch_clears', 'INSERT')", "('kill_switch_clears', 'UPDATE')",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: the insert right is read on the flag, not the update right", MIG,
        "VALUES ('kill_switch', 'UPDATE')", "VALUES ('kill_switch', 'INSERT')",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: DELETE on the flag is not read", MIG,
        "('kill_switch', 'DELETE'), ", "",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: TRUNCATE on the flag is not read", MIG,
        "('kill_switch', 'TRUNCATE'),\n", "\n",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: TRIGGER on the stops is not read", MIG,
        "('kill_switch_stops', 'TRIGGER'), ", "",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: TRIGGER on the clears is not read", MIG,
        "('kill_switch_clears', 'TRIGGER'),\n", "\n",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    mutant("S2: TRIGGER on the flag is not read", MIG,
        "('kill_switch', 'TRIGGER'), ('kill_switch_stops'", "('kill_switch_stops'",
        "test_s2_migrate_refuses_a_third_role_that_holds_a_right_to_clear", "DID NOT RAISE"),
    # One edit; two tests each kill it (an empty search_path, and a schema without the tables): one mutant, pinned
    # on the first.
    mutant("S2: the check passes when no relations are found", MIG,
        "    if not schema or missing or shadowed:", "    if False:",
        "test_s2_an_empty_search_path_is_refused_not_passed", "DID NOT RAISE"),
    mutant("S2: a view or index with a stop table's name counts as the table", MIG,
        "AND c.relkind IN ('r','p') \"", "AND TRUE \"",
        "test_s2_a_view_with_a_stop_table_name_is_refused_not_passed", "DID NOT RAISE"),
    mutant("S2: a superuser or the owner that is a member of a listed role is listed", MIG,
        "WHERE m.member NOT IN (SELECT oid FROM outside) AND {usable}", "WHERE {usable}",
        "test_s2_a_superuser_with_a_right_or_a_membership_is_not_listed", "assert ["),
    mutant("S2: the allow-list is removed (an accepted CREATEROLE role is listed)", MIG,
        " AND r.rolname::text <> ALL(%(accepted)s::text[])", "",
        "test_s2_below_16_an_accepted_createrole_role_is_not_listed_and_another_one_still_is", "assert ["),
    mutant("S2: the allow-list is applied to grants too", MIG,
        "SELECT a.grantee FROM rel, pg_catalog.aclexplode(rel.relacl) a WHERE a.privilege_type = rel.priv\n",
        "SELECT a.grantee FROM rel, pg_catalog.aclexplode(rel.relacl) a WHERE a.privilege_type = rel.priv\n"
        "      AND a.grantee NOT IN (SELECT r.oid FROM pg_catalog.pg_roles r WHERE r.rolname::text = ANY(%(accepted)s::text[]))\n",
        "test_s2_an_accepted_role_that_holds_a_grant_or_a_membership_here_is_still_listed", "assert ["),
    mutant("S2: the allow-list name format check is removed", MIG,
        "    if not all(_accepted_name_ok(a) for a in accepted):", "    if False:",
        "test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection", "Regex pattern did not match"),
    mutant("S2: the allow-list forbidden names check is removed", MIG,
        "    if any(_accepted_name_forbidden(a) for a in accepted):", "    if False:",
        "test_s2_a_forbidden_accepted_role_name_is_refused_before_any_connection", "Regex pattern did not match"),
    mutant("S2: the allow-list bare string check is removed", MIG,
        "    if isinstance(accepted_admin_roles, str):", "    if False:",
        "test_s2_accepted_roles_given_as_one_string_are_refused", "Regex pattern did not match"),
    mutant("S2: the allow-list without named roles is accepted", MIG,
        "    if accepted and not named:", "    if False:",
        "test_s2_accepted_roles_without_named_roles_are_refused", "Regex pattern did not match"),
    mutant("S2: the members of an accepted CREATEROLE role are not listed", MIG,
        'vouched = "FALSE" if new else _VOUCHED', 'vouched = "FALSE"',
        "test_s2_below_16_a_member_of_an_accepted_createrole_role_is_listed_and_the_role_alone_is_not", "assert ["),
    mutant("S2: the allow-list may name a role the command grants", MIG,
        "    if overlap := sorted(set(accepted) & set(named)):", "    if False:",
        "test_s2_an_accepted_role_that_is_also_a_named_role_is_refused", "Regex pattern did not match"),
    mutant("tests: migrate does not take the shared server gate", "tests/conftest.py",
        '            mp.setattr(mod, "migrate", patched)', "            pass",
        "test_the_server_gate_holds_every_migrate_while_another_session_holds_it_exclusively",
        "migrate ran while another session held"),
    mutant("S2: the check passes when one relation is missing", MIG,
        "    if not schema or missing or shadowed:", "    if not schema or shadowed:",
        "test_s2_one_missing_stop_table_is_refused_not_passed", "DID NOT RAISE"),
    mutant("S2: the check passes when a bare name resolves to another relation", MIG,
        "    if not schema or missing or shadowed:", "    if not schema or missing:",
        "test_s2_a_temporary_table_with_a_stop_table_name_is_refused_not_passed", "DID NOT RAISE"),
    mutant("S2: the refusal does not name the schema and the search_path", MIG,
        "(schema {schema!r}, search_path {path!r}, missing", "(missing",
        "test_s2_a_search_path_whose_first_schema_has_no_stop_tables_is_refused_not_passed", "is not named in"),
    mutant("S2: the check runs only when a reset role is named", MIG,
        "        if named and (others := who_else_can_clear(db, reset_role, accepted)):",
        "        if reset_role and (others := who_else_can_clear(db, reset_role, accepted)):",
        "test_s2_migrate_naming_only_the_runtime_role_refuses_the_reset_role_of_an_earlier_call",
        "DID NOT RAISE"),
    mutant("S7: the missing-row raise is removed", PG,
        "                flag.rowcount != 1\n", "                False\n",
        E6, "DID NOT RAISE"),
    mutant("S7: the missing-row raise is removed (through the command line)", PG,
        "                flag.rowcount != 1\n", "                False\n",
        "test_s7_cli_reset_with_the_flag_row_missing_exits_2_audits_reset_failed_and_stays_on", "system:kill_switch_row_missing"),
    mutant("S7: the missing-row raise is removed (the stop is cleared behind the missing row)", PG,
        "                flag.rowcount != 1\n", "                False\n",
        "test_s7_a_reset_with_the_flag_row_missing_clears_nothing_so_the_stop_survives_the_repair",
        "DID NOT RAISE"),
    mutant("B-2: the read-back after the reset is removed", CLI,
        '    if state.on:\n        print(\n            f"kill switch still ON',
        '    if False:\n        print(\n            f"kill switch still ON',
        "test_b2_cli_reset_says_still_on_when_a_stop_commits_after_its_clear_statement_began",
        "assert [0] == [2]"),
    mutant("B-4: the same-secret refusal is removed", CLI,
        "        if reset_ref and reset_ref == b.store.dsn_secret_name:", "        if False:",
        "test_b4_a_reset_ref_equal_to_the_runtime_secret_name_is_refused_before_any_connection",
        "was called"),
    mutant("S12: the isfinite CHECK is removed from the stops", SQL,
        "    ts   TIMESTAMPTZ NOT NULL DEFAULT now() CHECK (isfinite(ts))",
        "    ts   TIMESTAMPTZ NOT NULL DEFAULT now()",
        "test_s12_a_stop_row_cannot_carry_an_infinite_ts_even_by_hand", "DID NOT RAISE"),
    mutant("S12: the isfinite CHECK is removed from the clears", SQL,
        "    ts      TIMESTAMPTZ NOT NULL DEFAULT now() CHECK (isfinite(ts))",
        "    ts      TIMESTAMPTZ NOT NULL DEFAULT now()",
        "test_s12_a_clear_row_cannot_carry_an_infinite_ts_even_by_hand", "DID NOT RAISE"),
    mutant("S12: the stop sends the caller's ts", PG,
        """sql.SQL('INSERT INTO {stops} ("by") VALUES (%s)').format(**t), (ks.by,)""",
        """sql.SQL('INSERT INTO {stops} ("by", ts) VALUES (%s, %s)').format(**t), (ks.by, ks.ts)""",
        "test_s12_the_stores_own_stop_does_not_send_ts", "assert [(False,)] == [(True,)]"),
    # ---- the two that were PENDING ----
    mutant("migration 0006: the stop id is a serial number again (BIGSERIAL)", SQL,
        "    id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),", "    id   BIGSERIAL PRIMARY KEY,",
        "test_h2_the_runtime_login_cannot_make_a_later_stop_fail", "UniqueViolation"),
    mutant("loop: the limits_unavailable hunk is removed (first check)", LOOP,
        LOOP_FIRST, LOOP_FIRST.replace(LOOP_RETURN, "            raise\n"),
        "test_e9_an_unreadable_stop_state_at_the_first_check_means_no_model_call", "InsufficientPrivilege"),
    mutant("loop: the limits_unavailable hunk is removed (after the plan)", LOOP,
        LOOP_PLAN, LOOP_PLAN.replace(LOOP_RETURN, "            raise\n"),
        "test_e9_a_stop_state_that_turns_unreadable_at_any_later_read_means_no_card_and_no_action",
        "InsufficientPrivilege"),
    mutant("loop: the limits_unavailable hunk is removed (recheck)", LOOP,
        '            return "recheck.limits_unavailable"\n', "            raise\n",
        "test_e9_an_unreadable_stop_state_at_the_recheck_means_no_action", "InsufficientPrivilege"),
]  # fmt: skip

# Further edits a mutant needs in other files: {mutant name: [(file, old, new)]}.
ALSO = {
    "migration 0006: the stop id is a serial number again (BIGSERIAL)": [
        (SQL, "    stop_id UUID PRIMARY KEY REFERENCES", "    stop_id BIGINT PRIMARY KEY REFERENCES"),
        (MIG, '    "kill_switch_clears": Grant("table", "SELECT", reset=_APPEND),\n',
            ('    "kill_switch_clears": Grant("table", "SELECT", reset=_APPEND),\n'
             '    "kill_switch_stops_id_seq": Grant("sequence", "USAGE"),\n')),
    ],
}  # fmt: skip

# Mutants no test can kill; (name, file, reason). Printed, never run.
# (None now: the one that was here was a dead filter, `WHERE grantee <> 0`, and the filter was deleted.)
EQUIVALENT: list[tuple[str, str, str]] = []

# Mutants of one PostgreSQL branch: run on a server of that branch only (the other branch is dead code there and the
# mutant would survive). Run the list on a 15 and on a 17 server; every mutant is then KILLED on one of the two.
GE16 = {
    "S2: membership without inheritance is not counted",
    "S2: a membership with the ADMIN option only is not counted (the creator of the reset role)",
    "S2: a membership with the ADMIN option only is not counted (a role that holds the right)",
    "S2: from 16 a CREATEROLE login with no membership is listed",
}
LT16 = {
    "S2: a dropped column is counted",  # PostgreSQL 15 keeps the ACL of a dropped column, 17 clears it
    "S2: below 16 a membership is not counted",
    "S2: below 16 a CREATEROLE login is not listed",
    "S2: the allow-list is removed (an accepted CREATEROLE role is listed)",
    "S2: the members of an accepted CREATEROLE role are not listed",
}


def _server_version() -> int:
    import psycopg

    with psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"]) as db:
        return int(db.execute("SHOW server_version_num").fetchone()[0])


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
    targets = {m.file for m in chosen} | {f for m in chosen for f, _, _ in ALSO.get(m.name, [])}
    dirty = subprocess.run(  # noqa: S603 - fixed arguments
        ["git", "status", "--porcelain", "--", *sorted(targets)],  # noqa: S607 - git from PATH
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    if dirty.strip():
        print("refused: a target file has uncommitted changes:\n" + dirty)
        return 1
    bad, clean, tally = 0, {}, {}
    version = _server_version()
    for m in chosen:
        if (m.name in GE16 and version < 160000) or (m.name in LT16 and version >= 160000):
            tally["N/A"] = tally.get("N/A", 0) + 1
            print(
                f"N/A      | {m.name} | needs the other PostgreSQL branch (this is {version}) | {m.only_test}",
                flush=True,
            )
            continue
        edits = [(m.file, m.old, m.new), *ALSO.get(m.name, [])]
        before = {f: (ROOT / f).read_bytes() for f, _, _ in edits}
        after = {f: data.decode("utf-8") for f, data in before.items()}
        missing = []
        for f, old, new in edits:
            if old not in after[f]:
                missing.append(f)
            after[f] = after[f].replace(old, new)
        if m.only_test not in clean:
            clean[m.only_test] = _killer(m.only_test)[0] == 0
        if not clean[m.only_test]:
            verdict = "BASELINE FAILS (the killer fails on the clean tree)"
        elif missing:
            verdict = f"NOT APPLIED (the old text is not in {', '.join(missing)})"
        else:
            try:
                for f, text in after.items():
                    (ROOT / f).write_bytes(text.encode("utf-8"))
                code, out = _killer(m.only_test)
            finally:
                for f, data in before.items():
                    (ROOT / f).write_bytes(data)
            if code == 0:
                verdict = "SURVIVED"
            elif m.expect not in out:
                verdict = f"FAILED FOR ANOTHER REASON (no {m.expect!r} in the output)"
            else:
                verdict = "KILLED"
        bad += verdict != "KILLED"
        key = verdict.split(" ")[0]
        tally[key] = tally.get(key, 0) + 1
        print(f"{verdict:8} | {m.name} | {m.file} | {m.only_test}", flush=True)
    for name, file, reason in EQUIVALENT if not only else []:
        tally["EQUIVALENT"] = tally.get("EQUIVALENT", 0) + 1
        print(f"EQUIVALENT | {name} | {file} | {reason}", flush=True)
    counts = " ".join(f"{k}={tally.get(k, 0)}" for k in ("KILLED", "N/A", "EQUIVALENT", "SURVIVED"))
    other = sum(v for k, v in tally.items() if k not in ("KILLED", "N/A", "EQUIVALENT", "SURVIVED"))
    print(f"SUMMARY server={version} mutants={len(chosen)} {counts} OTHER={other}", flush=True)
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
    for name, _file, reason in EQUIVALENT:
        print(f"equivalent (not run): {name}: {reason}")
    sys.exit(0 if all(good for *_, good in results) else 1)
