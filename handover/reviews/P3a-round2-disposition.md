# P3a round 2: disposition of the 22 findings (ticket revision 4)

Findings: `P3a-round2-adversarial.md` (A1-A13), `P3a-round2-correctness.md` (C1-C9). Resolve report: `P3a-round2-resolve-report.md` (all 22 PROPOSE FIX). Each claim was re-checked in the code at core `ce70eb5` before editing (commands at the end). Section = field of `handover/tickets/P3a.md`. No finding was rejected.

| id | severity | disposition | section | one line |
|---|---|---|---|---|
| A1 | MAJOR | FIXED | Interface (`check_ledger`, `migrate()`), FAIL-BEFORE 5 | `check_ledger` now reads each file's bytes, decodes UTF-8 and turns `OSError`/`UnicodeDecodeError` into problem lines; "check_grants raises ConfigError as now" reworded (`check_grants` returns a list, `migrate()` raises). Verified: `_scan` uses `read_text` (`migrate.py:131`); `is_file()` is no readability test. |
| A2 | MAJOR | FIXED | Rollback runbook (c), Tests runbook case (iv) | Collision between a release branch and main: the applied hotfix keeps its name, main renumbers; exact steps for a production database and for a dev database (rename row, then `--accept-late`); a release branch reserves its number on main first; both cases have tests. |
| A3 | MAJOR | FIXED | Interface (`accept_late`, decision paragraph, `cli.py`), Tests (a)-(e), Security | Decided: a supported `migrate --accept-late STEM` (one locked transaction, grants in the same run) replaces the hand recipe; tests cover a dependent late file, upgraded equals fresh, wrong stems, atomicity, the lock. Reason and cost stated. Verified: lock `_LOCK` is internal (`migrate.py:69`); grants only with role flags (`:340-345`). |
| A4 | MAJOR | FIXED (text); manifest decision stays PENDING LEAD | Open point 3 | Weaknesses named (released lags applied; line plus file edit passes CI; manual git-diff gate; ledger holds only the stem), the stronger option (every merged migration + CI diff job) and the cost of declining stated; checksum column left out with the reason (Source). |
| A5 | MAJOR | FIXED | Tests (layer 1) | Layer 1 now also compares functions, policies, rules, ACLs, types, comments, sequence settings, seeded data; A built from manifest-hashed files only; reworded to "catalog structure of the listed kinds on seeded tables"; planted cases for each kind. |
| A6 | MAJOR | FIXED | Merge precondition, Tests runbook case (v), Open point 2 | Precondition has two parts (branch-built database; ledger row renamed to `0006_evidence`) and the `SELECT version` check covers both; runbook says rename it back; test seeds that ledger. |
| A7 | MAJOR | FIXED | Tests (layer 2), Done, Open point 6 | Layer 2 stated as NOT recurring; "layer 2 run logged" requested for P4d-b, P3b, P3c (or a CI job); probe idempotent. |
| A8 | MINOR | FIXED | Tests runbook case (vi), mutant M13 | Test for a ledger with only non-matching stems (refused by `gone`, no exception from `order_problems`). |
| A9 | MINOR | FIXED | Interface (non-transactional statements) | Named `CREATE/DROP INDEX CONCURRENTLY`, `REINDEX CONCURRENTLY`, `VACUUM`, `CREATE/DROP DATABASE`, `CREATE TABLESPACE`, `ALTER SYSTEM`, `ALTER TYPE ... ADD VALUE`; added to `_UNREAD` (existing refusal); one mutant each; `lock_timeout` left to P4d. |
| A10 | MINOR | FIXED | Tests (layer 1 baseline), constants | `PREVIOUS_RELEASE_LAST` derived from the manifest's last released entry; fallback constant has a review date (2026-11-05) and a test that it names a file; `POLL_TIMEOUT_S`, `FUZZ_CASES`, `FUZZ_SEED` named. |
| A11 | MINOR | FIXED | Mutation plan | Added: manifest rules (M30), min vs max (M11), runtime refuses symlink (M16), cap off by one (M7), suffix match (M8), `.bak`/`__pycache__` refusal (M18), readability (M9), accept-late (M22-M26), layer-1 kinds (M27-M29). |
| A12 | MINOR | FIXED | Tests (header), Evidence 1, Done | Any "skipped" in the two new test files is a failed evidence run; the runner greps for it; the unreadable-file test patches `read_bytes`, so no root skip. |
| A13 | MINOR | FIXED | Header, Files, Interface | Edits described by symbol; "released" defined once (manifest list) with the no-manifest case separate; error text explains why "Do not rename it" differs from the `gone` advice. |
| C1 | MAJOR | FIXED | Interface (`check_ledger`), FAIL-BEFORE 5, property test | Same fix as A1; plain sentence that `is_file()` is not a readability test; mutant M9; exact-type check in the property test. |
| C2 | MAJOR | FIXED | Tests (layer 1) | Functions compared via `pg_get_functiondef` (verified: `hadavin_audit_append_only` in `0002_audit_chain.sql:25-26`, called by four triggers; `_SAFE_CREATE` allows `CREATE OR REPLACE FUNCTION`, `migrate.py:81`); planted no-op case; mutant under M27. |
| C3 | MINOR | FIXED | FAIL-BEFORE 4-5 | Tests use `pytest.raises(Exception)` then `assert isinstance(e.value, ConfigError)` and the file name in the message, so they fail on an assertion on `ce70eb5`. |
| C4 | MINOR | FIXED | Tests (layer 2) | Probe uses `ADD COLUMN IF NOT EXISTS`; the wrapper runs the new SQL only when the original returned a non-empty list (verified: old tests call `migrate` repeatedly, `test_p2_postgres.py:157-170`). |
| C5 | MINOR | FIXED | Tests (layer 1) | Schemas read under their own `search_path` with any schema prefix stripped; test that identical A and U show no difference; mutant M28. |
| C6 | MINOR | FIXED | Open point 3 | Cost of declining stated: without the manifest CI has no out-of-order check; plan row P3a is then met only at run time. |
| C7 | MINOR | FIXED | Security notes, Problem 2, Open points | Corrected: `test_k5_round10_postgres.py:137-142` shows `migrate` refuses a PUBLIC grant on `schema_migrations` (reworded); transaction spans `migrate.py:312-359` (verified: `return applied` ends it); `test_k2_migrations.py:36-55`; plan rule 10, not F6, lists `migrate.py` and CHANGELOG (F6 lists `cli.py`). |
| C8 | MINOR | FIXED | Tests (a), mutant M25 | The test pulls the stem out of the real error message (`--accept-late (\S+)`) and runs it; a mutant corrupts the stem. |
| C9 | MINOR | FIXED | Interface (`MigrationNumberError`), Tests | Exact type checks (`type(e) is MigrationNumberError`) because `ConfigError` derives from `ValueError` (verified `errors.py:4`). |

Counts: 22 findings; FIXED 22; REJECTED 0; ESCALATED 0. The manifest itself (Open point 3) remains PENDING LEAD, as ordered.

## Re-verified in code (commands)
`sed`/`grep` on `src/hadavin_sdk/cli.py` (`migrate` sub-parser, `_migrate`), `src/hadavin_sdk/store/migrate.py` (lines 69, 312-360), `src/hadavin_sdk/errors.py:4`, `src/hadavin_sdk/store/migrations/0002_audit_chain.sql:22-36`, `tests/test_k5_round10_postgres.py:134-143`, `tests/test_k2_migrations.py:28-36, 104-150`, `.github/workflows/ci.yml:78-90`, `LEAD-ORDERS.md` order 5, `amendments.md` A14; earlier probes (Unicode digits, `.SQL`, directory named like a migration).

## Still UNVERIFIED
Everything that needs Postgres (no server here); seeding every table and schema-name printing in layer 1; `accept_late` with grants in one transaction (design only); the layer 2 plugin; the dangling-symlink, non-UTF-8 and permission crashes (by code reading); the owner's answers to both precondition questions.
