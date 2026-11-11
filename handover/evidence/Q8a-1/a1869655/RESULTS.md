# Q8a-1 evidence, round 8, head a18696556beacbf13664da0299cabf56d48d1ddf (previous 4ccb4f9a, base origin/main 2a8c2aac)
Runner: EVIDENCE RUNNER (records only; nothing fixed, nothing committed on the branch, nothing pushed). Detached worktree, own venv, own Postgres 16.15 (127.0.0.1, port 56733, run as the `postgres` OS user; stopped and deleted at the end). Raw logs outside the repo: /home/user/build/evidence-raw/q8a1-a1869655/. Marker in every probe is built from parts; none is written out here.

## Failures and not-run items (first)
1. FULL PYTEST AT THIS HEAD FAILS: `12 failed, 10973 passed, 1 skipped, 28 deselected in 294.40s`, rc 1 (heavy.sh, no queue wait). I re-ran the six files that held a failure alone with the server environment corrected (see item 2): `11 failed, 350 passed`. The 11 still failing (all assert the OLD error wording, the real text no longer matches):
   - tests/contracts/test_secrets.py::test_a_missing_name_is_a_config_error_at_the_start_up_probe x7 (aws_secrets_manager, azure_key_vault, env, fake, gcp_secret_manager, mounted_file, vault). Expects `'missing' cannot be read at start-up`; actual `secret missing cannot be read at start-up (ConfigError)` (`(KeyError)` for env).
   - tests/test_k3_pilot_env.py::test_k3_http_refused_in_pilot. Expects `executor http is not available in pilot or prod`; actual `chain c step 0: approver_ids entry 0 is not a person in principals.yaml`.
   - tests/test_p2_postgres.py::test_cli_limits_without_a_readable_dsn_is_a_config_error. Expects `'pg-dsn' cannot be read`; actual `refused: secret pg-dsn cannot be read at start-up (KeyError)`.
   - tests/test_s3_gate.py::test_bad_unknown_chain. Expects `unknown chain`; actual `action lookup_record: chain_id names no chain`.
   - tests/warden_port/test_audit_chain.py::test_audit_verify_that_cannot_build_its_store_could_not_verify. Expects `could not verify: secret 'pg-dsn' cannot be read`; actual `could not verify: secret pg-dsn cannot be read at start-up (KeyError)`.
   The same six files, unmodified, on origin/main src: `361 passed` (rc 0). Of the 11, only tests/test_k3_pilot_env.py is among the files the branch changed; the other four files are not in `git diff origin/main...HEAD`.
2. The 12th failure in the full run was tests/demo_askdata/test_validate_harm.py::...[dblink-connect]: my Postgres server was first started without PGHOST/PGPORT/PGUSER in the SERVER environment (my setup slip). I restarted the server with them (checked in /proc environ) and the file passes in the re-run. I did NOT repeat the whole 11000-test run after that; the full-run line above is the first run, with this one test failing for my own reason.
3. READABLE-MARKER PROBES: 7 results show the marker in the raised text, all from a marker typed as a lower-case plain id (agent id x2, action id x2, chain id x1, principal id x2; list in section Probes). The previous probe set (the 107 of 4ccb4f9a, same script) now gives 0 readable (was 8), 30 hidden-in-suppressed-context only (was 29).
4. NOT RUN: Python 3.12 CI job (this machine has 3.13 only); `pytest -m perf` (the ticket names no perf item); Vault-server tests needing HADAVIN_TEST_VAULT_ADDR (no Vault server here; the only skip is tests/contracts/test_llm.py:95); CI scanners semgrep, zizmor, pip-audit, trivy; `app.build` endpoint use of the URL fields (`app.py` source/LLM building) was not probed, only `load_config`, `load_registry`, `SourceConfig` and the settings classes. `uv sync --locked --no-build` not used (it fails for the editable project here); `uv sync --locked --all-extras --group test` (rc 0) was used.
5. The Decimal case: a validator that calls `Decimal(marker)` raises `decimal.InvalidOperation`, which pydantic does not turn into a validation error and `load_config` does not catch (not in its except list): it escapes `load_config` as the raw exception. Its text holds no marker (`[<class 'decimal.ConversionSyntax'>]`). Recorded as a fact (probe_decimal.py).

