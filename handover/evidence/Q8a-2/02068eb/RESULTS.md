# Q8a-2 raw evidence, head 02068ebe718afac418f5402e1b4964c617f4ff04 (branch core/q8a-2-neutral-callback-and-guard)

EVIDENCE RUNNER record. Model: Fable 5.2 (claude-fable-5-2). Run 2026-11-11 about 14:50 to 15:08 UTC (20:20 to 20:38 IST).
This file records commands, exit codes and outputs. It holds no verdict. The builder's report, checkpoint and /home/user/build/q8a2-build were not read.

Trees: head worktree /home/user/build/EV-Q8a2-02068eb (02068ebe); origin/main 2a8c2aac; origin/core/q8a-1-live-override-refusals f6fad26f; commits fc77df07, ccb4eb57, 02068ebe.
Environment: venv /home/user/build/venv-evq8a2 (`uv sync --all-extras --group test`, rc 0, Python 3.13.18); own PostgreSQL 16.15 on 127.0.0.1:56150 (trust, socket dir /tmp, initdb -E UTF8 --locale=C.UTF-8); every test command ran under `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`.
Raw logs and JUnit XML: /home/user/build/evidence-raw/Q8a2-02068eb/ . Scripts: /home/user/build/ev-q8a2-scripts/ .

## Failures, non-zero exit codes and things not run (first)

