<!-- full hand-back report of sub-agent a061e753, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

PLAN REVIEW round 2 (design), P3a-2 round 13, ticket rev 2

VERDICT: NOT READY for build. Blocker 0, Major 6, Minor 9, Nit 2.
All 8 round-1 Majors have a design in the text, and I judge 5 of 8 closed. Two are closed only in part and one has a new hole.
- Closed: M2 (step-8 failures), M4 (pg_monitor fix), M5 (grantor), M7 (O5), M8 (options).
- Partly closed: M1 (oracle), M3 (COMMIT unknown), M6 (object side).
- The six-commit order is not green per commit as written.
- Most Majors are fixable in the ticket text. The oracle one (F1) needs probes before the text can be trusted.

What I read: the whole ticket (1115 lines), the round-1 design review, the author report, evidence README, and the outputs f2, dfg, a-revoke-grantors, e-redefer, h-pg-monitor, run_queries_r2, c-public-schema, mutclass (first 80 lines).
I ran no SQL. Statements marked "from memory" are my own PostgreSQL knowledge, not a probe.

I re-counted the mutant arithmetic: 29 retired (27 named plus MT1 and MT2), 45+2 re-pointed, 55 new (42+13), 288-29+55=314. It is consistent.

=== (1) Round-1 Majors: is there a design, not a table row ===

M1 (oracle blind spots) is PARTLY closed. See F1.
- The 7.2 table now covers all 37+2 effects, with every column, typed NULLs, CALL for procedures, UPDATE with no column on the right, and default rights via fresh objects.
- The author probed none of these attempts. The README lists no oracle probe. Only facts 18 and 19 touch it.
- Several attempts will not work as written.

M2 (step 8 failure) is CLOSED in design.
- All of step 8 sits in one try, outside the `_limit_error` try. The limits are set inside `verify`. There is a role-level timeout test. Fact 36 is a real probe: 100 of 100 cancelled without the limits, 100 of 100 passed with them.
- Residue: F7 (the order of the SET LOCAL statements).

M3 (COMMIT unknown) is PARTLY closed.
- The two probed cases are right (f2.out): the server refuses with an SQLSTATE, the connection stays open and the status is IDLE; the connection is cut, the status is UNKNOWN, and the row IS committed.
- The classification rule is too narrow. See F5.

M4 (pg_monitor) is CLOSED.
- Q2 filters system-schema items twice (SQL and `_judge`). The h-pg-monitor and run_queries_r2 outputs show no pg_catalog item for the pg_monitor member.
- Residue: the pseudo-membership `pg_database_owner` has no printable fix (F9).

M5 (grantor) is CLOSED for object rights and memberships. The probes a1-a12 are real and `Problem` carries the grantor.
- Residue (F9): the grant-option fix form has no `SET ROLE <grantor>` variant.

M6 (object side) is CLOSED by an honest decision. It is stated as an AUTHOR ADDITION, there is a CHANGELOG sentence, and the C10 third-role cells are "not promised".
- It is not "safe". It is the more permissive of the two options. See (9).
- O8 is a good catch of the author's own and holds up (see (5)).

M7 (O5) is CLOSED. It is struck and 1.4 says so. See (5) for what this does to retired tests.

M8 (`options=`) is CLOSED. Fact 35 is a real probe (d3: the keyword replaces the DSN `options`, so the role switch is lost; `connect` takes no `options` anyway). There is a C9 test.

=== (2) Six-commit order: NOT truly green per commit ===

F2. Major. Section 9.3 and 7.6, last bullet.
Commit 1 owns "tests/test_migration_verify.py" and its G command runs that file. Several tests the ticket puts in that file cannot pass at commit 1:
- `test_every_runner_catalog_read_is_pinned`. It checks that `_refuse_privileged_role`, `_read_back` and the others run only inside `pinned_read`. That change to `migrate.py` is commit 3.
- `test_the_rights_table_equals_what_apply_grants_is_called_with`. `_apply_grants` gets its `schema` argument in commit 3.
- `test_the_promise_table_is_the_same_in_the_docstring_and_the_changelog`. The markers land in commit 6.
- `test_every_problem_kind_is_produced_and_named`. It checks the CHANGELOG list (commit 6).
- "the rewritten TCMP tests of 5.4". They are rewritten against `_judge`, but the code they test (`_refuse_unlisted_grantees`) lives until commit 3.

