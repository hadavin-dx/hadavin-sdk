# bd-R76 builder report: PR76 core/P2a-1 (kill switch stop state)

## Second pass (head 7f32349) - NOT done or uncertain (first)
- Full suite at the final head: see the pytest summary line in the hand-back message (log /tmp/r76-final.log, junit /tmp/r76-final.xml).
- NOT RUN: PostgreSQL 17 (local PG16 only; CI matrix 16.15 + 17.10 not seen green). The MAINTAIN-on-17 test skips on 16.
- NOT done: ACCEPTED_CHANGES entry. No such dictionary exists at this base (grep of the repo finds none; P3a's has not merged). The CHANGELOG upgrade entry and the rollback test stand in for it.
- NOT done: the DB and loop mutants (migrate lock bound, version compare, open-count compare, group substring, loop recheck guard) cannot run in tools/mutation_runner.py: it gives a mutant run no DSN and no conftest by design. They are listed as HAND in tests/stop_state_mutants.py and were run by hand: 5 of 5 killed (the group-substring one first SURVIVED, the test was weak; fixed with a real prefix role, then killed). The runner file M has 4 mutants, 4 of 4 good.
- ASSUMPTION A1 (B8): a bounded advisory wait before the lock is correct. ASSUMPTION A2 (B10): the 0007 `by` rewrite is authorised. Both proceed as read; lead to confirm.
- bandit -ll (uvx, same command as CI on src demos tools): 0 issues.

## Fixed in the second pass
- Fallout of the new app.py rule: test_k3_pilot_env (pilot_cfg now names runtime_role), test_k5_round8_postgres, test_k5_round5 failed before; pass after. Cause: pilot tests had no limits.runtime_role.
- Non-superuser migrator world (design M2): tests/contracts/kinds/store_postgres.py pg_schema(runtime=True) now migrates as a CREATEROLE non-superuser that owns the schema; connect_admin is that owner; new connect_superuser only for the one test that switches triggers off. The pilot start-up probe now passes for real roles in test_k3_pilot_app_has_no_executor and the round-8 test (they use runtime=True and name the real roles).
- effective_problems: a NOINHERIT member of a relation owner role is refused ("is a member of"); test fails with DID NOT RAISE on the old migrate.py.
- Contract row: guard_report on both backends. Probe substring test strengthened (killed mutant above).

## First pass (head d1855a9) - kept for the record
- NOT RUN: the full suite at the final head d1855a9. The machine was overloaded: one full run reached 19% in 15 min with one failure (F at about 13%, test not identified, log /tmp/r76-full.log) and was stopped; a second, narrower run (60 files that mention pilot/postgres/limits/cli/tick, plus tests/contracts) never got a slot and was stopped. The existing pilot/postgres app tests are therefore NOT confirmed against the new app.py requirement (limits.runtime_role / reset_group and the start-up probe). Treat that as a likely failure area.
- Run locally and green: tests/test_stop_state_{db,probe,cli,loop,rollback,limits,memory,config}.py on PG16 (59 passed, 1 skipped before the rollback test was added), ruff check, ruff format --check.
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
