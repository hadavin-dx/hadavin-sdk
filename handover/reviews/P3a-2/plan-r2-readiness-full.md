<!-- full hand-back report of sub-agent a7f7ca0c, saved verbatim by the lead's script; model output, unverified unless the summary file beside it says otherwise -->

VERDICT: NOT READY. Blocker 0, Major 9, Minor 14, Nit 3. This is plan review round 2, implementation readiness, for the ticket in /home/user/build/snap/p3a2-plan-r2/tickets/P3a-2-r13-verify-final-state.md. Line numbers below are lines of that ticket file unless I say otherwise.

Round 1 B1 (commit order) and B2 (public schema) are answered in the text. The six-commit order is buildable in principle. Most of the other round 1 majors are closed on paper. What remains are gaps that stop a builder from finishing, and I found three places where the ticket contradicts itself. WP A1 can start today, but the builder will have to invent several interfaces (M5).

## 1. Can WP A1 start now?
Yes, with assumptions. These are missing or ambiguous (details in M1 and M5):
- The row shape that `_read` returns and `_judge` takes is not defined.
- The `Problem.line()` wording is given for only 4 kinds. The ticket's own list has 25 `PROBLEM_KINDS`.
- A group role reached by two named roles is not defined for rule S5.
- The `Problem` record has no field for ordering printed statements.
- Several tests named in 7.6 are not assigned to a commit. Some of them cannot pass at commit 1.
- There is no instruction for starting a Postgres 16 server and setting the DSN.

## 2. Findings

### Major

**M1. Commit 1 is not green as written, and the per-commit test assignment is missing (9.3 line 970, 7.6 line 877, 5.2 line 583, 3.3 line 426).**
- Commit 1's green command runs whole files: `tests/test_migration_verify.py`, `tests/test_migration_verify_pg.py` and `tests/test_migration_rules.py`.
- Line 877 puts these tests in `tests/test_migration_verify.py` with no commit label:
  - `test_every_runner_catalog_read_is_pinned` (AST check). It needs the `pinned_read` wrapping in `migrate.py`, which is commit 3.
  - `test_the_rights_table_equals_what_apply_grants_is_called_with`. It needs the commit 3 wiring.
  - `test_every_problem_kind_is_produced_and_named`. Line 426 requires each kind to be "named in the CHANGELOG list", which only exists in commit 6.
  - `test_every_catalog_name_in_the_queries_is_qualified`. Line 583 says the repository test greps the SQL constants of `MIG` as well, but those are unqualified until the edit assigned to no commit.
- Only the promise-table test is placed (commit 6).
- Fix: give a table "test -> commit" for every test in 7.6 and 7.8.
- Also state which commit adds the three new test files to `MIGRATION_TEST_FILES` (TR:28).
- Also state in which commit the `pg_catalog.` prefixing of kept `MIG` queries happens (see M7).
- Also state in which commit `problems_with_the_list()` learns to check parametrised killer ids (line 644). It is unassigned.

**M2. The environment and the acceptance commands cannot be run as written (9.1 lines 932-960, 6.3 line 720).**
- `DSN=... $T pytest ...` is used literally in about 15 items. Taken literally, that sets an env var named `DSN`, not `HADAVIN_TEST_PG_DSN`. The legend at line 932 only says what `DSN` stands for.
- No instruction says how to start "own Postgres 16" on this machine.
  - The ticket does not give the binary path, port or superuser.
  - The server needs `max_prepared_transactions` above 0.
  - Line 720 makes the prepared-transaction test FAIL when that is 0, so a default server fails the whole suite after commit 4.
  - The author's own cluster (`initdb`, port 56231) is not described in a reusable form.