Failure scenario: the builder follows 9.3 literally and commit 1's own G command is red. Either a test is skipped, which violates the repository's skip rule, or commit 1 absorbs commit 3.
Fix: give each test an explicit commit. Pure `_judge` tests and the Q-text tests go in commit 1. The AST, rights-table, rewritten-TCMP and promise-table tests go in the commit that makes them true.

F3. Minor. Section 9.4.
Commit 3 (package A2, estimated 2 sessions of 60 minutes) bundles:
- deleting about 700 lines;
- the new step order;
- a new exception class and cli exit code;
- COMMIT handling;
- about 100 test edits across 5 files;
- re-planting 45 mutants with killers;
- the step-8 tests.
That is not a 2-session unit. Nothing in the plan says what to do when a session ends mid-switch with a red tree. The "one commit because the deletion and new order depend on each other" argument is fine. The sizing is a guess presented as a plan.
Suggest naming a checkpoint inside commit 3 that is a branch-local WIP and not a commit on the pull request.

Not checked: whether the branch's skip rule allows module-level `pytestmark = skipif(not DSN)` (the ticket says it does, TR:87-130). I cannot read the branch.

=== (3) The oracle ===

F1. Major. Section 7.2 effect table.
The claim "an attempt shows every effect" is wrong for at least three effects, and probably more. This is from memory of the PostgreSQL source. The ticket's own sensitivity control would find them, but only at build time, after commit 2.
- E03 REFERENCES: `CREATE TEMP TABLE <u> (c type REFERENCES s.t (col))`. PostgreSQL rejects "constraints on temporary tables may reference only temporary tables" (42P16) before it checks the REFERENCES privilege. That is INCONCLUSIVE in every case. A permanent referencing table is needed, so the oracle must create one owned by the probed role (made by the superuser, then `ALTER ... OWNER`), then `ALTER TABLE ... ADD FOREIGN KEY`.
- E20 USAGE on a type and E21 USAGE on a language use `CREATE TEMP TABLE` and `CREATE FUNCTION pg_temp....`. They run on variant (T), which revokes everyone's TEMPORARY. Without TEMPORARY the role gets 42501 on the temp namespace before the type or language check. The oracle reads "refused" even when USAGE is held. Hidden excess.
  - The (T) variant needs TEMPORARY revoked only for E19. For E20 and E21 revoke only the type or language right.
  - Use attempts that do not need TEMPORARY: `SELECT NULL::s.typ`, and `DO $$ BEGIN END $$ LANGUAGE plpgsql`.
- E24 is similar but runs on the non-(T) variant, so it is fine.
- `REINDEX TABLE s.t` "on every relation" (the MAINTAIN direction): a view or sequence gives 42809, which is INCONCLUSIVE.
- INSERT, UPDATE and DELETE attempts on a view, materialized view, foreign table or sequence give 55000 or 42809 from the rewriter before any privilege check. Section 7.7 direction 2 says "every other operation the oracle tries on every object of the database". The shipped schema has views and sequences. So the CI promise test would fail with INCONCLUSIVE unless the oracle chooses attempts by relkind. The ticket does not say so.
- Confounding by schema USAGE: probing `other.t` as a role with no USAGE on `other` gives 42501 whatever the table right is. The fixtures for C10 and "E01 x C12 in another schema" must grant USAGE on that schema. The ticket does not say so.

Superuser login requirement: acceptable. CI's service container user is a superuser, and failing visibly is right. Under "Superuser or failure" the ticket handles the no-DSN case correctly.