## Table
| item | command | exit | last line |
|---|---|---|---|
| full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (PG DSN set, HADAVIN_REQUIRE_PINNED_UNIDATA=1) | 1 | 12 failed, 10973 passed, 1 skipped, 28 deselected in 294.40s |
| re-run of the 6 failing files (PG env fixed) | same marker expression, 6 files | 1 | 11 failed, 350 passed in 24.85s |
| same 6 files on origin/main (untouched) | same | 0 | 361 passed in 25.36s |
| stage_mutants | `heavy.sh python tests/stage_mutants.py` (alone, after pytest) | 0 | 138 of 138 good; problems: [] ; KILLED lines 132, CRASH lines "ok" 4 (M17i, M17q, M17s, M17zb) |
| git status after mutants | `git status --short` | 0 | empty (clean) |
| diff | `git diff --name-only origin/main...HEAD` | 0 | 35 files (changed-files.txt) |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 321 files already formatted |
| bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only warnings (nosec B102 tools.py:398 with no failed test; "pinned"/"bytes" not test names) |
| scan_repo | `python tools/scan_repo.py` | 0 | no output beyond a uv warning |
| gitleaks | `gitleaks git --log-opts=2a8c2aac..HEAD` | 0 | no leaks found |
| probes | probe_new.py (own script, runs as an unprivileged user) | 0 | 260 probes, 239 error results; see below |
| fail-before | head test files (+conftest) overlaid on 4ccb4f9a and origin/main trees, each tree's own src (hadavin_sdk.__file__ confirmed per tree) | head 1 / 4ccb4f9a 1 / main 1 | head 811 passed 1 failed; 4ccb4f9a 729 passed 83 failed; origin/main 395 passed 417 failed |
| timing-harness flake | see below | | |

## Fail-before (12 changed test files in `git diff origin/main...HEAD -- tests`; stage_mutants.py is a script, not collected; 812 ids collected from the 11 pytest files at head; 351 of them also exist in the origin/main copies of the files, 461 are new ids)
| tree (own src) | new ids PASSED | new ids FAILED | existing ids PASSED | existing ids FAILED |
|---|---|---|---|---|
| head a1869655 | 461 | 0 | 350 | 1 (tests/test_k3_pilot_env.py::test_k3_http_refused_in_pilot, same one as in the full run) |
| 4ccb4f9a | 381 | 80 | 348 | 3 |
| origin/main 2a8c2aac | 60 | 401 | 335 | 16 |
New ids passing on 4ccb4f9a: 381 (92 distinct test functions; 224 of the 225 in tests/test_q8a_live_overrides.py, 157 of the 236 in tests/test_stage_names.py), listed by function in new-pass-on-4ccb4f9a-by-function.txt. New ids passing on origin/main: 60 (18 functions; 44 + 16), new-pass-on-main-by-function.txt. Per-test table: failbefore-per-test.tsv. The Q8a-1 test files for the ids are tests/test_q8a_live_overrides.py (225) and tests/test_stage_names.py (236).