- `$T` is `uv run --all-extras --group test`. With "no downloads", the ticket does not say whether the environment is pre-synced or `uv run --offline` is needed.
- Item 24 needs `bandit`, `gitleaks`, `tools/scan_repo.py` and `tests/stage_mutants.py`. The ticket says "copy the lines from the workflow at the final head", so a builder cannot tell whether they are installed offline. Item 24 also says "run header line 11" for `tests/migration_numbers_mutants.py` instead of giving a command.
- Item 19 (CI on PostgreSQL 17.10) cannot be run on this machine. It needs a push and a pull request, and the ticket never says who has that access.
- Item 8 asks for `-s` output and the cell counts. Item 12 expects the output line `N of N killed`. I cannot confirm from here that the runner prints that format (the tests are not readable).
- Items 10 and 24 both run the whole matrix and the whole suite. No time bound is given for either.
- Fix: one "how to run here" block with the exact initdb and start commands, the DSN value form, and the `uv` offline flag. Replace `DSN=...` with `HADAVIN_TEST_PG_DSN=<...>`.

**M3. The commit and work-package scheme contradicts itself on size, checkpointing and parallelism (9.3-9.4 lines 966-992, line 28).**
- Commit 3 (package A2) is one commit that:
  - deletes about 20 names;
  - installs the new order, `AppliedNotVerifiedError`, cli exit 5 and step 8;
  - edits about 25 fake-database wiring tests and 13 `test_k2` tests;
  - re-points about 22 `TPG` tests;
  - retires 29 and re-plants 45 mutants;
  - adds the 7.6 step-8 and COMMIT tests.
- A2 is estimated at 2 sessions of 60 minutes.
- Line 981 says "stops at 60 minutes with a commit". A session boundary inside the single commit 3 therefore produces a red commit.
- The branch is fast-forward only with no rebase (line 28). There is no rule for how a half-built A2 is kept, for example a side branch squashed at the end, or whether red WIP commits are allowed.
- The "Can run in parallel with" column (A1 || B1, C1 || B2) conflicts with one linear branch and ff-only.
- B2 (commit 5) is listed as depending on "A2, B1" only. Its mutants plant into code from commit 4 (C1):
  - the lock join and `l.pid IS NULL` (7.5 line 848);
  - the duplicate-CREATE rule (7.5 line 848);
  - LW7 and LW8 (5.5 line 642, 9.3 line 973).
  So B2 depends on C1 and cannot run in parallel with it.
- The 2-session estimate for A2 is not credible. It is also marked a guess at line 982.
- Fix: say how a multi-session commit is stored. Either split commit 3 into green steps (the order of 3.1-4.1 could be built beside the old code), or name a side-branch and squash rule. Add C1 to B2's dependencies. State that "parallel" means separate worktrees merged without rebase, or remove it.

**M4. The heavy-job rules do not match this machine (7.10 lines 900-908, 9.1 items 10, 12, 24).**
- The caller's environment has `heavy.sh` with 3 slots. The ticket says `tools/heavy_slot.py` does not exist and falls back to bare `timeout 3000`. It never mentions `heavy.sh`.
- Item 12 mutant batches use `HADAVIN_TEST_PG_DSN=... timeout 3000 uv run ...`.
- Items 10 and 24 run the matrix and the whole suite bare.
- Studio rule 2 requires heavy jobs to go through the slot tool.
- Fix: name `heavy.sh` and its arguments in 7.10 and in the item commands.
- Fix: say whether `timeout 3000` applies inside the slot.
- Fix: give the whole-suite run a time bound.
- Batch plan check: 314 = 55 + 65 + 97 + 97, and the batch sizes add up. The estimates are plausible but unmeasured.
  - The V* killers (10-20 s each, "estimate") could be much slower if a killer is a whole matrix.
  - `test_verify_cost_on_a_large_catalog` (5,000 tables, 20,000 functions, 2,000 large objects, 500 roles) is the killer of the "UNION ALL" mutant. Its fixture is rebuilt on every run, and the mutant itself waits for a 60 s statement timeout.
  - Whether `-m perf` tests are deselected when the mutant runner calls a killer is not stated.

**M5. Interfaces and semantics that A1 would have to invent (3.1 lines 163-219, 3.3 lines 448-449, 4.2 line 545).**
- `_read(db, ...)` "returns plain rows". Their shape is not given: tuples by position, dicts, or dataclasses.
  - The `_judge` signature is missing.
  - The pure tests rewritten in commit 3 and the wiring answers (5.4b) depend on the shape.
