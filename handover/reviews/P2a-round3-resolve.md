# P2a round 3 resolve report (egm:egm-resolve, Opus 5.5)

Status: resolved (categorised; ticket NOT edited here; the author rewrites revision 5)
Target: `handover/tickets/P2a.md` rev 4 (6d84ad6). Inputs: `P2a-round3-adversarial.md` (A1-A17), `P2a-round3-correctness.md` (C1-C11). Interactive gate skipped (auto mode). No contest, no escalation.
Cross-ticket constraints: P4d-b reads kill_switch with a plain SELECT (P4d rev 5); P2a depends on all five P4d sub-PRs; P3a merges before P2a-1a (migrate/cli editing).

| id | category | decision for revision 5 |
|---|---|---|
| A1 (blocker) | PROPOSE FIX | `sync_from_store` must never clear a non-durable stop: keep a `durable` marker on the local flag; clear only a flag known durable-and-reset, or when the store shows a newer version. Race test for store down/up. |
| C1 (blocker) | PROPOSE FIX | Rename the reset DSN config field so it does not end in `_secret_name`, so `platform_secrets.secret_names()` does not collect it; test that `check()` and runtime start never read it. |
| A2 | PROPOSE FIX | Trigger bumps `version` only on a real change (OFF to ON); ON to ON changes nothing; test; correct the remedy text. |
| A3 + C2 | PROPOSE FIX | Rollback is a DBA hand step with exact SQL under the migration lock; remove "run old migrate" (old migrate refuses). Test the recipe on a scratch DB. |
| A4 + C3 | PROPOSE FIX | MERGE 1a and 1b (accepted recommendation Q9): migration, `Limits.reset(expect_version=...)`, CLI and contract rows land together so every head is green. |
| A5 | PROPOSE FIX | `effective_problems` also blocks membership in the owner/migration role (`pg_has_role`) for runtime, portal, purge, reset; negative test. |
| A6 + A15 | PROPOSE FIX | Store only a masked label (keyed hash) of `session_user`, never the raw login; erasure limits and key-rotation note. |
| A7 | PROPOSE FIX | Reset audit order: `reset_attempted`, clear, then `reset` or `reset_failed`; test each failure point. |
| A8 | PROPOSE FIX | Breakglass: distinct login role in the reset group whose resets write a flagged audit row; the owner of the external alarm is PENDING LEAD; UNVERIFIED. |
| A9 | PROPOSE FIX | Specify and test the secrets-store ACL for the reset name per backend; runtime provider cannot read it; negative test. |
| A10 | PROPOSE FIX | `lock_timeout`/`statement_timeout` on stop writes and reset; a stop must not block behind a runtime row lock; second-connection test. |
| A11 + C10 | PROPOSE FIX | Persist the reset group (one-row config table) so a routine `migrate` without `--reset-role` does not replace the function with deny-all; test. |
| A12 | PROPOSE FIX | Probe re-runs periodically and at each stop/reset; owner `DISABLE TRIGGER` is detected. |
| A13 | PROPOSE FIX | Correct the stated reason for the 240/744 guard change; limit to persistent kill-switch read errors. |
| A14 | PROPOSE FIX | Missing `kill_switch` row: re-seed step in the DBA recipe; clear error; test. |
| A16 | PROPOSE FIX | Unique role names per test run, cleanup finalizer, local-socket setup stated; CI fail rule. |
| A17 | PROPOSE FIX | Add the listed surviving mutants; recount. |
| C4 | PROPOSE FIX | Correct the existing-test update list (`rt.limits` built without `reset_store`; fix lines found by grep). |
| C5 | PROPOSE FIX | Define the Store methods the probe needs and their mapping, or put the probe in `migrate.py` on a read-only connection. |
| C6 | PROPOSE FIX | Flag the deviation from A13(3) (runtime keeps SELECT+UPDATE for an open stop) as PENDING LEAD; extend `effective_problems` for per-person logins. |
| C7 | PROPOSE FIX | Fix citations and the hot-file list by reading the code. |
| C8 | PROPOSE FIX | Correct the premise about `judge()` / exit 0 in `testing/mutation.py`; drop or reword the two rows. |
| C9 | PROPOSE FIX | Fix per-sub-PR mutation counts after the 1a+1b merge. |
| C11 | PROPOSE FIX | Mark FAIL-BEFORE (5) as plausible; run on the old code via the evidence runner. |

Counts: 28 findings (A1-A17 grouped with C1-C11); PROPOSE FIX 28; CONTEST 0; ESCALATE 0; DECLINE 0. PENDING LEAD: breakglass alarm owner (A8), A13(3) deviation (C6). Severity unchanged. The author re-reads each finding in the review files; this table is a summary of decisions. Model: Opus 5.5 (resolve skill).
