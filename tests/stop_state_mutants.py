"""Mutants of the stop state (step B). Each reverts ONE guard; the pinned test of ``tests/test_stop_state_roles.py``
must fail, and its output must hold ``expect``. Not collected by pytest. Re-anchored after fix rounds 2 and 3, and again for the E5 guards (see the end of ``HAND``).

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
import tempfile
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
APP = "src/hadavin_sdk/app.py"
SECN = "src/hadavin_sdk/secret_name.py"
E5S = "tests/test_step_b_e5_search_path.py"
E5R = "tests/test_step_b_e5c_role_settings.py"
E5M = "tests/test_step_b_e5_maintain.py"
E5B = "tests/test_step_b_e5b_reset_ref.py"
H4 = "tests/test_trigger_hardening_round4.py"
UNIT = "tests/test_stop_state_unit.py"
LOCKT = "tests/test_store_lock_timeout_pg.py"
NOROLES = "tests/test_step_b_e5_no_roles.py"
NEW = "tests/test_mutants_stop_state_e5.py"

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


PARAM: dict[
    str, str
] = {}  # mutant name -> "[id]": a killer pinned on one parameter of a parametrized test


def mutant(name, file, old, new, killer, expect, test=TEST):
    base, bracket, rest = killer.partition("[")
    PARAM[name] = bracket + rest
    return Mutant(
        name,
        file,
        old,
        new,
        expect,
        test_file=test,
        only_test=base,
        pinned=test[:-3] + "::" + base,
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
        '"audit_entries": Grant("table", _APPEND, portal=True, reset=_APPEND, release=_APPEND)',
        '"audit_entries": Grant("table", _APPEND, portal=True, reset="SELECT", release=_APPEND)',
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
    mutant('S2: the note is not appended to the notes list', MIG, '                notes.append(note)', '                pass',
        'test_cli_migrate_prints_and_logs_every_accepted_admin_role', 'assert'),
    mutant('S2: the note is not logged', MIG, '            _LOG.warning("migrate: %s", note)', '            pass',
        'test_cli_migrate_prints_and_logs_every_accepted_admin_role', 'assert'),
    mutant('cli: the note is not printed', CLI, '            _say(note)', '            pass',
        'test_cli_migrate_prints_and_logs_every_accepted_admin_role', 'assert'),
    mutant('cli: the note is printed without escaping (a stdout that cannot encode the name)', CLI, '    print(text.encode(enc, "backslashreplace").decode(enc))', '    print(text)',
        'test_cli_migrate_notes_never_fail_on_a_stdout_that_cannot_encode_the_name', 'u4e2d'),
    mutant("S2: the from-16 'no effect' note is removed", MIG, '                note = f"accepted_admin_roles has no effect from PostgreSQL 16 on (named, not used: {names})"', '                note = ""',
        'test_cli_migrate_prints_and_logs_every_accepted_admin_role', 'assert'),
    mutant('S2: the note is not appended to the refusal message', MIG, '                + (f". {note}" if note.startswith("accepted administrator") else "")', '                + ""',
        'test_s2_below_16_the_refusal_names_the_accepted_roles', 'assert'),
    mutant('S2: a superuser or the owner is a seed of the vouched walk', MIG, '    SELECT r.oid FROM pg_catalog.pg_roles r WHERE {vouched} AND r.oid NOT IN (SELECT oid FROM outside)', '    SELECT r.oid FROM pg_catalog.pg_roles r WHERE {vouched}',
        'test_s2_below_16_a_member_of_an_accepted_superuser_is_not_listed', 'assert ['),
    mutant('S2: an accepted CREATEROLE role is listed for being a seed (flag TRUE)', MIG, '    SELECT oid, FALSE FROM vouched', '    SELECT oid, TRUE FROM vouched',
        'test_s2_below_16_a_member_of_an_accepted_createrole_role_is_listed_and_the_role_alone_is_not', 'assert ['),
    mutant('S2: a vouched role is listed for being a member of another vouched role', MIG, 'can.listed OR m.member NOT IN (SELECT oid FROM vouched)', 'TRUE',
        'test_s2_below_16_a_vouched_role_is_not_listed_for_being_a_member_of_another_vouched_role', 'assert ['),
    mutant('S2: the name length check is removed', MIG, '        0 < size <= 63', '        True',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[length64]', 'Regex pattern did not match'),
    mutant('S2: the name surrounding-space check is removed', MIG, '        and name == name.strip()', '        and True',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[trailing_space]', 'Regex pattern did not match'),
    mutant('S2: the name category check is removed', MIG, 'unicodedata.category(c) in _REFUSED_CATEGORIES for c in name', 'False for c in name',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[bel]', 'Regex pattern did not match'),
    mutant('S2: category Cc is not refused', MIG, '{"Cc", "Cf", "Zl", "Zp"}', '{"Cf", "Zl", "Zp"}',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[bel]', 'Regex pattern did not match'),
    mutant('S2: category Cf is not refused', MIG, '{"Cc", "Cf", "Zl", "Zp"}', '{"Cc", "Zl", "Zp"}',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[zero_width_space]', 'Regex pattern did not match'),
    mutant('S2: category Zl is not refused', MIG, '{"Cc", "Cf", "Zl", "Zp"}', '{"Cc", "Cf", "Zp"}',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[line_separator]', 'Regex pattern did not match'),
    mutant('S2: category Zp is not refused', MIG, '{"Cc", "Cf", "Zl", "Zp"}', '{"Cc", "Cf", "Zl"}',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[paragraph_separator]', 'Regex pattern did not match'),
    mutant('S2: a lone surrogate name raises instead of being refused', MIG, '    except UnicodeEncodeError:', '    except ZeroDivisionError:',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[lone_surrogate]', 'UnicodeEncodeError'),
    mutant('S2: the wildcards are not refused', MIG, ' or name in _WILDCARDS', '',
        'test_s2_a_forbidden_accepted_role_name_is_refused_before_any_connection[star]', 'Regex pattern did not match'),
    mutant('S2: the forbidden names are compared in letter case', MIG, 'name.lower() in _FORBIDDEN_ROLES', 'name in _FORBIDDEN_ROLES',
        'test_s2_a_forbidden_accepted_role_name_is_refused_before_any_connection[public_upper]', 'Regex pattern did not match'),
    mutant('S2: only the trailing space of a name is refused (a leading space is taken)', MIG, '        and name == name.strip()', '        and name == name.rstrip()',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[leading_space]', 'Regex pattern did not match'),
    mutant('S2: only the leading space of a name is refused (a trailing space is taken)', MIG, '        and name == name.strip()', '        and name == name.lstrip()',
        'test_s2_an_accepted_role_name_of_the_wrong_format_is_refused_before_any_connection[trailing_space]', 'Regex pattern did not match'),
    mutant('S2: a vouched role is not listed for being a member of a listed role', MIG, 'can.listed OR m.member NOT IN (SELECT oid FROM vouched)', 'm.member NOT IN (SELECT oid FROM vouched)',
        'test_s2_a_vouched_role_that_is_a_member_of_a_listed_role_is_listed', 'assert ['),
    mutant('S2: the owner is a seed of the vouched walk (only superusers are outside)', MIG, 'WHERE {vouched} AND r.oid NOT IN (SELECT oid FROM outside)', 'WHERE {vouched} AND NOT r.rolsuper',
        'test_s2_below_16_a_member_of_an_accepted_owner_is_not_listed', 'assert ['),
    mutant('cli: a broken stdout (OSError) changes the exit code', CLI, '    except (OSError, ValueError):', '    except ZeroDivisionError:',
        'test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[oserror]', 'assert 3 =='),
    mutant('cli: a closed stdout (ValueError) changes the exit code', CLI, '    except (OSError, ValueError):', '    except OSError:',
        'test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[closed]', 'assert 3 =='),
    mutant('cli: the applied line is not guarded', CLI, '    _say(f"applied: {\', \'.join(applied) or \'nothing (up to date)\'}")', '    print(f"applied: {\', \'.join(applied) or \'nothing (up to date)\'}")',
        'test_cli_migrate_a_fully_broken_stdout_never_changes_the_exit_code[oserror]', 'assert 3 =='),
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
        "    if state.on:\n        who = (",
        "    if False:\n        who = (",
        "test_b2_cli_reset_says_still_on_when_a_stop_commits_after_its_clear_statement_began",
        "assert [0] == [2]"),
    mutant("B-4: the same-secret refusal is removed", CLI,
        "            and collides(reset_ref, [b.store.dsn_secret_name], file_backed=_file_backed(b))",
        "            and False",
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
    # ---- the guards added since (verify_schema, role settings, MAINTAIN, no_roles, reset-ref overlap, lock_timeout) ----
    mutant("verify_schema: an empty search_path is not refused", PG,
        '    if not schema:\n        raise ConfigError(\n            "store postgres: the search_path names no schema',
        '    if False:\n        raise ConfigError(\n            "store postgres: the search_path names no schema',
        "test_s1_a_search_path_that_names_no_schema_is_refused_at_connect", "Regex pattern did not match"),
    mutant("verify_schema: the effective path is not compared with the expected one", PG,
        "    if effective != expected or schema != expected[0]:", "    if schema != expected[0]:",
        "test_e5e_an_extra_schema_on_the_effective_path_is_refused", "DID NOT RAISE", test=NEW),
    mutant("verify_schema: current_schema() is not compared with the first expected schema", PG,
        "    if effective != expected or schema != expected[0]:", "    if effective != expected:",
        "test_e5e_a_path_that_starts_with_pg_catalog_is_refused_by_current_schema", "Regex pattern did not match", test=NEW),
    mutant("verify_schema: the missing stop tables are not refused", PG,
        "    if missing := [t for t in _STOP_TABLES if t not in found]:", "    if missing := []:",
        "test_missing_stop_tables_say_kill_switch_not_found_in_current_schema_and_name_it", "DID NOT RAISE", test=E5S),
    mutant("verify_schema: a view with a stop table's name counts as the table", PG,
        "c.relkind IN ('r','p') AND c.relname = ANY(%s)", "c.relkind IN ('r','p','v') AND c.relname = ANY(%s)",
        "test_e5e_a_view_named_like_a_stop_table_is_not_the_stop_table", "DID NOT RAISE", test=NEW),
    mutant("verify_schema: the connection is left open when the check refuses", PG,
        "    except BaseException:\n        conn.close()\n        raise", "    except BaseException:\n        raise",
        "test_e5e_a_refused_schema_check_closes_the_connection", "assert False is True", test=NEW),
    mutant("lock_timeout: the setting is not sent", PG,
        '    conn.execute(\n        sql.SQL("SET lock_timeout = {}").format(sql.Literal(defaults.STORE_LOCK_TIMEOUT_MS))\n    )\n',
        "",
        "test_the_default_is_ten_seconds_and_the_runtime_connection_carries_it", "== '10s'", test=LOCKT),
    mutant("lock_timeout: the value is not the default", PG,
        "sql.Literal(defaults.STORE_LOCK_TIMEOUT_MS)", "sql.Literal(0)",
        "test_the_value_comes_from_the_default_at_build_time", "2500ms", test=LOCKT),
    mutant("migrate: --no-roles together with a role is accepted", MIG,
        "    if no_roles and named:", "    if False:",
        "test_no_roles_together_with_a_role_is_refused", "AssertionError: connected", test=NOROLES),
    mutant("migrate: a run that names no role and not --no-roles is accepted", MIG,
        "    if not named and not no_roles:", "    if False:",
        "test_a_migrate_that_names_no_role_is_refused_before_connecting", "AssertionError: connected", test=NOROLES),
    mutant("migrate: --no-roles is not honoured", MIG,
        "    if not named and not no_roles:", "    if not named:",
        "test_the_explicit_flag_gets_past_the_refusal", "ConfigError", test=NOROLES),
    mutant("migrate: check_role_settings is not run", MIG,
        "            for note in check_role_settings(db, named):", "            for note in []:",
        "test_a_role_wide_default_survives_and_this_database_is_pinned_to_the_schema", "assert", test=E5R),
    mutant("role settings: a database-wide default is not refused", MIG,
        "        if setrole == 0:", "        if False:",
        "test_migrate_refuses_a_database_wide_search_path_that_is_not_the_schema", "unknown (OID=0)", test=E5S),
    mutant("role settings: a role-wide row that this database overrides is not skipped", MIG,
        "            if role in wide:\n                continue  # overwritten by the SET below",
        "            if False:\n                continue  # overwritten by the SET below",
        "test_e5e_a_role_with_a_role_wide_row_and_a_row_for_this_database_is_changed_once", "could not be repaired", test=NEW),
    mutant("role settings: the read-back is not checked", MIG,
        "    if left := _effective_rows(_path_rows(db, named), schema):", "    if left := []:",
        "test_e5e_a_search_path_default_that_the_repair_did_not_change_is_refused", "DID NOT RAISE", test=NEW),
    mutant("role settings: what changed is not reported", MIG,
        "        changes.append(note)\n", "        pass\n",
        "test_a_role_wide_default_survives_and_this_database_is_pinned_to_the_schema", "assert", test=E5R),
    mutant("migrate: check_maintain is not run", MIG,
        "            check_maintain(db, named)\n", "            pass\n",
        "test_e5e_migrate_runs_check_maintain_for_the_named_roles", "assert [] == [", test=NEW),
    mutant("maintain: the version gate is lowered", MIG,
        "        < 170000\n", "        < 160000\n",
        "test_below_postgresql_17_nothing_is_checked_or_named", "MAINTAIN named", test=E5M),
    mutant("maintain: the grants are not revoked", MIG,
        "    for table, grantee in _maintainers(db, schema):\n        who", "    for table, grantee in []:\n        who",
        "test_a_maintain_grant_on_a_stop_table_is_revoked", "is still held on the stop tables", test=E5M),
    mutant("maintain: a grant that stays is not refused", MIG,
        "    if left := _maintainers(db, schema):", "    if left := []:",
        "test_a_maintain_grant_that_stays_after_the_revoke_is_refused", "DID NOT RAISE", test=E5M),
    mutant("maintain: a named role that can maintain through a membership is not refused", MIG,
        "    for role in named:\n        for table in _STOP_TABLES:\n            if _holds(",
        "    for role in []:\n        for table in _STOP_TABLES:\n            if _holds(",
        "test_a_named_role_that_can_maintain_through_pg_maintain_is_refused", "DID NOT RAISE", test=E5M),
    mutant("app: a reset_credential_ref that the runtime reads is accepted", APP,
        "        if ref and collides(ref, runtime_names, file_backed=file_backed):", "        if False:",
        "test_a_secret_the_runtime_reads_that_folds_to_the_reset_ref_stops_the_start", "DID NOT RAISE", test=E5B),
    mutant("app: the reset_credential_ref is not checked (only the release ref is)", APP,
        '    for ref_field in ("release_credential_ref", "reset_credential_ref"):',
        '    for ref_field in ("release_credential_ref",):',
        "test_a_secret_the_runtime_reads_that_folds_to_the_reset_ref_stops_the_start", "DID NOT RAISE", test=E5B),
    mutant("app: a path-shaped ref is accepted", APP,
        "        if ref and path_form_problem(ref, file_backed):", "        if False:",
        "test_a_dot_segment_ref_gets_a_path_form_message_not_the_collision_text", "DID NOT RAISE", test=H4),
    mutant("collides: a path-shaped name does not fail closed for a file-backed provider", SECN,
        "    if file_backed and (is_path_shaped(ref) or any(is_path_shaped(n) for n in names)):", "    if False:",
        "test_collides_fails_closed_for_a_file_backed_provider_when_there_is_something_to_compare", "assert", test=H4),
    mutant("collides: no names still fails closed", SECN,
        "    if not names:\n        return False\n", "",
        "test_e5e_collides_with_no_names_is_false_for_a_file_backed_provider_too", "assert True is False", test=NEW),
    mutant("collides: the file-system fold is not added", SECN,
        '        out.add(canonical_secret_name(unicodedata.normalize("NFKC", name).casefold()))\n', "        pass\n",
        "test_a_folding_file_system_name_collides_with_the_sender_for_mounted_file", "assert", test=H4),
    mutant("cli: the path-shaped reset ref is not refused", CLI,
        "        if reset_ref and path_form_problem(reset_ref, _file_backed(b)):", "        if False:",
        "test_the_reset_command_gives_the_path_form_message", "Failed: connected", test=H4),
    mutant("cli: two names for one login are not refused", CLI,
        "        if reset_ref and _same_login(secrets, reset_ref, [b.store.dsn_secret_name]):", "        if False:",
        "test_a_reset_ref_holding_the_same_login_under_another_name_is_refused", "assert", test=E5B),
    mutant("cli: the still-ON reset exits 0", CLI,
        '"a second reset erases that stop too.",\n            file=sys.stderr,\n        )\n        return 2',
        '"a second reset erases that stop too.",\n            file=sys.stderr,\n        )\n        return 0',
        "test_reset_exits_2_and_says_still_on_when_the_read_back_is_on", "assert", test=UNIT),
    mutant("cli: the still-ON message does not warn against a second reset", CLI,
        '"have just set it, or an older flag is on. Check the stop reason with them before resetting again: "',
        '"have just set it, or an older flag is on. "',
        "test_a_reset_that_finds_the_switch_on_does_not_say_reset_again", "assert", test=E5B),
    mutant("cli: the still-ON message does not say who set it", CLI,
        "            f\"set by {state.by!r} at {state.ts.isoformat()}\"", "            \"set by someone unknown\"",
        "test_a_reset_that_finds_the_switch_on_does_not_say_reset_again", "assert", test=E5B),
    mutant("cli: the unknown setter is not said", CLI,
        '            else "set by someone unknown"', '            else ""',
        "test_e5e_a_reset_that_finds_the_switch_on_with_no_known_setter_says_so", "someone unknown", test=NEW),
    mutant("cli: a reset with the audit down exits 2, not 3", CLI,
        '"The kill switch stays ON. Fix the audit store, then try again.",\n            file=sys.stderr,\n        )\n        return 3',
        '"The kill switch stays ON. Fix the audit store, then try again.",\n            file=sys.stderr,\n        )\n        return 2',
        "test_e8_cli_reset_with_the_audit_down_exits_3_and_clears_nothing", "assert"),
    mutant("cli: an unreachable store at the read-back exits 2, not 4", CLI,
        "        return 4 if is_connectivity_error(exc) else 2\n    if state.on:", "        return 2\n    if state.on:",
        "test_reset_exits_4_when_the_state_cannot_be_read_back_because_the_store_is_gone", "assert", test=UNIT),
    mutant("cli: a read-back that fails with an answer exits 4, not 2", CLI,
        "        return 4 if is_connectivity_error(exc) else 2\n    if state.on:", "        return 4\n    if state.on:",
        "test_reset_exits_2_when_the_read_back_is_answered_with_an_error", "assert", test=UNIT),
    mutant("cli: a clean reset does not exit 0", CLI,
        '    print(f"kill switch OFF (by {by})")\n    return 0', '    print(f"kill switch OFF (by {by})")\n    return 1',
        "test_reset_exits_0_and_says_off_only_after_reading_off", "assert", test=UNIT),
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
    "S2: the from-16 'no effect' note is removed",
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
    "S2: the note is not appended to the refusal message",
    "S2: a vouched role is not listed for being a member of a listed role",
    "S2: the owner is a seed of the vouched walk (only superusers are outside)",
    "S2: a superuser or the owner is a seed of the vouched walk",
    "S2: an accepted CREATEROLE role is listed for being a seed (flag TRUE)",
    "S2: a vouched role is listed for being a member of another vouched role",
}


def _server_version() -> int:
    import psycopg

    with psycopg.connect(os.environ["HADAVIN_TEST_PG_DSN"]) as db:
        return int(db.execute("SHOW server_version_num").fetchone()[0])


def _killer(name: str, test: str = TEST) -> tuple[int, str]:
    # A mutant that keeps the size of the file (``return 2`` -> ``return 0``) and is written in the same second as
    # the clean file would be served from the clean bytecode: every killer gets a fresh bytecode cache.
    with tempfile.TemporaryDirectory() as cache:
        done = subprocess.run(  # noqa: S603 - this interpreter, a fixed test id
            [sys.executable, "-m", "pytest", f"{test}::{name}", "-q", "-x", "-p", "no:cacheprovider"],
            cwd=ROOT, capture_output=True, text=True, timeout=900, check=False,
            env={**os.environ, "PYTHONPYCACHEPREFIX": cache},
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
        killer = m.only_test + PARAM.get(m.name, "")
        if (m.name in GE16 and version < 160000) or (m.name in LT16 and version >= 160000):
            tally["N/A"] = tally.get("N/A", 0) + 1
            print(
                f"N/A      | {m.name} | needs the other PostgreSQL branch (this is {version}) | {killer}",
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
        key = (m.test_file, killer)
        if key not in clean:
            clean[key] = _killer(killer, m.test_file)[0] == 0
        if not clean[key]:
            verdict = "BASELINE FAILS (the killer fails on the clean tree)"
        elif missing:
            verdict = f"NOT APPLIED (the old text is not in {', '.join(missing)})"
        else:
            try:
                for f, text in after.items():
                    (ROOT / f).write_bytes(text.encode("utf-8"))
                code, out = _killer(killer, m.test_file)
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
        word = verdict.split(" ")[0]
        tally[word] = tally.get(word, 0) + 1
        print(f"{verdict:8} | {m.name} | {m.file} | {killer}", flush=True)
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