One database per case: sound. It was measured at 24 ms (createdb_cost.out) and it removes cross-test leakage. Remaining hole (Minor, F10): the cluster-wide objects (tablespace and parameter rights) are protected only by an advisory lock plus `finally`. A killed run on a persistent dev cluster leaves `GRANT CREATE ON TABLESPACE ... TO PUBLIC`. That then poisons every later case's `verify` (everyone is judged cluster-wide). The "no test role left" session-end check does not cover tablespaces or parameter rights.

INCONCLUSIVE handling: right in principle (never classed allowed, the case fails). In practice it will fire often. The count test demands exact equality, so each INCONCLUSIVE has to be turned into a documented exclusion by editing three tables. That is acceptable, but expect many iterations. It is also why the oracle needs its own probe pass before commit 2.

Precision is not tested. The property (7.1) is one-sided. Outcome (i) only needs before equals after; outcome (iii) needs the oracle to see nothing. A false refusal is caught only by the 12 clean controls. Note that `verify` is deliberately conservative (ADMIN-OPTION-only memberships, INHERIT FALSE) while the oracle only tries `SET ROLE`. So that part of the oracle never confirms a refusal was needed. Fine, but say so.

=== (4) Step 8, exit codes 2 vs 5, COMMIT, snapshot, limits ===

F5. Major. Section 4.1 step 7.
The rule for exit 2 is "the error has an SQLSTATE AND the connection is still open (`not db.closed`)". The probes show only two cases: 23503 with the connection open, and a cut with no SQLSTATE. Not probed: a server FATAL during COMMIT (57P01 admin shutdown, 57P02 crash, 57P03, class 08, XX).
- libpq can hand psycopg the ErrorResponse with an SQLSTATE before it notices the closed socket. Then the "SQLSTATE and open" test misclassifies a possible committed outcome as "refused, nothing was kept, exit 2".
- That is the exact false claim this step exists to remove.
Fix: classify by SQLSTATE class, not by connection state. Exit 2 only for classes the server uses to report an abort of a live transaction: 23, 40, 55P03, 57014 and the like, on a connection whose transaction status is IDLE. Everything else, including any 57P0x, 08 or XX, is "unknown", exit 5. Add a probe or test with `pg_terminate_backend` at COMMIT. The ticket admits it has not seen how psycopg reports this (10.4, last bullets), and `test_a_lost_connection_at_commit_gives_exit_5` asserts wording only.

Step 8 on an autocommit connection: `store/postgres.connect` sends `psycopg.connect(dsn, autocommit=True)` (checked, postgres.py:146). Setting `db.isolation_level`, `db.read_only` and then `db.transaction()` on an autocommit connection is the plan. No probe shows that the BEGIN carries REPEATABLE READ and READ ONLY in that mode. The test `test_step_8_reads_one_snapshot` will show it, but only after the build.
Minor: add the 5-line probe before commit 1.

F7. Minor. Section 3.1, "How it runs", and fact 36.
`pinned_read` runs `SET LOCAL search_path` FIRST and the two limits AFTER. The probe that passed 100 of 100 (g3) put the limits first. Under a role-level `statement_timeout = 1`, the search_path statement, the `BEGIN` and `connect`'s own `SET TIME ZONE` all run under 1 ms (the ticket calls the last one luck).
- A flaky exit 5 on every run for such a role is possible.
- Put the limits first.
- PostgreSQL 17 (the CI version) adds `transaction_timeout`. A role-level value kills the whole transaction. It is not neutralised by `RECIPE_TIMEOUTS`. The result is still an honest exit 5, but the "saved role setting cannot stop the check" claim is statement_timeout only.

Exit codes: exit 5 is new, and cli.py in main uses 0-4 only (checked, no `return 5`). `AppliedNotVerifiedError` outside `ConfigError(ValueError)` is correct. Main's errors.py has `ConfigError` only, so the new class is a new base for library callers. That is fine, but say so in the CHANGELOG ("library callers now see a new exception after a committed run").

