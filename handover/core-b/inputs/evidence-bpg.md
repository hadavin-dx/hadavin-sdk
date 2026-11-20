# evidence-bpg: core-b money/audit/stop-state tests and mutants on real PostgreSQL (raw runner, no judgement)
sha: 7e1b9750d0986808aa6cd398e031f6a5e54fa108 (origin/cloud/core-b, worktree lead-bpg). WSL Ubuntu copy without .git; Python 3.13.12, uv sync OK (EXIT=0). Raw logs in raw/.
Containers hvbpg15 (postgres:15) and hvbpg17 (postgres:17), 127.0.0.1 random ports, POSTGRES_HOST_AUTH_METHOD=trust (as in .github/workflows/ci.yml); removed after (docker ps -a --filter name=hvbpg: empty). WSL copies removed.
## Setup deviations (mine)
1. First containers used password auth: run 1 below has 376 errors / many failures from "password authentication failed for user sb_*" (test throwaway roles carry no password). Rebuilt with trust.
2. A DSN quoting bug in my first rerun script: raw/02-INVALID-dsn-quoting-bug-pg17.log and raw/03-INVALID-dsn-quoting-bug-pg15.log are INVALID, ignore.
3. A throwaway `git init` + commit inside the WSL copy (never pushed): needed by `--hand` mutant scripts (git status) and by tests that call `git ls-files`.
4. psql is not installed in WSL (no sudo): 387 skips in run 1 (tests/demo_askdata only: test_validate_harm 252, test_corpus_on_server 66, test_roles 23, test_pgsource_layers 22, test_verify_readonly 15, test_cli 9), none in the money/audit/stop modules.
5. Time limit 90 min exceeded (about 3 h): full-suite run takes 46 min on 3 workers; other agents also ran in this WSL.
## Run 1: PG17 whole suite, -n 3 (raw/01-pg17-full.log, EXIT=1). INVALID for role tests (password auth, deviation 1)
437 failed, 12168 passed, 398 skipped, 4 xfailed, 376 errors in 2749.58s. Skips: 387 psql, 4+2+1+1 below-PG16, 1 Stubber, 1 "None is the way to say no run", 1 "gate not in this tree".
Not re-run in full after trust fix; instead the 45 files that failed/errored in run 1 were re-run (run 2).
## Run 2: PG17 trust, the 45 files of run 1 (raw/failfiles.txt), -n 3 (raw/02-pg17-rerun-trust-45files.log, EXIT=1)
32 failed, 1839 passed, 10 skipped, 4 xfailed, 6 errors in 1378s. First error lines: raw/02-first-error-lines.txt; ids: raw/02-pg17-failed-ids.txt.
## Run 3: PG15, same 45 files, -n 2 (raw/03-pg15-45files.log, EXIT=1)
31 failed, 1844 passed, 6 skipped, 4 xfailed, 4 errors in 1633s. Failed ids: raw/03-pg15-failed-ids.txt. Same ids as PG17 except test_store_spend_model[postgres-seed137] fails on PG17 only. Skips PG15: 2 "None is the way to say no run", 1 MAINTAIN needs PG17, 3 below-PG16.
## Problem list (PG17 run 2; PG15 same unless said)
- ERROR at collection, tests/test_money_definer_pg.py:52 and tests/test_money_definer_mutants.py: `RESERVE, SETTLE, EXPIRE, PURGE, ADD = mig.MONEY_FUNCTIONS` -> ValueError: too many values to unpack (expected 5). The whole money definer battery and its mutants do not run at this head (also in run 1, on PG15 too).
- tests/test_audit_drain.py (7 fail): n1 (tick steps list is expire_reservations...check_caps, expected audit_drain...), e6 `[1,1]==[0,0]`, e7 `1==0`, cross_process x2, f6_pg x2.
- tests/test_spend_reservations_pg.py (6): step order after audit_drain, longer-age step `'open'=='expired'`, failing store `0==1`, runtime-login expiry mismatch.
- tests/test_stop_state_roles.py (11): migrate refusal regex not matching (reset role member of owner, S2 member of reset role, portal/purge role, public grant), e7 flag-before-0006 ConfigError "GRANTS names hadavin_caps, which no migration creates; hadavin_limits ...", cli accepted-admin-roles message.
- tests/contracts/test_store_spend_ids_caps.py (3): out-of-window cap 1E+999999 day/month, exponent outside window for zero amount. PG17 only: test_store_spend_model[postgres-seed137].
- tests/test_limits_reserve.py::test_the_refusal_log_line_names_the_error_class_and_not_its_message; test_money_definer_review_fixes::test_m2_the_header_states_the_expire_then_release_residual; test_migrations_0009_0010_round2::test_upgrade_from_0008_with_a_planted_ts...
- tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked: handover/BRIEF-PREAMBLE.md: 'Port.io' (content finding, not PG).
## Run 4: mutation scripts against PG17 (raw/04-mut-*.log)
- price_mutants.py: "21 of 22 good; problems: ['M6b the decimals branch is removed']" (SNIPPET NOT FOUND). EXIT=1.
- audit_drain_a10_mutants.py: M1..M4 all KILLED, EXIT=0.
- audit_drain_mutants.py (no --hand): RuntimeError "the unmutated copy does not pass its tests" EXIT=1 (no mutant run).
- audit_drain_mutants.py --hand: "0 of 4 good by hand": all 4 BASELINE FAILS (M9, M2 two-process, M1 two-process, F1). EXIT=1.
- stop_state_mutants.py --hand: `SUMMARY server=170011 mutants=137 KILLED=111 N/A=11 EQUIVALENT=0 SURVIVED=2 OTHER=13`. EXIT=1.
  SURVIVED: "S12: the isfinite CHECK is removed from the stops" and "...from the clears" (0006_stop_state.sql).
  OTHER (13): FAILED FOR ANOTHER REASON 1 (migrate: effective_problems is not run for the reset role); NOT APPLIED 5 (postgres.py NOT EXISTS; limits.py reset clears before intent; cli.py still-ON reset exits 0 / still-ON message / clean reset exit 0); BASELINE FAILS 7 (S2 membership without inheritance, S2 PUBLIC grant ignored, S2 second schema, S2 only when reset role named, cli OSError, cli closed stdout, cli applied line not guarded). N/A 11 need PG<16 (not run on PG15 for this script).
- reserve_mutants.py (no --hand): RuntimeError "the unmutated copy does not pass its tests" EXIT=1.
- reserve_mutants.py --hand: "23 of 27 good; problems: [H7 the settle claim has no status test (FAILED FOR ANOTHER REASON), H9 settle books on today's day (NOT APPLIED), H9 (no row for today) (NOT APPLIED), H10 the month key is taken from today (NOT APPLIED)]" EXIT=1.
- pytest mutant files (raw/04-mut-pytest-mutfiles-continue.log): `61 passed, 1 error` (error = test_money_definer_mutants collection). Files: test_money_caps_mutants, test_money_guard_mutants, test_mutants_audit_drain, _a10, _mark_and_expiry, _stop_state_e5, test_price_constraint_mutants, test_step_b_e7_mutants. EXIT=1 (first attempt without --continue-on-collection-errors aborted at collection, raw/04-mut-pytest-mutfiles.log).
## Not run
stop_state_mutants --hand and others on PG15; stage_mutants, migration_numbers_mutants, mutation_runner_mutants (outside money/audit/stop); full suite on PG15; full-suite rerun after the trust fix; the 387 psql tests (no psql).
