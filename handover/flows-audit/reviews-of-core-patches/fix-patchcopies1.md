# fix-patchcopies1: fixer log for patch-copies-readiness-r1 (B1-B3, M4-M8)
Date 2026-11-16. Fixer on a security and money path. Edited only: `patch-copies/README.md`, `DEAD-MAN-CHECK.md`, `A-01.patch`, `C-01.patch`, and added `G5-wording.patch` (copied, not rewritten). EGM skipped for the fixer step: the lead runs the result review.

## Failed or not done, first
- `bandit -ll`: NOT RUN (not installed, no network). UNVERIFIED.
- The gate was run with the repository's `.venv` tools, not through `uv run` (uv has no network here).
- Full test suite: one failure that is NOT caused by the patches: `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked` fails the same way on a pristine archive of `b4cce5b` (it scans `handover/` files: 'Port.io' in two files, one non-UTF-8 text file). Raw: see section 7.
- `C-01.patch` and `G5-wording.patch` do not apply on `176a0cbe0` or on head `ec65e4614` (section 2). Not rebuilt for those commits.
- M7: the NaN/Infinity price is already refused by the existing pydantic field check, so the new tests cannot fail on old code (they pin it). No new refusal code was needed; one comment line was added in the patch.
- Dead-man query and identity ran on a throwaway Postgres 16.15 with only the `tick_state` table, not on the real store or schema. The throwaway server folder was in `/tmp/hadavin-pgtest` (the scratchpad path was not readable by the database user); it was stopped and deleted at the end.

## 1. Base and scratch copy (B1)
`git cat-file -t b4cce5b` and `-t 176a0cbe0`: both `commit`. `git log -1 b4cce5b`: "core-hardening: plan v4 rulings, round 3 logs, build start". Archive:
`git archive b4cce5b | tar -x -C <scratchpad>/fresh` (also `/pristine`, `/old`). Path names below use `<scratch>`.

## 2. git apply --check (new patch copies, exact commands, results)
On `b4cce5b`: `git apply --check C-01.patch` rc 0; `A-01.patch` rc 0; `G5-wording.patch` rc 0. In order C-01, A-01, G5-wording: `check && apply` chain rc 0.
On `176a0cbe0` (archive of `src tests`): A-01 rc 0; C-01 rc 1 ("patch failed: src/hadavin_sdk/config.py:362"); G5-wording rc 1 ("patch failed: tests/warden_port/test_gate.py:1").
On head `ec65e4614`: A-01 rc 0; C-01 rc 1 (config.py:362); G5-wording rc 1 (test_gate.py:1).
Line cites at head `ec65e4614`: Route `config.py:64`, `refused = []` `:393` (at `b4cce5b`: `:55`, `:365`; the README cites are the `b4cce5b` ones and says so).
G5-wording: found at `handover/core-hardening/patches-ready/G5-wording.patch` in an earlier scratch copy (outside the repository); sha256 begins 92cacbd4714 for both that file and the copy now in `patch-copies/`; it is byte-identical to it. (Other versions under the scratchpad `x/.../v2-v5` differ and were not used.) A-01, C-01, README and DEAD-MAN-CHECK in that scratch copy were byte-identical to the previous `patch-copies` files (`cmp`), so it is the same source.

## 3. M6 (LocalDirSink memory-only log) and tests
`local_dir.py` inner `except` now logs `_LOG.error("audit outbox not written (%s): event %s is held in memory only", type, event_id)` before `self._pending.append(event)`. New test `test_local_dir_sink_logs_a_warning_and_then_an_error_when_the_outbox_fails_too` (a file stands where the outbox folder should be; checks warning, error, type, id, no error text, no run id, one pending event). Failed on first run (the audit folder did not exist); test fixed to create it; passed after. Test proves-fail-on-old: listed in the 14 failures in section 5.

## 4. M7 / M8 (C-01)
Probe (`PYTHONPATH=src:. python probe`, made-up config): for kinds `fake` and `anthropic`, price `NaN`, `sNaN`, `Infinity`, `-Infinity`: all `ConfigError "1 validation error for Config routes.default.input_usd_per_mtok  Input should be a finite number"`; price `1`: loads. Note `Decimal("NaN") <= 0` raises `InvalidOperation` (seen), but it is never reached.
New test `test_a_non_finite_price_is_a_clean_config_error` (2 kinds x 2 fields x 4 prices = 16 cases, `match="finite"`). M8: `AnthropicSettings` (`backends/table.py:43-61`): platform `api` needs `api_key_secret_name`; the test's `LIVE_LLM` matches; `test_a_priced_live_route_still_loads` now asserts `backends.llm.kind == "anthropic"` and `platform == "api"`. Fixture environment is `dev` (`tests/fixtures/config/config.yaml:2`); the environment-table refusal does not apply.