Step 7(b) skipping step 8: fine. The message tells the user to run migrate again.

=== (5) Rule O8, retired tests, weakening ===

O8 is sound. A package table or function in the schema of the run must be owned by a role of the family. Without it, a table handed to a third role in the run schema would pass. Q2's third clause returns the row (run_queries_r2.out shows `app.handed` owned by `q_third`). Minor gaps:
- O8 matches by name against `managed_relations` and `managed_functions` only. An unmanaged table a file creates and hands to a third role, in the run schema, is not judged. 1.4 does not list this as a non-promise.
- A schema (the run schema) handed to a third role is not covered by O8 either. The old code refused owner change for three kinds including schema (MIG:45-48), and the retired test was "for every kind". The re-pointed replacement covers table, view, sequence and function only.
- There is no named effect "owner handed to a third role" in E01-E39, although C10 refers to it.
Put it in 1.4 or add the effect.

F6. Minor. Section 5.4, retired tests.
Retiring tests whose code is deleted (the six TCMP tests, the field-comparison tests) is not a weakening. Several TPG retirements are different. They pinned a REFUSAL that the new design now ALLOWS:
- `test_an_owner_handed_over_by_dynamic_sql_is_refused_for_every_kind`
- `test_with_the_printed_role_an_owner_handed_over_is_the_one_cause_of_the_refusal`
- `test_a_function_that_kept_a_foreign_owner_...` (replaced by a control that asserts the opposite)
They are justified by O5 being struck and by the narrowed object side. Both are listed in 10.3, but the retired-test list itself does not separate "code gone" from "refusal dropped by decision".
9.1 item 24 says "no weakened or deleted test outside the lists of 5.4 and 5.4b". That makes the author's own list the authority.
Fix: add a column "refusal dropped on purpose, lead must sign off" to 5.4 and tie it to 10.3 items 3 and 11.

=== (6) Rung table (section 8) ===

F4. Major, process. Section 8, rows for pg_permissions, pgTAP and ldap2pg.
They are explicitly "from memory, UNVERIFIED (not researched live)" and the author report says the same. I could not verify them either. Under the project's rule 20 an outside-tool row must be live-researched before it supports a verdict.
- The KEEP-CODE verdict is probably right, for reasons that do not need the tool facts: the check must run as a plain role, inside the migration transaction, with no server-side install.
- But the table's "what only our code gives" cell says "least privilege ... is a safety guarantee of the product". That is a reason to care, not a capability that no tool has.
- Either research the three tools (current version, licence, last release, whether they read memberships, large objects, parameter rights, default rights; and whether a run-time-callable form exists), or rewrite the rows as "not evaluated" and rest the verdict on the stated constraint only. As it stands the verdict is unsupported on paper.
The behavioural-oracle and `pg_dump` rows are fine (own code and an existing tool in CI).

=== (7) PostgreSQL 17 (CI) vs 16 (probed) ===

Everything in facts 30-39 was run on 16.15 only. The author says so (Read first item 1, fact 25).
Gaps beyond what the ticket lists:
- Fact 25 (same 14 ACL columns on 17) is memory. The self-check will fail first in CI, after the build. Acceptable as a guard, but it means the first sight of any 17 difference is at the end of the build.
- The REVOKE and GRANTED BY forms (facts 30-32) and the `SET ROLE <grantor>; REVOKE ...` fix were not run on 17. I believe 17 behaves the same (from memory).
- MAINTAIN: the owner's own item on 17 includes MAINTAIN. O1 and S5 judge owner items as allowed, so this is fine. A named role never gets MAINTAIN from the grant map.
- `transaction_timeout` (F7).
- `file_fdw` and `allow_in_place_tablespaces` are only claimed for the `postgres:17.10` image (10.4). I believe both are available there (from memory).
- 18 is not claimed, and the self-check plus rule D4 (unknown default kind) are the guard. That is honest.

=== (8) Scope, wording, undefined terms ===

