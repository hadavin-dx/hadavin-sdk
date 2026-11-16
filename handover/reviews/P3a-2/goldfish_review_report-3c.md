Status: resolved

# Goldfish Annotated Review Report (P3a-2, commit 3c, round 2)

**Target:** branch `wip/cloud-p3a2-3c`, head `11bd1260`, snapshot `/home/user/build/snap/p3a2-3c-11bd1260`. SECURITY path, no round cap. No person was available: recommended option for every item. Reviews (read-only, nothing run): `p3a2-3c-design.md` (0 Blocker, 5 Major, 11 Nit) and `p3a2-3c-codebase.md` (0 Blocker, 2 Major, 8 Nit). Independent evidence for this head is NOT yet in (the runner waits for a free heavy slot). Builder's own run (unverified): full pytest 11237 passed, mutant lists green, timing test flaked once; gitleaks by the lead: no leaks. Builder-disclosed not done: full 37x13 matrix (ticket items 8 and 10, commit 5), two lock mutants (commit 4), `--list-batch`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`design` M4 + `codebase` C1] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:30`; `src/hadavin_sdk/store/migrate.py:1330-1460` (inner handler re-raises at 1449-1457); `src/hadavin_sdk/cli.py:73-86`.
*   **Discrepancy Description:** The text says a saved `transaction_timeout` can stop the check and then migrate says "could not run" (exit 2 before the commit). The code re-raises a raw driver error before the commit; `cli.main` prints `failed: <ClassName>` and exits 3. No test touches `transaction_timeout`. The direction is safe (nothing kept, never "applied"); the stated exit code and wording are wrong, and an operator script that retries on 2 and pages on 3 would behave wrongly.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Both reviewers found the same defect independently; a claim of "nothing was changed, exit 2" the code does not keep is a security-path documentation defect.
*   ***Proposed Edit:*** Map pre-commit driver errors raised by `verify` (all `psycopg.Error` other than the two already mapped) to the existing could-not-run refusal path (ConfigError, exit 2, "Nothing was changed"), keeping the post-commit path at exit 5. Add a real-server test with `transaction_timeout` set low (PostgreSQL 17 and later) and a fake-database unit test for an unknown driver error, plus a mutant. If the builder cannot map it safely, correct the CHANGELOG to say exit 3 and add a test pinning exit 3 (second choice, say why).

