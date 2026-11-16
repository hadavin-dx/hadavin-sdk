# Goldfish Annotated Review Report (resolve, round 2)

Status: findings categorised; the author applies them (ticket revision 4)

**Target:** `handover/tickets/P3a.md` (revision 3). Findings: `handover/reviews/P3a-round2-adversarial.md`, `handover/reviews/P3a-round2-correctness.md`. Counts: 22 findings, all PROPOSE FIX (none contested, none escalated: the lead answered the open questions in `LEAD-ORDERS.md` order 5 / amendment A14).

## Lead decisions that apply (order 5)
Order 5 (g): fix every major, or contest with evidence in the disposition file. The manifest stays PENDING LEAD with your recommendation (state plainly the weakness the reviewers named). No new lead decision applies to P3a beyond A13(5)-(6) and A14.

Note on the gate (skill Step 4): the owner told the cloud session to follow `LEAD-ORDERS.md` (allowed actions only) and to run the resolve step; the auto-accept path is taken for every PROPOSE FIX, as in round 1.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Major (finding id A1, adversarial)
*   **Affected Scope:** Interface `check_ledger`; Tests FAIL-BEFORE 5; `check_grants` of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The ticket contradicts itself on unreadable and non-UTF-8 files. FAIL-BEFORE 5 expects `ConfigError` for a non-UTF-8 `.sql` file. But the `check_ledger` problem list has no decode or readability check; it covers only name, `is_file`, duplicate and gap. `check_grants` returns a list and never raises. `_scan` calls `path.read_text(encoding="utf-8")`, which raises `UnicodeDecodeError`, a `ValueError` and not a `ConfigError`. `is_file()` does not test permission.
*   **Rationale:** evidence: `migrate.py:131`; ticket section "Interface" bullet `check_ledger`; text "it raises `ConfigError` as now" (`check_grants` returns a list).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface `check_ledger`; Tests FAIL-BEFORE 5; `check_grants`
    *   Change: Make the readable-and-decodable check part of `check_ledger` (or a wrapper that also turns `OSError`/`UnicodeDecodeError` into problems). Add an unreadable-file test (skip if running as root). Reword "check_grants raises ConfigError as now": `migrate()` raises it.

### [Issue 2] [`egm-design`] - Severity: Major (finding id A2, adversarial)
*   **Affected Scope:** Rollback runbook (a); Open point 1 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The ticket says the recipe "also covers a hotfix that needs an out-of-order number". It does not cover a hotfix whose number is already taken. Scenario: a release branch applied `0006_hotfix` on production, and main later merges `0006_x`. Two files carry 0006, `check_ledger` refuses the duplicate, and the recipe is irrelevant. Renumbering the hotfix to 0007 makes the production ledger name `0006_hotfix` have no file, so `gone` refuses. The runbook says renaming is NOT the fix. The only exit is a hand edit of the ledger, and that exit is not documented for this case.
*   **Rationale:** evidence: `migrate.py:97-107`, `:320-326`; ticket runbook (a)-(c).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Rollback runbook (a); Open point 1
    *   Change: Add a runbook case "number collision between a release branch and main": the hotfix file keeps its name, main renumbers to 0007, plus the exact ledger edit. Test it like the existing rename test. Also state that a release branch must reserve its number on main first.

### [Issue 3] [`egm-design`] - Severity: Major (finding id A3, adversarial)
*   **Affected Scope:** Interface `order_problems` message; Tests recipe test of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The recipe is unsafe or incomplete in four ways. (i) It takes no advisory lock; the key `_LOCK` is derived in code, so an operator cannot know it. A concurrent `migrate` can run while the operator is mid-recipe. (ii) It runs the 0004 SQL after 0005 is applied, with no check that 0004 does not depend on the 0005 schema state. A fresh install runs 0004 first, so an upgraded database and a fresh one can end up different. Layer 1 compares only the previous release against HEAD, never an upgraded database against a fresh one. (iii) It does not say to pass the same `--runtime-role`/`--purge-role` flags on the rerun; without them a table created by the recipe has no grants and the runtime fails later with a Postgres permission error. (iv) A plain `psql` run without `-1` and with the default (continue on error) can apply half the file. The recipe test only exercises the happy path through the test's own connection, with an independent 0004.
*   **Rationale:** evidence: `migrate.py:314` (lock), `:340-345` (grants only with role flags); ticket recipe text.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface `order_problems` message; Tests recipe test
    *   Change: Do not ask for a hand recipe. Add a `migrate --accept-late 0004_x` path: inside the locked transaction, apply the file and write the ledger row. If a hand recipe stays, include `psql -1 -v ON_ERROR_STOP=1`, the lock statement, and "rerun with the same role flags". Add a test where the late file depends on 0005, and a test that compares the upgraded schema with a fresh one.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** Manifest (PENDING LEAD; recommendation) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The recommended scope has two holes. (1) "Released" lags "applied". A file merged to main and applied by every main deployment or demo is "unreleased" until the lead tags it, and may be edited freely in that window. That is exactly how the 0005 problem arose. (2) CI cannot detect an edited file plus an edited manifest hash. The only guard is the lead's manual `git diff <last tag>` gate, which is unenforced in CI. A careless or hostile PR changes `0003_x.sql` and the hash in the same commit and goes green. Also the ledger stores only the stem, so even a correct manifest does not protect a database that applied old content.
