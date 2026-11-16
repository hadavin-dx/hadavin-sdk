# Q8a-1 independent evidence, head f6fad26f830771dbbf4c2298368a50c7bdd7ab80

EVIDENCE RUNNER record (model = Fable 5.2). Raw output only; this file does not judge. Date 2026-11-11, run from about 14:48 to 15:03 UTC (20:18 to 20:33 IST).
Branch `core/q8a-1-live-override-refusals`: two commits on `origin/main` = 2a8c2aac89f83dd0a45af0412563b59ff4fe5632 (464dee14, then the fix commit f6fad26f). Worktree `/home/user/build/EV-Q8a1-f6fad26` (detached at the head; `git status --short` was empty after the full suite, after the mutants and before removal).
Every command ran with `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`, venv `/home/user/build/venv-evq8a1b` (`uv sync --all-extras --group test`, exit 0).
Postgres: own 16 cluster as the postgres user (`initdb -E UTF8 --locale=C.UTF-8 -A trust`, exit 0), port 56140, listen 127.0.0.1, socket dir /tmp, started with PGHOST/PGPORT/PGUSER in the server's environment (exit 0); tests had the same three plus `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56140/postgres`. Stopped at the end (`pg_ctl -m fast stop`, exit 0).
Not read: the builder's report, `/home/user/build/B-Q8a1-evidence`. Read: the ticket, decision D-012, the earlier evidence folder `464dee1` (to reuse its helper scripts).

## Failures and items not run (first)
- Failing tests in the full suite on the head: 0. So "rerun each failing test's file on a clean origin/main worktree" had nothing to run (NOT RUN, no input).
- 1 skip in the full suite (reason in section 1).
- Fail-before, both bases: the new test file `tests/test_q8a_live_overrides.py` (97 tests on the head) does NOT import on either base. `ImportError: cannot import name 'VaultConnection' from 'hadavin_sdk.backends.table'` (the head renames `_VaultConnection` to `VaultConnection`). A file that fails at import shows nothing about its 97 tests. See section 3 for what did run, and for an extra labelled run with one alias line appended by the runner.
- The first fail-before command on each base stopped at that collection error (pytest ran no test: `1 error`, exit 2). It was run again with `--continue-on-collection-errors`; both logs are kept.
- Probe (b): `gate`, `replay` and `score` ended on missing input files of the runner's own made-up folders (no golden file, no cause list), after the config had loaded and the backends had been asked for. `migrate` was called only without `HADAVIN_MIGRATE_DSN` (it returns before any backend); with the variable set it connects to a database, so that call was NOT made.
- Probe (b) ran with every backend replaced through the test file's own seam (`plant_test_backends`); the real Vault, Postgres, Slack and model kinds were never built by the runner. For `replay` and `score` the runner also replaced `make` in `hadavin_sdk.k1b.audit_sink` (that module has its own import of `make`).
- Runner's slips in `probes.py`, left as recorded: (1) the "tick_state after" lines print `'?'` where a status was meant (the runner guessed an attribute name that does not exist); the time in each pair is the real `last_run_at`. (2) A "kill switch state" line is printed after every (b) row, also for commands that are not the kill switch.
- Not done: no mutation run other than `tests/stage_mutants.py`; no CodeQL, SonarCloud or CodeRabbit (not in the brief).