## 5. Tests, lint (patched copy of b4cce5b; `.venv` tools, no network, no cloud config)
- `ruff format` on the new test file: reformatted 1 file (my test); then `ruff format --check src tests`: `265 files already formatted`; `ruff check src tests`: `All checks passed!` (the same on the fresh copy after applying the three final patch files).
- Fresh copy, patches C-01, A-01, G5-wording applied from the final files: `pytest tests/test_a01_audit_reconcile.py tests/test_c01_route_limits.py tests/test_p7_tick.py tests/warden_port/test_gate.py -q` -> `87 passed in 21.54s`.
- Prove-fails-on-old-code: unpatched `b4cce5b` archive + the two new test files: `14 failed, 18 passed`. Failures: 6 `test_a_zero_or_negative_price_is_refused_for_a_live_model` cases, `test_max_tokens_above_the_ceiling_is_refused`, `test_max_tokens_at_the_ceiling_loads_and_zero_is_still_refused`, and the 6 A-01 tests (`test_the_step_is_in_the_tick_list`, `..._drains_the_outbox_and_logs_the_count`, `test_a_kind_without_reconcile_is_skipped`, `test_a_failed_outcome_write_logs_type_and_id_but_never_the_body`, `test_when_the_outbox_table_also_fails_an_error_line_is_logged`, `test_local_dir_sink_..._outbox_fails_too`). The 18 passes are controls and the 16 non-finite cases (those two groups cannot fail on old code, see above).
- `bandit -ll`: not run.

## 6. Dead-man query and identity (B3, M4, M5)
Postgres 16.15 started as the `postgres` OS user on a local socket (port 54399), database `dm`, table copied from `0003_approvals_tick.sql`. Query run with `psql -v ON_ERROR_STOP=1 -v limit_s=180 -At -f dead-man-check.sql`:
- empty table: 5 lines `MISSING (no row: never ran)`, rc 0.
- 5 fresh rows: no output, rc 0.
- after setting `stuck` 10 min old, `sweep` last_ok null, deleting `audit_reconcile`: 3 lines (`audit_reconcile|||MISSING...`, `stuck|...|STALE...`, `sweep||...|NEVER SUCCEEDED`), rc 0.
- without `-v limit_s`: `ERROR: syntax error at or near ":"`, rc 3.
Identity `deadman_reader` (CREATE ROLE ... NOSUPERUSER NOCREATEDB NOCREATEROLE; GRANT CONNECT; GRANT USAGE ON SCHEMA public; GRANT SELECT (step, last_ok_at, last_run_at) ON tick_state): query as that role returned the same 3 rows, rc 0. Each of `SELECT last_error`, `SELECT *`, INSERT, UPDATE, DELETE on tick_state, `SELECT * FROM audit_outbox` (a made-up table), `CREATE TABLE` in public: `permission denied`. After `REVOKE SELECT ON tick_state`: rc 3, `permission denied for table tick_state`. M5: `last_error` is no longer selected.
Credentials: none printed; the throwaway server used trust login on a local socket only.

## 7. Full suite on the patched copy
Command: `PYTHONPATH=src .venv/bin/python -m pytest -q -p no:cacheprovider -m "not live and not perf"` in the patched archive of `b4cce5b`. Result: `2 failed, 9396 passed, 454 skipped, 26 deselected in 218.01s`, exit 1. The 2 failures are not from the patches:
- `tests/test_no_reference_material.py::test_no_vendor_brand_string_is_tracked`: same failure on a pristine archive of `b4cce5b` (`1 failed, 2 passed`): vendor string in two `handover/` files and one non-UTF-8 file.
- `tests/test_repo_rules.py::test_licences_are_proprietary`: needs `git ls-files` (`CalledProcessError ... status 128` on the pristine archive too), because an archive folder is not a git repository. Not run inside a real checkout, so UNVERIFIED there.
The timing tests (`perf`) and live tests were not run (deselected, as CI does).
## 8. Cleanup
Throwaway Postgres stopped (`pg_ctl stop`) and `/tmp/hadavin-pgtest` removed; no background process left. No file outside the named ones was edited; `src` of the repository untouched.