*   **Rationale:** evidence: Ticket: Manifest rules and Open point 3; `migrate.py:331` (ledger stores only the stem).
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Manifest (PENDING LEAD; recommendation)
    *   Change: Define the manifest as "every migration merged to main" and append the hash in the PR that adds the file. Add a CI job that diffs the manifest against the PR base (`fetch-depth`, lead-only edit) and fails on any non-append change. Consider a ledger checksum column (decide the layout in this package or write the reason it is left out). If the lead keeps the "released" scope, say plainly that it is weak and name the window.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** Previous-release test, layer 1 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Layer 1 reads catalog structure on empty schemas and is blind to several breaking classes, but the ticket says it proves the old schema "is still present". Not compared or not run by the plan: function and trigger-function bodies (`CREATE OR REPLACE FUNCTION` that stops refusing UPDATE on `audit_entries` passes, because triggers are compared by presence and definition, not the function they call); data statements (`UPDATE`, `DELETE`, unit changes), which do nothing on empty tables (released 0003 already holds a `DELETE`, which the ticket concedes); privileges and ACLs (a `REVOKE` in SQL); row-level-security policies, rules, comments, enum and domain types, and sequence settings. Also A is built from HEAD's copies of the old files, so an edited released file changes A and B identically and passes.
*   **Rationale:** evidence: Ticket layer 1 list: relations, columns, constraints, indexes, triggers, views only.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Previous-release test, layer 1
    *   Change: Add `pg_proc` source/`prosrc` hashes for functions used by triggers, `pg_policy`, `pg_rewrite`, ACLs and type definitions. Seed small made-up rows into A and compare the data after B. Build A from the manifest-hashed files only. Reword to "catalog structure of listed object kinds, on empty tables". Add planted cases for each new kind.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** Merge precondition; CHANGELOG reword (Open point 2) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The old CHANGELOG line 11 told dev and demo users to rename the `0005_evidence` ledger row to `0006_evidence`. Anyone who followed it has a database whose ledger says `0006_evidence`. The replacement text says only "no rename is needed", and the merge precondition asks only about branch-built databases. After P3a, and especially after P4d-b takes 0006, that database is refused by `gone` (no file `0006_evidence`), or collides with the new 0006.
*   **Rationale:** evidence: `CHANGELOG.md:11, 38, 45, 52`; `migrate.py:320-326`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Merge precondition; CHANGELOG reword (Open point 2)
    *   Change: Add to the runbook and the precondition: "if you renamed your ledger row to `0006_evidence`, rename it back to `0005_evidence`". Extend the owner's question and the `SELECT version` check to cover this. Add a test with a ledger holding `0006_evidence`.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Layer 2 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Layer 2 is a one-time manual run on a planted ALTER-only migration, and it works only for ALTER-only changes. Later migrations (P4d-b, P3b, P3c) get no layer 2 unless the lead repeats it by hand. The plugin is UNVERIFIED.
*   **Rationale:** evidence: Ticket layer 2 and Done list.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Layer 2
    *   Change: Put "layer 2 run logged" in each later migration package's Done, or script the worktree run as a CI job against the last tag. Say plainly in the ticket that layer 2 is not recurring.

