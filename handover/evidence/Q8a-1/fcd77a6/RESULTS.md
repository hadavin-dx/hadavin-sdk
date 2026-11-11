# Q8a-1 independent evidence, head fcd77a683ab352cc7cd91e71b0fe22179ef8031b

EVIDENCE RUNNER record (model = Fable 5.2). Raw output only; this file does not judge. Date 2026-11-11, run from about 15:17 to 15:36 UTC (20:47 to 21:06 IST).
Branch `core/q8a-1-live-override-refusals`: three commits on `origin/main` = 2a8c2aac89f83dd0a45af0412563b59ff4fe5632 (464dee14, f6fad26f, then fcd77a68). Worktree `/home/user/build/EV-Q8a1-fcd77a6` (detached at the head; `git status --short` was empty before removal).
Every command ran with `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN -u VAULT_TOKEN -u VAULT_SECRET_ID` (section 6e sets the two Vault variables on purpose), venv `/home/user/build/venv-evq8a1c` (`uv sync --all-extras --group test`, exit 0).
Postgres: own 16 cluster as the postgres user (`initdb -E UTF8 --locale=C.UTF-8 -A trust`, exit 0), port 56170, listen 127.0.0.1, socket dir /tmp, PGHOST/PGPORT/PGUSER in the server's environment; tests had the same three plus `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56170/postgres`. The first two starts failed (exit 1, "could not bind IPv4 address 127.0.0.1: Address already in use"; no listener on 56170 was found, the port lies in the kernel's range for outgoing connections 32768-60999); the third start, a few seconds later, exit 0. Stopped at the end (`pg_ctl -m fast stop`, exit 0).
Not read: the builder's report, `/home/user/build/B-Q8a1-evidence`. Read: the ticket's "ERRATA rev 4", the earlier evidence folder `f6fad26` (its RESULTS.md as a layout, its helper scripts).

