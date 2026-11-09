# bd-peel2 report: PR 87 (core/peel-run-id) round-1 fixes, new head a909459b7cc1452cbc17563476abd50ba2240f4d
Written 2026-11-09 07:41 UTC (13:11 IST). Builder: Sonnet 5.5. No spend, no model call (fake model only), made-up data.

## Failed / uncertain / not done (first)
- Independent evidence run and EGM result review NOT done by me (not my role): PR 87 is a money path, so these rounds are uncapped.
- BL-core-peel-003 NOT fixed: `tools/mutation_runner.py` still cannot run these tests (`--noconftest`). I ran the mutants by hand with `handover/tools/peel_mutants.py`. Row stays OPEN.
- BL-core-peel-001 untouched (lead decision).
- The two askdata tests ([copy-program], [dblink-connect]) are FLAKY on the base too (see item 5). I did not change them in PR 87 (separate concern, different files); proposed one-line fix below needs the lead's yes to go in a small PR.
- Postgres was exercised for the store contract tests only (duplicate id, 8-thread race on create_run). There is no Runtime-over-Postgres handle test; the handle tests use the memory store.
- The first review claimed `tests/contracts/test_store.py:65` covers a duplicate `create_run`. I checked: it did not (no such test existed). I added it.
- Full suite NOT run (instruction). Run: tests/test_peel_run_id.py, tests/contracts/test_store.py, tests/test_s5_runtime.py (102 passed with Postgres), ruff check/format on src+tests, bandit.

## What changed (src: `runtime/agent_loop.py` only; `models.py` unchanged since 84abdf6)
- `Runtime.handle`: on `StaleState` from `create_run` for a GIVEN run_id, `_same_message_run` reads `store.get_run(run_id)`; if agent_id, principal_id and trigger_ref all equal this call's it returns that run (no note, no model call, no meter/limits call, no redaction); else re-raises the same `StaleState`; if the run vanished (`NotFound`) it raises the `StaleState`, not `NotFound`. `run_id=None` unchanged (re-raises). Order unchanged: Unqualified, then InvalidRunId, then create_run.
- Docstring rewritten: id shape "run-" then 32 characters 0-9 a-f; what the id is for; what happens on a repeat.

## Tests (tests/test_peel_run_id.py, tests/contracts/test_store.py)
t2 replaced by D2; added D0, D2b-direct (3 cases), D2c-direct, D2d (run vanished), race (2 threads at a barrier inside create_run, 10 rounds), t9 (check order), t8 now asserts `hasattr(models, "RUN_ID_PATTERN")`. Store contract (memory + Postgres): duplicate run_id is StaleState and changes nothing; 8 threads create the same id: 1 winner, 7 StaleState.
No fake meter exists on the base, so "no meter hold" is checked with a counting wrapper on `rt.limits` (no `blocked`/`charge` call) plus model-call, audit-note and store-call counts (`["create_run","get_run"]` only).

## 3. Mutants (handover/tools/peel_mutants.py, copied to the worktree; per-mutant temp copy, real conftest)
Final run `/home/user/build/peel2-mutants-final.log`: 17/17 killed for the stated reason. PM-1 (=MP1, counted once) ignored id; PM-2 loop runs again (killed by D2, via IllegalTransition "NO_ACTION is final" at the second call); PM-3/4/5 foreign agent/principal/trigger_ref returned (killed by the matching D2b-direct case, "DID NOT RAISE StaleState"); extra PM-6 any run returned, PM-7 check order swapped (t9), PM-8 limits called on the repeat path, PM-9 second note on the repeat path, PM-10 NotFound instead of StaleState (D2d); MP2-5, MP7, MP9, MP10 kept. Old MP6 removed (its code no longer exists; PM-2 replaces it). Honest note: PM-2 and PM-7 are killed by an exception raised inside the test, not by a plain assert; both still fail the pinned test.

## 4. Fail-before (copies of the new tests in fresh worktrees; logs under /home/user/build/peel2-failbefore.log)
Base 0dabf1f: D0 fails by assertion (`assert 2 == 1`: two run rows); t8 fails by assertion (`assert False`, no RUN_ID_PATTERN); D2, D2b, D2c, D2d, race, t1 fail with `TypeError: unexpected keyword argument 'run_id'` (the feature does not exist there; unavoidable). The two store contract tests PASS on base (they test existing store behaviour, they are new coverage not new behaviour). t9: base fails with TypeError. 
On 84abdf6: D0 fails by assertion ("second call raised StaleState"); D2 raises StaleState; D2b/D2c/D2d fail on the call-list assertion (no get_run), 3 of 11 selected pass (t1 etc.).

## 5. Two askdata tests, base vs head, same environment
Own Postgres 16 cluster (pgstart.sh peel2 56187: server env PGHOST=/tmp, PGPORT=56187, socket dir /tmp), HADAVIN_TEST_PG_DSN to it. Command: `pytest tests/demo_askdata/test_validate_harm.py -k "copy-program or dblink-connect"`.
- base 0dabf1f: 2 passed on first run; over 25 runs 2 failed.
- 84abdf6 + my uncommitted changes: first run 1 failed ([copy-program]), [dblink-connect] passed; 6 repeat runs all passed; over 25 runs 3 failed.
- Failure text every time: `psycopg.errors.InternalError_: could not close pipe to external command: Broken pipe`, only [copy-program]. [dblink-connect] passed in every run here.
Cause (class: test depends on a race): the attack is `COPY (SELECT 1) TO PROGRAM 'echo x'`; `echo` exits without reading its input, and when PostgreSQL writes after the exit it gets a broken pipe. Not related to PR 87 (same rate on base). Proposed fix, tried in a scratch worktree only and reverted: `TO PROGRAM 'cat > /dev/null'` in tests/demo_askdata/corpus.py:96: 0 failures in 40 runs of copy-program + dblink-connect + the test_roles PROGRAM case. Needs its own small PR (lead's call). dblink-connect failing in the earlier evidence run was not reproduced here (0 of ~60 runs).

## Ledger
BL-core-peel-002 -> FIXED-UNVERIFIED (a909459). 001 and 003 unchanged (OPEN).

## CHECKED BY ME
ruff check and format --check on src+tests: clean. `bandit -ll -r src` (via uvx, exit 0, 0 issues). Affected tests: 102 passed (incl. Postgres store contract). Mutants 17/17. Fail-before as above.
## NOT RUN
Full suite, CI, CodeQL/Sonar/CodeRabbit, Runtime-over-Postgres handle test, full mutation_runner. R-numbers: not looked up (no bible folder in this cloud checkout); rules used from CLAUDE.md/rules (class-level fixes, fix-dont-defer, reviewer-independence).