### [Issue 8] [`egm-codebase-details`] - Severity: Major (finding id C1, correctness)
*   **Affected Scope:** Interface (`check_ledger`, `migrate()` step 2); Tests FAIL-BEFORE 5; property test of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The ticket says non-regular entries and unreadable files are refused with `MigrationNumberError`, but the interface does not deliver that for a non-UTF-8 or unreadable regular file. `check_ledger` only tests `p.is_file()`, which says nothing about readability. Step 2 is the unchanged `check_grants` → `_scan` → `path.read_text(encoding="utf-8")`, so a `UnicodeDecodeError` or `PermissionError` still escapes raw. Three consequences: (a) the non-UTF-8 half of FAIL-BEFORE 5 cannot pass after the fix, because it expects `ConfigError`; (b) the property test "only `MigrationNumberError` is raised" is false for non-UTF-8 content; (c) "refuses ... with a message" in the Security section is true only for directories and dangling links.
*   **Rationale:** evidence: `migrate.py:131` (the `read_text` in `_scan`); `migrate.py:330` (the read in the apply loop); ticket interface text "not a readable regular file (`not p.is_file()`...)"
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Interface (`check_ledger`, `migrate()` step 2); Tests FAIL-BEFORE 5; property test
    *   Change: Make step 1 read each file's bytes, decode as UTF-8, and turn `OSError` and `UnicodeDecodeError` into problem lines starting with the file name. Or wrap `_scan`'s read. Add a mutant for it. State plainly that `is_file()` is not a readability test.

### [Issue 9] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Tests, layer 1 (pg_catalog comparison); Mutation M10a-f of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Layer 1 compares relations, columns, constraints, indexes, triggers and views. It does not compare functions (`pg_proc`). `0002_audit_chain.sql` defines `hadavin_audit_append_only()`, which every append-only and no-truncate trigger runs. The guard explicitly allows `CREATE OR REPLACE FUNCTION` in migrations. A migration that replaces that function body (say with a no-op) leaves every trigger row, constraint and column unchanged, so layer 1 passes. That contradicts "the old schema is still present" for the audit protection. None of the planted cases covers it.
*   **Rationale:** evidence: `0002_audit_chain.sql:25-35`; `migrate.py:81` (`_SAFE_CREATE` allows `CREATE OR REPLACE FUNCTION`)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, layer 1 (pg_catalog comparison); Mutation M10a-f
    *   Change: Add functions (`pg_get_functiondef` or the `prosrc` hash, for functions owned by the schema) to the comparison. Add the planted case `CREATE OR REPLACE FUNCTION hadavin_audit_append_only() ... no-op` that must fail, and mutant M10g that drops the function comparison.

### [Issue 10] [`egm-design`] - Severity: Nit (finding id A10, adversarial)
*   **Affected Scope:** Constants / tests of `handover/tickets/P3a.md`
*   **Discrepancy Description:** `PREVIOUS_RELEASE_LAST = "0005_evidence"` becomes stale at the next release if the manifest is declined; the 10-second poll and the 2,000-case count are hard-coded in tests.
*   **Rationale:** evidence: Ticket layer 1.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Constants / tests
    *   Change: Either require the manifest or derive the baseline from the newest tag; state the constant's review date.

### [Issue 11] [`egm-design`] - Severity: Nit (finding id A11, adversarial)
*   **Affected Scope:** Test plan, mutants of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Missing mutants: manifest rules "numbers run 1..k" and "unreleased above k"; "released file is missing"; "`order_problems` uses min instead of max applied"; "runtime refuses a symlink to a regular file" (the ticket requires acceptance); off-by-one in the 20-problem cap (`and N more`); `list_migration_files` dropping the suffix match. The `__pycache__` and `.bak` refusal exists only in CI; one mutant should drop it.
*   **Rationale:** evidence: Ticket mutation plan M1-M16.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Test plan, mutants
    *   Change: Add the mutants and name the killing tests.

### [Issue 12] [`egm-design`] - Severity: Nit (finding id A12, adversarial)
*   **Affected Scope:** Evidence / skip of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Postgres tests skip without `HADAVIN_TEST_PG_DSN`; the ticket asks for "0 skipped" only in the evidence output. CI does set the DSN and checks the client (`ci.yml:82-88`), so CI is covered; a local green run with skips is not.
*   **Rationale:** evidence: `ci.yml:82-88`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Evidence / skip
    *   Change: State that "skipped" in the two new files is a failed evidence run, and have the evidence runner assert it.

### [Issue 13] [`egm-design`] - Severity: Nit (finding id A13, adversarial)
*   **Affected Scope:** Wording of `handover/tickets/P3a.md`
*   **Discrepancy Description:** (1) "check_grants ... raises ConfigError as now" (see A1). (2) The ticket says "released" in two senses (tagged, or merged when no manifest exists). (3) "Do not rename it" in the error text clashes with the earlier rename advice in the `gone` message for a different case. A builder or operator could apply the wrong one. (4) "Line numbers" of `migrate.py` are used as the change specification and will drift once P4d edits GRANTS.
*   **Rationale:** evidence: Ticket "Files to change".
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Wording
    *   Change: Describe edits by symbol (`_FILE`, `_migration_files`, `check_ledger`, the `migrate()` body), not by line.