## Failures and items not run (first)
- **Full suite: NOT RUN (stopped in the queue by the lead; head superseded).** Attempt 1 asked for a heavy slot at 15:18:01 UTC and never got one (all three slots were held by other jobs); the waiting command was ended by a signal (exit 143) about 15 minutes later. The lead then wrote that it had stopped it because a new fix batch supersedes this head. Before that message reached the runner, the runner had started attempt 2 (asked 15:34:00, slot 15:34:30 UTC); the runner stopped it itself at 15:34:45 UTC after about 15 seconds. Its log shows about 97 result characters (one `s`), no summary line, no JUnit XML. So: no counts, no failure list, no skip list for the full suite on this head.
- **"Rerun each failing test's file on a clean origin/main worktree": NOT RUN** (no full-suite result to take failing tests from).
- **Mutants (`python tests/stage_mutants.py`): NOT RUN.** They were to start after the full suite, through the same slot wrapper; the lead's stop came first. No mutant row exists for this head.
- Fail-before base (a), origin/main: `tests/test_q8a_live_overrides.py` (123 tests on the head's file, counted on base (b)) does NOT import: `ImportError: cannot import name 'VaultConnection' from 'hadavin_sdk.backends.table'`. A file that fails at import shows nothing about its tests on that base. No helper line was added on either base.
- Fail-before base (a) took 183 s of wall clock for 114 results while no single test took over 1 s (the time is outside the test bodies; the machine load was 11 to 15 on 4 cores). Not looked into further.
- Section 6e, first run: 39.08 s; the same command with the runner's recorder plugin: 3.90 s. Not looked into further.
- Not done: CodeQL, SonarCloud, CodeRabbit (not in the brief).

## 1. Full suite
NOT RUN, see above. Raw: `full-meta-attempt1.txt`, `full-meta.txt`, `full.log` (the partial 15 seconds).

## 2. Lint and scanners (on the head)
| command | exit | last line / count |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | at the reported level: Medium 0, High 0 (Low 12, not shown at -ll) |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | no output from the tool (the log holds only uv's own deprecation warning) |

Lines ADDED by `git diff origin/main...fcd77a68` that contain `noqa`, `nosec`, `type: ignore` or `pragma: no cover`: **0** (`suppressions-added.txt` is empty).

## 3. Fail-before, two bases, each untouched
Same four files each time: `tests/test_k3_pilot_env.py tests/test_k5_round8_postgres.py tests/test_q8a_live_overrides.py tests/test_stage_names.py`, with `--continue-on-collection-errors`, with the database address, own venv per base (`hadavin_sdk.__file__` printed the base worktree's `src`). `tests/stage_mutants.py` was overlaid too (not a pytest file). 0 skipped in both runs. Every test with result and first error: `fail-before-per-test.md`; failures only: `fail-before-failures.txt`; grouped by first error text: `fail-before-groups.txt`.

Base (a): origin/main 2a8c2aac + the five files of `git diff --name-status origin/main fcd77a68 -- tests` (stage_mutants.py M, test_k3_pilot_env.py M, test_k5_round8_postgres.py M, test_q8a_live_overrides.py A, test_stage_names.py M).
Base (b): f6fad26f + the five files of `git diff --name-status f6fad26f fcd77a68 -- tests` (the same five names, all M).

| run | exit | last line | test_q8a_live_overrides.py | test_stage_names.py | test_k3_pilot_env.py | test_k5_round8_postgres.py |
|---|---|---|---|---|---|---|
| (a) origin/main | 1 | `5 failed, 108 passed, 1 error in 183.25s (0:03:03)` | whole file: collection error (ImportError, missing name `VaultConnection`) | 5 failed, 97 passed | 10 passed | 1 passed |
| (b) f6fad26f | 1 | `31 failed, 205 passed in 8.98s` | 29 failed, 94 passed (imports, collects) | 2 failed, 100 passed | 10 passed | 1 passed |

(a) origin/main, first assertion or error line of each failure:
```
ERROR   tests/test_q8a_live_overrides.py (collection): ImportError: cannot import name 'VaultConnection' from 'hadavin_sdk.backends.table'
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_test_object_handed_to_build :: AssertionError: a live build took a test object ('pilot'): "secret 'pg-dsn' cannot be read at start-up"
FAILURE test_stage_names::test_pilot_and_prod_refuse_sources_and_tools_handed_to_build :: AssertionError: a live build took sources= ('pilot', _FalsyDict of 1): "secret 'pg-dsn' cannot be read at start-up"
FAILURE test_stage_names::test_demo_refuses_a_timeout_that_is_out_of_range :: AssertionError: demo took timeout_s=0: ''
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_static_vault_token :: AssertionError: a static Vault token was accepted for secrets (pilot, {}): "secret 'pg-dsn' cannot be read at start-up"
FAILURE test_stage_names::test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick :: AssertionError: a live tick took a time handed to it ('pilot'): ''
```
(b) f6fad26f, 31 failures:
```
test_q8a_live_overrides::test_run_tick_refuses_a_given_step_list_outside_demo, 14 cases (pilot, prod, and the five values that are not a stage; each with one step and with an empty list): Failed: DID NOT RAISE ConfigError
test_q8a_live_overrides::test_demo_refuses_a_timeout_outside_the_range_or_of_another_type, 15 cases:
   3 cases [10**400], [3601], [3600.1]: Failed: DID NOT RAISE ConfigError
  12 cases [0], [0.0], [-1], [-0.5], [True], [False], [nan], [inf], ['5'], [[5]], [Decimal('2.5')], [Fraction(5, 2)]: a ConfigError WAS raised on the base, with the text
     "timeout_s= must be greater than 0"; the head's test asks for "timeout_s= must be an int or float between 0 (not included) and 3600"
test_stage_names::test_demo_refuses_a_timeout_that_is_out_of_range :: AssertionError: demo took timeout_s=0: 'timeout_s= must be greater than 0' (the test loops over 0, -1, inf, 3601, True and stops at the first mismatch)
test_stage_names::test_pilot_and_prod_refuse_a_time_or_a_step_list_handed_to_the_tick :: AssertionError: a live tick took a step list handed to it ('pilot'): '', ran ['recorded']
```
Timeout, value by value on three code versions (`timeout-three-versions.txt`, script `timeout_base.py`: `build(demo, timeout_s=x)` with nothing else changed). The full refused message seen on each:
- origin/main: none of the 22 values is refused. 0, 0.0 and False give `executor.timeout_s=10.0`; -1, -0.5, True, nan, inf, '5', [5], Decimal('2.5'), Fraction(5, 2), 10**400, 3601, 3600.1 are handed on as given.
- f6fad26f: 0, 0.0, -1, -0.5, True, False, nan, inf, '5', [5], Decimal('2.5'), Fraction(5, 2) -> `ConfigError: timeout_s= must be greater than 0`; 10**400, 3601, 3600.1 -> no exception, handed on as given.
- head: all 15 of those -> `ConfigError: timeout_s= must be an int or float between 0 (not included) and 3600`.
- 3, 0.001, 2.5, 3600, 3600.0, 1e-9, 5e-324: no exception and handed on as given, on all three.
The two positive pilot tests: passed on both bases (rows in the per-test file).

## 4. The two positive pilot tests on the head, with the database
`uv run --all-extras --group test pytest -v -rs -p no:cacheprovider <the two ids>` -> exit 0, wall 1 s, not skipped:
```
tests/test_k3_pilot_env.py::test_k3_pilot_app_has_no_executor PASSED     [ 50%]
tests/test_k5_round8_postgres.py::test_the_app_deletes_evidence_only_through_the_purge_identity PASSED [100%]
============================== 2 passed in 0.82s ===============================
```

## 5. Mutants
NOT RUN, see above.

## 6. Probes on the head
Script `probes.py` (copy beside this file), run on the head without the database variables: exit 0, 176 lines in `probes.txt`, verbatim (exception type and message, or "no exception" with what was returned; line breaks inside a message shown as `\n`). Apps: demo = `build` on the fixture config (`make_cfg` + `qualify`, `secrets=FakeSecretProvider`); pilot = the pilot config through the test file's `live_dir`, backends planted with `plant_test_backends` (in-memory store, fake channel, scripted model), as `test_a_live_build_with_no_test_keyword_is_not_refused` does; prod = the same with the stage copied to prod. Extra block: pilot the way the run_tick tests build it (`_demo_app_at`). Rows by output text, no interpretation:

(a) `run_tick(app, steps=...)`, a new app per row; "recording step" = a step of the runner that notes that it ran.
| steps= | demo | pilot | prod |
|---|---|---|---|
| `[]` | returned 0; no step ran; no tick state | `ConfigError: steps= is for tests; it is refused in pilot and prod` | same ConfigError |
| `[one recording step]` | returned 0; ran `['recorded']` | same ConfigError; recording step did not run | same |
| `tick.STEPS` (the module's own list) | returned 0; all six steps have a tick state | same ConfigError; no tick state | same |
| `()` | returned 0; no step ran | same ConfigError | same |
| `(one recording step,)` | returned 0; ran `['recorded']` | same ConfigError | same |
| generator of one recording step | returned 0; ran `['recorded']` | same ConfigError | same |
| `None` | returned 0; all six steps have a tick state | returned 0; all six steps have a tick state | returned 0; all six |
| falsy non-list object (`__bool__` False, iterates to one recording step) | returned 0; ran `['recorded']` | same ConfigError | same |
| extra `0` | `TypeError: 'int' object is not iterable` | same ConfigError | same |
| extra `False` | `TypeError: 'bool' object is not iterable` | same ConfigError | same |
| extra `''` | returned 0; no step ran | same ConfigError | same |

The extra pilot block (`_demo_app_at`) gives the pilot column again, row for row.

(b) both given, pilot app: `now=future, steps=[]`; `now=future, steps=[one recording step]`; `now=2020-01-01, steps=tick.STEPS` -> 3 x `ConfigError: now= is for tests; it is refused in pilot and prod` (the message names `now`). Reference rows: `now=None, steps=[]` -> the `steps=` message; `now=future, steps=None` -> the `now=` message. No step ran in any row.

(c) `tick.purge_evidence(tick.TickContext(app, <time>))` called by hand. The app has two in-memory stores (`app.purge_store is app.store`: False); the runner planted its own made-up rows in the one the purge uses: three tool calls (created today, 10 days ago, 100 days ago) and one redaction map for each of the three run ids. Retention in the config: 30 days, ceilings 400 days.
| app | time handed in | result | tool calls left | redaction maps left |
|---|---|---|---|---|
| pilot | today + 500 days | no exception; returned None | none | none |
| prod | today + 500 days | no exception; returned None | none | none |
| pilot | today + 31 days | no exception; returned None | none | none |
| prod | today + 31 days | no exception; returned None | none | none |
| pilot | today (reference) | no exception; returned None | today, 10d | today, 10d, 100d |
| prod | today (reference) | no exception; returned None | today, 10d | today, 10d, 100d |
| pilot | reference: `run_tick(app, now=today + 500 days)` | `ConfigError: now= is for tests; it is refused in pilot and prod` | all three | all three |

(d1) `build(..., timeout_s=x)` in demo. 0, -1, True, 3600.0000001, 3601, 10**400, inf, nan, Decimal("2.5"), Fraction(5, 2), "5" -> 11 x `ConfigError: timeout_s= must be an int or float between 0 (not included) and 3600`. 1e-9, 5e-324, 0.5, 3600 -> no exception, `executor.timeout_s` equals the value given (3600 stays an int). Not passed -> 10.0.

(d2) the same values as one line `executor_timeout_s: <text>` appended to a demo config.yaml, then `load_config`, then `build` with no keyword. YAML has no Decimal or Fraction; the texts used are in the table.
| value | yaml text | keyword `timeout_s=` (d1) | config field: `load_config` | then build: `executor.timeout_s` |
|---|---|---|---|---|
| 0 | `0` | refused | ConfigError: Input should be greater than 0 | |
| -1 | `-1` | refused | ConfigError: Input should be greater than 0 | |
| True | `true` | refused | accepted, 1.0 | 1.0 |
| 1e-9 | `1.0e-9` | accepted | accepted, 1e-09 | 1e-09 |
| 5e-324 | `5.0e-324` | accepted | accepted, 5e-324 | 5e-324 |
| 0.5 | `0.5` | accepted | accepted, 0.5 | 0.5 |
| 3600 | `3600` | accepted | accepted, 3600.0 | 3600.0 |
| 3600.0000001 | `3600.0000001` | refused | accepted, 3600.0000001 | 3600.0000001 |
| 3601 | `3601` | refused | accepted, 3601.0 | 3601.0 |
| 10**400 | 1 followed by 400 zeros | refused | ConfigError: Input should be a valid number | |
| inf | `.inf` | refused | accepted, inf | inf |
| nan | `.nan` | refused | ConfigError: Input should be greater than 0 | |
| Decimal("2.5") | `2.5` | refused | accepted, 2.5 (a float) | 2.5 |
| Fraction(5, 2) | `5/2` | refused | ConfigError: unable to parse string as a number | |
| "5" | `'5'` | refused | accepted, 5.0 | 5.0 |

Rows where the keyword is refused and the config field is accepted: True/`true`, 3600.0000001, 3601, inf/`.inf`, "5"/`'5'` (and `2.5`, which in YAML is a plain float, not a Decimal).

(e) Vault tests with both Vault variables SET to made-up values (built from parts in the shell of that one command, never printed) and `HTTPS_PROXY`, `HTTP_PROXY`, `https_proxy`, `http_proxy` = `http://127.0.0.1:9`, `NO_PROXY` unset, no database variables:
`pytest -v -rA -p no:cacheprovider -k "vault or Vault" tests/test_stage_names.py::test_pilot_and_prod_refuse_a_static_vault_token tests/test_q8a_live_overrides.py`
- as written: exit 0, `33 passed, 91 deselected in 39.08s` (1 test of test_stage_names.py, 32 of test_q8a_live_overrides.py). Lines of the output that hold "vault.example", "connection", "proxy", "127.0.0.1:9", "urlopen" or "socket": 0.
- again with the runner's plugin `ev_sockrec.py` (it writes one line for every `socket.connect`, `connect_ex` and `getaddrinfo` of the test process, and one line per test saying whether the two variables are set when the test body starts): exit 0, `33 passed, 91 deselected in 3.90s`. Connect or name-lookup lines: 0. The two variables at plugin load: both set. In the test body: `test_stage_names.py::test_pilot_and_prod_refuse_a_static_vault_token` both SET; the 32 tests of `test_q8a_live_overrides.py` both NOT set (that file's own fixture removes them for every test).
- The made-up values appear 0 times in the two logs and the recorder file (grep count).

## 7. gitleaks
`/home/user/build/bin/gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..fcd77a68" <worktree>` -> exit 0, "3 commits scanned", "scanned ~94048 bytes", "no leaks found".
`/home/user/build/bin/gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8a-1/fcd77a6` -> result in the runner's final report (run after this file was written; this file was not changed afterwards).

## Durations, slot waits, loads
Machine: 4 cores; load average 11 to 15 during the run, 6 at 15:34 UTC. Heavy-slot wait: attempt 1 waited from 15:18:01 UTC until it was stopped (about 15 minutes, no slot); attempt 2 waited 30 s. Fail-before (a) 184 s, (b) 11 s; probes under 1 minute; lint and scanners together under 2 minutes; the two pilot tests 1 s.

## Clean-up
Own Postgres stopped (exit 0) and its folder removed; the four worktrees (head, two fail-before bases, one unused clean origin/main) removed with `git worktree remove` (the two bases with `--force`: they held the overlaid test files and nothing else); the three venvs and the probe temp folder removed. The runner's own full-suite processes and its own watch loop were stopped by the runner; `pgrep` for the runner's paths: 0 processes. No process of anybody else was signalled. No commit, no push, no sub-agent, no paid call.

## Files
Here: RESULTS.md, fail-before-per-test.md, fail-before-failures.txt, fail-before-groups.txt, timeout-three-versions.txt, probes.txt, probes.py, timeout_base.py, ev_sockrec.py, suppressions-added.txt (empty). No mutant-rows file (not run).
Raw, `/home/user/build/evidence-raw/Q8a1-fcd77a6/`: full-meta-attempt1.txt, full-meta.txt, full.log (partial), fbmain.log / fbf6.log with their JUnit XML and file lists, fb-setup.log, timeout-*.log, pilot-two.log, probes.log, probes.err, vault-env.log, vault-env-rec.log, vault-env-sockets.txt, ruff-check.log, ruff-format.log, bandit.log, scan-repo.log, gitleaks-git.log, gitleaks-dir.log, pg-init.log, pg-start*.log, pg-stop.log, pg-server.log, uv-sync*.log, worktree-list-before-removal.txt and an `*-rc.txt` per command. Helper scripts: `/home/user/build/ev-q8a1c-scripts/`.
