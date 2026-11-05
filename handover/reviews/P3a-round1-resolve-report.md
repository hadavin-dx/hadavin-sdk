# Goldfish Annotated Review Report (resolve, round 1)

Status: findings categorised; fixes to be applied by the ticket author under the owner's standing instruction (see the note below)

**Target:** `handover/tickets/P3a.md` (full file). Findings: `handover/reviews/P3a-round1-adversarial.md`, `handover/reviews/P3a-round1-correctness.md`. Decisions applied: `handover/studio-notes/amendments.md` A11, A12, A13.

Counts: PROPOSE FIX 23, ESCALATE 1, CONTEST 0, DECLINE 0. Nothing was contested: for every finding the reviewer cited a file and line that could be read, and the author re-checks it before editing. The skill's severity names are Blocker / Major / Nit; the review files say BLOCKER / MAJOR / MINOR (MINOR = Nit, and every Nit is also fixed because the fix is cheap).

Note on the gate (skill Step 4): the owner told the cloud session to run resolve and rewrite the tickets, and set the standing rule that only major decisions wait for the owner. So the "auto accept" path is taken for every PROPOSE FIX; ESCALATE items are NOT applied as decisions: the ticket carries the recommended position marked PENDING LEAD and the item is listed in `handover/questions-for-lead.md`.

## Prioritized Findings & AI Suggestions

### [Issue 1] [`egm-design`] - Severity: Blocker (finding id A1, adversarial)
*   **Affected Scope:** Interface `order_problems`; the message `renumber it above 0005` of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The refusal tells the operator to do something the same ticket's gap rule forbids. A file below the highest applied number can only be refused when the folder is gapless and holds a file for the highest applied number (otherwise `gone` fires first). So the folder is 1..M with M >= N. Renumbering that file to M+1 leaves a hole at its old number, and `folder_problems` refuses with "migration 000X is missing". Renaming every later file instead makes `gone` fire on every database that applied them. Scenario: ledger 0001-0003 + 0005_y (a database that ran a branch). The folder has 0001-0005 gapless. The new run refuses 0004, and the operator follows the advice, renames 0004 to 0006, and gets the gap error. The operator is locked out of a live database with no working fix in the message. The ticket never documents the only real escape: run the file's SQL by hand and INSERT its row into `schema_migrations`. After that, `migrate` accepts it, because the name is in `applied`.
*   **Rationale:** evidence: ticket line 27; `migrate.py:97-107` (gap rule), `:320-326` (`gone`)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(5): the message gives a recipe that works (apply the file by hand in a transaction, insert the ledger row, rerun); renumbering is not the fix. The finding is valid: the reviewer cites evidence that can be read (ticket line 27; `migrate.py:97-107` (gap rule), `:320-326` (`gone`)). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface `order_problems`; the message `renumber it above 0005`
    *   Change: Replace the message with the real recipe: apply 000X by hand in a transaction, insert the ledger row, rerun. Put the recipe in the error text, the CHANGELOG and the runbook. Add a test that runs the recipe and then expects `migrate` to succeed. Say plainly in the ticket that renumbering is not the fix for a database-side order refusal.

### [Issue 2] [`egm-design`] - Severity: Blocker (finding id A2, adversarial)
*   **Affected Scope:** `folder_problems`: "each entry must be a regular file (no symlink)" of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The rule runs inside `migrate()` on the installed package folder at production runtime, not only in CI. Installers that link files into site-packages (uv with `--link-mode=symlink`, some distro or Nix-style layouts, symlinked editable installs) make every migration file a symlink. Scenario: a client image built with symlink link-mode makes `migrate` refuse 0001 to 0005 at deploy, so nobody can migrate. The threat it closes, a symlink in a repo folder, is a repo-review threat, not a runtime one. Also unspecified: dangling links, and whether the check follows the link or only checks `is_symlink` on the entry.
*   **Rationale:** evidence: `migrate.py:304-306` (the check runs in `migrate`); ticket line 44
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(5): symlink refusal only in the CI check, not at runtime in migrate(). Runtime still refuses directories and dangling links with MigrationNumberError (see C1). The finding is valid: the reviewer cites evidence that can be read (`migrate.py:304-306` (the check runs in `migrate`); ticket line 44). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `folder_problems`: "each entry must be a regular file (no symlink)"
    *   Change: Do the symlink check only in `check_migration_numbers` (CI and tests), not in the runtime path. Or resolve the link and require the target to sit inside the package folder. Add a runtime test with a symlinked install layout.