### [Issue 14] [`egm-design`] - Severity: Nit (finding id A8, adversarial)
*   **Affected Scope:** `order_problems` of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The compare is "number at or below the highest applied". A file with a number equal to an applied one but a different stem is handled by `gone` first, which is fine. But the ticket does not say what happens with applied stems that fail the ASCII pattern when the file list is otherwise empty; the fuzz case is mentioned only for no raw `ValueError`.
*   **Rationale:** evidence: Ticket M13/M16.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: `order_problems`
    *   Change: Add a test for a ledger with only non-matching stems.

### [Issue 15] [`egm-design`] - Severity: Nit (finding id A9, adversarial)
*   **Affected Scope:** Statements that cannot run in a transaction of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The ticket names only `CREATE INDEX CONCURRENTLY`. `ALTER TYPE ... ADD VALUE` (new value unusable in the same transaction), `VACUUM`, `CREATE DATABASE`, and long `ACCESS EXCLUSIVE` locks with no `lock_timeout` on live tables are also relevant. A failed run rolls back the whole batch, so the ledger stays consistent (good).
*   **Rationale:** evidence: `migrate.py:312-332`.
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Statements that cannot run in a transaction
    *   Change: Name those statements; add a scan refusal for the non-transactional ones; consider a `lock_timeout` setting in `migrate()` (decide in P4d).

### [Issue 16] [`egm-codebase-details`] - Severity: Nit (finding id C3, correctness)
*   **Affected Scope:** Tests, FAIL-BEFORE header ("each fails on an assertion on `ce70eb5`"); items 4 and 5 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Tests 4 and 5 do not fail on an assertion on `ce70eb5`. `IsADirectoryError` (`FileNotFoundError` or `UnicodeDecodeError` for 5) is raised inside `with pytest.raises(ConfigError)`. It is not a `ConfigError`, so it propagates and pytest reports an error from that exception, not an assertion failure. Evidence command 5 ("save the failing output with the failing assertion of each") cannot be met as written. Test 1 is fine: "DID NOT RAISE" is a pytest failure.
*   **Rationale:** evidence: `migrate.py:131` raises raw; the ticket's own wording for 4 and 5
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, FAIL-BEFORE header ("each fails on an assertion on `ce70eb5`"); items 4 and 5
    *   Change: Write the tests as `with pytest.raises(Exception) as e: ...` followed by `assert isinstance(e.value, ConfigError)` and `assert "0006_x.sql" in str(e.value)`. They then fail on an assertion on `ce70eb5`.

