# P3a round 1: disposition of the 24 findings

Ticket: `handover/tickets/P3a.md` (revision 3). Findings: `P3a-round1-adversarial.md` (A1-A14), `P3a-round1-correctness.md` (C1-C10). Resolve report: `P3a-round1-resolve-report.md`. Each claim was re-checked in the code at core `ce70eb5` before editing (commands in the last section). No finding was rejected. "Section" names the ticket field.

| id | severity | disposition | section | one line |
|---|---|---|---|---|
| A1 | BLOCKER | FIXED | Interface (`order_problems`), Tests (recipe test), Rollback (runbook), Open point 2 | The refusal text now gives the working recipe (hand-apply in one transaction, insert the ledger row, rerun); "renumbering is not the fix" is stated; a test runs the recipe and expects `migrate` to succeed. Verified: renaming leaves a gap that `check_ledger` refuses (`migrate.py:97-107`) and renaming applied files triggers `gone` (`:320-326`). |
| A2 | BLOCKER | FIXED | Interface (`check_ledger`, `check_migration_numbers`, "runtime path never refuses a symlink") | The symlink refusal runs only in `check_migration_numbers` (CI, tests); the runtime accepts a symlink to a regular file; a Linux guard test says so. Verified: the check ran inside `migrate()` (`migrate.py:304-306`). |
| A3 | MAJOR | FIXED | Interface (`_migration_files`, test seam) | `migrate()` keeps calling module-level `_migration_files()` and passes its list to `check_ledger`; tests patch `_migration_files`, never `MIGRATIONS` (verified: `test_k2_migrations.py:108, 390`, `test_k5_fixes2.py:300`; default argument bound at `migrate.py:93`). |
| A4 | MAJOR | FIXED | Open point 2, Files (CHANGELOG) | Lines re-checked with `grep -n 0006`: 11, 38, 45, 52 are false; line 10 is correct. All four are REWORDED in a reviewable edit plus a runbook is appended. |
| A5 | MAJOR | FIXED | Tests (layer 1) | Layer 1 reads `pg_catalog` as the owner role (columns, defaults, NOT NULL, constraints, indexes, triggers, views) and says it proves the old schema is still present, not that old code works; planted cases and mutants M10a-f. |
| A6 | MAJOR | FIXED | Tests (layer 2), manifest | Layer 2 works only for ALTER-only migrations; procedure defined (old tree's own five files, new SQL applied directly through a wrapper plugin); `previous_release.ref` is informational. Feasibility of the plugin stays UNVERIFIED until the lead runs it. |
| A7 | MAJOR | FIXED | Rollback (runbook a-c), Tests (recipe, newer ledger) | Runbook for order refusal and hotfix, rename, and code revert; each case has a test. Verified by grep that `src/` calls `migrate` only from the `cli.py` command, so a failed `migrate` does not stop a running service; an init-step deployment is UNVERIFIED. |
| A8 | MAJOR | FIXED | Tests (header), FAIL-BEFORE 3 | Evidence on Linux (`ci.yml:34, 98` is `ubuntu-24.04`); `.SQL` test checks the name with `os.scandir` and is Linux-only; symlink tests skip only on Windows. |
| A9 | MAJOR | ESCALATED | Interface (Manifest), Open point 3 | Recommendation kept and marked PENDING LEAD: manifest scoped to released entries, lead extends at tag time, the lead's `git diff` check is a gate, builders may edit unmerged files freely; fallback without the manifest is written. |
| A10 | MINOR | FIXED | Interface (`order_problems`), Tests (hostile, property) | Unparseable ledger names are ignored by `order_problems` (the `gone` refusal reports them); ledger fuzz case and mutant M13 added. |
| A11 | MINOR | FIXED | Interface (constants), Evidence 1 | Named constants `NAME` and `MAX_PROBLEMS_SHOWN` with reasons; `tests/test_no_hardcoded_values.py` and `tests/test_repo_rules.py` are in the evidence command (read: the first scans `src/` strings for key, host, URL shapes; the second has no migration rule). |
| A12 | MINOR | FIXED | Mutation plan | M15 (order check before the lock) with a deterministic lock-wait test; M16 (swap `gone` and order) with `test_gone_wins_over_order`; M13 for ledger parsing. |
| A13 | MINOR | FIXED | Depends on (hot files), Existing code reused | Manifest named a hot file (lead edits only); `tests/test_repo_rules.py` read (no migration rule); `tests/test_lockin_guard.py:69` unchanged. |
| A14 | MINOR | FIXED | Header words, Security notes | "Stem", "applied", "released" defined where first used; one-transaction constraint stated (`CREATE INDEX CONCURRENTLY`, from PostgreSQL documentation, not run; none in the repo by grep); the `breaking` flag is dropped. |
| C1 | MAJOR | FIXED | Interface (`migrate()` steps) | Two sequential steps: `check_ledger` raises `MigrationNumberError`, then `check_grants` only on regular files. Reproduced on `ce70eb5`: a directory named `0002_x.sql` passes `check_ledger` and raises a raw `IsADirectoryError` in `check_grants`. FAIL-BEFORE 4-5. |
| C2 | MAJOR | FIXED | Interface (`check_ledger`, `folder_problems`) | `check_ledger(paths)` is the implementation; `folder_problems(folder) = check_ledger(list_migration_files(folder))`; `_migration_files(folder=MIGRATIONS)` keeps its signature (`test_k5_fixes2.py:269` passes a folder). |
| C3 | MAJOR | FIXED | Tests (FAIL-BEFORE 1-5) | Every fail-before uses the existing API (`mig.check_ledger(mig._migration_files(tmp))`, real `migrate()` with a seeded ledger) and names the assertion that fails on `ce70eb5`; new-API tests import inside the test and are not counted as fail-before. |
| C4 | MAJOR | FIXED | Tests (layer 1, layer 2), Done | Layer 2 only for ALTER-only migrations, one planted at P3a verification, result is a Done item; layer 1 compares constraints and triggers too. Note for P4d: `tests/test_p2_postgres.py:290` hard-codes the applied list (verified); also `tests/test_k5_fixes2.py:299-307` and `tests/test_k2_migrations.py:357-371` (catalog equals `GRANTS`). |
| C5 | MAJOR | FIXED (flag dropped) | Interface (no `breaking` flag) | The flag is removed everywhere (A13); a destructive migration carries its own loud-failure test; layer 1 refuses such a change until that package's ticket justifies it. |
| C6 | MINOR | FIXED | Mutation plan (M8), Tests | Only `test_late_number_is_refused` kills M8; the "refuses before connecting" pattern cited correctly as `tests/test_k2_migrations.py:106-115` (it checks that `connect` is not called). |
| C7 | MINOR | FIXED | Problem 4, Tests (hostile), Existing code, Security | Corrected: `assert len(files) >= 4` is `tests/test_k2_migrations.py:31`; `MIGRATIONS` uses are `test_k5_fixes2.py:266, 272` and `test_p2_postgres.py:28, 47, 168, 280`; `DROP TABLE` strings at `test_k2_migrations.py:125` and `test_p2_postgres.py:78` (not every file searched); memo 4 line numbers off (`_FILE` 71 not about 64; lock 314 not about 219). |
| C8 | MINOR | FIXED | Interface (`order_problems`) | "Stem" is explicit; number rule is `int(stem[:4])` for ASCII-pattern stems only. |
| C9 | MINOR | FIXED | Header, Path class, Done, Evidence | "Tier A (store), no cap, escalation after round 5"; one evidence file name (`handover/evidence/P3a-<n>.md`, the lead copies it to `evidence-p3a.md`); IST stated. |
| C10 | MINOR | FIXED | Tests (header, FAIL-BEFORE 3) | Same as A8: Linux evidence, `.SQL` and symlink tests Linux-only, "0 skipped" judged on Linux. |

Counts: 24 findings; FIXED 23 (C5 by dropping the flag); REJECTED 0; ESCALATED 1.

## ESCALATED (for the lead)
- A9: the migration manifest (hash of released migrations). Decide yes or no. Recommended: yes, scoped to released entries, lead-edited at tag time, `git diff` check as a gate (ticket Open point 3). Marked PENDING LEAD in the ticket.

## What I re-checked in code (commands)
- `git rev-parse origin/main` = `ce70eb5`; `grep -n 0006 CHANGELOG.md` (lines 11, 38, 45, 52); `sed` of CHANGELOG lines 10-11.
- `sed`/`grep` of `src/hadavin_sdk/store/migrate.py` (lines 15, 69, 71, 93-107, 131, 304-332), `tests/test_k2_migrations.py` (31, 106-125, 357-371, 387-394), `tests/test_k5_fixes2.py` (262-307), `tests/test_p2_postgres.py` (28, 47, 78, 157, 168, 280, 290), `.github/workflows/ci.yml` (lines 34, 98), `tests/test_repo_rules.py`, `tests/test_no_hardcoded_values.py`, `.gitattributes`.
- Probes in the scratchpad: `check_ledger` on Unicode digits and `.SQL` (no problem returned); directory named `0002_x.sql` (passes `check_ledger`, raw `IsADirectoryError` from `check_grants`).
- `grep -rn CONCURRENTLY src tests` (none); `grep migrate src/hadavin_sdk/app.py` (none); migration SQL has triggers (`0002`) and no view.

## Still UNVERIFIED
Postgres behaviour (no server here; late number, recipe, layer 1, layer 2 plugin, lock-wait test); dangling-symlink and non-UTF-8 crashes (by code reading); `CREATE INDEX CONCURRENTLY` inside a transaction (PostgreSQL documentation); deployments that run `migrate` as an init step; owner's answer on branch-built databases.