F8. Minor. Section 6.4 contradicts section 10.1.
10.1 says "Not to build: more text rules or spellings". Section 6.4 adds a text rule (duplicate CREATE in `_scan`) and says it carries no security claim. If it is an accident guard it is the kind of rule D-020 told the builder not to add.
Either move it to a split ticket or state the exception in 10.1.

Scope: sections 6.1-6.3 (prepared-transaction message, unreadable lock view, CI server setting) are operator safety and independent of `verify`. They are already in a separate commit 4, so they can ship alone. The ticket as a whole is about 8 builder sessions plus a matrix of about 1000 cases that CI runs on every pull request. If the matrix exceeds 20 minutes the ticket says the builder "reports the number to the lead", which leaves CI cost undecided. Say now what happens (nightly job or fewer cells), not later.

Wording for non-technical readers: section 1 is good. The terms "role", "grant map", "migration role", "everyone" and the three promise rows are explained plainly. Undefined or late-defined in the part an owner reads:
- "family" (defined only in the Q1 text).
- "subject".
- "hidden COMMIT".
- "owning group" (1.4).
- "carrier", "effect", "cell", "outcome (i)".
- The prefixes R-B1, D-M2 and so on in the changes list refer to documents the reader does not have.
- Several "Read first" items cite files under `handover/` that are not in the snapshot.
Add a 10-line glossary.

The first sentence of the stderr message ("the database is over-privileged now; run these statements") is clear. See F11 for its danger on a shared database.

=== Findings not tied to one question ===

F9. Minor. Section 3.3 S2 and 4.2.
S2 refuses `pg_database_owner` as a built-in membership (fact 8), which is not a row of `pg_auth_members`. Q1b has no row for it, so there is no grantor and no `REVOKE pg_database_owner FROM x` statement is possible. The ticket says "the fix is the membership statement with its grantor" for every S2 line. For this one the fix must be by hand ("the role owns the database; `ALTER DATABASE ... OWNER TO`").
Also, Q2's `fam` and `subj` CTEs are built from `pg_auth_members` and do not include the pseudo-role. Python adds it to Q1 only. For a migration role that owns the database (variant O, allowed by D-020), the `public` schema is owned by `pg_database_owner` and shows `family_owned = false` in Q2.
The grant-option fix form in 4.2 (`REVOKE GRANT OPTION FOR ... CASCADE`) has no `SET ROLE <grantor>` variant. A grant option held from another grantor stays after the superuser runs it (same mechanism as fact 30). The test cases listed cover rights, not grant options.

F11. Major. Section 4.1 step 2 and 4.2, and 9.5 upgrade note.
The refusal message for a shared database prints `REVOKE ... FROM PUBLIC` on another application's tables and says "a database administrator runs the statements printed". The test `test_printed_statements_remove_every_problem_...` makes "run them all" the intended use.
- The warning "if such an object belongs to another application, do not remove it" exists only in the CHANGELOG, not in the message the administrator reads at 2 a.m.
- This is the round-1 M4 class (a printed fix that damages something outside the package). Round 1 closed it only for system schemas.
Fix: when the object is outside the schema of the run, or owned by a role outside the family, the line must carry "not this package's object: confirm with its owner before running" and the statement block must mark those statements.

F12. Major, design gap. Section 3.4 line 2, S5, O6.
Extension members are excused for SECURITY DEFINER (S7) but not for baseline line 2. Any database with `pg_stat_statements` (public view, `GRANT SELECT ... TO PUBLIC` in its install script), PostGIS (`spatial_ref_sys`, `geometry_columns`, `geography_columns` readable by everyone) or similar is refused at step 2, with a printed REVOKE against an extension-owned object. That is from memory of those extension install scripts, not probed.
- A later `ALTER EXTENSION UPDATE` re-grants and the refusal returns.
- The only way out stated is "a database of its own".
This is the most common real-world false refusal I can see. D-020 says "no exception list", so the ticket may be right to refuse. But it must be a stated decision for the owner (questions list), with the alternative "objects that are members of an extension the family does not own are judged only for the named roles and not for everyone". It is not in the owner questions or in 10.3 at all.

