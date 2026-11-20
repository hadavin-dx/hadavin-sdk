# review-code-who-else-2 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

RESULT REVIEW of who_else_can_clear (worktree lead-fix-B, commit 7caa8c15c). Read-only static review. I had no shell, no git and no PostgreSQL, so I could not produce git diff 2dae86b68 7caa8c15c. I read the final files in the worktree and judged the code, not the diff. The builder file build-who-else-round2.md is only a patch script (it edits stop_state_mutants.py), so none of its evidence claims could be checked against it. I ran nothing.

COUNTS: Blocker 0, Major 2, Minor 4, Nit 5.

BLOCKER
None found. I traced the query in migrate.py:284-317 (_CAN_CLEAR) and found no unlisted path that clears a stop through grants, memberships or ownership, apart from the limits in the findings below. No SQL injection: the only .format substitutions are the two constants usable and creators (migrate.py:379-381); the reset name is bound through %(reset)s; there is no stray brace in the query; named roles pass _ROLE and _FORBIDDEN_ROLES earlier.

MAJOR

1. Test isolation reintroduces E4 on PostgreSQL 14/15 and under xdist (tests/test_stop_state_roles.py:44-47, 1371).
- Only this one module takes the advisory lock GATE (shared at line 176, exclusive at 1371).
- Nine other test files also call migrate with a runtime, portal, purge or reset role: warden_port/test_audit_chain.py, test_stop_state_unit.py, test_p7_store.py, test_p7_tick.py, test_p2_postgres.py, test_k5_round10_postgres.py, test_k2_migrations.py, test_audit_drain.py, contracts/kinds/store_postgres.py. None takes the lock.
- On PG below 16, test_s2_below_16_a_createrole_login... creates a LOGIN CREATEROLE role, which creators lists server-wide. Any of those other modules running migrate with a role during that window gets a false ConfigError. That is the same flake ESCALATIONS E4 described.
- It cannot appear on PG17, which is why the claimed green runs hide it. The claimed PG15 run (197 passed) probably ran serially, so it would also hide it.
- Fix: make the below-16 CREATEROLE case not create a real server-wide role. Either unit-test the SQL on a throwaway database or cluster, or have every migrate-with-roles test module take the shared GATE via a conftest fixture. Also run the suite on PG15 with -n 3 and attach the output.

2. The below-16 rule "every non-superuser CREATEROLE role" makes migrate depend on unrelated roles of the whole server, with no way out (migrate.py:380, runbook 50-52, 61-62).
- The path is real: on PG14/15 a CREATEROLE login can GRANT the reset role to itself. But the check is server-wide.
- Scenario: a shared PG15 server (or managed PG15 such as Azure or RDS) holds another application's admin login with CREATEROLE that does not own these tables. Migrate refuses forever. The only remedy is REVOKE CREATEROLE from a role the operator may not own, or an upgrade to PG16.
- This contradicts the purpose of E4 (healthy shared servers must not be refused). The builder admits the risk is untested (inputs/build-who-else-round2.md line 15).
- Fix, one of these: (a) an explicit, audited allow-list option for named administrator roles, which is the fix the earlier review AB-2 already proposed; (b) at least a documented decision by the owner that managed PG 15 and older is out of scope for named-role migrate, with the refusal message saying so. The runbook currently gives no way out.

MINOR

3. UPDATE, DELETE and TRUNCATE on kill_switch_stops and kill_switch_clears are not read by the check (migrate.py:285-288). It relies on the append-only triggers.
- A trigger is not enforced when session_replication_role = replica. From PG15 a superuser can GRANT SET ON PARAMETER session_replication_role to any role. A role holding DELETE on the stops table plus that parameter right can then delete a stop. It is not listed and not documented.
- Fix: add one sentence to the runbook Limits and SECURITY.md (no code). Revoking SET on that parameter is the operator's job.

