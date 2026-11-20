# Batch 10: non-PostgreSQL mutant batteries and unit tests

Scope: evidence only. No code changed, nothing committed or pushed. `HADAVIN_TEST_PG_DSN` unset for every run.

## Environment

- Repo: `/home/user/hadavin-sdk`, branch `cloud/core-b`, HEAD `316345dc471285d1163346a5d98eaef5cb200c16`
- Start 12:46:36Z, finish about 12:50Z
- Runner: `uv run --all-extras --group test`

## Warning: uncommitted changes in the working tree

`git status` at the end of the run shows two modified tracked files that I did not touch:

- `src/hadavin_sdk/limits.py` (mtime 12:49:55Z)
- `src/hadavin_sdk/runtime/tick.py` (mtime 12:49:55Z)

The diff is a logging change (`limits_unavailable` log without the error message; `check_caps` agent id truncated to 64 chars). I did not check `git status` before the run, so I cannot say whether these edits were there before it. The mtime falls inside the run window, and the baseline-failing mutant scripts (below) ran about then. Someone should confirm the working tree before this evidence is relied on. Nothing was fixed or reverted here.

## 1. Mutant scripts (no `--hand`, no DSN)

Command form: `uv run --all-extras --group test python tests/<name>.py`

| Script | Exit | Result |
|---|---|---|
| `tests/audit_drain_mutants.py` | 1 | Aborted at baseline: `RuntimeError: the unmutated copy does not pass its tests`. Mutants not run. |
| `tests/audit_drain_a10_mutants.py` | 0 | 4 of 4 KILLED (M1 to M4). |
| `tests/migration_numbers_mutants.py` | 0 | 37 of 37 good. |
| `tests/mutation_runner_mutants.py` | 0 | 62 of 62 good. |
| `tests/price_mutants.py` | 1 | 21 of 22 good. Failure below. |
| `tests/reserve_mutants.py` | 1 | Aborted at baseline: `RuntimeError: the unmutated copy does not pass its tests`. Mutants not run. |
| `tests/stage_mutants.py` | 1 | 36 of 37 good. Failure below. |
| `tests/stop_state_mutants.py` | 0 | Lists only. The runnable list M is empty; all mutants are in `HAND` and need PostgreSQL. Reported as skipped: 0 run. |

Logs: `/tmp/claude-0/-home-user/85e86c49-3cea-5848-97d8-d0336bed6f60/scratchpad/b10/<name>.log`

### Failures in scripts

