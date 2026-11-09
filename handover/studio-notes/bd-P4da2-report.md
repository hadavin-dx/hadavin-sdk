# bd-P4da2 report, PASS 2 (head 39ff5ef; pass 1 head ff1a8c8 follows below)

NOT DONE / UNCERTAIN (first):
- The full suite was NOT run at this head (ordered). Run on PostgreSQL 16 only, not 17: 459 affected tests passed (proofs, schema, memory lone caller, missing_methods, reserve, reserve_pg, writes_pg, cost_rounding, p2_postgres, k5_fixes2, lockin_guard, store_registry). CI, CodeQL, Sonar, CodeRabbit not run.
- B8(c) (old code on the new schema, ce70eb5 contract rows against a database with the new table) is the evidence runner's step by the ticket; I did not run it. The migration-refusal message test of test_k2_migrations stays as it was.
- B8 (a) and (b) are built, but with a 12-line local builder because tests/migration_schemas.py does not exist on any branch: P3a (ticket P3a.md, item (1)) creates it and has not merged. Move the builder there when P3a lands.
- Not built: B4(ii) same-id race at 50 repeats (one 8-thread run exists), the "set_kill_switch from a second handle completes meanwhile" row, T1-T3 rows for reserve_spend with a never-released lock beyond the one existing StoreBusy row, B4 deterministic variants (admin FOR UPDATE on the day row then a booking that fills the cap, expecting SpendCapExceeded), B7 owner fixture that disables the INSERT trigger (I age rows with session_replication_role=replica, like the existing `_age`), the 5000 vs 2000 T4 number difference in the older test. B5 model-based property test with reservation methods not built.
- Not killed or not run mutants: b29 is moot (MemoryStore already uses a plain Lock and a lone caller finishes; the rows guard against a future re-entrant helper). The full b/w/i tables were NOT run: 20 mutants were run (list below). b14 (per-edge matrix mutants), b1-b10, b12, b13, b19-b27, w1-w13 not re-run this pass.
- X3 (a reserve-order mutant on the vii-c row) survives by design: vii-c tests settle, not reserve. The settle-order mutant kills vii-c (checked by hand, no log file; see below).
- bandit: CI covers `src demos tools` only; ran on src, rc 0 (warnings only). Not run on tests (the gate does not cover them).
- B-1 is a LEAD DECISION (below). I built b-ticket rows under the a2 label because the lead ordered it.

LEAD QUESTION (B-1, exact): PR 75 is labelled P4d-a2 but carries the P4d-b money SQL (migration 0006, reserve/settle/release/sweep in postgres.py and memory.py, six Protocol methods, GRANTS). Ticket P4d N1 says b starts only after P3a merges. P3a has not merged and tests/migration_schemas.py exists on no branch. Do you (1) accept b inside this PR now, retitle the PR and CHANGELOG "P4d-a2-i and P4d-b", and treat the B8 rows as built on a local helper until P3a lands; or (2) split the PR so a2 carries only the wrapper, timeouts and rounding, and b moves to its own PR after P3a? I changed no scope.

BUILT THIS PASS (tests; src unchanged except none): tests/contracts/test_store_reserve_proofs_pg.py (vii-a, vii-b, vii-c with pg_stat_activity head match for the runtime role and wait_event assertion; exact floor(cap/amount) count of 12 handles; settle race x50 and deadlock stress x50 with `on_retry` collecting zero retries and pg_stat_database deadlocks unchanged; N6 T4 with budget 5000, run row released at 2.5 s, day row at 6.0 s, StoreBusy and nothing booked; 8-process spawn race with exact count 10; SIGKILL while blocked then backend-gone poll; SIGKILL after commit then replay, list, release; database-clock rows c1 and c2 under clocks +/-10 years), tests/contracts/reserve_workers.py (spawn workers, no driver import), test_store_reserve.py (B3 e1/e2: 5 values x open/expired; e3 per counter with lowering still working; r1-r4 release guard for run/day/month/missing month row x open/expired; B5 10,000 pairs on both stores), test_store_reserve_schema_pg.py (B8 a, b), test_memory_lone_caller.py (B4b c), tests/test_p4d_missing_methods.py (B8 d).
Finding on the way: settle and release send quoted identifiers (`UPDATE "runs" SET`), reserve does not, so the ticket's literal head `UPDATE runs SET` would never match a settle; the proofs match `UPDATE "?runs"? SET` and `UPDATE "?spend"? SET` (the optional quote and the space keep `spend_month` out).
Finding on the way: the 8-process test as first written got 14 grants not 10 because a worker settled (freeing room) before the others had finished attempting; the workers now wait at a second barrier before settling. That was a test bug, not a store bug.
Finding on the way: T4's elapsed time ends near 6.0 s (the day row's release), not at 5.0 s: statement_timeout is set once to the whole budget, and the budget is enforced by the deadline check before each statement. The row asserts 5.5 to 7.4 s plus nothing booked; the deadline-check mutant dies on it.