## Probes (probe_old.py = the previous probe with the path changed; probe_new.py adds the round-8 probes; run as user `nobody`, so "no permission" is a real refusal)
Result counts by group (error results; "ok" = no error raised, not counted as results):
| group | clean | hidden (marker only in suppressed `__context__`) | readable |
|---|---|---|---|
| previous 107 probes | 74 | 30 | 0 |
| plain-id probes (new) | 7 | 0 | 7 |
| URL fields (new, 9 fields x 8 shapes) | 65 | 0 | 0 |
| configured read source `sources:` kubernetes (new) | 11 | 1 | 0 |
| egress.yaml (new) | 14 | 0 | 0 |
| unhashable YAML key (new) | 10 | 0 | 0 |
| OSError cases (new, temp path itself holds the marker) | 8 | 12 | 0 |
Readable rows (marker typed as a lower-case plain id, shape `a-z 0-9 - _ .`): `agent <marker>: scope_allowed entry 0 has no contract`; `agent <marker>: model_route is not one of the configured routes`; `action <marker>: target_system names no configured system`; `action <marker>: chain_id names no chain`; chain id (with unknown approver) in a `chain <marker> step 0 ...` line; `principal <marker>: approver_of entry 0 names no chain`; `principal <marker>: rights entry 0 names no action`. Not readable: duplicate ids (`duplicate id in entry N`), action id with a bad risk_class, ids where nothing else is wrong (no error).
URL fields probed (8 shapes each: ascii `user:marker@host`, `marker@host`, fullwidth brackets, fullwidth percent, fullwidth `@` and `:`, ascii percent, ascii `[marker]`, clean control): systems.base_url, openai_compat base_url, vault address, vault_transit address, azure_key_vault vault_url, azure_key_vault_key key_id, s3_object_lock endpoint_url, azure_immutable_blob account_url, slack api_base, plus `sources:` kubernetes api_url. Every raised error was a fixed sentence (`a URL must not contain a login`, `not a valid URL (plain ASCII host, no percent sign)`), marker 0 in str, repr, chain, traceback. No marker shape was accepted without an error in any of the 10 URL fields (the clean control row was accepted in 8 fields; for the two anchor kinds the control itself is refused by a separate rule, `needs backends.audit kind chain`, but the URL shapes are refused earlier at the settings level with the fixed sentences, so the probes are not masked). The direct class call `KubernetesSettings(api_url=...)` (not through load_config) gives a pydantic error whose own `str(e)` holds the URL (that class has no `hide_input_in_errors`); through load_config the text is the fixed sentence.
Tool call URL (`ToolContext.fetch`): `user:marker@host`, `marker@host`, fullwidth brackets, fullwidth percent, ascii percent, marker in path, backslash: fixed sentences, marker 0. Marker typed as the HOST (`https://<marker>/x`): READABLE, `host '<marker>' is not in this tool's manifest hosts`. Marker in port and bad ipv6: `the URL is not valid`, marker only in suppressed context. Tool-author-supplied `operation=` and `method=` values are echoed (`operation '<marker>' is not on the manifest's read list`), counted here as outside the configuration files.
egress.yaml: an extra plain key (no marker) raised no error at load_config or load_registry; the marker as an extra key: `<unknown key>` form, marker 0; 13 non-bare host shapes (scheme, path, login, port, space, fullwidth colon, upper case, percent, wildcard, fullwidth brackets, empty, int, nested list) and non-list/top-level-list/top-level-string: every error text has marker 0; the per-row outcome (error or accepted) is in probes-head.txt.
OSError: directory instead of file and no-permission (uid 65534): `config.yaml: cannot be read (IsADirectoryError|PermissionError)` at load_config, `a value was refused (<type>)` at load_registry for agents/principals/chains/actions; marker 0 in visible text, 12 hidden in context (the path, which holds the marker). Facts, not judgments: a symlink loop used as config.yaml or principals.yaml/chains.yaml/agents.yaml is read as an empty file (no OSError raised: `backends: audit, llm must be set`, `approver_ids entry 0 is not a person`, ...); a no-permission `actions/` folder gives no error at load_config and "no contract" at load_registry (read as empty); `tools/test-agent.yaml` as a directory raised nothing; a no-permission prompt file raised nothing at load_registry.
Unhashable YAML key (list used as a key, marker inside it): config.yaml, egress.yaml, agents.yaml, principals.yaml, chains.yaml, actions/lookup_record.yaml, tools/test-agent.yaml, nested under routes and backends, tuple-like mapping key: all error texts marker 0.
Validator in a module named `hadavin_sdk._x` (pydantic model, field validator): `int(marker)`, `float(marker)`, `bytes.fromhex(marker)`, plain `ValueError(marker)`, `ValueError(f"bad {marker!r}")`, a ValueError subclass, `AssertionError(marker)`: visible text `a value was refused (ValueError)` (or `assertion_error`), marker 0 through both `config_error_text` and `_validation_text`; the same through a real `load_config` (a backend kind with such a validator): `backends.secrets (xx): ... a value was refused (ValueError)`, marker only hidden in context. A `ConfigValueError` with a fixed sentence is shown as written; for contrast a `ConfigValueError(marker)` (an author slip) shows the marker (2 rows, expected by the class contract). `Decimal(marker)`: see item 5 above.
Unknown-value rows of the previous probe set: the 8 rows that were readable at 4ccb4f9a (`unknown model_route`, `no contract for`, `unknown system`, `unknown chain`, executor kind pydantic tag, `outside check_modules`, tools/<marker>.yaml file name, operation in tools manifest) now read `<not shown>` or the fixed sentences; per-row text in probes-head.txt.

## Direct URL parsing in src/ (grep, 50 lines, urlsplit-grep.txt)
Only direct `urlsplit` call: src/hadavin_sdk/safe_url.py:32. No `urlparse`, `urljoin`. Other `urllib.parse` imports: executor.py `quote`, gemini.py `quote`, kubernetes.py `quote`, runmap.py `unquote`, hmac_v0.py `parse_qs` (request body), tools.py `quote, quote_plus, urlunsplit` (urlunsplit builds from safe_urlsplit parts). Everything else goes through `safe_urlsplit` / `config_urlsplit`.

## Files here
RESULTS.md, probe_old.py, probe_new.py, probe_decimal.py, probes-head.txt, failbefore-per-test.tsv, new-pass-on-4ccb4f9a-by-function.txt, new-pass-on-main-by-function.txt, urlsplit-grep.txt, changed-files.txt, pytest-failures.txt.