## 1. Full suite with the database (through heavy.sh)
`/home/user/build/heavy.sh <script>`; the script runs `uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs` -> exit 0, wall 546 s. Asked for a slot 14:48:41 UTC, got it 14:48:41 UTC (wait 0 s; load average then 5.59 on 4 cores), ended 14:57:47 UTC.
Last line: `10652 passed, 1 skipped in 536.55s (0:08:56)`.
From the XML (testsuite attributes): tests=10653 failures=0 errors=0 skipped=1; counted testcase elements: passed 10652, failed 0, error 0, skipped 1.
Skip: `tests.contracts.test_llm::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses a malformed Converse shape before the kind sees it" (tests/contracts/test_llm.py:95).
The files that hold the ticket's four negative tests, run as whole files: `pytest -q -rs tests/test_stage_names.py tests/test_k5_round10.py tests/test_k5_round9b.py tests/test_k5_round5.py` -> exit 0, `275 passed in 16.42s`, no skip.

## 2. Lint and scanners
| command | exit | last line / count |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified. Medium 0, High 0 (Low 12, not shown at -ll) |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | no output from the tool (the log holds only uv's own deprecation warning) |

## 3. Fail-before, two bases
Same four files each time: `tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py tests/test_q8a_live_overrides.py tests/test_stage_names.py`, with the database address, own venv per base (`hadavin_sdk.__file__` printed the base worktree's `src`). `tests/stage_mutants.py` was overlaid too (it is not a pytest file). 0 skipped in every run. Every test with its result and first error: `fail-before-per-test.md`; failures grouped by first error text: `fail-before-groups.txt`.

Base (a): origin/main 2a8c2aac + the five files of `git diff --name-only origin/main f6fad26f -- tests` (stage_mutants.py M, test_k3_pilot_env.py M, test_k5_round8_postgres.py M, test_q8a_live_overrides.py A, test_stage_names.py M).
Base (b): 464dee14 + the five files of `git diff --name-only 464dee14 f6fad26f -- tests` (the same five names, all M).

| run | exit | last line | test_q8a_live_overrides.py | test_stage_names.py | test_k3_pilot_env.py | test_k5_round8_postgres.py |
|---|---|---|---|---|---|---|
| (a) base untouched | 1 | `3 failed, 108 passed, 1 error in 5.57s` | whole file: collection error (ImportError, name `VaultConnection`) | 3 failed, 97 passed | 10 passed | 1 passed |
| (a-extra) + one alias line | 1 | `70 failed, 138 passed in 7.90s` | 67 failed, 30 passed | 3 failed, 97 passed | 10 passed | 1 passed |
| (b) base untouched | 1 | `2 failed, 109 passed, 1 error in 5.17s` | whole file: collection error (ImportError, name `VaultConnection`) | 2 failed, 98 passed | 10 passed | 1 passed |
| (b-extra) + one alias line | 1 | `41 failed, 167 passed in 7.45s` | 39 failed, 58 passed | 2 failed, 98 passed | 10 passed | 1 passed |

The "extra" runs: the runner appended ONE line to the base's `src/hadavin_sdk/backends/table.py` (`VaultConnection = _VaultConnection`) so the new file imports; nothing else was changed; the line was removed with `git checkout` afterwards. This line is not part of any commit; it is the runner's own addition and is labelled as such.

Failures with base untouched, first assertion or error line:
```
(a) origin/main
ERROR   tests/test_q8a_live_overrides.py (collection): ImportError: cannot import name 'VaultConnection' from 'hadavin_sdk.backends.table'
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_test_object_handed_to_build :: AssertionError: a live build took a test object ('pilot'): "secret 'pg-dsn' cannot be read at start-up"
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_static_vault_token :: AssertionError: a static Vault token was accepted for secrets (pilot, {}): "secret 'pg-dsn' cannot be read at start-up"
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_time_handed_to_the_tick :: AssertionError: a live tick took a time handed to it ('pilot'): ''
(b) 464dee14
ERROR   tests/test_q8a_live_overrides.py (collection): ImportError: cannot import name 'VaultConnection' from 'hadavin_sdk.backends.table'
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_static_vault_token :: hadavin_sdk.errors.ConfigError: 1 validation error for Config / Value error, environment pilot: refused: secrets: vault auth token (the default; set auth: kubernetes or auth: approle) [type=value_error]
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_time_handed_to_the_tick :: AssertionError: a live tick took a time handed to it ('pilot'): ''
```
Failing tests of the new file in the extra runs, counted per test function (parametrised cases added up):
```
(a-extra) 67: test_each_test_keyword_is_refused_in_pilot_and_prod 12; test_demo_refuses_a_timeout_that_is_not_a_number_greater_than_0 10;
  test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads 8; test_run_tick_refuses_a_given_time_outside_demo 7;
  test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage 5; test_a_test_keyword_is_refused_for_a_value_that_is_not_a_stage 5;
  test_with_several_given_only_the_first_in_the_fixed_order_is_named 5; test_the_kill_switch_command_is_not_refused_for_a_static_vault_token 4;
  test_a_zero_timeout_is_refused_in_pilot_as_a_test_keyword 2; and 1 each: test_a_falsy_sources_mapping_is_refused_in_pilot,
  test_a_falsy_test_object_is_refused_in_pilot, test_a_falsy_tools_mapping_is_refused_in_pilot,
  test_a_new_kind_built_on_the_vault_settings_class_is_refused_too, test_an_empty_sources_or_tools_mapping_is_refused_in_pilot,
  test_both_static_vault_tokens_are_named_in_one_refusal, test_demo_uses_a_falsy_sources_or_tools_mapping_instead_of_dropping_it,
  test_demo_uses_a_falsy_test_object_instead_of_dropping_it, test_the_factory_hands_a_falsy_secret_provider_to_the_backend