MUTANT RUNS this pass (raw: /home/user/build/B-P4da2-out/mutants-pass2.log, plus the X-runs printed in my session; each applied to a copy, restored by writing the original text back; `git status` clean afterwards):
| mutant | result | killer |
| b15 lock order inverted (run last) | KILLED | vii-a, vii-b (each alone), and the earlier probe row |
| b15 on settle/release order inverted | KILLED | vii-c |
| b18c / w14 deadline check removed | KILLED | T4 (N6 numbers) |
| b11c release guard dropped | KILLED | r1-r4 (postgres-run-open first) |
| b11d damaged counter on close not an error | KILLED | damaged-counter row |
| b28b ceiling applied to a settle excess | KILLED | e3 (postgres-run) |
| b16 sweep age with the Python clock (well formed) | KILLED | database-clock c1 (clock-ahead) |
| b22 day bound from the Python clock | KILLED | database-clock c2 |
| M5 purge as one huge batch | KILLED | test_M5_the_statements_are_batches_of_the_configured_size |
| i10a/b/c/d no rounding, ROUND_DOWN, HALF_UP, HALF_EVEN | KILLED (each) | test_reply_rounds_the_cost_up[a1] first; |
| M3 i10a, i10b on the agent-loop rows only | KILLED (each) | test_d_the_loop_books_the_producer_rounded_cost |
First b16 try died on a malformed statement (parameter count), so it proved nothing; the well-formed rerun is the one counted.

FAIL-BEFORE this pass:
- M5: with the purge as one huge batch the batch-size row fails (above). M3: with no producer rounding the agent-loop row fails (above); the old hand-booking test did not.
- M6: adding a file `0007_probe.sql` to the migrations folder makes the pinned assertion fail (`test_audit_checkpoints_migration_adds_alg_and_label_and_old_rows_get_defaults`: 1 failed, 4 passed); a list built from the folder would have passed. File removed afterwards.
- B8(d): the same test on ce70eb5: `assert [] == ['get_spend_reservation', ...]` (1 failed, 1 passed); on this head 2 passed.

Processes: pg cluster bpa2 (port 56175) restarted by me and stopped at the end; ce70eb5 worktree removed.

---- PASS 1 REPORT (head ff1a8c8) ----
# bd-P4da2 report (builder, PR75 round-1 fixes), head ff1a8c8

NOT DONE / UNCERTAIN (first):
- B-2 is only partly closed. Built: lock-order probes (NO KEY UPDATE, NOWAIT, pg_stat_activity), SELECT-only-role reserve test, ceiling rows, same-id/settle/8-thread races with deadlock count, transition-matrix rows. NOT built: 8-process spawn, SIGKILL, 50-repeat race, lock_timeout 60000 exact count, T4 numbers from BN N6, B7 db-clock rows c1/c2, B5 10,000 pairs, B8 behind-schema rows (tests/migration_schemas.py is absent, belongs to P3a), B4b(c) memory lone-caller rows, B3 e1-e3/r1-r4 release-guard rows, b15 raw vii-a/b/c rows beyond the probes. Each needs lead agreement on scope or a follow-up.
- B-1 scope question (b money SQL under an a2 label) is a lead decision; I did not change scope.
- Ran on PostgreSQL 16 only; CI uses 17. Not run on 17.
- M5 fail-before is only an AttributeError (old code had no batch function), so it proves absence, not behaviour.
- M4 and M2 tests read worktree source (AST); they pin structure, not runtime.
- One expired-to-open matrix mutant is equivalent and not killed.
- The S603 noqa in tests/contracts/test_store_registry.py was kept: ruff requires it and it is not a review finding.
- Only the mutants in mutants-proofs.log were run (L1 reverse lock order, K1/K2 kill-switch lock modes, C1/C2 ceiling); not the full i/w/b mutant tables. ce70eb5 fail-before and P4d-venv-probe.md not done.
- bandit via uvx: rc 0 on src (warnings only); tests not scanned.

FULL SUITE (PG16, HADAVIN_REQUIRE_PG=1, -rfEs): `10665 passed, 1 skipped in 470.38s (0:07:50)`, exit=0. Log: /home/user/build/logs-bpa2/full.log. Skip: tests/contracts/test_llm.py:95 (Stubber, unrelated).
Lint: ruff check src tests clean; ruff format --check clean (286 files).

| finding | class | fix | fail-before | pass-after |
|---|---|---|---|---|
| M1 no timeout validation | constructor accepts out-of-range config | _checked_ms in PostgresStore.__init__ | failbefore-round1-a.log: 18 M1 rows failed | full suite pass |
| M2 kill switch two readers | duplicated read | reserve_spend uses get_kill_switch | same log: M2 failed; mutants K1/K2 killed | pass |
| M5 purge hits 5 s budget | unbatched DELETE | _purge_in_batches | same log: 4 M5 failed (23 failed, 8 passed total) | pass |
| M4 back-off | tenacity multiplier valid in 9.2.1 (review suspicion false) | pin test added | n/a | pass |
| M3 agent-loop rounding | hand-booking replaced by loop rows d, d2, v3, v4 | test_cost_rounding.py | not run against old producer | pass |
| M6 weakened test | migrate() assertion pinned to explicit list | test_p2_postgres.py, test_k5_fixes2.py | not shown | pass |
| B-2 lock order | no probe | test_store_reserve_proofs_pg.py | mutants-proofs.log: L1 3 failed | pass |
| ceiling | boundary | test_store_reserve.py | C1 3 failed, C2 4 failed | pass |
| nits | suppressions TRY004, type-ignore, S608, DTZ001, S106; uv.lock churn | removed / restored | n/a | ruff clean |

NOT RUN: PG17, B-2 items above, full mutant tables, CI/CodeQL/Sonar/CodeRabbit.
Citations: no R-numbers read this session (studio bible not on this machine).