1. Step 5c, exit code 1: the head's tests/test_lockin_guard.py on the source of the q8a-1 branch (f6fad26f): 14 failed, 108 passed. The two real-tree scans report 6 problem lines there (1 string, 5 names), listed below and in guard-on-q8a1-source.txt.
2. Step 5d, exit code 1: `git merge-tree` reports one conflicted file: CHANGELOG.md.
3. Step 3, exit code 1 (the fail-before run on main's source): 41 failed, 152 passed, 0 errors, 0 skipped. Nothing failed at import or collection.
4. Receiver probes (step 6), recorded without interpretation: on the fake kind `POST //channel/actions` returned 401, the same status as the right path; every other listed wrong path returned 404 (the empty path 400). Extra probes show `//`, `///`, `////` + the kind's own path return 401 on the head for both kinds and also on origin/main.
5. Hostile names (step 7): the scan returned an empty list for `import boto3 as awsclient`, `class AWSclient: pass` and `Slаck = 1` (Cyrillic a); it returned one line for each of the other seven.
6. Full suite: 0 failures, 0 errors, 1 skip. Because no test failed, no failing file was re-run on main (nothing to re-run).
7. Not run: the import scan (`import_problems`) on the hostile line `import boto3 as awsclient` (only the identifier scan and the string scan were called); CodeQL, SonarCloud, CodeRabbit (not local); mutation run of the Q8a-2 guard itself (the brief names only tests/stage_mutants.py); no live model call, no spend.
8. A slip of my own, corrected: my first merged-tree run (extra step 5e) exported only src, tests and pyproject.toml, so 3 tests failed on missing docs/ and demos/ files. Those two raw files are renamed `...partial-export-VOID...`; the run was repeated on a whole-tree export (431 passed, rc 0). My first hostile-names output mislabelled the Cyrillic letter's position; the script label was corrected and the run repeated (same scan results).

## 1. Full suite (head, with the Postgres DSN)

Command (through /home/user/build/heavy.sh, inside the head worktree):
`env -u ... timeout 2400 uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs`
Exit code 0. Queued 14:52:40Z, slot got 14:52:40Z (wait 0 s), ended 15:04:32Z, 712 s wall (pytest: 703.95 s). Load average at start 6.72 on 4 cores.
Counts from the XML: tests 10649, passed 10648, failures 0, errors 0, skipped 1.
Skip: `tests.contracts.test_llm::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses a malformed Converse shape before the kind sees it".
Worktree after the run: `git status --porcelain` 0 lines.

## 2. Lint and scans (head)

| command | exit code | seconds | last line |
|---|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | 1 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | 4 | severity: High 0, Medium 0, Low 12 (not shown at -ll); 0 issues printed; 3 skipped by specific `# nosec BXXX` |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | 2 | no output |
| `uv run --all-extras --group test python tests/stage_mutants.py` (heavy.sh) | 0 | 59 (slot wait 0 s; load 12.30 at start) | 37 of 37 good; problems: [] |

## 3. Fail-before: the head's three test files on origin/main's source

Clean main worktree (2a8c2aac, 0 dirty lines), overlay of ONLY tests/test_q8a2_callback.py, tests/test_lockin_guard.py, tests/contracts/test_capabilities.py from 02068ebe; `PYTHONPATH=<main>/src python -m pytest <the three files> -q -p no:cacheprovider -rfEs`.
Imported package printed: /home/user/build/EV-Q8a2-02068eb-main/src/hadavin_sdk/__init__.py .
Exit code 1, 29 s: 41 failed, 152 passed, 0 errors, 0 skipped. No import or collection error (grep of the log for "error collecting", "ImportError", "errors during collection": no hit). Worktree restored afterwards (0 dirty lines).
Failures by file: test_q8a2_callback.py 25 of 28 (the 3 that pass on main: `test_the_vendor_kind_keeps_its_path`, `test_a_near_miss_of_a_path_is_not_served[fake]`, `test_a_near_miss_of_a_path_is_not_served[slack]`); test_lockin_guard.py 14 of 122; contracts/test_capabilities.py 2 (`test_channel_names_its_callback_path[fake]`, `[slack]`).
Per-test table with the first assertion line of every failure: fail-before-on-main.md .

## 4. Each commit (detached worktrees, `PYTHONPATH=<worktree>/src`, the DSN variables set)

`python -m pytest tests/test_lockin_guard.py tests/test_p7_tick.py tests/test_q8a2_callback.py -q -p no:cacheprovider` and `ruff check --no-cache`.

| commit | pytest exit | counts (guard / p7_tick / q8a2_callback) | seconds | ruff check exit |
|---|---|---|---|---|
| fc77df07 | 0 | 125 passed (56 / 41 / 28) | 162 | 0 |
| ccb4eb57 | 0 | 125 passed (56 / 41 / 28) | 75 | 0 |
| 02068ebe | 0 | 191 passed (122 / 41 / 28) | 77 | 0 |

The guard file has 56 test functions on main and 80 on the head (122 test cases with parameters). each-commit.txt has the raw lines.

## 5. The guard against real trees

(a) Head, printed verbatim:
`literal_problems(SRC, VENDOR_MODULES, LITERAL_OK) -> 0 line(s): []`
`identifier_problems(SRC, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES) -> 0 line(s): []`

(b) Removal of each allow entry in turn. The branch's own tests, run with -v on the head, exit code 0, 14 passed: `test_each_new_literal_allowance_covers_exactly_its_own_hits[key0..key4]`, `test_every_name_allowance_is_checked_by_the_removal_test`, `test_each_name_allowance_covers_exactly_its_own_hit[key0..key4]`, `test_removing_one_name_from_the_pinned_table_set_reports_that_name` (plus the two real-tree tests). Lines in guard-removal-tests-head.txt.
The branch's literal removal test covers 5 of the 9 LITERAL_OK entries (the 5 this branch adds). My own loop removed all 9 LITERAL_OK entries, all 5 IDENTIFIER_OK entries and all 18 pinned table names one at a time and printed what the scans return: every removal printed at least one line, each naming the removed entry (guard-scans-head-and-removals.txt).

(c) The head's tests/test_lockin_guard.py on the q8a-1 source (f6fad26f = origin's newest head; only that file overlaid; imported package printed from the q8a-1 tree). pytest exit code 1: 14 failed, 108 passed. Problem lines of the two scans, verbatim:
```
hadavin_sdk.approvals.receiver:18: vendor word in a path or key in '/slack/actions'
hadavin_sdk.approvals.gate:102: vendor word 'slack' in the name '_SLACK'
hadavin_sdk.approvals.receiver:22: vendor word 'slack' in the name 'handle_slack_action'
hadavin_sdk.defaults:130: vendor word 'slack' in the name 'K8S_LOG_SLACK_BYTES'
hadavin_sdk.llm.openai_compat:35: vendor word 'openai' in the name '_OPENAI_ALIAS'
hadavin_sdk.runtime.tick:40: vendor word 'slack' in the name 'TICK_SLACK_S'
```
The 14 failing tests are the same 14 guard tests that fail on main in step 3. Table in guard-on-q8a1-source.txt.

(d) `git merge-tree --write-tree origin/core/q8a-1-live-override-refusals 02068ebe`: exit code 1; tree 95eaef065ea10f2076452daf823fc3909b7d4282; conflicted file names: CHANGELOG.md (the only one). Messages: "Auto-merging CHANGELOG.md", "CONFLICT (content): Merge conflict in CHANGELOG.md", "Auto-merging src/hadavin_sdk/runtime/tick.py".

(e) EXTRA, not in the brief: the whole merged tree 95eaef06 exported with `git archive` to the scratchpad (CHANGELOG.md keeps its conflict markers). Both scans printed `[]`. `pytest tests/test_lockin_guard.py tests/test_q8a2_callback.py tests/test_p7_tick.py tests/test_q8a_live_overrides.py tests/test_stage_names.py tests/contracts/test_capabilities.py`: exit code 0, 431 passed, 70 s. The full suite was NOT run on the merged tree.

## 6. Receiver probes (head, real loopback socket, `receiver.serve(..., port=0)`, server shut down and closed; thread not alive afterwards)

Requests were written to a raw socket so the request line is exactly as shown. "Bad signature" = well-formed signature headers made with `hmac_v0.sign` and a wrong secret; body `payload=x` (9 bytes).

