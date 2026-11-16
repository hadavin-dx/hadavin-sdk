# A10a PR76 (core/P2a-1 head 7f32349) reviews, Wave 2 (cloud session saved a condensed copy; reviewers read the snapshot only and RAN NOTHING; void if the PR75 head changes)
## egm-design: NOT CLEAN, 1 Blocker, 6 Major
- B1 `limits stop` builds runtime store, signer, anchor and audit BEFORE the stopper store (cli.py 215-241 vs 262-276). Runtime store/audit down or runtime holding its connection limit means exit 4 "NOT set"; ticket ADV-R6-7 says stopper store first. No test. Also one CLI stop uses both slots of stop_connection_limit 2.
- M1 guard probe fails open on INCONCLUSIVE (app.py `_check_stop_guard`, runtime/tick.py `stop_guard_probe`: only a warning; ticket says retry once then refuse in pilot/prod; `ProbeInconclusive` unused).
- M2 mutation Done gate not met: 9 `mutant(` rows (4 run, 5 HAND); ticket says 199 of 199; lock-order/deadlock/53300 mutants absent; tools/mutation_runner.py not seen at this base.
- M3 `test_cli_kill_switch_reaches_every_process` lost its reset leg (weakened test); another test's exit code changed 3 to 5 with a stale name.
- M4 over-breadth: P4d money code (0006 spend reservations, round_cost_up, price validators) inside the diff; stacked on PR75? true delta unknown.
- M5 missing behavioural least-privilege tests (recording SecretProvider; 53300; 40P01; S33; B9; INCONCLUSIVE paths).
- M6 limits (runtime 20, stop 2, advisory wait) hard-coded, not in LimitsSettings.
- M7 runbook lacks bootstrap, HD003 steps, lock key, exit 8.
- Nits: matrix on required check name; reset audit order; StopNotConfirmed before audit row; literal schema_version 1; raw psycopg connect error; 10 s connect_timeout.
## egm-codebase-details: 0 Blocker, 2 Major
- M1 same as B1 above plus exit 8 ("stop DONE; audit row NOT written") not implemented anywhere.
- M2 fails-on-old-code evidence thin: 5 key mutants hand-run only; PG tests skip without HADAVIN_TEST_PG_DSN; ACCEPTED_CHANGES entry not found (depends on P3a).
- Nits: range check copied 3x (use protocol.check_int); MIN_KEY_BYTES duplicate; ticket says errors=replace, code surrogatepass; memory store has no cap; dead `PERFORM 1` in stop function; reset label-key check before name check; P4d money not reviewed.
Both: SQL core (guard/stop/reset functions, grants, append-only triggers, lock order) read as correct. NOT checked: anything at run time.