### [Issue 3] [`egm-design`] - Severity: Major (finding id A3, adversarial)
*   **Affected Scope:** `folder_problems(folder: Path)` vs `migrate()` of `handover/tickets/P3a.md`
*   **Discrepancy Description:** `migrate()` today calls `_migration_files()` with no argument and gets a list. Three existing tests replace it with `lambda: files` to inject bad lists: `test_k2_migrations.py:108`, `:390`, and `test_k5_fixes2.py:300`. The ticket says `migrate()` "calls `folder_problems` first (as now)", but `folder_problems` takes a folder. If the builder calls `folder_problems(MIGRATIONS)`, the monkeypatched lists are ignored and those tests either go vacuous or fail. The ticket also plants "a temporary folder" for the two-thread test, but `migrate()` has no folder parameter. The same goes for M8: `migrate()` cannot be handed a planted folder except through the `_migration_files` patch.
*   **Rationale:** evidence: `migrate.py:93-94, 304`; tests above
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`migrate.py:93-94, 304`; tests above). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `folder_problems(folder: Path)` vs `migrate()`
    *   Change: State that `migrate()` keeps calling the module-level `_migration_files()` and passes its list to a list-based checker. Make `folder_problems` a wrapper over `path_problems(paths)`. Document the patch point as the test seam.

### [Issue 4] [`egm-design`] - Severity: Major (finding id A4, adversarial)
*   **Affected Scope:** CHANGELOG correction (Open point 2) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The ticket names only CHANGELOG lines 10-11. The same false `0006_evidence` rename appears at lines 38, 45 and 52: "the evidence migration is `0006_evidence.sql`", the run-before-start step, and the table description. Appending one correction leaves four contradicting lines. An operator reading line 45 or 52 plans for a file that does not exist. Line 11 is an instruction that, followed, makes `migrate` refuse the database (`migrate.py:320`).
*   **Rationale:** evidence: `CHANGELOG.md` lines 10-11, 38, 45, 52
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decided by A13(6): the CHANGELOG lines that mention 0006_evidence are REWORDED, not only appended; list every line (10-11, 38, 45, 52; the author re-checks). The finding is valid: the reviewer cites evidence that can be read (`CHANGELOG.md` lines 10-11, 38, 45, 52). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: CHANGELOG correction (Open point 2)
    *   Change: The ticket must list all four lines. Because the old lines are actively harmful instructions, the lead should decide now to reword them (a reviewable edit), not only append.

### [Issue 5] [`egm-design`] - Severity: Major (finding id A5, adversarial)
*   **Affected Scope:** Previous-release test (schema-compat, layer 1) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The test gives false confidence. It records "tables, columns, types, nullability" and the ticket cites `information_schema`. Missed: column defaults (dropping a default on a NOT NULL column breaks old INSERTs); new CHECK, UNIQUE and FK constraints; dropped UNIQUE or index (old `ON CONFLICT` breaks); triggers; views (`v_*` views are not in "tables, columns"); sequences; grants and RLS; and data rewrites like the `DELETE` in 0003. Scenario: `ADD CONSTRAINT CHECK (state <> 'x')` or `DROP DEFAULT` passes the test and breaks old code. `information_schema.columns` also lists only columns the current role owns or can access, so a non-owner connection silently sees less. Schema A is built from the same files as B up to `last_migration`, so editing an old file (say 0003) changes A and B together and the test sees nothing. Only the optional manifest hash covers that.
*   **Rationale:** evidence: ticket lines 55, 57, 99
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 55, 57, 99). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Previous-release test (schema-compat, layer 1)
    *   Change: Read `pg_catalog` (attributes with `atthasdef`, `pg_constraint`, `pg_index`, `pg_trigger`, views) as the owner role. Compare constraints, indexes, defaults and views. Say in the test docstring and the ticket that it proves the old schema is still present, not that old code works. Treat layer 2 as non-gating but required for any `breaking` change.

