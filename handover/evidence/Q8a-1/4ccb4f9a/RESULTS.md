# Q8a-1 evidence, head 4ccb4f9a291972d8c791b31e5bb13d5bd7466cde (previous 3f3d4b6c, base origin/main 2a8c2aac)
Runner: EVIDENCE RUNNER (records only; nothing fixed, nothing committed on the branch). Detached worktree, own venv, own Postgres 16 (127.0.0.1, own port, stopped and deleted at the end). Python 3.13.18. Raw logs outside the repo: /home/user/build/evidence-raw/q8a1-4ccb4f9a/.

## Failures and not-run items (first)
1. HEAD HAS READABLE-MARKER RESULTS: 8 of 107 probe results show the made-up marker in the raised text (list below). All are registry-level "unknown name" messages (an identifier-shaped value is quoted back), plus one pydantic union-tag message. None came from a URL, YAML-syntax, or unknown-key probe.
2. 29 more probe results carry the marker only in the `__context__` of the raised error, with `__suppress_context__ = True` (so it is not in str, repr or the printed traceback, but `exc.__context__` holds the library error with the marker). Counted separately as "hidden".
3. 250 of the 285 new test ids (test ids not in the origin/main copies of the changed files) PASS on the previous head 3f3d4b6c; 47 pass on origin/main. 35 fail on 3f3d4b6c and 238 on origin/main (per-test table in failbefore-per-test.tsv).
4. NOT RUN: Python 3.12 CI job (this machine has 3.13.18 only); Performance step of CI (`pytest -m perf`, the ticket names no perf item); the flaky timing-harness test (item 9, no perf item); Vault-server tests needing HADAVIN_TEST_VAULT_ADDR (no Vault server here; the full run shows 1 skip only, in tests/contracts/test_llm.py:95); CI scanners semgrep, zizmor, pip-audit, trivy, stale-gitleaks step; app-build (`app.py` endpoint use) was not probed, only load_config, load_registry and the settings classes through load_config.
5. `uv sync --locked --no-build` (CI form) fails here (editable project has no binary distribution: rc 2); `uv sync --locked --all-extras --group test` was used instead (rc 0).

## Table
| item | command | exit | last line |
|---|---|---|---|
| diff | `git diff --name-only origin/main...HEAD` | 0 | 29 files (changed-files.txt) |
| ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| ruff format | `ruff format --check src tests demos tools` | 0 | 320 files already formatted |
| bandit | `uv run --with bandit bandit -q -r src demos tools -ll` | 0 | only 3 warnings (nosec B102 tools.py:394 with no failed test; "bytes is not a test name") |
| scan_repo | `python tools/scan_repo.py` | 0 | no output lines beyond a uv warning |
| gitleaks | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| full pytest | `heavy.sh pytest -p no:cacheprovider -q -m "not live and not perf" -rs` (PG DSN set, HADAVIN_REQUIRE_PINNED_UNIDATA=1) | 0 | 10807 passed, 1 skipped, 28 deselected in 258.90s |
| stage_mutants | `heavy.sh python tests/stage_mutants.py` (alone, after pytest) | 0 | 110 of 110 good; problems: [] ; worktree clean after |
| fail-before | head test files + conftest helper on 3f3d4b6c and origin/main trees (src from that tree) | head 0 / old1 1 / main 1 | head 543 passed; 3f3d4b6c 43 failed 500 passed; origin/main 251 failed 292 passed |
| probes | probe.py (107 probe results) | 0 | see below |
| urlsplit grep | `grep -rnE "urlsplit\|urlparse\|urlunsplit\|urllib.parse\|parse_qs\|urljoin" src/` | | see below |

Fail-before detail (new = test id not collected from the origin/main copy of the same files; 543 ids in head files, 260 existing, 285 new; the changed test files copied: all of `git diff` tests/ except stage_mutants.py, 10 files):
| tree | new PASSED | new FAILED | existing PASSED | existing FAILED |
|---|---|---|---|---|
| 3f3d4b6c (previous head) | 250 | 35 | 250 | 8 |
| origin/main | 47 | 238 | 245 | 13 |
New tests passing on 3f3d4b6c: 217 in tests/test_q8a_live_overrides.py, 33 in tests/test_stage_names.py (73 distinct test functions, see new-pass-on-3f3d4b6c-by-function.txt). New tests passing on origin/main: 44 and 3. src of each tree was confirmed loaded (hadavin_sdk.__file__ under that tree).