### [Issue 2] [`design` M1] - Severity: Major
*   **Affected Scope:** `migrate.py:19`; `CHANGELOG.md:22`; `tests/test_migration_verify.py:862`; `tests/test_migration_matrix.py:162, 848-866`; ticket 7.7.
*   **Discrepancy Description:** Promise row 1 says CI tests what each role can really do on the shipped files. The ticket 7.7 test `test_the_shipped_files_give_each_role_exactly_the_map` does not exist; the matrix checks the hand-written map only against GRANTS, and the two clean controls probe a few privilege calls.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The promise table test pins the words, so it cannot notice a missing test; the text must not claim a check that is not built.
*   ***Proposed Edit:*** Build the 7.7 test now (run the shipped files on an empty database, compare each role's rights, using the behavioural oracle, with a mutant). If it is not built in the same push, change the row to say "built in a later commit" until it exists and list it in the ledger as OPEN.

### [Issue 3] [`design` M2] - Severity: Major (disclosed)
*   **Affected Scope:** `tests/test_migration_matrix.py:684-698, 750`; CHANGELOG:17 ("on every schema").
*   **Discrepancy Description:** The reduced matrix (36 cells + 2 controls, plain GRANTs only) has no end-to-end cell for memberships, ownership handover, default rights, large objects, SECURITY DEFINER, C6, C8, C9, C13 or the ticket 7.9 must-fail list. Promise rows 1-2 rest on `_judge` unit tests and a few real-server tests, not the closed-property matrix.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The builder disclosed it, and it is a planned commit (5); it is still a gap against the promise and may not be hidden.
*   ***Proposed Edit:*** Add one sentence to the PR notes and the CHANGELOG: rows 1-2 are unproven for these classes until commit 5; the package must not be called done at commit 6 without the full matrix. Add a ledger row (Major, OPEN) tied to commit 5. The fix itself is commit 5.

### [Issue 4] [`design` M3] - Severity: Major
*   **Affected Scope:** `CHANGELOG.md:15`; `migration_verify.py:489-532`.
*   **Discrepancy Description:** CHANGELOG promises the message "the portal role has privileges outside the portal grant map ..." and a sequence-right wording; `src/` no longer produces it and no test pins it.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** An operator grepping for the sentence finds nothing.
*   ***Proposed Edit:*** Rewrite the bullet to the real `Problem.line()` forms (for example "can use it through the role X, SELECT") and add a test that every sentence form quoted in CHANGELOG occurs in `src/`.

### [Issue 5] [`design` M5] - Severity: Major
*   **Affected Scope:** `tests/migrate_mutants.py` (MT1, MT2 retired); `migration_verify.py:786-807` (`_allowed_for`); CHANGELOG:15.
*   **Discrepancy Description:** No test contains MAINTAIN any more; CHANGELOG promises it is one more right on PostgreSQL 17 and later. A later edit that lets rights through by prefix would pass every test; no unit test for an unknown right word.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** A retired mutant must leave its behaviour with a killer (class of Q8c-1 round 6, Issue 7).
*   ***Proposed Edit:*** `_judge` unit tests with made-up rows: MAINTAIN on a map table for a named role gives `right`; MAINTAIN for everyone gives `everyone`; an unknown right word is refused; plus a mutant that lets rights through by prefix.

### [Issue 6] [`codebase` C2] - Severity: Major (security path, fixed not declined)
*   **Affected Scope:** `migrate.py:1072-1106` (`_revoke_default_execute`, escape about 1098); `tests/test_migration_steps.py:531-560`.
*   **Discrepancy Description:** The step-4 REVOKE builds the function name with an ascii-based escape. Tests use plain lowercase names. A function name with a backslash or a non-ASCII letter could give a malformed REVOKE or one targeting another name, leaving EXECUTE granted to PUBLIC.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Class: identifier quoting built by hand instead of at the shared choke point; the standard is PostgreSQL identifier quoting.
*   ***Proposed Edit:*** Build the statement with `pg.quote_identifier` / `sql_template`; grep `migrate.py`, `migration_verify.py` and `cli.py` for the same hand escape (siblings); real-server test with a mixed-case and a non-ASCII function name, run against the old code to show it fails; mutant that breaks the quoting.

### [Issue 7] [`design` N1] - Severity: Nit
*   **Affected Scope:** `tests/migrate_mutants.py`; DELTA.patch.
*   **Discrepancy Description:** All 29 ids of ticket 5.5 appear as deleted against 4d328e3d and existed there; the builder says 17 retired and 12 never existed.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The count is a claim in the PR notes; it must match the diff.
*   ***Proposed Edit:*** Builder states which count is right (possibly 12 were retired earlier within the range) and corrects the notes and CHANGELOG, with the command used.

### [Issue 8] [`design` N2] - Severity: Nit
*   **Affected Scope:** `migrate_mutants.py:2951-3123`.
*   **Discrepancy Description:** Clause labels in V mutant descriptions do not match ticket 3.3 (V10, V13, V14, V17, V18, V20, V21, V25-V28).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Correct the labels to the clause each mutant really breaks.

### [Issue 9] [`design` N3] - Severity: Nit
*   **Affected Scope:** `migrate.py:61`, `:1111-1116, 1155-1161`; CHANGELOG:32.
*   **Discrepancy Description:** Docstring says the schema owner must be a role of the family; code excuses an owner unchanged since step 1; CHANGELOG says so. Touches open owner question `q-p3a2-o8-schema-owner`.
*   ***AI Suggestion:*** PROPOSE FIX (wording only)
*   ***Justification:*** Align the docstring with the CHANGELOG and the code; no decision on the exemption (strict default stays as decided).
*   ***Proposed Edit:*** Add the exception to the docstring; do not change behaviour.

### [Issue 10] [`design` N4 + `codebase` N5] - Severity: Nit
*   **Affected Scope:** `migrate.py:28-53, 1258-1288, 1358-1424`.
*   **Discrepancy Description:** Docstring steps 1-8 vs code comments 2-6; `migrate()` docstring omits `AppliedNotVerifiedError` and that a return means "checked".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Number comments to match; add the exception and the meaning of a return to the docstring.

### [Issue 11] [`design` N5] - Severity: Nit
*   **Affected Scope:** `migration_verify.py:84-139`; docstring `:57-61`.
*   **Discrepancy Description:** Objects with an empty access list are invisible to Q2, so a file that revokes everything from itself and PUBLIC hides an unreviewed SECURITY DEFINER function or an ownership handover from O4 and O8.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** This is a possible hole for a hostile file (promise row 3 fits it), not only wording; the reviewer reads it as covered by the promise but the docstring says "no SECURITY DEFINER function ..." without the exception. Security path: do not leave it as a note.
*   ***Proposed Edit:*** Builder checks by probe whether the O4 and O8 reads reach such objects by another route (for example, owner and `prosecdef` read straight from the catalogs, not through `aclexplode`). If they do not, close it (read those from the catalogs directly) with a test and mutant; if they do, add a test proving it and state the exception in the docstring.

### [Issue 12] [`design` N6] - Severity: Nit
*   **Affected Scope:** `CHANGELOG.md:29`; `migration_verify.py:985-1026`.
*   **Discrepancy Description:** CHANGELOG says a SECURITY DEFINER function callable by a named role is refused "unless" reviewed; code reports a named role's EXECUTE as a plain right regardless. Code is stricter than the text.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Reword to what the code checks. Also covers `codebase` N6 (state exactly what `_judge` checks: owner, `search_path`, EXECUTE rights).

### [Issue 13] [`design` N7 + N8] - Severity: Nit
*   **Affected Scope:** `tests/test_migration_verify_pg.py:445-461, 571-601`.
*   **Discrepancy Description:** The 50 ms statement-timeout test can pass vacuously on a fast machine (sensitivity check is `pg_sleep(0.5)`, not Q2; ticket asks Q2 alone cancelled at 1 ms; V48 killer is a fake-database unit test); the lost-connection-at-commit test does not assert the classifier saw 57P01; `test_a_cancel_at_commit_gives_exit_2` of ticket 7.6 is absent.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Tests that cannot fail on the case they name.
*   ***Proposed Edit:*** Use 1 ms and assert Q2 is the cancelled query; assert 57P01 was classified; add the 7.6 cancel test; each with a mutant or a stated control reason.

### [Issue 14] [`design` N9] - Severity: Nit
*   **Affected Scope:** `test_migration_verify_pg.py:134`.
*   **Discrepancy Description:** `migration_role="postgres"` hard-coded.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Take the cluster's superuser name from `current_user`.

### [Issue 15] [`design` N10] - Severity: Nit
*   **Affected Scope:** `migration_verify.py:1055`.
*   **Discrepancy Description:** `_judge` skips a grantee equal to `migration_role` only; with a login different from the migration role the login's own entry on a package object is reported as `other_grantee` (false refusal, rare setup).
*   ***AI Suggestion:*** DECLINE (behaviour change; fails closed)
*   ***Justification:*** The direction is safe (false refusal, never a missed excess); widening the skip on a security path needs its own review. Recorded; add one sentence to the docstring naming the case so an operator can recognise it.
*   ***Proposed Edit:*** Docstring sentence only.

### [Issue 16] [`design` N11 + `codebase` N3] - Severity: Nit
*   **Affected Scope:** `tests/test_migration_verify.py:878-880`.
*   **Discrepancy Description:** `A or any(...)` cannot fail for the case named.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Assert both parts, or only the strict one.

### [Issue 17] [`codebase` N1, N2, N8] - Severity: Nit
*   **Affected Scope:** `migration_verify.py:286`; `test_migration_verify.py:856-880`; `test_migration_postgres.py:2575-2612, 4326-4366`; `migrate_mutants.py:3506-3525`.
*   **Discrepancy Description:** Dead constant `_SYSTEM_SCHEMAS`; docstrings cite non-existent mutants PT3, PT4, PC1, PT1 and a stale docstring describes the deleted comparison; `problems_with_the_list` checks the killer function name but not parametrize ids or docstring ids.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Same class as the GM1 dead constant the builder retired; cheap to close at the shared checker.
*   ***Proposed Edit:*** Delete the constant (grep for other unused module constants); fix or drop the ids; extend `problems_with_the_list` to check ids named in docstrings and parametrize ids of killers, with a planted-fault test.

### [Issue 18] [`codebase` N4] - Severity: Nit
*   **Affected Scope:** `test_migration_rules.py:1010-1096`; `test_migration_postgres.py:4437-4466`.
*   **Discrepancy Description:** The no-early-return guard is satisfied trivially in the `mpt=0` branch.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** Make the branch call `migrate`, or exempt it explicitly in the guard with a written reason.

### [Issue 19] [`codebase` N7] - Severity: Nit
*   **Affected Scope:** `migrate.py:311-327` (`_commit_outcome`).
*   **Discrepancy Description:** SQLSTATE 40003 (statement completion unknown) sits with the refused classes; the commit may have happened, so "nothing was changed" may be too strong; untested.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** On a security path an unknown outcome must not claim "nothing changed".
*   ***Proposed Edit:*** Check against ticket F5; if 40003 can follow a commit, class it as unknown (exit 5 path) with a test and mutant; otherwise cite the standard text in a comment and test the class.

### [Issue 20] [`evidence`] - Severity: Minor (pending)
*   **Affected Scope:** independent evidence run not yet done.
*   **Discrepancy Description:** The builder's own run is the only evidence; the timing test flaked once; the 38 re-pointed mutants' old text occurring once, parametrize ids and the 16 re-checked killers were not checked by the reviewers.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Proposed Edit:*** The evidence runner runs the full suite and all mutant lists at the fixed head and lists every new or changed test that passes on old code; reviewers of the next round check the 38 re-pointed mutants' old texts.

## Handoff counts
Accepted (PROPOSE FIX): 19 (Issues 1-14, 16-20; Issue 9 and 15's docstring part wording only). Declined: 1 (Issue 15 behaviour change). Contested: 0. Escalated: 0 (the open owner questions `q-p3a2-e1-extension-lockout` and `q-p3a2-o8-schema-owner` are untouched; strict defaults stay). Unaddressed: the full 37x13 matrix, lock mutants and `--list-batch` stay for commits 4 and 5 as planned (Issue 3 makes this explicit in the text and the ledger). Ledger: P3a-2 3c rows M1-M5 and C1, C2 are OPEN until a fix builder pushes and an independent evidence run confirms them; Issue 11 stays OPEN until the probe result.