F10 (above) and F7 (above) are Minor.

=== (9) The three owner questions: are the safe defaults right ===

Author's report lists the owner questions as (1) sharing the migration role or the schema with another application, (2) confirm striking O5, (3) the CI route for `max_prepared_transactions`.

1. Sharing: the defaults taken are mixed.
   - The pre-flight refusal of another application's function or type in the run schema (10.3 item 5) is the strict choice.
   - The object side limited to the run schema (item 11) is the permissive choice. It leaves a gap for third-role rights outside the run schema, and is justified by the shared-role case.
   - So the "safe default" is strict in one place and loose in another, and one owner answer flips both. If the owner says "supported", F11 and F12 bite first.
   - For a security path, I would present it as one question with both consequences and add the extension question (F12).
2. O5 struck: acceptable as a default. The round-1 false refusal was real (a normal group-owner setup with no way out). It does leave the group-handover refusal gone. Cheap improvement the author did not take: print a non-refusing notice when a package table is owned by a group with other members. That makes the non-promise visible in a run, not only in a document.
3. CI route: the default (the test FAILS when `max_prepared_transactions` is 0) is safe and is the right default. The first route (`docker exec ... ALTER SYSTEM` plus `docker restart` of a service container) is plausible and untried. The ticket has a second route, so it is acceptable.

=== Not checked ===

- Branch `core/P3a-2-clean` at 4d328e3d: every claim about it. That is every MIG:/MN:/TPG:/TW:/TCMP:/MUT:/TR: line number, the existence and content of every named test and mutant, the skip rule at TR:87-130, `_refuse_foreign_owned` and `_managed_names`, `RECIPE_TIMEOUTS` values (60 s and 5 s), the CHANGELOG lines, ci.yml lines, `problems_with_the_list`, `heavy_slot.py`.
- Main 2a8c2aa: I confirmed only that `effective_problems` exists (migrate.py:193), `_apply_grants` is at 169 with `REVOKE ALL` and no CASCADE (line 179), `connect` has the signature the ticket cites (postgres.py:125-132, autocommit True at 146, `SET TIME ZONE` at 148), cli.py has no `return 5`, and errors.py defines only `ConfigError`. I did not verify the ticket's statements about D-020, D-019 or the design-review documents.
- Probe scripts: I read the outputs, not the `.sql` and `.py` files. I did not re-run any probe. I did not read queries.py or run_queries.out beyond r2, b-row-types.out, a2-orphan-column.out, x-extension-owner.out or createdb_cost.out in full.
- Mutant coverage claims (29 and 47 and 16 lists, "NOT-LISTED" rows in mutclass.out beyond line 80).
- Any PostgreSQL 17 or 18 behaviour.
- Every "from memory" PostgreSQL claim in this report (error order for REFERENCES on temp tables, TEMP privilege check order, REINDEX on non-tables, FATAL handling by libpq, extension install-script grants). Treat them as hypotheses for the author to probe, not facts.
- The cost of Q2 on a large catalog (acceptance 21 measures it; the evidence is a 49-row setup).
- Whether psycopg 3.3.6 `Rollback` raised from a post-yield helper behaves as `pinned_read` needs on an autocommit connection. It is plausible and not probed.

Relevant files:
- /home/user/build/snap/p3a2-plan-r2/tickets/P3a-2-r13-verify-final-state.md
- /home/user/build/snap/p3a2-plan-r2/evidence/f2.out
- /home/user/build/snap/p3a2-plan-r2/evidence/dfg.out
- /home/user/build/snap/p3a2-plan-r2/evidence/a-revoke-grantors.out
- /home/user/build/snap/p3a2-plan-r2/evidence/h-pg-monitor.out
- /home/user/build/snap/p3a2-plan-r2/evidence/run_queries_r2.out
- /home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk/store/postgres.py