- S5 does not say what happens to an item for a group role that is reached by two named roles (for example both runtime and portal). It does not say whether the item must be allowed for each reaching role or for any of them. The table of rights per role kind (3.2) is unambiguous only for a direct grant.
- `Problem.line()` text is given for 4 kinds. The ticket's own `PROBLEM_KINDS` has 25 kinds. The wording for the rest is left to the builder.
- Statement ordering (4.2 line 545) needs "object rights granted by someone other than the owner" first. `Problem` carries `grantor` but not the owner or `grantor_is_owner`. A builder must either add a field or parse the `fix` text.
- The ticket does not say which module and function builds the stderr message and the `statements` list from `Problem`s. It says only "How the statements are built".
- The 20-line cap (`_shown`) applies to exit-2 messages. Statements are printed only inside the capped lines, because standard output is used only for exit 5. A step 2 or step 6 refusal with more than 20 problems therefore shows fewer than all the statements, which contradicts the "all of them, not only the first 20" wording of line 535.
- `KNOWN_ACL_COLUMNS`: the value format ("mapped to the branch of Q2 or Q4") is not given.
  - The test "every live key appears, with its `pg_catalog.` prefix, in the text of Q2 or Q4" (line 507) cannot match as worded. The Q2 text has `pg_catalog.pg_class c` and `c.relacl` as separate fragments. Q0 returns `pg_class.relacl` with no prefix.
- `RUN_SCHEMA = ""` stays in `migrate.py`. `verify` must treat "" as "the schema of the run" without importing the constant. That duplicates the meaning.

**M6. The matrix cells are under-specified, and one carrier contradicts the rules (7.3-7.4 lines 799-844, line 837).**
- Carrier C10 is "(i) for named roles and everyone" in another schema that the migration role owns. Cell E11 (a function of the family left callable by everyone) is therefore expected to be refused there.
  - The rules do not refuse it. Baseline 3.4 line 3 limits "everyone gets nothing on family objects" to the schema of the run. The third bullet there says everyone's default on other objects is not judged except S7. The object side (3.3 line 453) is also limited to the schema of the run. 10.3 item 5 says option (a) would refuse every family function and type in every schema, so they are not refused today.
  - The oracle's expected set for everyone (line 789) contains only "functions of other owners". A family function in a second schema would be an excess the oracle sees while `verify` returns nothing. That produces "applied with excess:" for a case the design deliberately allows.
  - The same applies to a family-owned type or language with default USAGE for everyone in a second schema.
  - Fix: state the expected class for E10, E11 and E20/E21 under C10 explicitly, or move them to the "not promised" table.
- Q2's second WHERE clause also returns family-owned function, type and language items for everyone in all schemas (lines 347-349). The rules only use those rows in the schema of the run, so the clause returns more than anything uses.
- The ticket does not say how each of the 14 carriers performs each of the 39 effects, for example how C5 does E22. It does not say which cells are "empty by logic" or "server-refused". The builder must write those three tables (lines 844, 843-844) and the expected outcome per cell and per role-argument variant (line 821). Expectations derived from the code under test would be circular.
- Line 844 says "Clean controls (at least 12)". Only 10 are listed, and E27 and the group-owned database overlap.

