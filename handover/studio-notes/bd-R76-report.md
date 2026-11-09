# bd-R76 builder report: PR76 core/P2a-1 (kill switch stop state)

## NOT done or uncertain (first)
- NOT done: tests/stop_state_mutants.py (mutation plan file) was not written. The ticket's mutant rows are unbuilt, so no mutation run exists for this package.
- NOT done: ACCEPTED_CHANGES entry for the rollback (P3a's dictionary not checked at this base); only a rollback test exists.
- NOT done: `effective_problems` owner-role membership check for the NOINHERIT case.
- NOT done: tests/contracts kind `stop_state` rows; smaller codebase nits not all addressed.
- NOT done: non-superuser `pg_schema_migrator` world for the DB tests (design M2 second half). DB tests now use `require_backend` (fail in CI, skip on a laptop), but the migration still runs as the test superuser, so the pilot probe "superuser-owned function" finding is only exercised through `dev_tolerated`.
- NOT RUN: PostgreSQL 17 (only PG16 locally; the CI matrix runs 16.15 and 17.10 but I have not seen it green). MAINTAIN-privilege test skips on 16.
- Interpretation: B8 (bounded advisory wait before the lock) and B10 (0007 `by` rewrite) were read as authorising the current behaviour; the lead should confirm.
- Partial slice: B1 asked for the whole ticket. This is not the whole ticket (items above).

## Findings -> class -> fix -> fail-before -> pass-after
| finding | class | fix | fail-before | pass-after |
|---|---|---|---|---|
| B2 demo aliased to dev | silent stage alias | Limits accepts only dev/pilot/prod | tests/test_stop_state_limits.py (old code accepted "demo") | passes |
| B3 no PG16+17 matrix | CI coverage | matrix in ci.yml, names check/security unchanged | n/a (CI file) | not seen green |
| M1 stale pair | reset named by version only | pair (version, open) checked under FOR UPDATE | test in test_stop_state_db.py (hand mutant surviving, killed) | passes |
| M2 skipif / superuser | tests skip silently | require_backend | partial, see above | passes on PG16 |
| M3 unbounded stop, no busy mapping | missing timeout class | short_connect with timeouts, StoreBusy -> exit 7, one retry | CLI/probe tests | passes |
| M4 lock_timeout order / re-assert (codebase M1) | per-file setting leak | set after lock and after each file | lock-timeout-per-file test (fails when the re-assert is removed) | passes |
| M5 0007 rewrites by | B10 | accepted per B10 | old_by test | passes |
| codebase M4 pilot stop traceback | missing key handling | cli.py label_key=b"" off dev | test_stop_on_pilot_without_a_label_key_name_works_not_a_traceback fails on old cli.py with "a label key is required when environment is not dev" | passes |
| codebase M3 runbook, `limits check` | missing deliverable | docs/stop-state-runbook.md, `limits check` exit 0/10/7 | test_limits_check_exit_0_10_7_and_2, runbook-exists test | passes |
| codebase M5 CHANGELOG | docs | upgrade entry incl. "no running program refuses an action because of P2a" | n/a | n/a |
| loop guards (ticket 105) | unguarded limits read | guards at _limits_stop and _recheck | tests/test_stop_state_loop.py fails with RuntimeError on the P4d-a2 agent_loop.py | passes |
| group check substring / nonexistent role | catalog read raising | group_exists guard | test_the_group_check_is_exact_not_a_substring (UndefinedObject) | passes |
| rollback | old release | test_old_release_fails_loudly_on_a_guarded_database | n/a (no old-code run) | passes |

## Evidence
See the full-suite log named in the hand-back message. Local gates: ruff check, ruff format --check clean; bandit not installed in the local uv env (not run locally; CI runs it).