### [Issue 6] [`egm-design`] - Severity: Major (finding id A6, adversarial)
*   **Affected Scope:** Layer 2 of the previous-release test of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Layer 2 is useless exactly when needed. Any migration that adds a table also needs a `GRANTS` row. The old `check_grants` then reports "created by a migration but not in GRANTS" (`migrate.py:150-157`) and refuses, which the ticket calls "loud, acceptable". So layer 2 can never run for a table-adding migration. It is also manual and UNVERIFIED as feasible. `previous_release: {ref: "pre-P3a"}` is a tag that does not exist yet, and CI's `check` job has no tags or history, so the ref is a label no test can resolve. The ref is also ambiguous because the plan tags `pre-<P-id>` before every merge.
*   **Rationale:** evidence: ticket lines 29, 36, 57; `ci.yml` (`check` job has no `fetch-depth`)
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 29, 36, 57; `ci.yml` (`check` job has no `fetch-depth`)). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Layer 2 of the previous-release test
    *   Change: Define the layer-2 procedure so the old tree's migration list is the old tree's own, with only the new SQL applied directly (skip the old runner). Say which tag moves when. Mark the ref in the manifest as informational.

### [Issue 7] [`egm-design`] - Severity: Major (finding id A7, adversarial)
*   **Affected Scope:** Safe escape and rollback (attack 1) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Lock-out scenarios are not covered by any documented route. (a) Rolling back by reverting code after a later migration ran: the old image's `migrate` raises `gone` (`migrate.py:320`), and an init container running `migrate` would crashloop. The ticket's Rollback says "a revert needs no database step", true only for P3a itself. (b) A hotfix on a release line needing an out-of-order number: no route. (c) A rename: the hand-fix text exists (`migrate.py:322-325`), but there is no equivalent for the new order refusal.
*   **Rationale:** evidence: ticket line 78; `migrate.py:320-326`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket line 78; `migrate.py:320-326`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Safe escape and rollback (attack 1)
    *   Change: Add a short operator runbook (hand-applied file plus ledger row, rename, revert) and a test per case. State that `migrate` failing does not stop the runtime, if true (UNVERIFIED), and what the runtime does on a newer schema (Open point 6 defers it).

### [Issue 8] [`egm-design`] - Severity: Major (finding id A8, adversarial)
*   **Affected Scope:** Test plan on Windows (the studio laptop) of `handover/tickets/P3a.md`
*   **Discrepancy Description:** (1) FAIL-BEFORE 3 says `0002_b.SQL` is "ignored today". On Windows and macOS `glob("*.sql")` is case-insensitive, so it is matched and refused by the name check already. The fail-before test therefore passes on the old code on the laptop. (2) FAIL-BEFORE 4 and the symlink hostile inputs need `os.symlink`, which on Windows needs privilege or Developer Mode. The tests error or skip, but the done rule says "0 skipped". (3) Junctions and `is_symlink` differ on Windows.
*   **Rationale:** evidence: ticket lines 49-53, 69; `migrate.py:93-94`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 49-53, 69; `migrate.py:93-94`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Test plan on Windows (the studio laptop)
    *   Change: Make the fail-before tests platform-aware (use `os.scandir` names, not `glob`, in the new code), and have the symlink test either create links portably or be explicitly Linux-only with that stated. Run the evidence on Linux and say so.

### [Issue 9] [`egm-design`] - Severity: Major (finding id A9, adversarial)
*   **Affected Scope:** Manifest cost vs benefit of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The hash catches an edit to a listed file but not an edit to a line and its file together (Open point 4 leaves this to a manual diff). It adds a manifest edit to every migration PR and a hash recompute on every fix batch of a not-yet-merged file. Two PRs with different numbers (0006 and 0007) both pass alone and conflict only if the lead resolves with "keep both" (then M14, entry n has number n, catches it). Its value over the cheaper alternatives is small: the duplicate check already runs on main, and "require branches up to date" or a merge queue (Open point 5, UNVERIFIED) covers the race. The unique gain is the frozen hash of released files, and the check applies to unreleased files too, so a builder cannot fix their own new migration without touching the manifest.
*   **Rationale:** evidence: ticket lines 29, 85-87
*   ***AI Suggestion:*** ESCALATE
*   ***Justification:*** Whether the migration manifest exists at all (and its scope) is a decision of the lead; the ticket already lists it as Open point 3. Recommended: keep the manifest, scope the hash to RELEASED entries (list extended by the lead at tag time), make the lead's git diff check a gate.
*   ***Proposed Edit:***
    *   Location: Manifest cost vs benefit
    *   Change: Keep the hash idea but scope it to "released" entries (a list the lead extends at tag time). Put in the ticket that the lead's `git diff pre-P3a` check is a gate, not a recommendation. State whether editing an unmerged file in a fix batch is allowed.