### [Issue 17] [`egm-codebase-details`] - Severity: Nit (finding id C4, correctness)
*   **Affected Scope:** Tests, layer 2 (lead's plugin) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The plugin wraps the old `migrate()`, "calls the original, then runs the new SQL". The old tests call `migrate()` repeatedly on one schema: the fixture migrates, then a test calls it again, and `test_p2_postgres.py:169-170` asserts the second call returns `[]`. The planted probe `ALTER TABLE runs ADD COLUMN p3a_probe TEXT;` has no `IF NOT EXISTS`, so the second wrapped call fails with a duplicate-column error. Two threads in `test_p2_postgres.py:157` would also run it twice. The ticket marks "whether the plugin works" UNVERIFIED but does not say the probe or wrapper must be idempotent.
*   **Rationale:** evidence: `test_p2_postgres.py:157-170`; `tests/contracts/kinds/store_postgres.py:36`; `0004_audit_checkpoint_meta.sql:6-7` use `ADD COLUMN IF NOT EXISTS`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, layer 2 (lead's plugin)
    *   Change: Use `ADD COLUMN IF NOT EXISTS` in the probe. Better, have the wrapper run the new SQL only when the original returned a non-empty list. Record this in the ticket.

### [Issue 18] [`egm-codebase-details`] - Severity: Nit (finding id C5, correctness)
*   **Affected Scope:** Tests, layer 1 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Schemas A and B are different PostgreSQL schemas, but the ticket does not say how to remove the schema name from the compared text. `pg_get_indexdef` and `pg_get_triggerdef` print a schema-qualified table name. `pg_get_expr` of a column default (for example `nextval('...'::regclass)` for the serial columns) depends on the session `search_path`. A raw string comparison would report a difference between A and B for identical objects. This is implementable, but the first run would produce false failures.
*   **Rationale:** evidence: Ticket layer-1 text says only "Read `pg_catalog` for both"; `0001_core.sql` and `0003_approvals_tick.sql` have serial columns (via the `_seq_seq` entries in `GRANTS`, `migrate.py:66-67`)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, layer 1
    *   Change: Say in the ticket: compare with the schema prefix removed, or set `search_path` per schema for the read. Add one test: identical A and B produce no difference.

### [Issue 19] [`egm-codebase-details`] - Severity: Nit (finding id C6, correctness)
*   **Affected Scope:** Open point 3 (manifest) and Problem 5 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The cost of declining the manifest is understated. Plan row P3a (plan-v3.md line 96) says "CI fails on duplicate or out-of-order numbers". Without the manifest, CI (`check_migration_numbers`) can see only duplicates and gaps. Out-of-order is detected only at run time against a ledger (`order_problems`), and that check needs a database. A late-numbered file in a gapless folder is not visible to CI. The ticket says declining loses only "protection against edited released files". The recommendation (yes, with the lead's gate) is safe and correct.
*   **Rationale:** evidence: plan-v3.md line 96; ticket Open point 3
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Open point 3 (manifest) and Problem 5
    *   Change: Add: "without the manifest, CI has no out-of-order check; plan row P3a is then met only at run time". The lead decides knowing that.

### [Issue 20] [`egm-codebase-details`] - Severity: Nit (finding id C7, correctness)
*   **Affected Scope:** Existing code and Security notes of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Line-reference slips. (a) `tests/test_k5_round10_postgres.py:136-141` is cited as proving the "runtime role cannot read `schema_migrations`". The test is at 137-142, and it proves that `migrate` refuses a PUBLIC SELECT grant on `schema_migrations` (an extra privilege outside the map), not that the runtime role cannot read it. (b) "the whole run is one transaction (`migrate.py:312-332`)": the transaction runs from 312 to the end of the `with` (about 359), because the role checks and grants are in it. The constraint on future migrations still holds. (c) `tests/test_k2_migrations.py:35-54` should be 36-55. (d) "plan rule 10; amendment F6" for `migrate.py` and `CHANGELOG.md`: only plan rule 10 lists them; A9 F6 does not.
*   **Rationale:** evidence: `test_k5_round10_postgres.py:137-142`; `migrate.py:312-359`; `test_k2_migrations.py:36-55`; amendments.md F6; plan-v3.md line 68
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Existing code and Security notes
    *   Change: Correct the references and reword (a) to what the test shows.

### [Issue 21] [`egm-codebase-details`] - Severity: Nit (finding id C8, correctness)
*   **Affected Scope:** Tests, recipe test (`test_recipe_for_a_late_number_works`) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The recipe SQL itself is correct. The ledger column is `version` and the value is the stem without `.sql` (`migrate.py:317, 331`). A multi-statement `db.execute(text)` with no parameters works, as in `migrate.py:330`. The `ADD COLUMN IF NOT EXISTS` in 0004 makes it safe to apply. But the test hand-writes "the recipe exactly as in the message". It never reads the message, so a wrong message passes.
*   **Rationale:** evidence: ticket recipe text and test description
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Tests, recipe test (`test_recipe_for_a_late_number_works`)
    *   Change: Have the test pull the `INSERT ... VALUES ('<stem>')` and the "ONE transaction" wording out of `str(err.value)` and check that the insert text contains the real stem. Add a mutant that corrupts the message INSERT (for example the wrong column name).

### [Issue 22] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Hostile inputs and property test of `handover/tickets/P3a.md`
*   **Discrepancy Description:** `ConfigError` derives from `ValueError` (`src/hadavin_sdk/errors.py:4`). "Must not raise a bare `ValueError`" and "only `MigrationNumberError` is raised" are testable only with an exact type check (`type(e) is MigrationNumberError`), not `except ValueError` or `except ConfigError`.
*   **Rationale:** evidence: `errors.py:4`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** valid unless the author shows evidence otherwise: the reviewer cites a file and line that can be read. The author re-checks the cited line first; where two findings conflict or one is wrong, the disposition file says so with evidence (REJECTED).
*   ***Proposed Edit:***
    *   Location: Hostile inputs and property test
    *   Change: Say so in the test description.
