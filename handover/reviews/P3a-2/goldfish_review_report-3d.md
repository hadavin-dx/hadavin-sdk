Status: resolved

# Goldfish Annotated Review Report (P3a-2 commit 3d, round 3)

**Target:** branch `wip/cloud-p3a2-3d`, head `c7e0908a`. SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `p3a2-3d-design.md` (0 Blocker, 0 Major, 4 Nit) and `p3a2-3d-codebase.md` (0 Blocker, 1 Major, 2 Nit). Previous round: `goldfish_review_report-3c.md`.

**Evidence status (first):** there is NO independent evidence for `c7e0908a`. Only the builder's own report exists (ruff, format, bandit, `scan_repo` exit 0; `stage_mutants` 37/37; 581 migration tests passed; `migration_numbers_mutants` 40/40; `migrate_mutants` 352 of 353 at `fd3fee2` with V62 fixed in `c7e0908` and re-run alone 1/1; full pytest 1 failed, `tests/demo_askdata/test_validate_harm.py [dblink-connect]`, because the builder's server did not listen on the default socket; not in the diff). The independent evidence runs ONCE, on the final head after commits 4 and 5 (builder `a6f66b04` on `wip/cloud-p3a2-45`, started 03:39Z). The PostgreSQL 17 branches are unrun anywhere here (only PG16 exists); CI or a server of version 17 is needed.

Both reviewers found no readable secret and no new privilege path, and the round-2 fixes for Issues 1, 6, 11, 13 and 19 present in the code with a killer and a mutant each.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`codebase` D1] - Severity: Major
*   **Scope:** `tests/test_migration_verify.py:1094-1100` (`test_a_sentence_the_changelog_quotes_but_the_code_does_not_write_is_found`); the loop test `test_every_sentence_form_the_changelog_quotes_is_in_the_code...`; builder notes Issue 20 table.
*   **Description:** The planted-fault test never runs the checker: it asserts `planted not in source` for one sentence. Its docstring ("the checker above is not blind") is unsupported, and the builder notes claim "the planted-fault test proves the check fails on a stale quote" is wrong. The loop skips pieces shorter than 3 characters, so the form `has {right}` (piece "has") is never checked. If `line()` said "holds" and the CHANGELOG kept the stale form, nothing would fail.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A guard that cannot fail is the class "test that cannot fail"; on a security path this is a Major.
*   ***Proposed Edit:*** Factor the loop into a helper taking the block text and the source; call it on a planted block (for example "can see it through the role {via}") and assert it raises; drop the 3-character skip or require whole-form matching (the word plus its f-string fragment); add a mutant that edits `line()` to "holds" and is killed; correct the notes claim and the docstring.

### [Issue 2] [`codebase` D3 and `design` N1] - Severity: Nit (one finding)
*   **Scope:** CHANGELOG "The three calls" bullet and `migrate` docstring; `migrate.py:1412, 1481` (only wrapped spots), `:1440-1449, :1478-1480` (not wrapped); `tests/test_migration_verify_pg.py:1190-1227`.
*   **Description:** A saved `transaction_timeout` counts from BEGIN and can fire in `_take_the_lock`, the version read, `_refuse_*`, a migration file, `_check_read_back`, `_recheck_roles`, `_revoke_default_execute`; those raise a raw driver error and give exit 3 (the very behaviour Issue 1 of round 2 set out to remove; safe, nothing kept). The PG17 test uses `SET LOCAL` just before the first `verify`, so a role-saved value is not covered.
*   ***AI Suggestion:*** PROPOSE FIX (the stronger option)
*   ***Justification:*** A promise that the migration gives exit 2 and keeps nothing on any driver error before the commit is easy to state and to test; narrowing the sentence would leave a known exit-3 path.
*   ***Proposed Edit:*** Wrap the whole pre-commit body (steps 1 to 6) so any driver error before the commit gives a ConfigError, exit 2, nothing kept (limit errors keep their own message; a bug such as RuntimeError stays loud); lost-connection tests at steps 3, 4 and 6 on a real server; a role-saved `ALTER ROLE ... SET transaction_timeout` test on PG17 where a server exists (UNRUN here: say so in the notes and CHANGELOG); mutants for the wrapper at each step. Touches `migrate.py:1380-1500`, which the commit 4/5 builder may also edit (see handoff).