### [Issue 10] [`egm-codebase-details`] - Severity: Major (finding id C1, correctness)
*   **Affected Scope:** Interface, bullet "migrate() calls folder_problems first (as now)" of `handover/tickets/P3a.md`
*   **Discrepancy Description:** "As now" is false. Today `migrate()` evaluates `check_ledger(files) + check_grants(files)` in one expression, so `check_grants` always runs. The ticket also makes `_migration_files` list every entry (directories, `.sql.bak`, dangling symlinks). `_scan` then does `path.read_text(encoding="utf-8")` on each. A directory raises IsADirectoryError, a dangling symlink FileNotFoundError, a binary `.bak` UnicodeDecodeError. These are raw exceptions, not a refusal, and they fire before the `MigrationNumberError` message is built. A directory named `0002_x.sql` already crashes this way today.
*   **Rationale:** evidence: `migrate.py:304-306` (single `if problems := check_ledger(files) + check_grants(files)`); `migrate.py:131` (`_scan` read_text); `migrate.py:93-94`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Combine with A2: runtime refuses non-regular entries that cannot be read (directory, dangling link) with MigrationNumberError and not a raw OSError; a symlink to a regular file is allowed at runtime and refused only by the CI check. The finding is valid: the reviewer cites evidence that can be read (`migrate.py:304-306` (single `if problems := check_ledger(files) + check_grants(files)`); `migrate.py:131` (`_scan` read_text); `migrate.py:93-94`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface, bullet "migrate() calls folder_problems first (as now)"
    *   Change: Specify two sequential steps. First `folder_problems`, raise `MigrationNumberError` on any problem. Only then run `check_grants`, and only on regular files. Add a migrate-level hostile test (directory, dangling symlink, binary `.bak`) that expects `MigrationNumberError`, not a raw OSError.

### [Issue 11] [`egm-codebase-details`] - Severity: Major (finding id C2, correctness)
*   **Affected Scope:** Interface (`folder_problems(folder)` vs `check_ledger(paths)` "thin wrapper"); Tests of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The signatures do not fit together. `folder_problems` takes a folder, `check_ledger` takes a list of paths, and the ticket never says which one `migrate()` calls. Existing tests patch the seam `monkeypatch.setattr(mig, "_migration_files", lambda: files)` and migrate() then validates that list. If `migrate()` calls `folder_problems(MIGRATIONS)` it validates the real folder instead of the patched list, so the new hostile-name tests and the two-thread test with a planted file cannot reach it. Also `_migration_files(folder=MIGRATIONS)` binds its default at definition time. Patching `mig.MIGRATIONS` is a silent no-op, and the ticket says tests use `mig.MIGRATIONS`.
*   **Rationale:** evidence: `tests/test_k2_migrations.py:108`, `:390`; `tests/test_k5_fixes2.py:300`; `migrate.py:93`, `:304`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`tests/test_k2_migrations.py:108`, `:390`; `tests/test_k5_fixes2.py:300`; `migrate.py:93`, `:304`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface (`folder_problems(folder)` vs `check_ledger(paths)` "thin wrapper"); Tests
    *   Change: State that `migrate()` checks the list returned by `_migration_files()`. Make `check_ledger(paths)` the real implementation (it can test `is_symlink`, `is_file` and case on the Paths), with `folder_problems(folder)` as `check_ledger(_migration_files(folder))`. Tell the builder to patch `_migration_files`, never `MIGRATIONS`.

### [Issue 12] [`egm-codebase-details`] - Severity: Major (finding id C3, correctness)
*   **Affected Scope:** Tests, "FAIL-BEFORE (must pass on new code and fail on ce70eb5)"; Evidence command 5 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Items 1, 5 and 6 can only fail on ce70eb5 by ImportError, because `migration_numbers`, `order_problems`, `folder_problems`, `check_migration_numbers` and the manifest do not exist there. A module-level import makes the whole new test file a collection error. That includes the regression guard (the duplicate-number test), which should pass on old code. Such a run shows "module missing", not "old behaviour accepted this input". Studio rule 9 and plan rule 5 want proof of the old behaviour.
*   **Rationale:** evidence: the ticket's own test list; `ce70eb5` has no `store/migration_numbers.py`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (the ticket's own test list; `ce70eb5` has no `store/migration_numbers.py`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Tests, "FAIL-BEFORE (must pass on new code and fail on ce70eb5)"; Evidence command 5
    *   Change: Write items 2-4 against the existing API, which runs on both versions: `mig.check_ledger(mig._migration_files(tmp))`. Item 1 can use real `migrate()` against a seeded ledger, which also needs no new import. Put new-module tests in the file separate from these, or import lazily. State for each FAIL-BEFORE which assertion fails on ce70eb5 and why.

### [Issue 13] [`egm-codebase-details`] - Severity: Major (finding id C4, correctness)
*   **Affected Scope:** Tests, "Previous-release test"; Done of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The plan row (plan-v3 section 6 P3a and section 10) wants a test that the previous release's code reads the new schema or fails loudly. Layer 1, the only layer in CI, is structural: it compares `information_schema` columns and nullability and never runs old code. Layer 2 is infeasible as written for any migration that adds a table, which is the common case. (a) The old `check_grants`/`GRANTS` refuses any new table, so every `pg_schema` fixture in the old tree fails. (b) `tests/test_p2_postgres.py:290` hard-codes `migrate(...) == ["0004_audit_checkpoint_meta", "0005_evidence"]`. (c) `tests/test_k2_migrations.py:357-371` asserts the catalog equals `GRANTS`. P3a itself adds no migration, so at its own verification there is nothing to copy into the old tree. Done does not require Layer 2. Layer 1 also misses changes that break an old writer without touching columns, such as the `ADD CONSTRAINT ... UNIQUE` in `0003_approvals_tick.sql:12`, a CHECK constraint, or a trigger.
*   **Rationale:** evidence: `test_p2_postgres.py:290`; `test_k2_migrations.py:357-371`; `migrate.py:150-166`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`test_p2_postgres.py:290`; `test_k2_migrations.py:357-371`; `migrate.py:150-166`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Tests, "Previous-release test"; Done
    *   Change: Say plainly that Layer 2 only works for ALTER-only migrations and only for tests that do not hard-code the list. Add a planted ALTER-only migration so the lead's check runs once at P3a. Make Layer 2's result a Done item. Extend Layer 1 to compare constraints (`pg_constraint`) and triggers, or list that gap in the ticket.

### [Issue 14] [`egm-codebase-details`] - Severity: Major (finding id C5, correctness)
*   **Affected Scope:** Security notes ("`"breaking": true` manifest flag") of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The flag is mentioned once. It is not in the Interface (`Manifest` fields), the Tests, or the mutants. It is also tied to the manifest, which is conditional on Open point 3. Plan section 10 says a non-revertible change must carry a loud-failure test, and this flag is the ticket's only mechanism for it. The builder would have to invent the semantics. Layer 1 would fail a breaking migration, and nothing says how the flag interacts.
*   **Rationale:** evidence: the ticket's Security section; Interface "Manifest" bullet
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** Decision: DROP the 'breaking' manifest flag (not needed for v1); a destructive migration must carry its own loud-failure test, written by that migration's builder. The finding is valid: the reviewer cites evidence that can be read (the ticket's Security section; Interface "Manifest" bullet). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Security notes ("`"breaking": true` manifest flag")
    *   Change: Define the `Manifest` field, what the flag exempts from the compat test and what it requires instead, add a test and a mutant for it, and say what applies if the lead declines the manifest.

