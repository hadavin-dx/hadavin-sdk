# PR 73 (P3a-2, head 2b0941b) round 1: resolve (egm:egm-resolve, headless)

Status: resolved (categorised only. This resolver edits no ticket and no source code).
Target: `handover/tickets/P3a.md` (the full file, 286 lines; the proposed build notes BN-P3a-2-a to -e are at the end).
Findings in: `reviews/PR73/round1-design.md` (egm-design: M1-M4, N5-N11) and `reviews/PR73/round1-codebase.md` (egm-codebase-details: B1, M1-M4, N1-N8). 23 findings, merged into 14 groups.
Path class: migrations and the ledger are the money and state path. NO round cap. This is round 1.

## What I checked and what I did not
- Read: both review files. From the ticket: lines 39-49, 70, 91 and 270-286 (the BN-P3a-2 notes).
- Read in the snapshot `/home/user/build/snap/P3a-2-2b0941b`: `migration_numbers.py:1-35`, `:315-335`, `:626-690`; `migrate.py:225-250`, `:315-345`, `:350-470`, `:500-580`; `tests/fixtures/dsn_skip.py`; `test_migration_numbers_guards.py:505`; `test_migration_postgres.py:37`, `:515`; CHANGELOG line 6.
- Read in the repo: `git diff --name-status origin/main...2b0941b`, `pyproject.toml` (build backend, test group), `.github/workflows/ci.yml:39-40` and `:86`.
- Read in the evidence: `evidence/P3a-2/2b0941b-cloud2/README.md`, `evidence/P3a-2/recon-2026-11-09/` (CHECKPOINT, TABLE, `run-p3a2-mutants.txt`), `evidence/dblink-rerun-2026-11-09/PR73-31{2,3}.txt`, and `LEAD-ORDERS.md` order 172.
- Not run: no test, no build, no SQL. Not read: the other test files of the snapshot in full, `migration_numbers.py` outside the lines above, PostgreSQL 17 behaviour.
- Facts the reviewers did not have:
  - (a) A reconstruction run killed 66 of 66 P3a-2 mutants at 2b0941b (`recon-2026-11-09/run-p3a2-mutants.txt`). The baseline passed 46 killer tests. The runner exists only at `/home/user/build/recon/p3a2/p3a2_mutants.py`, outside the repo, and its mutant texts were rebuilt from names, because the original texts were lost.
  - (b) The dblink re-run at 2b0941b gives `1 passed` on both Pythons, on a cluster with the default socket. The full-suite failure was caused by the test machine, not by the code.
  - (c) ORDER 172 (06:29Z) already answers two points. (1) There is one release manifest, at `tests/fixtures/migrations_released.json`. (2) The merge order is P3a-1, then P3a-2, then P3a-3. Point (1) conflicts with the code; see G73-4.

## Groups, by severity

### G73-1 [Blocker] Stale docstrings say nothing calls the rules yet (codebase B1, design N9 first half) - PROPOSE FIX
- Verified: `migration_numbers.py:5-6` says "(a later change, P3a-2: until it merges, NOTHING calls them and none of the rules here is in force)". Lines 14-15 say "the read-back in `migrate()` after each file (a later change)". After this PR both statements are false: `migrate.py:516-541` calls the rules.
- Fix (**builder**): rewrite both sentences in the present tense and cite the call sites: `migrate.migrate()` runs `check_ledger`, `released_problems`, `read_files`, `check_grants` and `order_problems` before it applies anything, and `_check_read_back` after each file. Then grep `src/` and `tests/` docstrings for "later change", "P3a-2" and "until it merges", and fix every sibling.

### G73-2 [Major] Trigger read-back is a deny-list; same-name recreate passes; `tgrelid` unused (design M1, codebase N5) - PROPOSE FIX + NEEDS LEAD (part c)
- Verified: `migrate.py:446-452` refuses only a trigger that becomes `D` or `R`. A change from `A` (always fires) to `O` (fires only outside replica mode) passes, and so does `O` to `A`. The saved triggers are keyed by name only (`:395-399`), so dropping a trigger and recreating it under the same name with another body passes. `_relid` is read and never used (`:398`).
- Fix (**builder**), parts (a) and (b), with no conflict with the ticket:
  - (a) For a trigger that existed before the file, refuse any change of `tgenabled`, in any direction.
  - (b) Replace `t.tgrelid` with `pg_get_triggerdef(t.oid)` plus `md5(p.prosrc)`, `p.prosecdef` and `pg_get_userbyid(p.proowner)` (join `pg_proc p ON p.oid = t.tgfoid`).
  - Keep these in the saved state and name each change in the refusal message.
  - New wiring-stub rows: A to O, O to A, and same name recreated with another body. Each needs a mutant: the any-change check narrowed back to D/R, and the definition not compared.
