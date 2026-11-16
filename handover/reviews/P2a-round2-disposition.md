# P2a round 2: disposition of the 30 findings (applies `P2a-round2-resolve-report.md` and lead order 5 / amendment A14 to `handover/tickets/P2a.md`, revision 4)

Written 2026-11-05 (UTC) by the ticket author (Sonnet 5.5). Counts: FIXED 30, REJECTED 0, ESCALATED 0. Items the lead still decides stay "PENDING LEAD" inside the ticket (wiring owner, PR split, F6 extension, P2a-2/-3 scope); they are not findings of this round. Each claim was re-read in core `ce70eb5` or the PR #50 snapshots before editing. Corrections to the reviewers' text are noted in the last column.

| id | severity | disposition | section of the ticket | one line |
|---|---|---|---|---|
| A1 | BLOCKER | FIXED | Interface (`set_kill_switch` plain UPDATE); Security "Privileges", "Effect on old code" | Chose plain `UPDATE` (runtime grant `SELECT, UPDATE`, no INSERT); old upsert at `postgres.py:453-460` then fails loudly; way back = old release's `migrate --runtime-role`; real-login test: stop succeeds, clear refused. |
| A2 | BLOCKER | FIXED | Interface `StopGate`; Security "Process split" | `release` and `restore(False)` removed from the runtime gate; `StopGate.sync_from_store()` (read only) and operator-side `StopOperator`; test that the runtime cannot build a reset-capable `Limits`. |
| A3 | MAJOR | FIXED | Security "Trigger", "`migrate(reset_role=...)`" | Python-issued `CREATE OR REPLACE FUNCTION` with `sql.Literal`, deny-all when no role, group checked by `pg_has_role`, added to validation, pairwise and `effective_problems`. |
| A4 | MAJOR | FIXED | Security "Trigger" | `session_user`, `ENABLE ALWAYS`, schema-qualified function with pinned `search_path`, `migrate` refuses a runtime role that owns the table or function, tests use real logins. |
| A5 | MAJOR | FIXED | Security "Roles", "Privileges" | Per-person LOGIN roles in a NOLOGIN group; trigger writes `session_user` to `kill_switch_resets`; breakglass is a separate dormant login; exact grants listed (reset handle writes no audit; audit goes through the runtime handle, checked at `audit/chain.py:180-231`). |
| A6 | MAJOR | FIXED | Security "Probe" | Start-up and `limits reset` probe (trigger enabled, function pinned, runtime not in group, rolled-back dry run); refuses in pilot/prod; a P2a-1a merge condition. |
| A7 | MAJOR | FIXED | Interface "Fail closed" | All `limits.blocked` sites handled (lines 240, 670, 744). Correction: there are three sites and six paths, not five; and the guard gives NEEDS_PERSON `limits_unavailable`, not STOPPED, because STOPPED is a final state (`runs.py:10-24`). Limit of the fix stated. |
| A8 | MAJOR | FIXED | Tests "Executor done condition"; Open point 1 | P2a-1c done condition: a stop blocks the executor call, including the in-flight case (test with the real `Executor` behind a fake transport). Wiring owner stays PENDING LEAD. tick.py settled: it has no stop check but isolates step errors (`tick.py:315`). |
| A9 | MAJOR | FIXED | Package line; Depends on; Files | Gate PR split into P2a-1a (database), 1b (Limits, masking, CLI, loop), 1c (gate); five PRs in total; P4b1 and P4c queue behind 1b only. Plan deviation flagged PENDING LEAD item 2. |
| A10 | MAJOR | FIXED | Mutation plan; Tests | New rows for the trigger SQL, `GRANTS`, every WHERE condition and the memory twin; Postgres tests create their own logins and FAIL without Postgres; thread test labelled smoke; runner refuses a skipped killer. |
| A11 | MINOR | FIXED | Rollback | Rewritten to the true behaviour: loud failure on old `stop` until grants are restored, trigger refuses old `reset`; downgrade test against true old code at core. |
| A12 | MINOR | FIXED | Interface "Config" | `MAX_CACHE_TTL_S = 10` ceiling in `defaults.py`, config above it rejected, the `status()` token path never cached. |
| A13 | MINOR | FIXED | Interface (stored state, CAS) | Server-side `version BIGINT` bumped by the trigger is the reset token; `ts` written with the database clock; lock-out by a looping runtime documented with its remedy. |
| A14 | MINOR | FIXED | Interface "Masking" | Stated: `by` is unauthenticated unless it is `session_user`; hash is privacy not authenticity; erasure position (delete the key); dev key never stored beyond the process. Audit rows also carry the masked `session_user`. |
| A15 | MINOR | FIXED | Neutral default | `StopBackend` outline carries its own restricted-reset identity, `Limits` takes it by injection, contract case "runtime credential cannot clear", single-dependency line added. |
| A16 | MINOR | FIXED | Neutral default; Files P2a-1b | Memory store refuses `limits stop/reset/status` and `Limits` construction outside dev, tested in P2a-1b. |
| A17 | MINOR | FIXED | Interface (stop audit failure, deterministic wording, `CREATE OR REPLACE FUNCTION`) | CLI exit 7 for "stop written, audit failed"; `stop_identities` sentence deleted; migration uses `CREATE OR REPLACE` only; "deterministic" wording fixed. |
| C1 | BLOCKER | FIXED | Interface; Security (all of "Privileges", "Reset credential path", "Trigger", tests) | (a) plain UPDATE; (b) reset role `SELECT, UPDATE` on `kill_switch`, audit through the runtime handle; (c) `reset_dsn_secret_name` in `backends/table.py:120`, resolved only in `cli.py` `limits reset` (precedent `app.py:152-160`); (d) function created from Python; (e) real-login tests, existing owner-DSN reset tests listed. |
| C2 | MAJOR | FIXED | Interface `StopGate`; Security "Process split" | Same as A2; `restore(False)` replaced by a read-only `sync_from_store`. |
| C3 | MAJOR | FIXED | Files P2a-1b, P2a-1c | Added `test_cuj.py:244-249` and `:283-306`, `test_p2_postgres.py:122-141`, the new `FakeLimits` (PR50 `test_promoted_controls.py:225-262`), the new `cli.kill_switch` signature and exit codes 0, 2, 3, 4, 5, 6, 7. |
| C4 | MAJOR | FIXED | Tests "FAIL-BEFORE" | Per test: head, call shape, failing line; tests rewritten so the old-shape step runs first and an assertion fails; the one "missing API" case is named as accepted. |
| C5 | MAJOR | FIXED | Mutation plan "weak row" | Claim removed: the test (`test_pr50_fix_batch3.py:353-358`) and the row (`promoted_mutants.py:2088-2095`) exist, verified; only fix (i) kept. |
| C6 | MAJOR | FIXED | Tests (d); Interface | Reworded: the final state is ON and the flag is on; an engage between the `_gen` check and the write can leave the store OFF briefly (`stop_gate.py:322-336`); test asserts the final state only. |
| C7 | MAJOR | FIXED | Mutation plan | Rows for trigger, `GRANTS`, SQL conditions and the memory twin; final count per sub-PR 43 / 14 / 22 / 17 / 49 = 145; runner refuses a skipped killer; evidence command 3 sets the DSN. |
| C8 | MAJOR | FIXED | Files P2a-2 | `tests/test_stop_state_runner.py` added to P2a-2 for the 21 runner and judge rows. |
| C9 | MINOR | FIXED | Interface "Fail closed" | Limit stated (`_to` and `_note` use the same store; effect only when the kill-switch read alone fails); `_recheck` (line 744) guarded. |
| C10 | MINOR | FIXED | Interface "Who may do what" | The `stop_identities` sentence is deleted (no such list exists in core or either PR50 head). |
| C11 | MINOR | FIXED | Interface (core methods, masking) | `Limits.is_stopped()` listed as NEW in core and in the gate's constructor check; gate audit rows ask `Limits` for the masked form. |
| C12 | MINOR | FIXED | Mutation plan "Re-pointed existing rows" | 23 re-pointed rows listed by name and by target (18 to P2a-1c, 4 labels to P2a-1b, 1 to P2a-1a); 25 stay. |
| C13 | MINOR | FIXED | Depends on | P2a-1a sits after P4d and before P6b2 on `store/postgres.py`; CHANGELOG order stated (P2a-2, P2a-3, P2a-1a, P2a-1b, P2a-1c). |

## Corrections to the reviewers' or lead's text (verified)
- `limits.blocked` call sites in `agent_loop.py`: three (240, 670, 744), reached by six paths; the brief said five.
- A guard that returns STOPPED on a read error would end runs permanently: `STOPPED` is outside `ALLOWED` in `runs.py:10-24`, so it is final. The ticket uses NEEDS_PERSON `limits_unavailable` (also what line 670 does).
- `tick.py` has no reference to limits or the kill switch; it catches exceptions per step (`tick.py:315`).

## ESCALATED
None among the 30 findings. Still PENDING LEAD in the ticket (from earlier rounds and this order): wiring owner (P4c recommended), F6 extension and the five-PR split, scope of P2a-2/P2a-3, hash-all masking, evidence file name, runner overlap with P2c, CI changes for Postgres.