### [Issue 15] [`egm-design`] - Severity: Nit (finding id A10, adversarial)
*   **Affected Scope:** `order_problems` malformed input of `handover/tickets/P3a.md`
*   **Discrepancy Description:** `order_problems(applied, files)` is pure and tested in isolation. A hostile or hand-edited ledger name that does not match `NAME` (non-ASCII digits, empty, no number) would make `int(name[:4])` raise a bare `ValueError`, not `MigrationNumberError`. The seeded fuzz test asserts "only `MigrationNumberError` is ever raised" but covers folders, not ledger values.
*   **Rationale:** evidence: ticket lines 27, 59
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 27, 59). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: `order_problems` malformed input
    *   Change: Specify: unparseable applied names are ignored here (`gone` handles them) or reported as a problem. Add the fuzz case.

### [Issue 16] [`egm-design`] - Severity: Nit (finding id A11, adversarial)
*   **Affected Scope:** Hard-coded values of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The 20-problem cap and the `[0-9]{4}` pattern (so 9999 migrations) are literals. The repo has `tests/test_no_hardcoded_values.py`; the ticket does not say whether these pass it. Copying `bad[:20]` from `migrate.py:344` is precedent, not a justification.
*   **Rationale:** evidence: ticket lines 24-25, 77
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 24-25, 77). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hard-coded values
    *   Change: Named module constants with a one-line reason. Run the guard in the evidence list explicitly (it is named under Done but not under the commands).

