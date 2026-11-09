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