### [Issue 3] [`codebase` D2] - Severity: Nit
*   **Scope:** `tests/test_migration_verify_pg.py:250-256, 874-881, 133-136`.
*   **Description:** `SELECT current_user` as the grantor is right only when the DSN user is the bootstrap superuser (ticket fact 32).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Read the grantor from the data (`SELECT pg_get_userbyid(10)` or the recorded `pg_auth_members` row).

### [Issue 4] [`design` N2] - Severity: Nit
*   **Scope:** CHANGELOG (SECURITY DEFINER paragraph); `migration_verify.py:15-27`; code `:1106-1157`.
*   **Description:** "The owner of such a function must be a role of the family" and "empty-ACL objects are still judged for owner" read wider than O4/O8 (managed names and the schema only; run schema only).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Reword to "a managed object, and the schema, must be family-owned"; add "in the schema of the run" to the empty-ACL paragraph.

### [Issue 5] [`design` N3] - Severity: Nit
*   **Scope:** `store/postgres.py:171-174`; `migrate.py:1129`; `test_migration_verify_pg.py:1365`.
*   **Description:** The `sql_words` docstring says database text passes only after a plain-name check; step 4 passes the server's identity-argument text unchecked (safe: server-quoted). Tests use plain arguments only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** State the one exception in the docstring; add a real-server case `CREATE FUNCTION "f"("Odd Arg" "MixedType")` with a mutant.

### [Issue 6] [`design` N4] - Severity: Nit
*   **Scope:** `tests/test_migration_verify_pg.py:1242-1256, 1270-1303`.
*   **Description:** The 1 ms test relies on `env.db` being autocommit; the commit-sleep killer ends any other session in `pg_sleep` on a shared server.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Assert the fixture is autocommit; filter the sleeper killer by application name or pid.

### [Issue 7] [`design` question 1, SQLSTATE 40003] - Severity: decision
*   **Description:** The builder classes 40003 as "unknown" (exit 5); ticket F5 lists all of class 40 as refused. The design reviewer judged the builder right (an idle session after a proxy's 40003 may mean a commit that did happen; exit 2 would skip step 8; matches ticket 4.1 step 7 "errs towards unknown").
*   ***AI Suggestion:*** ESCALATE (the ticket edit only)
*   ***Justification:*** The ticket is a studio document; the lead does not edit it without the owner. The code stays as built (safe default); recorded as decision D-40003 in `DECISIONS.md`. Proposed ticket line: "class 40 except 40003". Added to `questions-for-lead.md` with the default.

### [Issue 8] [`evidence`] - Severity: Minor
*   **Description:** 352 of the 353 mutants were not re-run after the `c7e0908` test edit (by reading no other mutant uses that test); the 29 retired ids' existence at `4d328e3d` was not checked by any reviewer; the PG17 branches are unrun.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The final evidence run runs the full mutant list once and the command `git show 4d328e3d:tests/migrate_mutants.py | grep` for the 29 ids; the evidence file lists the PG17 branches as unrun unless a version 17 server is available.

## Handoff counts
Accepted (PROPOSE FIX): 7 (Issues 1-6, 8). Escalated: 1 (Issue 7, ticket edit; code stays). Declined: 0. Contested: 0. Remaining unaddressed: none.

**Who fixes it:** Issues 1, 3-6 touch tests and docs only. Issue 2 touches `migrate.py:1380-1500`, which the commit 4/5 builder (`wip/cloud-p3a2-45`) may also edit; so after that builder reports, ONE fix builder (batch 3e) rebases on its head and fixes Issues 1-6 and 8 together, then one independent evidence run and two `egm:*` reviewers read the final head. The ledger rows for M1-M5, C1, C2 and the commit-5 matrix stay OPEN until that evidence exists.