### [Issue 17] [`egm-design`] - Severity: Nit (finding id A12, adversarial)
*   **Affected Scope:** Mutation plan of `handover/tickets/P3a.md`
*   **Discrepancy Description:** No mutant targets the lock order. M8 removes the `order_problems` call. A mutant that moves `order_problems` before the advisory lock or reads `done` outside the transaction would survive, because the one-transaction design already protects it. Also no mutant for the `done` set parsing (name versus number) and none for the `gone`-before-order ordering.
*   **Rationale:** evidence: ticket lines 63-68
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 63-68). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Mutation plan
    *   Change: Add: M15 order check before `pg_advisory_xact_lock`; M16 swap `gone` and order checks.

### [Issue 18] [`egm-design`] - Severity: Nit (finding id A13, adversarial)
*   **Affected Scope:** Hot-file ordering and later packages of `handover/tickets/P3a.md`
*   **Discrepancy Description:** P3b and P3c builders hit the manifest and `tests/test_k2_migrations.py` together, and the spec says each renames its file and its manifest entry by hand. `previous_release.last_migration` is lead-owned but is also a hot line in the same JSON file. Also unspecified: new top-level file `store/migration_numbers.py` and the repo guard tests (`test_repo_rules.py`, the lock-in guard) - the ticket asserts they pass but did not read them.
*   **Rationale:** evidence: ticket lines 8, 36, 83
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 8, 36, 83). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Hot-file ordering and later packages
    *   Change: Add the manifest to the hot-file list for P4b1, P3b and P3c. Read `tests/test_repo_rules.py` before building.

### [Issue 19] [`egm-design`] - Severity: Nit (finding id A14, adversarial)
*   **Affected Scope:** Wording of `handover/tickets/P3a.md`
*   **Discrepancy Description:** "A refusal rolls back (the whole run is one transaction)" is fine, but the ticket also says "partial failure" never occurs. A migration using statements that cannot run in a transaction (for example `CREATE INDEX CONCURRENTLY`) fails, so the one-transaction claim is a constraint on future migrations the ticket should state. "A breaking: true manifest flag" appears in the security notes (line 45) but not in the manifest interface or the tests. "Released name never changes" is undefined without a release.
*   **Rationale:** evidence: ticket lines 29, 45, 78
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (ticket lines 29, 45, 78). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Wording
    *   Change: Define each term where it is first used, or drop the flag.

### [Issue 20] [`egm-codebase-details`] - Severity: Nit (finding id C10, correctness)
*   **Affected Scope:** Tests, FAIL-BEFORE 3 and 4; Evidence of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Both depend on the OS. `Path.glob("*.sql")` is case-insensitive on Windows and macOS, so `0002_b.SQL` is already refused there and FAIL-BEFORE 3 would not fail before. Creating symlinks needs a privilege on Windows. The studio work is done partly on a Windows laptop (CLAUDE.md mentions PowerShell), and the "0 skipped" rule would be hit by a symlink skip.
*   **Rationale:** evidence: `migrate.py:94`; CLAUDE.md rules
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`migrate.py:94`; CLAUDE.md rules). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Tests, FAIL-BEFORE 3 and 4; Evidence
    *   Change: State that the evidence runner must be Linux (CI is `ubuntu-24.04`, `ci.yml:34`). Mark the symlink tests Linux-only and say how "0 skipped" is judged on a laptop.