- (c) **NEEDS LEAD.** Should the read-back refuse a changed trigger definition or trigger-function body?
  - Ticket line 39 (b) lists "a file that replaces a trigger FUNCTION with a body that does nothing" as a stated limit (v1.1 row V-a).
  - Ticket line 49 says P2a uses `CREATE OR REPLACE TRIGGER`, "which passes". Refusing would break that planned P2a file.
  - Recommendation: refuse by default. Allow a definition change only for a file named in a reviewed list next to the release manifest (stem plus trigger name, with a reason). Write it as a build note. The audit triggers are the tamper-evidence guarantee.

### G73-3 [Major] Released-file hash reads the file a second time, not the text that runs (design M4, codebase M2, codebase N1) - PROPOSE FIX
- Verified: `migrate.py:518` calls `released_problems(MIGRATIONS, ...)` before `read_files(files)` (`:522`). `migration_numbers.py:330` hashes `p.read_bytes().replace(b"\r\n", b"\n")`, but `read_files` decodes with universal newlines, so a lone CR becomes LF in the text and stays CR in the hash. `released_problems` also lists the constant folder `MIGRATIONS` and not the `files` list that `migrate()` runs, so the checked set and the run set have two sources. The existing test patches only `Path.read_text`.
- Fix (**builder**): read once, then check what runs.
  - `texts = read_files(files)` moves before the released check.
  - `released_problems(files, texts, manifest)` hashes `texts[p].encode("utf-8")` over the same `files`.
  - For files without a lone CR this gives the same hash as today, so the manifest does not change. A test asserts this for all five released files.
  - New rows: a released file with a lone CR, and a test that patches `read_bytes` and `read_text` to differ (the check must follow the text). Mutant: the hash taken from `read_bytes` again.

### G73-4 [Major] Where the release manifest lives (codebase M1) - NEEDS LEAD (conflicts with ORDER 172 (1))
- Verified:
  - The PR moves the file unchanged: `git diff --name-status origin/main...2b0941b` shows `R100 tests/fixtures/migrations_released.json -> src/hadavin_sdk/store/migrations_released.json`. Only one copy exists on this head.
  - Product code reads the file at run time: `migrate.py:320` `RELEASED_MANIFEST = MIGRATIONS.parent / "migrations_released.json"`, `:334-340` `_released_manifest()`, called at `:518`.
  - The CHANGELOG says "shipped inside the package". The build backend is `uv_build`, which packages `src/hadavin_sdk` only, so `tests/fixtures/` is not in an installed wheel.
  - ORDER 172 (1) says the manifest lives in `tests/fixtures/`. Following it literally makes every installed `migrate` fail with "the list of released migration files cannot be read".
  - `origin/core/P6a`, `core/P1a` and `core/P1b` still have `tests/fixtures/migrations_released.json`; `origin/core/P6a:tests/test_migration_numbers_guards.py` names it.
- Recommendation: keep ONE file, at `src/hadavin_sdk/store/migrations_released.json`.
  - Update BN-P3a-2-c to that path (**ticket edit**).
  - Re-point the tests of P1a, P1b and P6a when they rebase onto P3a-2 (**their builders**).
  - P3a-3 reuses the same file.
  - **Evidence runner:** `uv build` and list the wheel to show the JSON is inside it. Whether it is inside is UNVERIFIED until then.