4. Stale runbook step 2 (docs/stop-state-runbook.md:12-15) still says migrate reads only kill_switch (UPDATE) and kill_switch_clears (INSERT). Lines 58-65 describe the real rule (DELETE, TRUNCATE, TRIGGER, ADMIN, CREATEROLE). A reader of step 2 is told less than the check does. Line 65, "Before this change (2026-11-20) ...", is a dated change note inside a runbook; delete it.

5. The point-in-time nature is not stated. The check runs only when migrate runs. A role or grant added afterwards is not seen. SECURITY.md:21-23 ("only the reset login can") reads as continuous. Say "as of the last migrate with all roles named".

6. Mutant list (tests/stop_state_mutants.py).
- Two entries are the same edit (lines 263-268, the empty search_path and the schema without tables: same old and new text, different killer test). That is one mutant counted twice.
- There is no mutant for the clause m.member NOT IN (SELECT oid FROM outside) (migrate.py:309). Only the base-set exclusion is mutated.
- There is no mutant for relkind IN ('r','p') in _check_stop_relations.
- The claimed "KILLED 61/60" is not a coherent ratio and I cannot reproduce it. Re-run and paste the real count of killed, N/A and EQUIVALENT.

NIT

7. The EQUIVALENT claim (grantee 0 removed) is correct: no role has oid 0, so it cannot change the result. But that means the filter WHERE grantee <> 0 (migrate.py:303) is dead code. Delete it (the PUBLIC branch at 312 does the work) and delete the mutant with it.
8. Over-listing in the recursion: usable is evaluated per edge, not along the path. Example: M is a member of Y with INHERIT only, and Y is a member of X with SET only. M is listed, but M cannot reach X. It is conservative and rare.
9. A holder of only DELETE or TRUNCATE on kill_switch, or of a column INSERT grant that excludes stop_id, cannot clear a stop alone. The latter fails because stop_id has no default. Both are listed; this is a harmless false refusal. Docs say "clear or defeat", which is slightly generous.
10. The docs say "any member (with or without inheritance)", but on PG16 and later a membership with INHERIT, SET and ADMIN all false is not listed (correct behaviour, loose wording).
11. A grant of ADMIN on the owner role (not membership) is not followed, because the owner is outside the guarantee. This is covered by the "membership in the owner" wording but not named.

ANSWERS TO THE HUNT LIST
(1) Unlisted paths. Covered correctly by reading: table and column grants, PUBLIC, NOINHERIT members (SET ROLE), chains of members, ADMIN-only on PG16 and later, CREATEROLE below 16, WITH GRANT OPTION (the grantee also holds the privilege), default privileges (relacl is materialized when the table is created, and the tables are made in the same transaction), dropped columns, TRIGGER on all three tables, DELETE and TRUNCATE on the flag, a temporary table shadowing a stop table (checked by to_regclass). Not listed and not fully documented: finding 3 only. Documented as outside the guarantee: owner (can DROP the tables), schema owner, superuser, managed-database admins, predefined roles, SECURITY DEFINER functions. Row-level policies, rules and event triggers need ownership or superuser, so they add no new path. A search_path that differs between the migrate login and the runtime login is documented ("set the same search_path") but not checked in code; the store takes its schema from its own session (postgres.py:211).
(2) False refusals. The query is scoped to current_schema() relations only. A second schema and unrelated roles are ignored, and test_s2_a_second_schema... and test_s2_roles_of_the_server_with_no_grant... show it. The only server-wide input is the below-16 CREATEROLE rule (Major 2).
(3) Docs. The Limits text matches the code, except for the staleness in findings 4 and 5 and the missing item in finding 3. I found no claim that the code contradicts.
(4) The changed ADMIN-creator test expectation (listing the creator) is right. A holder of the ADMIN option can GRANT the reset role to itself with SET, and can ALTER its password when it also has CREATEROLE. The usual case, where the migrate login is both the table owner and the creator, is excluded as the owner, so a standard deployment is not refused. The test also proves SET ROLE is denied today, then that REVOKE ADMIN OPTION FOR makes migrate pass.
(5) Requiring all three tables is safe. Migrations 0001 (kill_switch) and 0006 (the other two) run inside the same transaction before the check (migrate.py:450-455, then 489). A plain migrate naming no role skips the check. A deployment whose tables sit in another schema, or where one was dropped by hand, is refused with a message that names schema, search_path and what is missing. That is correct fail-closed behaviour.
(6) PG14 and PG16 were not run; only 15 and 17 are claimed. Points to confirm on 16: the implicit ADMIN-only grant to a creator and the REVOKE ADMIN OPTION FOR statement, whose grantor rules changed across 16.x (the test shows it on 17 only). CREATE OR REPLACE TRIGGER in 0006 needs PG14 or later.
(7) Weak tests: _refused_naming checks the role name with a substring test (random suffixes make a false pass unlikely). The version-gated mutants are N/A on the wrong server, so each gets only one server's evidence.
(8) SQL built with sql.Identifier: the new code builds no identifiers from input. Pass.
(9) Stage names: grep for staging or dev as a stage in the five touched files found nothing. No lock-in: managed-database role names appear only in documentation.

