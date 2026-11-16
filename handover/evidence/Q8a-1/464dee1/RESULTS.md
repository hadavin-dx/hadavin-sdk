# Q8a-1 independent evidence, head 464dee14f59b716cff54f7fe8cf95b4061c839bf

EVIDENCE RUNNER record (model = Fable 5.2). Raw output only; this file does not judge. Date 2026-11-11, times UTC (IST = UTC+5:30).
Branch `core/q8a-1-live-override-refusals`; base `origin/main` = 2a8c2aac89f83dd0a45af0412563b59ff4fe5632. Worktree `/home/user/build/EV-Q8a1-464dee1` (detached at the head, `git status --short` empty after all runs).
Every command ran with `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`, venv `/home/user/build/venv-evq8a1` (`uv sync --all-extras --group test`, exit 0).
Postgres: own 16 cluster (`initdb -E UTF8 --locale=C.UTF-8 -A trust`, exit 0), port 56090, listen 127.0.0.1, socket dir /tmp, server started with PGHOST/PGPORT/PGUSER in its environment; tests had the same three plus `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56090/postgres`. Stopped at the end.
The builder's report and `/home/user/build/B-Q8a1-evidence` were not read.

## Failures and items not run (first)
- Failing tests in the full suite on the branch: 0. Because there were none, step "rerun each failing file on a clean origin/main" had nothing to run (NOT RUN, no input).
- 1 skip in the full suite (reason below).
- Probe row `(ref)` (demo with a falsy channel) raised `ConfigError: secret 'fixture-token' cannot be read at start-up`: the runner's own probe did not supply the demo fixture secret, so that row shows nothing about the falsy object. Left in the log as recorded.
- Probe (e), "auth through an environment-variable override": `config.py` reads only `HADAVIN_CONFIG_DIR` from the environment (class `Settings`, `env_prefix="HADAVIN_"`, one field `config_dir`); no loader path for backend settings from variables was found by reading `load_config`. Five variable names were tried anyway; rows are in `probes.txt` under (e2) and (e3).
- Wait before heavy runs: `pgrep -fc "pytest"` showed 11, 9, ..., 5 from 14:22:16 to 14:23:36 and 2 at 14:23:56 UTC; heavy runs started 14:24:04 UTC (waited about 3 min of the 15 allowed). Lint, scanners and probes ran during the wait.
- Slip by the runner: one shell command of mine contained a stray `rm -f /nonexistent`; the harness refused the whole command, nothing was removed, and it was rerun without that part.
- Not done: no mutation run other than `tests/stage_mutants.py`; no CodeQL, SonarCloud or CodeRabbit (not in the brief).

## 1. Full suite with the database
`uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs` -> exit 0, wall 453 s.
Last line: `10616 passed, 1 skipped in 448.27s (0:07:28)`.
From the XML (testsuite attributes): tests=10617 failures=0 errors=0 skipped=1; counted testcase elements: passed 10616, failed 0, error 0, skipped 1.
Skip: `tests.contracts.test_llm::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses a malformed Converse shape before the kind sees it" (tests/contracts/test_llm.py:95).
Files named in the ticket for the four negative tests, run as whole files: `pytest -q -rs tests/test_stage_names.py tests/test_k5_round10.py tests/test_k5_round9b.py tests/test_k5_round5.py` -> exit 0, `274 passed in 11.26s`, no skip.

## 2. Lint and scanners
| command | exit | last line / count |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified. Medium 0, High 0 (Low 12, not shown at -ll) |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | no output |

## 3. Fail-before (branch test files on origin/main code)
Worktree at 2a8c2aac with ONLY these five files taken from 464dee14 (`git diff --name-only origin/main 464dee14 -- tests`): tests/stage_mutants.py (M, not a pytest file), tests/test_k3_pilot_env.py (M), tests/test_k5_round8_postgres.py (M), tests/test_q8a_live_overrides.py (A), tests/test_stage_names.py (M). Own venv `/home/user/build/venv-evq8a1-fb`; `hadavin_sdk.__file__` printed the fail-before worktree's `src`.
`pytest -q -p no:cacheprovider -rfEs tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py tests/test_q8a_live_overrides.py tests/test_stage_names.py --junitxml=...` (with the DSN) -> exit 1, `38 failed, 134 passed in 6.55s`, 0 skipped.
Every test with result and first error: `fail-before-per-test.md` (172 rows). First-error text of the 38 failures, grouped (count, text):
```
      9 `AssertionError: / - secret 'pg-dsn' cannot be read at start-up / + channel= is for tests; configure backends.channel in pilot and prod` |
      8 `Failed: DID NOT RAISE ConfigError` |
      4 `AssertionError: / - secret 'pg-dsn' cannot be read at start-up / + timeout_s= is for tests; it is refused in pilot and prod` |
      3 `psycopg.ProgrammingError: missing "=" after "unused" in connection info string` |
      3 `AssertionError: / - secret 'pg-dsn' cannot be read at start-up / + llm= is for tests; configure backends.llm in pilot and prod` |
      3 `AssertionError: / - secret 'pg-dsn' cannot be read at start-up / + detector= is for tests; configure backends.detector in pilot and prod` |
      3 `AssertionError: / - secret 'pg-dsn' cannot be read at start-up / + clock= is for tests; it is refused in pilot and prod` |
      1 `hadavin_sdk.errors.ConfigError: secret 'fixture-token' cannot be read at start-up` |
      1 `KeyError: 'fixture-token'` |
      1 `AssertionError: timeout_s=0 was replaced by the configured timeout / assert 10.0 == 0.0 / +  where 10.0 = <hadavin_sdk.actions.executor.Executor object at 0x…>.timeout_s / [+1 more line; full report in element text]` |
      1 `AssertionError: a static Vault token was accepted (pilot, secrets, {}): '' / assert 'environment pilot: refused: secrets: vault auth token (the default; set auth: kubernetes or auth: approle)' in ''` |
      1 `AssertionError: a live build took a test object ('pilot'): "secret 'pg-dsn' cannot be read at start-up" / assert "secret 'pg-d...d at start-up" == 'channel= is ...ilot and prod' / - channel= is for tests; configure backends.channel in pilot and prod / + secret 'pg-dsn' cannot be read at start-up` |