**`tests/audit_drain_mutants.py` (baseline)**
- Last error line: `RuntimeError: the unmutated copy does not pass its tests`
- Cause: the runner's baseline pytest run of `tests/test_audit_drain.py` with `--noconftest` fails. Diagnostic run: 1 failed, 58 passed, 29 errors. The errors are `fixture 'live_cfg_dir' not found`, because `--noconftest` drops `tests/conftest.py`. The one FAILED id in that run is `tests/test_audit_drain.py::test_n1_audit_drain_is_the_last_tick_step`, last error line `AssertionError: assert ['expire_rese... 'check_caps'] == ['audit_drain...reservations']`. Diagnostic log: `.../scratchpad/b10/diag_audit.log`

**`tests/reserve_mutants.py` (baseline)**
- Last error line: `RuntimeError: the unmutated copy does not pass its tests`
- Diagnostic run (`pytest -q -p no:cacheprovider --noconftest tests/reserve_mutants.py`): 4 failed, 184 passed.
  - `tests/reserve_mutants.py::test_a_failing_store_marks_the_step_failed_and_the_other_steps_still_run`: `AssertionError: assert 0 == 1`
  - `tests/reserve_mutants.py::test_the_step_expires_old_reservations_and_keeps_young_ones_and_the_totals`: `AssertionError: assert ('open', None) == ('expired', Decimal('1.00'))`
  - `tests/reserve_mutants.py::test_the_step_is_the_last_one_and_comes_after_audit_drain`: `assert 'check_caps' == 'expire_reservations'`
  - `tests/reserve_mutants.py::test_the_step_uses_the_longer_age_while_a_run_could_still_be_working`: `AssertionError: assert 'open' == 'expired'`
- Diagnostic log: `.../scratchpad/b10/diag_reserve.log`

**`tests/price_mutants.py`**
- Mutant `M6b the decimals branch is removed`: `BAD ERROR`, last line `[SNIPPET NOT FOUND]`. The mutation text was not found in the source, so the mutant was not applied.

**`tests/stage_mutants.py`**
- Mutant `M4d the demo-only refusal is switched off`: `BAD WRONG_REASON`. Killer `test_pilot_and_prod_refuse_every_relaxed_kind` failed with a reason other than the one expected.

## 2. Mutant and unit test files (pytest, no DSN)

Command:
```
pytest -q -p no:cacheprovider -n 2 -rfEs tests/test_mutants_audit_drain.py tests/test_mutants_audit_drain_a10.py tests/test_mutants_mark_and_expiry.py tests/test_mutants_stop_state_e5.py tests/test_money_caps_mutants.py tests/test_money_definer_mutants.py tests/test_money_guard_mutants.py tests/test_price_constraint_mutants.py tests/test_step_b_e7_mutants.py
```

Result: **28 passed, 33 skipped, 2 errors** (exit 1)

- Skipped: 33, all with reason `HADAVIN_TEST_PG_DSN not set`, in `test_mutants_stop_state_e5.py`, `test_money_caps_mutants.py`, `test_money_guard_mutants.py`, `test_step_b_e7_mutants.py`.
- Errors (collection, 2 entries): `ERROR tests/test_money_definer_mutants.py`. Last error line: `ValueError: too many values to unpack (expected 5)`, raised at `tests/test_money_definer_pg.py:52` (`RESERVE, SETTLE, EXPIRE, PURGE, ADD = mig.MONEY_FUNCTIONS`).

`tests/reserve_mutants.py` run under pytest is covered in section 1 (4 failed, 184 passed).

## 3. Unit test batch (requested command)

Command, verbatim:
```
pytest -q -p no:cacheprovider -n 2 tests/test_audit_drain*.py tests/test_config*.py tests/test_limits*.py tests/test_price*.py tests/test_refused_before_response.py
```

Result: **no tests ran**, exit 5. `tests/test_config*.py` matches no file in the repo, so the shell passes the literal pattern and pytest collects nothing. Nothing is missing from the batch apart from that glob.

Same command without the `test_config*.py` glob:
```
pytest -q -p no:cacheprovider -n 2 tests/test_audit_drain*.py tests/test_limits*.py tests/test_price*.py tests/test_refused_before_response.py
```

Result: **635 passed, 1 failed, 9 skipped** (exit 1, 14.67 s)

- FAILED `tests/test_audit_drain.py::test_n1_audit_drain_is_the_last_tick_step`
  - Last error line: `AssertionError: assert ['expire_rese... 'check_caps'] == ['audit_drain...reservations']`
  - `tests/test_audit_drain.py:108`. The step order has `expire_reservations` and `check_caps` at the end of `tick.STEPS`, not `audit_drain` then `expire_reservations`. This is the same working tree as section 1's warning.
- Log: `.../scratchpad/b10/batch_noconfig.log`

## Summary

| Battery | Passed/Good | Failed/Bad | Skipped/Not run |
|---|---|---|---|
| Mutant scripts (8) | 4 full runs clean (a10, migration_numbers, mutation_runner, stop_state lists) | 4 (audit_drain and reserve baseline aborts, price M6b, stage M4d) | stop_state: 0 mutants run |
| Mutant/test files via pytest (9 + reserve) | 28 + 184 | 4 (reserve) + 2 collection errors | 33 (PG DSN) |
| Requested unit batch (verbatim) | 0 | 0 (exit 5, no tests) | n/a |
| Unit batch without `test_config*` glob | 635 | 1 | 9 |

No fix was attempted, as instructed.