(b-extra) 39: test_demo_refuses_a_timeout_that_is_not_a_number_greater_than_0 10;
  test_a_build_refuses_a_static_vault_token_in_pilot_and_prod_and_the_config_still_loads 8; test_run_tick_refuses_a_given_time_outside_demo 7;
  test_a_build_refuses_a_static_vault_token_for_a_value_that_is_not_a_stage 5; test_the_kill_switch_command_is_not_refused_for_a_static_vault_token 4;
  and 1 each: test_a_falsy_sources_mapping_is_refused_in_pilot, test_a_falsy_tools_mapping_is_refused_in_pilot,
  test_a_new_kind_built_on_the_vault_settings_class_is_refused_too, test_an_empty_sources_or_tools_mapping_is_refused_in_pilot,
  test_demo_uses_a_falsy_sources_or_tools_mapping_instead_of_dropping_it
```
The two positive pilot tests on both bases, all four runs: `passed` (rows in the table file).

## 4. The two positive pilot tests on the head, with the database
`uv run --all-extras --group test pytest -v -rs -p no:cacheprovider <the two ids>` -> exit 0, wall 4 s:
```
tests/test_k3_pilot_env.py::test_k3_pilot_app_has_no_executor PASSED     [ 50%]
tests/test_k5_round8_postgres.py::test_the_app_deletes_evidence_only_through_the_purge_identity PASSED [100%]
============================== 2 passed in 2.65s ===============================
```

## 5. Mutants (through heavy.sh)
`/home/user/build/heavy.sh <script>`; the script runs `uv run --all-extras --group test python tests/stage_mutants.py` -> exit 0, wall 160 s. Asked for a slot 14:57:54 UTC, got it 14:57:54 UTC (wait 0 s; load average then 13.49), ended 15:00:34 UTC. Started only after the full suite had ended.
Last line: `46 of 46 good; problems: []`. All 46 rows: `mutant-rows.txt`. Rows whose names are not in the 464dee1 evidence (39 rows there): M12c, M12d, M12e, M12f, M12g, M13a, M13b. The M12 and M13 rows:
```
ok  KILLED       M12a a live build takes a test object (app.py: the refusal of the six keywords is switched off)  [test_pilot_and_prod_refuse_a_test_object_handed_to_build]
ok  KILLED       M12b a static Vault token is allowed in pilot and prod (app.py: the check never matches)  [test_pilot_and_prod_refuse_a_static_vault_token]
ok  KILLED       M12c the six keywords are tested for truth, not for being given (app.py)  [test_pilot_and_prod_refuse_a_test_object_handed_to_build]
ok  KILLED       M12d clock dropped from the six keywords (app.py)  [test_pilot_and_prod_refuse_a_test_object_handed_to_build]
ok  KILLED       M12e timeout_s dropped from the six keywords (app.py)  [test_pilot_and_prod_refuse_a_test_object_handed_to_build]
ok  KILLED       M12f the Vault check is narrowed to the secrets kind (app.py)  [test_pilot_and_prod_refuse_a_static_vault_token]
ok  KILLED       M12g the Vault check runs in prod only (app.py)  [test_pilot_and_prod_refuse_a_static_vault_token]
ok  KILLED       M13a a live tick takes a time handed to it (tick.py: the refusal is switched off)  [test_pilot_and_prod_refuse_a_time_handed_to_the_tick]
ok  KILLED       M13b the tick refuses a handed time in demo too (tick.py)  [test_pilot_and_prod_refuse_a_time_handed_to_the_tick]
```

## 6. Probes on the head
Script `probes.py` (copy beside this file), run on the head without the database variables: exit 0, 138 output lines in `probes.txt`, verbatim (exception type and message, or "no exception" with what was returned; line breaks inside a message shown as `\n`, cut at 700 characters; the temp folder path replaced by `<tmp>`). Configs come from the test file's own helpers (`vault_dir`, `live_dir`, `make_cfg` + `qualify`); pilot apps are built the way `test_a_live_build_with_no_test_keyword_is_not_refused` builds one (memory store, fake channel, scripted model through `plant_test_backends`). Rows by output text, no interpretation:
- (a) pilot and prod, `backends.secrets = {kind: vault, address: https://vault.example}`, auth left out: `load_config` -> 2 x "no exception", returned config shows `auth='token'`; `build` -> `ConfigError: environment pilot: refused: secrets: vault auth token (the default; set auth: kubernetes (recommended) or auth: approle)` and the same text with `environment prod`. Extra, not in the brief: the same for `backends.signer = vault_transit`: `load_config` 2 x "no exception"; `build` 2 x `ConfigError: environment <stage>: refused: signer: vault_transit auth token (...)`.
- (b) `cli._main` with that same config, pilot and prod (14 rows): `limits stop --by ops` -> 2 x returned 0, stdout `kill switch ON (by ops)`; `limits reset --by ops` -> 2 x returned 0, stdout `kill switch OFF (by ops)`; `audit verify` -> 2 x returned 0, stdout `0 rows, signed through row 0 (0 not signed yet)\nintact`; `gate ito-agent` -> 2 x `FileNotFoundError: ... golden/ito-agent.jsonl`; `migrate` without `HADAVIN_MIGRATE_DSN` -> 2 x returned 2, stderr `refused: set HADAVIN_MIGRATE_DSN to the migration role's DSN`; `replay ...` -> 2 x `ConfigError: cause list: services.json is missing or not readable`; `score ...` -> 2 x the same ConfigError. No row shows the text "vault auth token". Each row lists the (capability, kind) pairs the command asked the factory for; `('secrets', 'vault')` is in every row except `migrate`.
- (c) `run_tick(app, now=...)`, a new app per row. Demo app: past datetime -> returned 0; future (today + 500 days) -> returned 0, `last_run_at` 2028-03-25; `None` -> returned 0; falsy datetime subclass -> returned 0, `last_run_at` 2020-01-01; `0` -> returned 1, stderr `step=stuck error_kind=TypeError ...` and `step=purge_evidence error_kind=TypeError ...`, `last_run_at` 1970-01-01; `False` and `''` -> returned 1, stderr `tick_state not saved` for every step, no tick state. Pilot app: past, future, falsy datetime subclass, `0`, `False`, `''` -> 6 x `ConfigError: now= is for tests; it is refused in pilot and prod`, tick state of every step `None` after the call; `now=None` and `now` not passed -> returned 0, all six steps have a tick state. Extra: prod app, future -> the same ConfigError.
- (d) `build(..., timeout_s=x)` in demo: 0, 0.0, -1, True, False, nan, inf, "5" -> 8 x `ConfigError: timeout_s= must be greater than 0`; 1e-9 -> "no exception", `executor.timeout_s=1e-09`; 5 -> "no exception", `executor.timeout_s=5`.
- (e) demo: `sources={}`, `tools={}`, `sources=None`, `tools=None` -> 4 x "no exception" (`sources=[]`, `hooks.tools={}`). Pilot: `sources={}` -> `ConfigError: sources= is for tests; configure Config.sources in pilot and prod`; `tools={}` -> `ConfigError: tools= (plain callables) is for replay and tests; use tools/<agent>.yaml in pilot and prod`; `sources=None`, `tools=None` -> 2 x "no exception" (`executor=NoneType`).
- (f) pilot app, default step names `['sweep', 'reconcile', 'stuck', 'checkpoint', 'purge_evidence', 'reprobe_sources']`: `steps=[]` -> "no exception", returned 0, no step has a tick state afterwards; `steps=` the default list with one step left out, six rows (one per step) -> each "no exception", returned 0, the left-out step has tick state `None`, the other five have one; `steps=None` -> returned 0, all six have one.
Rows with "no exception" outside demo, in full: the 2 (+2 extra) `load_config` rows of (a); 8 rows of (b); 2 rows of (c) (`now=None`, `now` not passed); 2 rows of (e) (`sources=None`, `tools=None`); all 8 rows of (f).

## 7. gitleaks
`/home/user/build/bin/gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..f6fad26f" <worktree>` -> exit 0, "2 commits scanned", "scanned ~59432 bytes", "no leaks found".
`/home/user/build/bin/gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8a-1/f6fad26` -> result in the runner's final report (run after this file was written; this file was not changed afterwards).

## Clean-up
Own Postgres stopped and its folder removed; the three worktrees (head, two fail-before bases) removed with `git worktree remove`; the three venvs and the probe temp folder (it held generated test key files) removed. `pgrep` for the runner's paths: 0 processes. No commit, no push, no sub-agent, no paid call.

## Files
Here: RESULTS.md, fail-before-per-test.md (four tables, every test), fail-before-groups.txt, mutant-rows.txt, probes.py, probes.txt.
Raw, `/home/user/build/evidence-raw/Q8a1-f6fad26/`: full.log, full-junit.xml, full-meta.txt, fbmain*.log / fb464*.log with their junit XML (untouched base, stopped-at-collection first attempt, shim extra), fb-setup.log, pilot-two.log, negative-files.log, mutants.log, mutants-meta.txt, probes.log, probes.err, ruff-check.log, ruff-format.log, bandit.log, scan-repo.log, gitleaks-git.log, gitleaks-dir.log, pg-init.log, pg-start.log, pg-stop.log, pg-server.log, uv-sync*.log, and an `*-rc.txt` per command. Helper scripts: `/home/user/build/ev-q8a1b-scripts/`.