## Probes (probe.py, marker built from parts; config copied from tests/fixtures/config, each probe mutates one file)
Totals: 107 probe results: 55 clean, 29 hidden-in-suppressed-context-only, 8 readable (marker in str/repr/printed traceback), plus 15 results where the code raised nothing (listed in probes-head.txt as ok-no-error rows; 64 ok rows include "clean config + mutated other files" rows).
URL probes (config systems.base_url, backends.llm openai_compat base_url, backends.secrets vault address, 16 netloc shapes each: fullwidth @ and : (U+FF20, U+FF1A), fullwidth # / ? (U+FF03, U+FF0F, U+FF1F), small-form @ : # ? (U+FE6B, U+FE55), U+2100, U+2105, fullwidth brackets, unbalanced [ , bad ipv6, bad port, ascii login, fullwidth percent): every error raised was the fixed sentence ("not a valid URL" / "must not contain a login" / "must be https"), marker count 0 in str, repr, chain and traceback. Nothing raised (accepted without error) for: fullwidth brackets and fullwidth percent in all three fields, and an ascii login `user:<marker>@host` in openai_compat base_url and vault address (systems.base_url refuses it with "must not contain a login"). These accepted values are not echoed anywhere (no error).
Broken YAML (marker on the bad line) for config.yaml (2 shapes + duplicate key + alias + non-UTF-8 bytes + python tag), egress.yaml, agents.yaml, principals.yaml, chains.yaml, actions/lookup_record.yaml, tools/test-agent.yaml (2 shapes + non-UTF-8): the text is "not valid YAML (line N, column M)" only; marker 0 in str, repr and printed traceback. The raw YAML error does stay in `__context__` (suppress flag set) and holds the marker in the results marked hidden in probes-head.txt.
Unknown KEY marker in config.yaml, agents.yaml, principals.yaml, chains.yaml, actions/*.yaml, egress.yaml, tools/<agent>.yaml and nested (routes, backends, systems, backend settings, budget_usd, executor, chain step): text shows `<unknown key>`; marker 0 in visible text (hidden in context for the pydantic ones). egress.yaml with an extra key raised nothing.
READABLE (unknown VALUE, load_registry unless stated), raw text line:
1. agents.yaml model_route: `agent test-agent: unknown model_route <marker>` (str count 1, traceback 1)
2. agents.yaml scope_allowed name: `agent test-agent: no contract for <marker>`
3. actions target_system: `action lookup_record: unknown system <marker>`
4. actions chain_id: `action lookup_record: unknown chain <marker>`
5. actions executor kind: pydantic `Input tag '<marker>' found using 'kind' does not match any of the expected tags: 'none', 'manual', 'http'`
6. actions verify_check: `action lookup_record: <marker> is outside check_modules`
7. tools/<marker>.yaml (file name with no agent): `tools/<marker>.yaml: no agent <marker>` (marker twice)
8. tools/test-agent.yaml operations: `...tool t: operation <marker> is not on the read list of to...` (the same probe put the marker also in function, hosts, secret_names: those were not echoed)
Not readable: unknown values for status, data_class, risk_class, principal kind, tool side_effect, tool name pattern, environment, backend kind, route key (clean or accepted without error; see rows). Unknown values for tools_allowed, principals approver_of / rights, chains approver_ids, egress host, route key were accepted without any error at load_registry.

## Direct URL parsing in src/ (grep, 43 lines in urlsplit-grep.txt; .pyc matches removed)
Only direct `urlsplit` call: src/hadavin_sdk/safe_url.py:25 (inside safe_urlsplit, wrapped, `from None`). No `urlparse`, `urljoin` anywhere in src/. Other urllib.parse imports: executor.py:16 `quote`, gemini.py:15 `quote`, kubernetes.py:17 `quote`, runmap.py:22 `unquote`, hmac_v0.py:15 `parse_qs` (line 68, parses a request body, not a configured URL), tools.py:38 `quote, quote_plus, urlunsplit` (urlunsplit at tools.py:605 builds from the parts returned by safe_urlsplit at tools.py:573). Every other URL split goes through safe_urlsplit (config.py:185,194; secrets_vault.py:67; llm/common.py:263; llm/openai_compat.py:49; backends/table.py several; app.py:398,449; guard/egress.py:28; tools.py:573).

Files here: RESULTS.md, probes-head.txt (full probe output), probe.py (my own script), failbefore-per-test.tsv, new-pass-on-3f3d4b6c-by-function.txt, urlsplit-grep.txt, changed-files.txt.