| request | fake kind (callback_path /channel/actions) | Slack kind (callback_path /slack/actions) |
|---|---|---|
| POST `/channel/actions` | 401 | 404 |
| POST `/slack/actions` | 404 | 401 |
| POST `/channel/actions/` | 404 | 404 |
| POST `/CHANNEL/ACTIONS` | 404 | 404 |
| POST `/channel/actions?x=1` | 404 | 404 |
| POST `//channel/actions` | 401 | 404 |
| POST `/channel/../channel/actions` | 404 | 404 |
| POST `/channel/actions%2f` | 404 | 404 |
| POST with an empty path (request line `POST  HTTP/1.1`) | 400 "Bad HTTP/0.9 request type ('POST')" | 400 (same) |
| POST 70-character path (`/` + 69 `a`) | 404 | 404 |
| POST the kind's right path, body of 2,097,152 bytes | 413 | 413 |
| GET the kind's right path | 501 "Unsupported method ('GET')" | 501 |
| POST right path with no signature headers at all | 401 | 401 |

Extra probes, not in the brief (receiver-probes-extra-own-path.txt): the same near-miss forms built from each kind's OWN path, on the head and on origin/main. On the head, both kinds: `//path`, `///path`, `////path` -> 401; `path/`, upper case, `?x=1`, `#f`, `%2f`, `/x/..path`, absolute URL `http://127.0.0.1path`, leading backslash -> 404. A trailing space after the path -> 401 (the request line then simply holds the right path followed by two spaces). origin/main gives the same statuses for the same forms of `/slack/actions`.

## 7. Hostile names (identifier scan)

Temp copy of the neutral module approvals/receiver.py in the scratchpad (outside the repo), one line appended at a time (line 81), call `identifier_problems(tmp, VENDOR_MODULES, {}, frozenset())`. Baseline with no line added: `[]`. The real file was unchanged afterwards.

| line added | what the scan returned |
|---|---|
| `def handle_SLACK(): pass` | `["hadavin_sdk.approvals.receiver:81: vendor word 'slack' in the name 'handle_SLACK'"]` |
| `import boto3 as awsclient` | `[]` |
| `from x import slack` | `["hadavin_sdk.approvals.receiver:81: vendor word 'slack' in the name 'slack'"]` |
| `class AWSclient: pass` | `[]` |
| `gcs_bucket = 1` | `["hadavin_sdk.approvals.receiver:81: vendor word 'gcs' in the name 'gcs_bucket'"]` |
| `def f(aws_region=None): pass` | `["hadavin_sdk.approvals.receiver:81: vendor word 'aws' in the name 'aws_region'"]` |
| `Slаck = 1` (third character Cyrillic U+0430) | `[]` |
| `S3Uploader = 1` | `["hadavin_sdk.approvals.receiver:81: vendor word 's3' in the name 'S3Uploader'"]` |
| `slack2_url = 1` | `["hadavin_sdk.approvals.receiver:81: vendor word 'slack' in the name 'slack2_url'"]` |
| `x = dict(aws_key=1)` | `["hadavin_sdk.approvals.receiver:81: vendor word 'aws' in the name 'aws_key'"]` |

The string scan (`literal_problems`) returned `[]` for all ten lines. Verbatim output: hostile-names.txt .

## 8. gitleaks

`/home/user/build/bin/gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..02068ebe" /home/user/build/EV-Q8a2-02068eb`: exit code 0, "3 commits scanned", "no leaks found".
`/home/user/build/bin/gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8a-2/02068eb`: exit code 0, last line "3:06PM INF no leaks found"; run again after this file was complete: exit code 0, "no leaks found".

## Clean-up

Own Postgres stopped (pg_ctl stop rc=0; processes left for that data folder: 0) and its data folder removed. Worktrees removed with `git worktree remove` (no prune): EV-Q8a2-02068eb-main(rc=0,dirty=0) EV-Q8a2-02068eb-q8a1(rc=0,dirty=0) EV-Q8a2-02068eb-c1(rc=0,dirty=0) EV-Q8a2-02068eb-c2(rc=0,dirty=0) EV-Q8a2-02068eb(rc=0,dirty=0); my EV-Q8a2-02068eb* worktrees left in `git worktree list`: 0 (one worktree named EV-Q8a2, not started by me, appeared during the run and was left alone). Venv /home/user/build/venv-evq8a2 removed. Scratchpad copies removed. Processes of my scripts still running: 0. No commit, no push, no sub-agent, no process of anyone else touched. Main checkout /home/user/hadavin-sdk: only this evidence folder was added.

## Files in this folder

RESULTS.md; fail-before-on-main.md; each-commit.txt; guard-scans-head-and-removals.txt; guard-removal-tests-head.txt; guard-on-q8a1-source.txt; merge-tree-and-merged-scan.txt; receiver-probes.txt; receiver-probes-extra-own-path.txt; hostile-names.txt.