### G73-5 [Major] "The migration role is not a superuser" is stated, not enforced (design M2) - NEEDS LEAD
- Verified: `effective_problems` (`migrate.py:236-243`) checks `rolsuper`, `rolcreaterole`, `rolcreatedb` and `rolbypassrls` for the runtime and purge roles only. Nothing checks `current_user`, the role that runs the files. The ticket keeps this as a stated precondition on purpose (lines 45, 49, 70). Line 91 says the CI test role is `postgres`, a superuser, and that one test fails when `rolsuper` is false. CI connects as `postgres` (`ci.yml:86`).
- Why the lead decides: enforcing it changes the ticket design and every PostgreSQL test fixture.
- Recommendation: enforce it. Before the first file, refuse a run when `current_user` is a superuser or has bypass-row-security, using the same `pg_roles` query as `effective_problems`. Do not add a run-time override switch: it would be one more door. Tests create a plain migration role from the superuser connection and run `migrate()` as that role. The one test that needs a superuser (line 91) calls `_check_read_back` directly. A second question: should `rolcreaterole` and `rolcreatedb` also be refused? The recommendation is yes, matching the standard `effective_problems` already applies.

### G73-6 [Major] The additive-only check (layer 1) is not in force until P3a-3 (design M3) - PROPOSE FIX + NEEDS LEAD (one question)
- ORDER 172 (2) fixes the merge order. Still missing: the PR text and the CHANGELOG do not say that layer 1 is absent between the two merges.
- Fix (**builder**): add one sentence to the PR body and the CHANGELOG: "The check that a migration only adds and never removes or retypes a column (layer 1) is not in force until P3a-3 merges; the downgrade-read test (`test_the_previous_release_columns_survive_the_newest_migrations`) is the only column check until then."
- NEEDS LEAD: confirm that no release tag and no client deploy happen between the P3a-2 merge and the P3a-3 merge.

### G73-7 [Major] No PostgreSQL 17 evidence (codebase M3) - PROPOSE FIX
- Verified: local runs used 16.15 (`2b0941b-cloud2/README.md`). Only PostgreSQL 16 is installed here (`/usr/lib/postgresql/16`). CI's service is `postgres:17.10` (`ci.yml:40`), and CI has not run on this head.
- Fix:
  - **Evidence runner:** after the fix batch is pushed, record the CI run id, its conclusion and the PostgreSQL version line from the job log. That is the 17.10 evidence.
  - **Builder:** the CHANGELOG states exactly what was tested: "local runs on PostgreSQL 16.15; CI on 17.10". Until CI is green, write "not yet tested on 17".

### G73-8 [Major] The 66 P3a-2 mutants are a rebuild whose runner is outside the repo; fail-before was run at ea40242 (codebase M4) - PROPOSE FIX
- Verified: fact (a) above. `evidence/P3a-2/ea40242/fail-before.txt` belongs to the older head.
- Fix:
  - **Builder:** commit the runner as `tests/migrate_mutants.py`, following the committed pattern of `tests/migration_numbers_mutants.py`, with each mutant's text in the file. Add the new mutants from G73-2, -3, -9 and -11.
  - **Evidence runner (a different agent):** on the final head, run it once alone. Then copy the new and changed tests onto the P3a-1 base and record FAIL or PASS per row. Save the raw output to `handover/evidence/P3a-2/<head>/`.
- Class: "a mutant runner kept outside the repo". PR 72 has the same problem (G72-1).

### G73-9 [Nit, reviewer said nit-to-major] Settings that persist and the two time limits are not in the read-back (design N5, N10) - PROPOSE FIX (read-back part) / CONTEST (lock-order part)
- Fix (**builder**):
  - Add `pg_db_role_setting` (database name, role name, `setconfig`) to the read-back. Compare it as a set, the way role memberships are compared.
  - Add `current_setting('lock_timeout')` and `current_setting('statement_timeout')` to `_READBACK_VALUES`. They are saved after `RECIPE_TIMEOUTS` is set (`:538-539`), so the saved values are the recipe values.
  - Add one row and one mutant for each.
- CONTEST (the claim that the limits come after the advisory lock): `migrate.py:535-539` and CHANGELOG line 6 ("They start right after `migrate` takes its advisory lock") record this as the design. The advisory lock is how `migrate` queues behind another `migrate`. That other run is itself held by its statement limit, so the wait is bounded by its statements. A lock limit placed before the lock would make two deploys started together fail instead of queue. The lead may overrule.

