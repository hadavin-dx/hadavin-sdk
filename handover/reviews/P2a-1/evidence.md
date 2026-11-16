# P2a-1 evidence (builder: Sonnet 5.5). Head SHA: e323ac7 (pushed; PR 76, draft, base core/P4d-a2).

Honest summary first: this is a time-boxed VERTICAL SLICE, not the whole ticket. See "Not built" below.

## Commands and results
- Lint: `uv run --all-extras --group test ruff check` -> All checks passed. `ruff format --check` -> 325 files already formatted.
- `uvx bandit -ll -r src -q` -> 0 issues (the first run found B608 in my PostgreSQL call helper; fixed by two whole-literal statements, commit ca9b449).
- Full pytest py3.12 (head 38a1f55, `heavy.sh uv run --python 3.12 ... pytest -m "not live and not perf"`): `1 failed, 10389 passed, 1 skipped, 26 deselected in 316.86s`. The 1 failure is tests/demo_askdata/test_validate_harm.py[dblink-connect]: unix socket /var/run/postgresql/.s.PGSQL.5432 missing in this container. The file is unchanged from origin/main (git diff origin/main -- tests/demo_askdata is empty). Not caused by this branch; not fixed here. Log: full-312.log.
- Full pytest py3.13 at ca9b449: `3 failed, 10387 passed` (full-313.log). The 3 = the same dblink test + two tests of mine that needed the new API (test_k5_round8_postgres: label-key secret; test_p7_tick: --reset-role). Both fixed in 38a1f55; the re-run of those two files passed (42 passed).
- Full pytest py3.13 at FINAL head e323ac7 (full-313-final.log): `10392 passed, 1 skipped, 26 deselected in 331.08s`, rc=0, zero failures. The dblink test did not fail this time (it failed in the two earlier runs); I did not find out why, so it is environment-dependent and not proven fixed.
- PostgreSQL: 16.15 at 127.0.0.1:55432, database p2a_1, HADAVIN_REQUIRE_PG=1 (a missing database fails, not skips). Load average seen: 3.3 to 7.6.

## Fail-before
New test files copied onto the base 1e4752f (git worktree, removed afterwards): all 5 new test modules fail at collection (`ModuleNotFoundError: hadavin_sdk.audit.labelkey`). See failbefore.txt. This proves the tests need the new code; it is a weak proof for the behaviour tests. The behaviour proof is the mutant table below.

## Mutants (15 hand-made, run by mutants_runner.py against the 6 new/affected test files, `-x`)
All 15 KILLED in the end. 2 SURVIVED the first time (guard group check; version-only stale pair in the memory store); I added one test each (e323ac7) and both are now KILLED. Raw first run: mutants.log. This is NOT the ticket's ~199-mutant run (no runner was built).
| mutant | result |
|---|---|
| stop label check removed | killed |
| reset version check removed | killed |
| reset open-count check removed | killed |
| guard group membership check removed | killed after new test |
| guard registered-label check removed | killed |
| cap check removed | killed |
| state view ignores open requests | killed |
| memory reset version check removed | killed after new test |
| memory reset open check removed | killed |
| memory stop label check removed | killed |
| Limits reset-names check removed | killed |
| labelkey surrogatepass -> replace | killed |
| labelkey fullmatch -> match | killed |
| Postgres reserve ignores the switch | killed |
| memory reserve reads the flag only | killed |

## What was built (summary)
Insert-only stop request table, SECURITY DEFINER stop and reset functions, guard trigger as the single recorder, state view, keyed labels (audit/labelkey.py), reset by (version, open count) pair with HD001/HD003/HD004/HD005 mapped to typed errors, grant map (runtime and stop roles hold no table right), advisory-locked migrate() with reset_role required, Limits/CLI/config changes, memory and PostgreSQL stores, merged with origin/core/P4d-a2 (migration renumbered 0007).
Fixed on the way in P4d-a2's code: reserve_spend read the switch flag directly in both stores; now reads the state view.

## Not built / not run (say so first in the report)
probe, tick step, short connection / StoreBusy, `limits check`, exit codes 7/8/10, the 199-mutant file and its run, the runbook, CHANGELOG, ACCEPTED_CHANGES, contract kind `stop_state`, CI PostgreSQL 16 job (needs ci.yml; forbidden by the brief), EGM reviews (lead runs them). The PostgreSQL negative tests ran as real logins but only on one cluster (16.15); not on a second version.

## Least privilege (identities, read/write)
- runtime login: EXECUTE on stop function; SELECT on kill_switch_state and kill_switch_resets; no right on kill_switch, kill_switch_stop_requests, kill_switch_login_labels or the request sequence (tested).
- stop login: EXECUTE on stop function; SELECT on kill_switch_state only (tested).
- reset group (NOLOGIN) members: EXECUTE on reset function; SELECT on state view; the guard needs membership AND a registered label (both tested).
- Credential refs `stop_credential_ref` / `reset_credential_ref` do not end in `_secret_name`, so the app never resolves them (tested).