**M7. The mutant lists are not closed (5.5 lines 634-646; the author's own `evidence/mutclass.out`).**
- `mutclass.out` lines 198-232 flag 35 "affected" ids that the author's lists should cover. These 15 are not in the retired, re-pointed or re-checked lists:
  - MW3 (only mentioned as "confirm still passes", line 628).
  - MW4 and MW5 (lines 1601 and 1604, both flagged "in a changed region").
  - LV2 and LV3 (lines 1556-1557).
  - N16, N17, N18, N19 (CHANGELOG-planted).
  - P1, P2, P3, P5, P6, P7 (CHANGELOG-planted).
  - Commit 6 rewrites the CHANGELOG. The rule at line 642 covers only mutants whose text is inside `migrate()` (MIG:1512-1677), so it does not cover the CHANGELOG ones. It says nothing about `migration_numbers.py` mutants either.
- Line 583 requires a `pg_catalog.` prefix on every kept query in `MIG` (432-477, 609-627, 669-684, 1257-1271). Many mutants plant into exactly those lines according to `mutclass.out`. Examples: M102 (476), T2-T5 (472-473), R4 (464), SC1 and SC2 (465, 452), NR2 (447), NS1 and NS2 (458, 444), NM1 (459), R2 (590), PS1 (591), SC5 (589), PA2-PA4 (623-625), FO and OW mutants (669-684). Editing those lines can break the "old text exactly once" check. None of these are in any list. `mutclass.out` did not flag them, so its classification missed the prefix edit.
  - Suggested rule: re-check every mutant whose `old` text is inside any line this commit edits, in any file.
- 5.4b item 1 requires "the users of `READS_BEFORE` and `WIRING_VAL`" to stay killed (line 628). The 16 re-checked ids in 5.5 (line 640) do not name them.
- Line 972 (commit 3) says "run them: batch 2 ids that exist at this commit". `--list-batch` is only built in commit 5 (line 974). Batch 2's membership (47 re-pointed, 16 re-checked, LW7, LW8) must be hard-coded in the runner. The ticket does not say where those id sets live.
- The 55 V* mutants:
  - Ids, planted text and killers are not enumerated. 13 killers are named (line 850). The builder invents the rest.
  - Counts check out: 42 + 13 = 55 and 288 - 29 + 55 = 314.
  - The retired (29), re-pointed (47) and re-checked (16) lists add up and match the ids, but I could not confirm they exist on the branch.

**M8. Query evidence: pasted texts match, but two items are not backed, and the "every name qualified" rule contradicts the pasted texts (3.2 lines 221-423, 3.1 line 208).**
- Compared with `evidence/queries.py`:
  - Q1, Q1b, Q2, Q3, Q4 and the step-4 query are identical, apart from the trailing `;` in the ticket.
  - `evidence/run_queries.out` and `run_queries_r2.out` show all six ran: Q2 49 rows in 25.6 ms, the 25-level diamond Q1 in 1.6-1.9 ms, no error.
- Q0 and the version read do not appear in `queries.py`, `run_queries*.py` or any evidence file in this snapshot. A grep of `evidence/` for `_aclitem` and `server_version_num` finds nothing. Line 221 says "each ran without error ... fact 40" and line 223 lists Q0. Fact 40 (line 157) does not list Q0. Q0 is attributed only to fact 9 / author files outside the snapshot.
- Queries were probed only on a non-autocommit psycopg connection with `c.transaction()`. These were not probed:
  - an empty `named` or `managed` array (the no-role-arguments case);
  - a two-entry `family`;
  - the step-8 setup (`isolation_level` and `read_only` set on an autocommit connection, then `db.transaction()`).
  The ticket's own tests (`test_step_8_reads_one_snapshot`) cover the last item, but no probe shows psycopg issues BEGIN with those options in that mode.
- The order inside `pinned_read` (path first, then limits, line 206) differs from the probed order (limits first, fact 36 / `dfg.out`). The ticket itself calls the 1 ms outcome "luck". Nit.
- Line 208 says every catalog table, view, function and type is qualified. The pasted texts that must be copied "without rewording" use unqualified `bool_or(...)` (Q1), `::text[]`, `::"char"`, `::bigint` and `::int`. The pinned path makes them safe. The rule and the texts conflict, and acceptance item 4 (`test_every_catalog_name_in_the_queries_is_qualified`) has no definition of "catalog name" (tables only, or functions and types too). A strict implementation fails on Q1.

### Minor

- **m1.** Q1 gets `pg_database_owner` from Q2's database row (line 239). That row appears only when some item for a subject or everyone exists. If everyone's CONNECT and TEMPORARY were revoked and the owner's entry removed, the row could be absent. Read `datdba` explicitly.
- **m2.** Ticket body uses review ids as normative references: D-M6, D-m9, R-M4, C-F9, D-020, "round-12 design finding 6", "EVIDENCE RUNNER". The files they point to (`handover/...`) are on another branch. A builder without them cannot resolve these. Undefined terms inside the body: "pre-flight" (defined at 4.1 step 2), "family", "carrier" (defined), "the bible".
- **m3.** 1.5 and CHANGELOG instructions (lines 85-110) tell the builder to delete sentences quoted from CL and MIG lines I could not read. Many MIG/CL/MN citations (MIG:1-1677, MN:677-723, CL:6-34, TPG, TW, TCMP, MUT line numbers) are unconfirmable here. See "Not checked".
- **m4.** 9.1 item 6 markers `[promise table]` and `[end of promise table]` appear in a docstring (indent 0) and in the CHANGELOG (nested, indent 2). The comparison needs a stated whitespace normalisation.
- **m5.** 9.1 item 2b: `grep -n "current_schema()" migrate.py` must print exactly one line. Comments and docstrings count too (3.1 line 200 and 5.2 mention it). Say "no comment may contain it" as item 3 does for the new module.
- **m6.** 3.1 says `verify` has no default for `reviewed_definers` and `migrate()` passes it at call time. The 3.1 signature note is fine, but the module's `from __future__ import annotations` or `TYPE_CHECKING` form for `Grant` is not stated. Trivial for the builder; flag only so that the import-cycle claim can be tested.
- **m7.** The pinned-read sites 5.4b item 1 lists need a fake `_Db.transaction()` (savepoint). The ticket says the shared helper answers "the savepoint and SET LOCAL lines" but never says whether the fake already has a `transaction()` method. Not readable from here.
- **m8.** 7.2: the one-database-per-case fixture uses `login_dsn` and `create_login_role` from `tests/fixtures/migration_role.py`. Whether `login_dsn` can name a different database than the shared one is not stated.
- **m9.** 7.6 `test_step_8_with_a_saved_statement_timeout_still_checks` uses a 5 ms timeout. The ticket admits this is unverified on CI (10.4 line 1043).
- **m10.** 7.6 `test_a_lost_connection_at_commit_gives_exit_5` is only expected to give wording, and the psycopg code path is unprobed (10.4 line 1046).
- **m11.** 5.5 line 644 and 7.5: a parametrised killer id is checked. Which commit changes `problems_with_the_list()` is not stated (see M1).
- **m12.** 4.2 sets exit code 5 for both "applied but not verified" and "commit outcome unknown". 5 is free on main (main `cli.py` returns 0-4), so this is fine. The cli.py line 9 reference matches main (the migrate usage line), but the exit-code docstring format (lines 9-17 on main) puts exit codes in separate lines. Say where the new line goes.
- **m13.** 6.3 CI route uses `docker exec ${{ job.services.postgres.id }}`. Never tried (10.3 item 10 admits it). `psql` is not necessarily in PATH inside the pinned image as the postgres user without `-U postgres`. The ticket gives `-U postgres`; fine.
- **m14.** 7.9 old-head proof relies on the `getattr(hadavin_sdk.errors, "AppliedNotVerifiedError", None) or adapter class` form. The new test files must not import `migration_verify` at module level, but 7.2 and 7.6 tests for `verify` obviously do. Only the matrix file is copied, so this works, but state it.

### Nit

- **n1.** 4.1 step 5 and the `step[0]` text are fine, but the other step texts use different names for the same thing ("applied" versus "committed").
- **n2.** 5.4: the TCMP count adds up (6 retired + 7 rewritten + 1 + 2 kept = 16). The TPG retired list has 10 and the re-pointed list 22. I could not confirm each name exists.
- **n3.** 9.1 item 17's python one-liner prints `[]` only if `check_grants` returns a list. On main `check_grants` returns `list[str]`, so that is consistent.

## 3. Checks asked for

**Commit green.** Per-commit command (9.3 line 968) is defined: ruff plus affected files plus `test_every_migrate_mutant_still_applies_to_the_source`. Commit 1 can be green only after M1 is fixed. Commit 3 is one large commit (M3). Commits 2, 4, 5 and 6 look green if their named tests are assigned (commit 4 needs the server with `max_prepared_transactions` above 0). The mutant list change is in the same commit as its code for commit 3 only for ids the ticket lists (M7).

**Names real.** Confirmed in main (`/home/user/build/q8a2-dryrun/main-2a8c2aa/src/hadavin_sdk`):
- `store/migrate.py`: `effective_problems` at line 193 (ends at 262), `Grant` (line 24) with fields `kind`, `runtime`, `portal`, `purge`, `purge_cols`, `GRANTS` (line 46), `_scan` (line 123), `check_grants` (line 150), `_TABLE_PRIVS` (line 190), `current_schema()` reads at lines 172 and 210.
- `errors.py`: `ConfigError` (`ValueError` subclass, line 4).
- `store/migration_numbers.py:80`: `MigrationNumberError(ConfigError)`.
- `store/postgres.py`: `connect` at 125-132 with no `options` argument, `SET TIME ZONE 'UTC'` at line 148.
- `cli.py`: no `return 5` (returns 0-4 exist), `migrate` usage at line 9, `ConfigError` exit 2 at lines 19-20.

Not in main (new names or branch-only, so unconfirmed): `escape_name`, `_label`, `_shown`, `RECIPE_TIMEOUTS`, `REVIEWED_DEFINER_FUNCTIONS`, `RUN_SCHEMA`, `_managed_names`, `AppliedNotVerifiedError`, `END_OF_RUN`, `PROBLEM_KINDS`, `KNOWN_ACL_COLUMNS`, `pinned_read`. Main also has no `_refuse_unlisted_grantees` or the mutant runner in src. `tools/heavy_slot.py` is not in src.

**Queries identical to probed.** Yes for Q1, Q1b, Q2, Q3, Q4 and the step-4 query (see M8). Q0 and the version read are not in the evidence.

**Module layout.**
- No import from `migrate` into the new module: the design is sound (psycopg, `hadavin_sdk.errors`, `migration_numbers`, `Grant` under `TYPE_CHECKING`).
- `_label` moving to `migration_numbers.py` with a re-import: fine, but I could not confirm the no-mutant-inside-`_label` claim or that `escape_name` exists on the branch.
- The reviewed list is passed at call time with no default: correct, and it keeps the `monkeypatch` at TPG:2804 working.
- Circular import risk: low. The one hidden duplication is the "" schema constant (M5).

**Time.** Mutant batches 55 + 65 + 97 + 97 = 314 with estimates of 9-18, 8-10, 10-12 and 10-12 minutes. Totals about 37-52 minutes, plus matrix 15-25 and whole suite. All estimates are unmeasured.

## 4. What I did not check
- Any code or test on the P3a-2 branch. The tests, `tests/migrate_mutants.py`, `tests/test_migration_*.py`, `tests/fixtures/*`, `.github/workflows/ci.yml` and the snapshot `/home/user/build/snap/p3a2-r12-4d328e3/` were not readable. So every MIG, MN, CL, TPG, TW, TCMP, MUT, TR and ci.yml line citation is unconfirmed, as is the existence of every test and mutant id other than what `mutclass.out` lists. Everything about `heavy.sh` behaviour and its arguments is unchecked (not in the snapshot).
- PostgreSQL behaviour of any SQL (no server). I compared texts with the probe files and read the recorded outputs only. Facts 1-40 are the author's runs, not re-run.
- Whether `psycopg` honours `isolation_level` and `read_only` when `transaction()` starts a transaction on an autocommit connection.
- The design review `reviews/plan-r1-design*.md` beyond the answer table in section 11. I did read `plan-r1-readiness-full.md`, the author's report and the `evidence/README.md`.
- Probe outputs other than the grep of `run_queries*.out` and `mutclass.out`.
- PostgreSQL 17 behaviour (the ticket also states none was run).

Relevant files: /home/user/build/snap/p3a2-plan-r2/tickets/P3a-2-r13-verify-final-state.md, /home/user/build/snap/p3a2-plan-r2/evidence/queries.py, /home/user/build/snap/p3a2-plan-r2/evidence/mutclass.out, /home/user/build/snap/p3a2-plan-r2/evidence/run_queries_r2.py, /home/user/build/snap/p3a2-plan-r2/reviews/plan-r1-readiness-full.md.
