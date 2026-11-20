# review-code-AB-1 (lead's local Fable agent, 2026-11-20; read-only draft from the code, nothing run; verify every line; contest in DECISIONS.md)

# Early review: tickets A (audit drain) and B (stop state), worktree cloud-core-b

**Verdict:** No Blocker found by reading. Three Majors: two code gaps (one in A, one in the B command line) and most of ticket B's tests and docs are not written yet. Nothing was run; every verdict below is from reading only.

## What I reviewed

I could not name a commit (no git access), and the worktree moved under me: `handover/core-b/notes/builder-B-report.md` describes an older state (BIGSERIAL id, `WHERE "on"`, loop hunk not taken) than the files I read (UUID id, `WHERE id = 1`, loop hunk present). The state I reviewed is the later one.

All paths are under `C:\Users\rakes\Downloads\Hadavin\_local\scratch\wt\cloud-core-b\`.

- **Source read in full:** `src\hadavin_sdk\audit\chain.py`, `runtime\tick.py`, `store\migrate.py`, `store\migrations\0006_stop_state.sql`, `store\migrations\0002_audit_chain.sql`, `limits.py`, `cli.py`, `backends\platform_secrets.py`.
- **Source read in part:** `store\postgres.py` (130-250, 436-490), `store\protocol.py` (1-125), `store\memory.py` (212-227), `backends\table.py` (117-127), `runtime\agent_loop.py` (240-264, 708-721, 776-834).
- **Tests read:** `tests\test_audit_drain.py` and `tests\test_stop_state_loop.py` in full; `tests\test_p7_store.py` 120-247; `tests\contracts\kinds\store_postgres.py`; `tests\test_k5_fixes2.py` 256-285; `tests\test_migration_numbers_guards.py` 340-379; grep hits in `tests\test_p2_postgres.py` and `tests\fixtures\migrations_released.json`.
- **Specs read:** `egm\core-complete-2026-11-20\tickets\draft-A-B.md`, `handover\core-b\tickets\A-audit-drain.md`, `handover\core-b\tickets\B-stop-state.md`, the builder-B report, and the persona file.
- **Baseline:** only `store\memory.py` 212-227 was compared directly against `sdk-main` (identical). Everything else was judged against the tickets' description of main.

## Ticket A invariants

| # | Invariant | Verdict | Where |
|---|---|---|---|
| 1 | Every outbox row in the chain after one tick, exactly once, deleted only after | HELD for delete-after and exactly-once; BROKEN for "every row" (finding A-1) | `chain.py:278-280`, dedupe `188-189`, gap at `286-293` |
| 2 | Flush only after a successful append, stop at first failure | HELD | `chain.py:217-218`, `237-238`, `247-251` |
| 3 | `write_outcome` never raises; `write_intent` raises only two types; flush failure never raised | HELD | `chain.py:211-216`, `223-239`, `245-253` |
| 4 | Unreadable row never blocks, never deleted, count only in the error | HELD | `chain.py:270-277`, `281-283`; `tick.py:325` |
| 5 | Non-connectivity read error fails the step; connectivity error is a quiet return | HELD | `chain.py:262-267` |
| 6 | Chain order is write order; drained event keeps its own ts; verify ok | HELD | `chain.py:185` |
| 7 | Stated limit: memory-only events lost on exit | HELD | `chain.py:173-174`; `SECURITY.md:12-14`; pinned by `test_audit_drain.py:555-567` |
| 8 | `_note_card` unchanged | HELD | `agent_loop.py:243-248` matches the ticket's text; not diffed against baseline |

The tick step is last (`tick.py:243-248`, `274`); the docstrings at `tick.py:4-5` and `cli.py:9-12` are updated.

## Ticket B invariants

| # | Invariant | Verdict | Where |
|---|---|---|---|
| 1 | Runtime role cannot turn ON to OFF | HELD by the grant map; no real-login test yet | `migrate.py:59-61`; `0006_stop_state.sql:17-24`; catalogue check at `test_p7_store.py:157-165` |
| 2 | ON = row missing OR flag on OR an open stop | HELD | `postgres.py:444-462` |
| 3 | Stop is one INSERT, works with audit down, UUID id | HELD | `postgres.py:465-470`; `limits.py:45-46`; `0006_stop_state.sql:7` |
| 4 | Reset clears only visible stops; two resets both succeed | HELD by reading | `postgres.py:473-484`; no concurrency test yet |
| 5 | Reset audited first; audit down means exit 3; refused reset leaves `reset_failed` | HELD in code | `limits.py:51-56`; `cli.py:450-458`; no test for `reset_failed` |
| 6 | Reset role holds exactly the listed rights | HELD | `migrate.py:59-64`, `369-374`, schema USAGE at `181` |
| 7 | Four different roles, not members of each other | HELD | `migrate.py:312-318`, `348-354`, owner membership `226-229`; see B-5 |
| 8 | Both new tables append-only by trigger and by grant | HELD | `0006_stop_state.sql:17-24`; `migrate.py:60-61`; owner case tested at `test_p7_store.py:227-233` |
| 9 | Runtime never resolves the reset DSN | HELD | `table.py:121-124`; `platform_secrets.py:18-33`; no test (U3 missing) |
| 10 | Unreadable stop state means no model call | HELD | `agent_loop.py:250-254` (called at 407 and 469, before `llm.chat` at 473), `718-721`, `788-791` |
| 11 | Python signatures unchanged; memory store unchanged | HELD | `memory.py:218-224` identical to baseline; `limits.py:43`, `48`; `protocol.py:112-120` docstrings only |
| 12 | Flag ON at upgrade stays ON | HELD | `postgres.py:451-452`; `test_p7_store.py:210-217` (flag set after migrating, not the 0005-to-0006 sequence) |
| 13 | Stated limits in SECURITY and CHANGELOG | NOT IMPLEMENTED YET | No reset-role text in README, SECURITY or CHANGELOG |

## Findings

### Major

**A-1. An outbox row that cannot be appended for a non-connectivity reason is kept silently and the step reports ok.**
- Where: `chain.py:286-293` (`_drain` swallows every exception) and `278-280`.
- Why: if the runtime role lacks INSERT on `audit_entries`, or a row is rejected by the database, the tick logs `drained=0`, exits 0, and the outbox grows forever. This is the same "missing grant looks like nothing to do" case that invariant 5 closed for the read. `test_audit_drain.py:238-248` pins exit 0 only for an `OSError`.
- Fix: let `_drain` report the exception; in `reconcile`, count rows that failed for a reason where `is_connectivity_error` is false and raise `RuntimeError` with the count after the loop, as for unreadable rows. Add a test that revokes INSERT on `audit_entries` and expects the step FAILED.

**B-1. Most of ticket B's tests and docs are not in the tree.**
- Missing files: `tests/test_stop_state_roles.py`, `tests/test_stop_state_unit.py`, `tests/stop_state_mutants.py`, `docs/stop-state-runbook.md`, and the README, SECURITY and CHANGELOG text for B.
- Consequence: every reset test in `test_p7_store.py:185-233` runs on the schema owner's DSN (`pg_schema()` default). Nothing yet proves, with a real non-owner login:
  - the runtime login is refused a reset;
  - the reset login can insert a clear through the foreign key;
  - the pilot and prod refusal at `cli.py:196-204`;
  - the `reset_failed` outcome;
  - any `migrate --reset-role` refusal;
  - the two-resets and uncommitted-stop cases.
- Fix: write them as the ticket lists, by an agent other than the builder.

**B-2. `limits reset` prints "kill switch OFF" without reading the state back.**
- Where: `cli.py:459`.
- Why: it is false when a stop was committed during the reset (invariant 4) and when the flag row is missing (the UPDATE at `postgres.py:474-477` touches 0 rows and succeeds; `test_p7_store.py:220-224` confirms it still reads ON). The operator is told OFF, exit 0, while runs stay stopped.
- Fix: after `limits.reset`, call `get_kill_switch()` and print the real state; exit non-zero or warn when it is still ON.

### Minor

**A-2. One permanently unwritable event at the head of `_pending` blocks all later ones for the life of the process.**
- Where: `chain.py:247-249`.
- Why: stop-at-first-failure is per the ticket, but it cannot tell "database down" from "this event can never be written"; each later write also pays one failed transaction.
- Fix: on a non-connectivity failure, move that event aside and count it, then continue.

**A-3. The flush runs inline in the caller's `write_intent` or `write_outcome`.**
- Where: `chain.py:217-218`, `237-238`.
- Why: after a long outage, one action's intent write pays for every parked event (`test_h3` shows 200). No cap.
- Fix: cap the number flushed per write; reconcile takes the rest.

**A-4. A DELETE failure inside `reconcile` aborts the loop and loses the unreadable count.**
- Where: `chain.py:279`.
- Why: the step does fail, so this is only a diagnosability loss.
- Fix: none needed unless A-1 is restructured anyway.

**B-3. The reset role's table-wide UPDATE on `kill_switch` lets it also set the flag ON, or change `id` so the row reads as missing.**
- Where: `migrate.py:59`.
- Why: it matches the ticket's grant list and both effects are in the safe direction, but it contradicts the ticket's answer "may the reset login also stop: no".
- Fix: a column-level grant UPDATE ("on", "by", ts), or accept and say so in the docs.

**B-4. `reset_credential_ref` equal to `dsn_secret_name` is not refused.**
- Where: `cli.py:195-214`.
- Why: in pilot or prod the reset then runs on the runtime login; the database refuses it only if the grants were applied.
- Fix: refuse with exit 2 when the two names are equal.

**B-5. Membership between roles is checked only among the roles named in the same `migrate` call.**
- Where: `migrate.py:348-354`.
- Why: with `migrate --runtime-role R` alone, a runtime role that is a NOINHERIT member of the reset role passes (`has_table_privilege` is false, yet it can SET ROLE).
- Fix: document "name all roles in one command" (the CHANGELOG step is missing), or have `effective_problems` check membership in any role that holds UPDATE on `kill_switch` or INSERT on `kill_switch_clears`.

**B-6. A plain `migrate` with no `--runtime-role` leaves the old runtime grants on `kill_switch` and none on the new tables.**
- Where: `cli.py:378-388` prints a warning only.
- Why: until the second run, `limits stop` on the runtime login fails with exit 2 and the runtime keeps UPDATE on the flag. The runtime read does fail closed.
- Fix: put this in the upgrade steps; consider refusing when 0006 is applied in a run that names no runtime role.

**B-7. Refusal text on the stop tables says "the audit log is append-only".**
- Where: reuse of `hadavin_audit_append_only()` at `0006_stop_state.sql:17-24`.
- Why: a ticket choice, but misleading to an operator.
- Fix: say so in the runbook.

**B-8. `test_stop_state_loop.py` does not assert that no model call happened.**
- Where: `tests\test_stop_state_loop.py:35-39` asserts state and `creates == 0` only.
- Why: invariant 10 is "no model call".
- Fix: add an assertion on the fake LLM's call list.

## The specific things you asked me to look for

- **Runtime role turning the stop off:** none found through the grants or the code.
- **Reset not audited first:** none; `limits.py:51` precedes line 53.
- **Grants wider than the ticket:** none; the map matches exactly (B-3 is about what table-wide UPDATE implies).
- **Unreadable outbox row that blocks or is deleted:** none.
- **Flush that raises into the caller or loops on a down database:** none; it breaks on the first failure and catches everything.
- **SQL built from input:** safe. Role names pass the `_ROLE` regex and `_FORBIDDEN_ROLES` (`migrate.py:313-315`) and are always wrapped in `sql.Identifier` (`179-195`); privilege strings come only from the constant map; values are parameters.
- **Migration against the grant guard:** passes by reading. Both CREATE TABLE and all four `CREATE OR REPLACE TRIGGER` statements match `_SAFE_CREATE`; there is no SERIAL, IDENTITY or sequence; both tables are in `GRANTS` as tables. `tests/test_k5_fixes2.py:260-280` is updated for the new file.
- **Tests that cannot fail:** none found.
  - Postgres tests skip only when `HADAVIN_TEST_PG_DSN` is unset (`store_postgres.py:22-24`).
  - `test_e7` expects `InsufficientPrivilege` by name, so a missing relation would not pass.
  - The owner trigger test has rows present, so the row triggers fire.
- **Project-specific words in core types:** none new.
- **Hard-coded values that belong in config:** none new.

## Not checked

- Nothing was executed: no tests, no ruff, no mutants.
- The sha256 of `0006_stop_state` in `tests/fixtures/migrations_released.json:7` against the current file. The file changed from BIGSERIAL to UUID after the builder's report, so recompute it. The manifest row is also already written, although the ticket says "written at merge".
- That PostgreSQL's foreign-key check lets the reset role insert a clear.
- That `gen_random_uuid()` passes the lexer in `tests/test_migration_numbers.py`.
- `tests/test_p7_tick.py`, `tests/test_s5_runtime.py` and `tests/demo_askdata/test_pipeline.py` changes beyond grep hits.
- `tests/test_k2_migrations.py`, `tests/test_cuj.py` pinned substrings, `audit/local_dir.py`, and `app.py` beyond grep.
- README content.
- A line-by-line diff against `sdk-main` for any file other than `store/memory.py`.