```
The two positive pilot tests (new seam) on origin/main code: both `passed` (rows in the table).

## 4. The two positive pilot tests on the branch, with the database
`pytest -v -rs -p no:cacheprovider <the two ids>` -> exit 0:
```
tests/test_k3_pilot_env.py::test_k3_pilot_app_has_no_executor PASSED     [ 50%]
tests/test_k5_round8_postgres.py::test_the_app_deletes_evidence_only_through_the_purge_identity PASSED [100%]
============================== 2 passed in 31.26s ==============================
```

## 5. Mutants
`uv run --all-extras --group test python tests/stage_mutants.py` -> exit 0, wall 89 s. Last line: `39 of 39 good; problems: []`. All 39 rows: `mutant-rows.txt`. The two rows added by this branch:
```
ok  KILLED       M12a a live build takes a test object (app.py: the override refusal is switched off)  [test_pilot_and_prod_refuse_a_test_object_handed_to_build]
ok  KILLED       M12b a static Vault token is allowed in pilot and prod (config.py: the rule never matches)  [test_pilot_and_prod_refuse_a_static_vault_token]
```

## 6. Hostile probes
Script `probes.py` (copy beside this file), run on the branch without the DSN: exit 0, 188 output lines in `probes.txt`, verbatim (exception type and message, line breaks inside a message shown as `\n`, message cut at 700 characters). Pilot configs come from the test file's own `live_dir` / `vault_dir` helpers. Row counts by output text, no interpretation:
- (a) 18 rows (6 falsy objects + timeout_s 0, 0.0, False; pilot and prod): 18 x `ConfigError`, 0 x "no exception".
- (b) 60 rows (every ordered pair of two keywords, pilot and prod): 60 x `ConfigError`; message names secrets 20, channel 16, detector 12, llm 8, clock 4.
- (c) 4 rows (`clock=hadavin_sdk.app.now` and `hadavin_sdk.models.now`, same object): 4 x `ConfigError: clock= is for tests; it is refused in pilot and prod`.
- (d1) 12 rows, stage value put on the loaded config with model_copy, `build(channel=FakeChannel())`: 12 x `ConfigError: channel= is for tests; configure backends.channel in pilot and prod` (values 'Pilot', 'PROD', 'PILOT', 'Prod', ' pilot', 'pilot ', ' prod ', ' demo', 'demo ', 'Demo', 'DEMO', '\tdemo\n').
- (d2) and (d3) 12 rows each, the same values written in config.yaml, `load_config` and `build`: 24 x `ConfigError: 1 validation error for Config \n environment \n Input should be 'demo', 'pilot' or 'prod' [type=literal_error]`.
- (e1) 40 rows, pilot and prod, kinds vault and vault_transit: auth 'TOKEN', 'Token', ' token', 'token ' and yaml null -> 20 x `ConfigError ... validation error for VaultSettings / VaultTransitSettings ... auth: Input should be 'token', 'approle' or 'kubernetes'`; auth 'token' and auth left out -> 8 x `ConfigError ... environment <stage>: refused: <capability>: <kind> auth token (the default; set auth: kubernetes or auth: approle)`; kind in other case or with a trailing space -> 12 x `ConfigError: backend <capability>: unknown kind ...`.
- (e2) 16 rows: file leaves auth out + variable set (5 names x 2 stages) -> 10 x the "refused: secrets: vault auth token" ConfigError; file says `auth: kubernetes` + variable says token (3 names x 2 stages) -> 6 x "no exception", loaded auth printed as 'kubernetes'.
- (e3) 1 row: HADAVIN_CONFIG_DIR names the folder, HADAVIN_ENVIRONMENT=demo and HADAVIN_BACKENDS__SECRETS__AUTH=kubernetes set, file says pilot + Vault with auth left out -> the "environment pilot: refused: secrets: vault auth token" ConfigError.
- (ref) 1 row: see "Failures and items not run".
Total "no exception" rows: 6 (all in e2, listed above).

## 7. gitleaks
`gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..464dee14" <worktree>` -> exit 0, "1 commits scanned", "no leaks found".
`gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8a-1` -> exit 0, "scanned ~85712 bytes", "no leaks found" (run after RESULTS.md and the other four files were written; rerun after this line was added: see final report).

## Where the raw files are
`/home/user/build/evidence-raw/Q8a1-464dee1/`: full.log, full-junit.xml, failbefore.log, failbefore-junit.xml, pilot-two.log, negative-files.log, mutants.log, probes.log, ruff-check.log, ruff-format.log, bandit.log, scan-repo.log, gitleaks-git.log, gitleaks-dir.log, wait.log, pg-init.log, uv-sync.log.
