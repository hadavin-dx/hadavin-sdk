# Evidence Q8a-1, head f0febfb66fa353521a87d4de5b389b29e50533e3 (tag Q8a1r9; evidence runner, records only)
Head confirmed equal, tree clean. origin/main = 2a8c2aac89f83dd0a45af0412563b59ff4fe5632. Raw logs: /home/user/build/evidence-raw/Q8a1r9-f0febfb6/.

## Failed or not run (first)
- Known flaky `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, alone with all 3 slot locks: FAILED on head 2 of 2 runs that ran (a third run waited 300 s for the locks and never started; a later rerun also FAILED, so 3 of 3 started runs failed) and FAILED on origin/main 3 of 3 (about 0.6 s each, "a quadratic function must be flagged"). It passed inside the full suite.
- Not run: the security-job steps of ci.yml (pip-audit, Semgrep, zizmor, stale-ignore check); the perf step (the ticket names no perf item); the Vault test (no Vault server, HADAVIN_TEST_VAULT_ADDR not set; those tests may skip, the only skip listed is test_llm.py:95).
- `uv sync --locked --no-build` fails here (editable project has no binary build); synced without --no-build.
- Fail-before runs include the changed test files only; tests that need a helper the old code lacks fail on old code (see lists).

## Table
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 changed files | git diff --name-only origin/main...HEAD / 18741c8c HEAD | 0 | 58 files vs main, 25 since 18741c8c (lists in raw dir) |
| 2 ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| 2 ruff format | ruff format --check src tests demos tools | 0 | 321 files already formatted |
| 3 bandit | bandit -q -r src demos tools -ll | 0 | only a nosec warning (tools.py:410) |
| 4 scan_repo | python tools/scan_repo.py | 0 | (no output) |
| 4 stage mutants | python tests/stage_mutants.py via heavy.sh, alone | 0 | 175 of 175 good; problems: [] |
| 4 gitleaks origin/main..HEAD | gitleaks git --log-opts origin/main..HEAD | 0 | no leaks found |
| 5 full pytest (own Postgres 16, port 56319) | pytest -p no:cacheprovider -q -m "not live and not perf" -rs via heavy.sh | 0 | 11041 passed, 1 skipped, 28 deselected in 269.20s |
| 6 fail-before on 18741c8c src | changed test files of the diff (7 files) | 1 | 38 failed, 486 passed |
| 6 fail-before on origin/main src | same files | 1 | 299 failed, 225 passed |
| 7 probe | probe.py (own script) | 0 | 83 scenarios, 2 hits (see below) |

Fail-before notes: new test functions added since 18741c8c: 13; one passes on the old code (test_the_guard_finds_each_way_of_printing_a_configured_name_and_a_stale_allowance). New test functions added since origin/main: 116; 5 pass on main code and 1 is mixed across parameters (lists in new-tests-passing-on-main.txt). Failed ids: failed-on-18741c8c.txt, failed-on-main.txt.

## Probe (item 7), probe.py and probe-output.txt here
Planted a plain lower-case word and a secret-shaped value (built from parts, not printed) in: get(name) of env, mounted_file (missing, `../`, absolute), cache, aws, azure, gcp, vault (invalid name, 404, 500, 200 without field, 200 HTML body); config `private_key_secret_name`, unknown signer field, mounted_file `dir` and `ttl_s`, other secrets-kind fields; golden case id and input_ref (missing file, `../`); action `verify_check`/`rollback` outside check_modules; 40-char, hex-run and secret-shaped agent ids (unknown route, unknown action, duplicate); tool manifest fields.
- Planted text found in message, traceback chain or log: 2 of 83 scenarios, both in my own artificial test class (`cache get(fetch raises ...: ARTIFICIAL)`, a subclass raising a message that holds the name). No product-code scenario showed it.
- Raw AWS (AccessDenied) and GCP (Forbidden) client errors propagate unchanged; my fakes put no name in them, so this says nothing about real ones. Azure other-HTTP error likewise propagates.
- `max_output_bytes: 0` shows as `tools/test-agent.yaml: invalid tool entry (max_output_bytes)` (field name shown, value not).
- 40-char, hex-run and secret-shaped agent ids print as `<not shown>` in these errors.
- 8 no-exception scenarios: config accepted values for aws region, gcp project_id, env prefix and a verify_check function name at load time (no error to inspect).