### G73-10 [Nit] Wording of trust limits and messages (design N6, N7, N11; codebase N6) - PROPOSE FIX
- Fix (**builder**), text only:
  - (a) The `pg_auth_members` read-back covers the whole server. The refusal message adds: "a membership change made by another session during the run also shows here; if no file changes roles, run migrate again".
  - (b) The COMMIT backstop text (`migrate.py:355`) says it DETECTS a hidden COMMIT after the fact and cannot undo what that COMMIT already made permanent. The existing test stays.
  - (c) Add to the trust-limit text in the `migrate()` docstring and the CHANGELOG: "`dblink_exec`, where the extension is already installed, runs SQL on a separate connection outside this transaction and outside the read-back; `CREATE EXTENSION` is refused, and a migration role that is not a superuser cannot use dblink without a password".

### G73-11 [Nit] Timeout detection matches English message text (design N8) - PROPOSE FIX
- Verified: `migrate.py:462` uses `"statement timeout" in str(e)`, which depends on the server's `lc_messages`.
- Fix (**builder**): drop the text test. Any `QueryCanceled` (SQLSTATE 57014) gives the message "a statement ran into the statement limit (statement_timeout) or was cancelled". New row: a fake `QueryCanceled` with a non-English message still gets the plain-words error. Mutant: the text test restored.

### G73-12 [Nit] pglast test skips silently (design N9 second half) - PROPOSE FIX
- Verified: `test_migration_numbers_guards.py:505` uses `pytest.importorskip("pglast")`. `pglast==8.7` is in the `test` group (`pyproject.toml:52`), so it is always installed where the gate runs.
- Fix (**builder**): a plain import, so a missing package is a failure, as `tests/fixtures/dsn_skip.py` already does for the database driver.

### G73-13 [Nit] The ticket says something different from the code (codebase N2, N3, N4) - PROPOSE FIX (ticket edit)
- Verified:
  - `PREVIOUS_RELEASE_LAST = "0005_evidence"` (`test_migration_postgres.py:37`, order 89), but BN-P3a-2-b says 0004.
  - The code refuses `CREATE ROLE|USER|GROUP|EXTENSION`, `LOAD`, `DISCARD`, `ALTER SYSTEM` and `COPY ... PROGRAM` (`migration_numbers.py:640-645`, `:685`), but ticket line 49 lists them as "NOT in the list".
  - The read-back has 9 values in 3 queries (`migrate.py:355-384`), and its triggers come only from `current_schema()`.
- Fix (**ticket edit** by the session that owns the handover branch): one build note "BN-P3a-2-f (as built)" with these three facts, plus the BN-P3a-2-c path from G73-4 once the lead answers. The frozen text stays.

### G73-14 [Nit] Double lexing (codebase N7); "CHANGELOG line 6 garbled" (codebase N8) - DECLINE / CONTEST
- N7, DECLINE: a cost nit with no correctness effect stated. No change.
- N8, CONTEST: CHANGELOG line 6 reads as one coherent paragraph. I read it all; nothing in it is garbled. It is very long. The builder may split it into bullets in the same push, but no fix is required.

## Counts
23 findings, 14 groups.
- PROPOSE FIX: 10 groups (G73-1, -2 a/b, -3, -6, -7, -8, -9 read-back part, -10, -11, -12, -13).
- NEEDS LEAD: 3 groups (G73-4, G73-5, plus G73-2 part c), and one question inside G73-6.
- CONTEST: G73-9 lock-order part and G73-14 N8.
- DECLINE: G73-14 N7.

Who does what:
- Builder (branch core/P3a-2): G73-1, -2, -3, -6, -7 (CHANGELOG), -8 (runner), -9, -10, -11, -12.
- Evidence runner: G73-4 (wheel listing), -7 (CI run), -8 (run plus fail-before).
- Ticket edit: G73-13 and the BN-P3a-2-c path.

Ledger: rows G73-1 to G73-8 (Blocker and Major) belong in `handover/ledger.md` as OPEN, area P3a. The lead adds them; this resolver did not write to the ledger.

Next steps: one fix batch, then a different evidence runner, then fresh round-2 egm-design and egm-codebase-details reviews on a snapshot of the new head. No round cap.