STATUS OF EARLIER FINDINGS
- B-WE-M1 (non-superuser admin-like roles): CLOSED in the code, by reading. Below 16 every CREATEROLE non-superuser is listed (migrate.py:380). From 16 a membership counts when INHERIT, SET or ADMIN is true (379). Tests exist for the ADMIN-only creator, ADMIN on a role holding the right, CREATEROLE below 16, and no listing from 16 without membership (test lines 1320-1392). The managed-database admin roles are now documented as outside the guarantee. Residual: Major 2 (no escape on managed PG 15 and older).
- B-WE-M2 (fail-open when nothing is found): CLOSED. _check_stop_relations (migrate.py:320-351) demands all three tables in current_schema() and checks that bare names resolve to them. It is called first in who_else_can_clear (373). Four refusal tests plus three mutants kill the alternatives (test lines 1426-1460).
- B-WE-M3 (TRIGGER, DELETE, TRUNCATE, owner, DEFINER documentation): CLOSED. TRIGGER on all three tables and DELETE and TRUNCATE on the flag are read (285-288), with parametrized tests and mutants. Owner DROP and SECURITY DEFINER functions are documented. Remaining small gap: finding 3.
- B-WE-m1 (mutants pinned on both PG branches): CLOSED in design (GE16 and LT16 sets, version gate in the runner, one mutant per PG branch). The count claim is unverified (finding 6).
- Ledger rows: B-E4 is closed for the false-refusal on unrelated schemas and roles. It stays open for below-16 server-wide CREATEROLE (Major 2) and parallel test isolation on PG 15 (Major 1). I would not close B-E4 until those two are decided.

NOT CHECKED
- I ran no test, no mutant, no PostgreSQL, no lint. The claims 199 passed on 17.10, 197 passed on 15, and KILLED 61/60 are all unverified.
- I did not produce the diff, so I did not confirm which lines changed versus 2dae86b68. In particular I could not confirm the claimed removal of the old ADMIN-only expectation except from the builder note in inputs/build-who-else-round2.md.
- I did not read the full text of every test body outside the S2 section (lines 1150-1530), the World fixture beyond line 70, cli.py, or the other nine modules' use of migrate beyond finding their names.
- I did not run anything on PG14 or PG16, nor on a managed server.
- I did not verify the remote or CI behaviour of the GATE lock.

Files reviewed (absolute): C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\lead-fix-B\src\hadavin_sdk\store\migrate.py, ...\store\postgres.py, ...\store\migrations\0006_stop_state.sql, ...\docs\stop-state-runbook.md, ...\SECURITY.md, ...\tests\test_stop_state_roles.py, ...\tests\stop_state_mutants.py; plus the cloud-core-b ESCALATIONS.md, the earlier reviews review-code-who-else-1.md and the builder file build-who-else-round2.md.
