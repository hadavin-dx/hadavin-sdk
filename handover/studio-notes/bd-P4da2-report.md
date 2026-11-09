# bd-P4da2 report, PASS 3 (new head 6cdf67a; pass 2 head 39ff5ef follows below)

NOT DONE / UNCERTAIN (first):
- Only the affected tests were run, not the full suite (ordered): 865 passed, 1 skipped (tests/contracts/, test_p4d_missing_methods, test_lockin_guard, test_p2_postgres, test_k5_fixes2, test_k2_migrations) on PostgreSQL 16 only (not 17). Log: /home/user/build/B-P4da2-out/affected.log. CI, CodeQL, SonarCloud, CodeRabbit not run. 39ff5ef was not sent for evidence or review (order 3).
- src is unchanged in pass 3; every new test passes on the existing src, so there is NO "fails on old code" for them; each one has a planted mutant that makes it fail (below). Mutants were applied by text edit, tests run with -x, file restored with `git checkout --` (git status clean after every run).
- NOT run: the other b/w/i mutants. Run this pass: 10 + 13 + 3 (the list below). Not run: b1, b4 (the Python-side form is N2), b5, b7, b9, b11, b11b, b14 (per-edge matrix, 8+11+4 mutants), b17, b18c (run last pass), b19, b21, b23, b24, b26a-f split forms (only the combined ceiling form b26 was run), b28/b28b/b28c, b30, w1-w13, i1-i9. b29 moot (as pass 2). Reason: each needs its own planted edit; I ran the ones whose test I built or touched.
- Plan of the ticket not built: the T4 number difference (5000 vs 2000) of the older test; B8(c) (evidence runner's step). The sweep-on-Postgres model test does not exist (by the ticket's N8: Postgres runs without sweep ops; the sweep is proved by B7 rows).
- The 200x30 model test took 19 s for both stores on Postgres 16 (CI limit in N8 is 180 s).
- Survivor found and fixed in this pass: b10 (month key from today) and b16 ordering mutants first SURVIVED the pass-2 tests; I added tests (far-month rows via the owner fixture; sweep order and tie rows with the planner's index scan switched off) and re-ran them: all killed. b16-no-order only dies with the index scan off (the partial index returns index order otherwise); that is a property of the test environment, stated here.
- bandit: `uvx bandit -q -r src demos tools -ll` rc 0 (warnings only: nosec comments in src/hadavin_sdk/tools.py:389, pre-existing). Tests are not scanned by the gate.

LEAD ORDER 182 (1): ACCEPTED. PR 75 retitled "P4d-a2-i and P4d-b ... with P4d-a2-ii ..." and body rewritten with scope, the builder note and the standard footer (GitHub update_pull_request, returned id 5188269901). The CHANGELOG entry was already titled "P4d-a2-i and P4d-b" (CHANGELOG.md line 6), so no file change. The 12-line builder stays only with the new test `test_the_local_schema_builder_gives_the_same_catalog_as_the_real_migration` (tests/contracts/test_store_reserve_schema_pg.py): it builds a schema from all six migration files with `_apply` and one with the real `migrate()`, snapshots columns, constraints, indexes, triggers and function bodies (schema name masked; `schema_migrations` excluded as bookkeeping written by migrate itself) and asserts equal; `test_the_catalog_comparison_notices_a_missing_migration_file` shows a builder with the newest file left out differs.
REMOVAL NOTE (not a TODO in code beyond the marked comment block): when P3a merges, `_apply`, `ALL_STEMS`, `_catalog` and the two equality tests in test_store_reserve_schema_pg.py are replaced by `tests/migration_schemas.py` in the same rebase of PR 75; the equality test is then replaced by whatever P3a ships for its own helper. The marker "REMOVAL NOTE" in that file names this.

BUILT THIS PASS (tests only; new file tests/contracts/pg_owner.py):
- B4 (ii) at 50 repeats: `test_b4_ii_eight_stores_reserving_the_same_id_book_it_once_fifty_times_without_a_retry` (8 stores, 50 ids, applied == 7 False + 1 True each time, zero retries, totals 50, run cost 50, 50 open rows).
- set_kill_switch from a second handle while a reserve waits at the day counter (HEAD_DAY lock wait seen in pg_stat_activity): `test_set_kill_switch_from_a_second_handle_completes_while_a_reserve_waits_at_a_counter`; afterwards the held reserve completes and the next reserve is KillSwitchOn.
- T1/T2/T3 for reserve_spend: `test_t1_t2_a_counter_row_that_is_never_released_gives_store_busy_within_the_limit` (lock_timeout 100 / budget 500; StoreBusy, elapsed in [0.09 or 0.45, 5) s, nothing booked) and `test_t3_reserve_sets_both_timeouts_from_the_settings_and_the_remaining_budget` (reads current_setting for lock_timeout and statement_timeout at the first statement of reserve_spend). The existing StoreBusy row is kept.
- Deterministic fill-the-cap: reserve (admin holds the day row; admin commits a booking that fills the cap; the waiting reserve raises SpendCapExceeded("day") with cap 3, current 3, requested 1, nothing booked, no row) and the same for settle on the reservation row (admin settles it first; the waiting settle returns the first result, applied False, counters unchanged).
- Owner fixture: `pg_owner.trigger_off/insert_aged/age/trigger_states`. Uses `ALTER TABLE spend_reservations DISABLE/ENABLE TRIGGER` inside one owner transaction (allowlist of the two trigger names; an error rolls the DISABLE back). Replaces `SET session_replication_role = replica` in the database-clock row c1 (now INSERTs an aged row, counters bumped) and in `_age` of test_store_reserve.py. Tests: both triggers enabled before and after, rollback on error, unknown name refused, and the negative test that the runtime login gets 42501 on the ALTER.
- New rows from survivors: settle/release lower the reservation's own day and month for 2020-12-31, 2021-01-01, 2024-02-29, 2023-12-31; sweep takes the oldest first and breaks ties by id (limit 2, three batches, then empty list; index scan off).
- b12 memory: `test_b12_memory_the_lock_covers_the_cap_check_and_the_write` (checkpoint hook holds thread 1 between cap check and write; thread 2 must be refused). This row did not exist in pass 2.
- B5 model test: `test_b5_model_reserve_settle_release_and_sweep_match_a_plain_python_ledger` (both stores; 200 seeds x 30 steps; own agent and run per seed; ops reserve with random caps (run/day/month, order run, day, month), replay same content (open: applied False; closed: StaleState), replay other content (ReservationConflict), settle (below and above reserved), release, memory only sweep with aged rows; after every step the day and month totals for three days, run cost, every row (status, settled, reserved) and the open list equal the model; counts assert the branches were reached: memory/postgres granted > 800, refused > 300, settled > 300, released > 100, closed replays > 50, expired > 100 on memory). Finding on the way: my first draft passed a run cap with no run (ValueError "run_cap needs a run_id"); fixed in the test.

MUTANTS this pass (raw: /home/user/build/B-P4da2-out/mutants-pass3.log, mutants-pass3b.log, mutants-pass3c.log; runner mut.py in the session scratchpad):
| mutant | result | killer (first failure) |
| N1 reserve's kill-switch read takes FOR UPDATE (b17-like) | KILLED | set_kill_switch row ("held up by the waiting reserve") |
| N2 b4 day cap moved to a Python read before the write | KILLED | fill-the-cap reserve (the reserve was granted) |
| N3 b6 settle claim without the status condition | KILLED | fill-the-cap settle (trigger refusal "change refused") |
| N4 b18a lock timeout not capped at the setting | KILLED | T1 (stuck 20 s join) |
| N5 b18b budget ignored | KILLED | T2 |
| N5a lock timeout ignores the remaining budget | KILLED | T3 |
| N6 same-id read-then-insert, no ON CONFLICT | KILLED | 50-repeat same-id row (not checked whether the old single 8-thread row also dies) |
| M-pg1 closed same-content replay not StaleState | KILLED | model test [postgres] |
| M-mem1 sweep leaves settled_usd empty | KILLED | model test [memory] |
| M-mem2 an expired row cannot be closed | KILLED | model test [memory] |
| b12 memory lock removed | KILLED | b12 row ("assert ['ok','ok'] == ['cap','ok']") |
| b2 day cap ignored; b3 `<=` to `<` | KILLED (each) | test_a_cap_is_exact_at_the_boundary... |
| b8 settle applies actual, not actual minus reserved | KILLED | test_settle_below_equal_above_and_the_replays |
| b10 month key from today | SURVIVED the 170 older rows; KILLED after the far-month rows (CounterDamaged) | far-month row [year-end] |
| b13 kill switch not checked | KILLED | test_the_kill_switch_refuses... |
| b20 list ignores the run filter | KILLED | test_list_open_orders_by_creation_and_filters |
| b22 day bound dropped; b25 run agent not compared; b27 closed row other content is Stale; b26 (combined ceiling) removed | KILLED (each) | the B1/B2 rows |
| b16 sweep floor removed | KILLED | sweep row |
| b16 sweep order changed (created_at DESC) and tie-break by id DESC | SURVIVED the older rows; KILLED after the new order row | sweep-order row |
| b16 sweep with no ORDER BY | SURVIVED until the index scan was switched off in the row; then KILLED | sweep-order row |
| planted fault in the owner fixture (ENABLE line removed) | KILLED | owner-fixture row (insert trigger left 'D') |

GATES (exact commands in /home/user/build/B-P4da2-out): `uv run --all-extras --group test ruff check` rc 0 "All checks passed!"; `ruff format --check` rc 0 "329 files already formatted"; `uvx bandit -q -r src demos tools -ll` rc 0; pytest affected (above) rc 0, `865 passed, 1 skipped in 196.00s`. No noqa and no type-ignore added. PostgreSQL 16 cluster bpa2c (port 56181) started with pgstart.sh and stopped at the end.
R-numbers: studio bible not on this machine, none read (same as pass 1 and 2).
Commit 6cdf67a783a3771692d2d6f1828dd4e46a6e84f7 pushed to origin core/P4d-a2 (normal push, base 39ff5ef).

---- PASS 2 REPORT (head 39ff5ef) ----
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