### [Issue 21] [`egm-codebase-details`] - Severity: Nit (finding id C6, correctness)
*   **Affected Scope:** Mutation plan, M8 of `handover/tickets/P3a.md`
*   **Discrepancy Description:** The second killer cannot kill M8. `order_problems` needs the ledger, which is only read after `connect()`, so a test with a patched `connect` or the `postgresql://unused` DSN stops earlier. Only Postgres test 1 kills M8. The cited `tests/test_k2_migrations.py:125` is the role-name injection test. The "refuses before connecting" pattern is at `test_k2_migrations.py:106-115`.
*   **Rationale:** evidence: `migrate.py:309-327`; `test_k2_migrations.py:106-125`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`migrate.py:309-327`; `test_k2_migrations.py:106-125`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Mutation plan, M8
    *   Change: Drop the second killer. Cite `:106-115`. Add a pure-function `order_problems` test that a mutated call site can reach only through Postgres test 1.

### [Issue 22] [`egm-codebase-details`] - Severity: Nit (finding id C7, correctness)
*   **Affected Scope:** Several cited line numbers and counts of `handover/tickets/P3a.md`
*   **Discrepancy Description:** (a) "asserts at least five files, as `tests/test_k2_migrations.py:30`": it is `assert len(files) >= 4` at line 31. (b) `mig.MIGRATIONS` "used in `tests/test_k5_fixes2.py:262`": line 262 is a docstring; the uses are `:266` and `:272`. `test_p2_postgres.py` imports `MIGRATIONS` directly (`:28`, uses at `:47`, `:168`, `:280`). (c) "the one `DROP TABLE` is an injection test string, `test_k2_migrations.py:125`": `tests/test_p2_postgres.py:78` has the same string. Other test files also contain DROP TABLE strings. (d) "Line numbers in memo 4 are a few lines off": memo says `_FILE` ~64 (actual 71) and the lock ~219 (actual 314, 95 lines off).
*   **Rationale:** evidence: `test_k2_migrations.py:31`; `test_k5_fixes2.py:262,266,272`; `test_p2_postgres.py:28,78`; memo-4 sec. 3
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`test_k2_migrations.py:31`; `test_k5_fixes2.py:262,266,272`; `test_p2_postgres.py:28,78`; memo-4 sec. 3). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Several cited line numbers and counts
    *   Change: Correct the four statements.

### [Issue 23] [`egm-codebase-details`] - Severity: Nit (finding id C8, correctness)
*   **Affected Scope:** Interface, `order_problems` of `handover/tickets/P3a.md`
*   **Discrepancy Description:** "every file whose name is not in `applied`": `applied` holds stems (`done = {r[0] ...}`, ledger stores `path.stem`). A file's `.name` ends in `.sql`, so a literal reading flags every file. The example message mixes both forms.
*   **Rationale:** evidence: `migrate.py:319`, `:328`, `:331`
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`migrate.py:319`, `:328`, `:331`). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Interface, `order_problems`
    *   Change: Say "stem" explicitly and show the number-parse rule (`int(stem[:4])`, ASCII digits only).

### [Issue 24] [`egm-codebase-details`] - Severity: Nit (finding id C9, correctness)
*   **Affected Scope:** Header (path class, review depth), Done of `handover/tickets/P3a.md`
*   **Discrepancy Description:** Three inconsistencies. (1) "Path class: other" with "Extended review (no round cap): yes". Studio rule 8 says non-money/redaction/security packages get at most 2 fix batches. The plan makes this Tier A with no cap, but plan section 4 rule 3 escalates to the lead after round 5. (2) The evidence file is named `handover/evidence/P3a-<n>.md` in one place and `evidence-p3a.md` (plan section 9 row) in Done. (3) Times are given only in UTC (studio rule 14).
*   **Rationale:** evidence: `STUDIO-RULES.md` rule 8, rule 14; `plan-v3.md` lines 61, 178; template line 4
*   ***AI Suggestion:*** PROPOSE FIX
*   ***Justification:*** The finding is valid: the reviewer cites evidence that can be read (`STUDIO-RULES.md` rule 8, rule 14; `plan-v3.md` lines 61, 178; template line 4). The ticket author re-checks the cited line before editing; if the citation is wrong, the ticket text is corrected, not the finding.
*   ***Proposed Edit:***
    *   Location: Header (path class, review depth), Done
    *   Change: Write "Tier A (store), no cap but round-5 escalation", pick one evidence file name, add IST.
