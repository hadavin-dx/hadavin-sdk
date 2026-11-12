# EVIDENCE RUNNER results: Q8a-1 batch 10 (tag Q8a1b10), head f4acee28a4888ea2f2840ae611b7e793ac41a427

Recorded, not judged. Nothing was fixed, committed or pushed. No ticket file for Q8a-1 exists on disk; the lead's brief items (a) to (d) plus the common brief were the acceptance list. Raw logs: `/home/user/build/evidence-raw/Q8a1b10-f4acee28/` (outside the repo). Base main 2a8c2aac, previous head f0febfb6.

## Failed or not run (first)

1. `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` FAILED 6 of 6 runs (3 on head, 3 on main), each with `AssertionError: a quadratic function must be flagged` (`is_superlinear(...)` returned False), through the three slot locks, each run 0.6 s. Machine was shared with other agents' jobs. This is a plain failure, not an intermittent one, in this session (see table item 9).
2. Full pytest took four runs; only the last passed. Run 0 (my slip): my script started in the wrong folder, "no tests ran", exit 5. Run 1: 2 failed (`test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]` and `[copy-to-file]`), because my Postgres server did not have PGUSER in its own environment (dblink-connect: `role "nobody" does not exist`). Run 2: 1 failed (`[copy-to-file]`: server could not overwrite `/tmp/askdata_p2_copy.csv`, a file owned by another agent's postgres user; my server ran as user nobody). Run 3, server run as user postgres with PGHOST, PGPORT, PGUSER in the server environment: 11043 passed, 1 skipped, 28 deselected, exit 0. All four logs kept. The two failures were in my environment set-up, not in the code under test, but I did not run the head on a differently set-up server to prove it beyond run 3.
3. Fail-before on old code: two of the four changed or new test functions pass on f0febfb6 src (listed in item 7). Also 63 passing instances (listed in `new-tests-pass-on-main.txt`) of new test names pass on main src (most are tests of features that main lacks only in part).
4. Not run: ticket file (does not exist), perf run beyond item 9 (the brief names none), `pip-audit`, Semgrep, zizmor, Trivy, Python 3.12 job (not requested by the brief; the CI steps relevant to this package are the stage-rename mutants and the redaction perf step).
5. Not read, as instructed: `handover/evidence/Q8a-1/b10/` (builder notes).

## Table

| # | Item | Command (short) | Exit | Last line |
|---|------|-----------------|------|-----------|
| 1 | Files changed vs main | `git diff --name-only origin/main...HEAD` | 0 | 60 files (list: `diff-name-only.txt`); 20 under tests/ |
| 2a | ruff check | `ruff check src tests demos tools` | 0 | All checks passed! |
| 2b | ruff format | `ruff format --check src tests demos tools` | 0 | 321 files already formatted |
| 3 | bandit | `bandit -q -r src demos tools -ll` | 0 | only a warning: nosec (B102) with no failed test at tools.py:410 |
| 4a | repo scan | `python tools/scan_repo.py` | 0 | (empty output) |
| 4b | stage mutants (a), own worktree | `python tests/stage_mutants.py` via heavy.sh | 0 | `176 of 176 good; problems: []` (159 lines KILLED, 17 lines CRASH, all marked ok) |
| 4c | gitleaks on origin/main..HEAD | `gitleaks git --log-opts=origin/main..HEAD` | 0 | no leaks found |
| 5 | full pytest (run 3) | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh | 0 | `11043 passed, 1 skipped, 28 deselected in 262.60s`; the 1 skip: tests/contracts/test_llm.py:95 |
| 5 | runs 0, 1, 2 | same | 5, 1, 1 | see item 2 above |
| 6 | mutant runners in ci.yml | only `tests/stage_mutants.py` (see 4b) | 0 | 176 of 176 good |
| 7a | fail-before (b): 3 changed test files + stage_mutants.py onto f0febfb6 src | pytest tests/test_stage_names.py tests/test_p1b_backends.py | 1 | `3 failed, 406 passed in 6.62s` |
| 7b | same files onto origin/main src | same | 1 | `279 failed, 130 passed in 25.28s` |
| 7c | all 20 changed test files of the diff onto main src (common item 7) | pytest -rA those files | 1 | `493 failed, 585 passed in 42.20s` |
| 8 | probes (c) | see below | n/a | head: 0 marker hits; f0febfb6: 112 of 196 rows and 72 of 100 rows |
| 9 | timing flake alone, 3 slot locks | 3 x head, 3 x main | 1 each | `1 failed in 0.6x s` each |

## 7 Fail-before detail

Test functions changed between f0febfb6 and head (from `git diff`): 2 new, 1 renamed, 1 with a changed body or signature.
- On f0febfb6 src (all in tests/test_stage_names.py):
  - FAILED `test_a_configured_kubernetes_namespace_is_never_printed_only_its_position` (new)
  - FAILED `test_the_rules_problems_label_is_said_as_given_and_holds_no_namespace` (new)
  - FAILED `test_no_config_derived_name_is_put_in_a_message_outside_the_one_filter` (existing; its guard lists changed)
  - PASSED `test_the_platform_secret_probe_names_a_secret_by_position_and_never_by_name` (renamed from `..._shows_a_configured_name_and_hides_a_pasted_one`)
  - PASSED `test_every_secret_provider_says_no_name_for_a_plain_word_and_imports_no_name_filter` (body changed, same name)
- On main src: the same four names did not pass (they are in the 279 failures); the 63 new-name instances that pass on main are in `new-tests-pass-on-main.txt` (tests/test_k3_pilot_env.py 1, tests/test_q8a_live_overrides.py about 45, tests/test_stage_names.py about 17).
- `tests/stage_mutants.py` is not collected by pytest; it was copied with the tests and run separately (4b, on head).

## 8(c) Probe of my own (marker value written as `<made-up-value>`)

Marker built from parts at run time, secret-shaped, not a real literal. Configured Kubernetes namespace positions tried through `KubernetesSettings` then `KubernetesSource.probe_scope()` with a fake fetch: one entry; marker in entry 2 of 3; duplicate entries; 20 entries (marker last-but-ten); empty list; empty string entry; dict form `[{name: marker}]`; mixed string and dict; a bare string; a dict; an int and the marker. Rule kinds: write verb, wildcard verb, shell access (pods/exec), secrets read, malformed rule, clean. Answer shapes: plain rules; evaluationError text that contains the namespace; incomplete; no status; resourceNames that contain the namespace. Also a fetch that raises with the request body in its text, and `rules_problems()` called directly. Also the route `sources.scope_problems({"kubernetes": src}, inventory)` with and without an inventory entry, 100 rows. (`scope_problems` lives in `sources/__init__.py`, not in kubernetes.py.)
- Head f4acee28: 0 rows with the marker in any returned message, exception text or traceback text (196 rows direct, 100 rows through scope_problems). Settings with a dict, a bare string, an int or an empty list are refused by validation; none of those refusal texts holds the marker. An empty-string entry is accepted by settings.
- f0febfb6: 112 of 196 rows hold the marker (every row for the four accepted marker positions, each shown as "namespace <marker>: ..."); 72 of 100 rows through scope_problems.
- Probe scripts: `/home/user/build/EV-Q8a1b10-f4acee28/probe_c.py` and `probe_c2.py` (build folder, removed at the end; summary in `probe-summary.txt`).
- Scan of the whole src tree for messages that print a configured name (words namespace, ns, project, bucket, cluster, tenant, region and compound names containing them), head, hits recorded without judgement (raw: `7-scan-*.txt` in the raw folder):
  - f-string lines with such a variable: 11 in all:
    - actions/secrets_gcp.py:39 (`projects/{self.project_id}/secrets/{name}/versions/latest`)
    - llm/anthropic.py:32 and :33 (region in a URL)
    - sources/kubernetes.py:237 and :251 (`/namespaces/{ns}/...` in an API path)
    - store/migration_numbers.py:251 (`SET search_path TO "{schema}"`)
    - store/migrate.py:212 (`{role}: can CREATE in schema {schema}`)
    - backends/table.py:367, 379, 380, 394 (region or bucket in a host name)
  - `%s` or `.format()` lines with such a word: 0. String-concatenation lines near raise, log, problem or append: 0.
  - sources/ modules: kubernetes.py (the two API-path lines above), `__init__.py` and `kinds.py` (no hits).
  - Which of these lines end up in a message or only in a request path was not traced.

## 9 Timing flake (alone, all three slot locks)

Head f4acee28 runs 1, 3, 5 and main 2a8c2aac runs 2, 4, 6: all FAILED with `a quadratic function must be flagged`, 0.62 to 0.68 s each. Waited 738 s for the three slots before run 1.

## Set-up notes

- Postgres 16 (my own folder, port 56871) first ran as user nobody, then as user postgres (server environment PGHOST, PGPORT, PGUSER set); stopped and its folder deleted at the end.
- `uv sync --locked --all-extras --group test` WITHOUT --no-build: exit 0.
- Old-code and main worktrees reused the head's venv with `PYTHONPATH=<worktree>/src` (checked: `hadavin_sdk.__file__` pointed into the right worktree).
- Wait for heavy slots: the first full run waited about 11 minutes (including my slip); the timing runs waited 12 minutes. My own work time was about 45 minutes.
