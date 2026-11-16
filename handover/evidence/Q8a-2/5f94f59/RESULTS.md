# Q8a-2 round 2: independent raw evidence for head 5f94f5980306901e30c3acdc6a0c9c391f1339f4

EVIDENCE RUNNER record. It lists what was run and what came out. It holds no verdict; the reviewers judge.
Model: Fable 5.2. Date: 2026-11-11. Real clock: 15:31 to about 15:41 UTC (21:01 to 21:11 IST).
Branch `core/q8a-2-neutral-callback-and-guard`; previous head 02068ebe; new commits e5fbdae9 and 5f94f598.
Bases: origin/main = 2a8c2aac; origin/core/q8a-1-live-override-refusals = fcd77a68.
Not read: the builder's report, checkpoint, `/home/user/build/q8a2-build`, `/home/user/build/B-Q8a2-pr-notes.md`.
Every test command ran under `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN`.
Python 3.13.18, venv `/home/user/build/venv-evq8a2r2` (`uv sync --all-extras --group test`, exit 0). Own PostgreSQL 16.15 on 127.0.0.1:56151 (trust, `initdb -E UTF8 --locale=C.UTF-8`), `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56151/postgres`.
Raw logs and JUnit XML: `/home/user/build/evidence-raw/Q8a2-5f94f59/`. Scripts: `/home/user/build/ev-q8a2r2-scripts/`.

## Failures and things to read first

1. **Full suite exit code 1: 1 failed** of 10695. `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in`, `AssertionError: a quadratic function must be flagged` (line 836). The branch does not change this test file (`git diff --name-only origin/main...5f94f598` lists 14 files; this one is not among them).
   Re-runs (file `full-suite-failures-and-skips.txt`): whole file on clean origin/main: exit 1, `1 failed, 132 passed`; whole file on the head: exit 0, `133 passed`. The one test alone, three more times per tree: main failed, failed, passed; head failed, passed, failed. Machine load average during these runs was 3.9 to 4.9 on 4 cores.
2. **Head's guard test file against the Q8a-1 branch source (fcd77a68): exit 1, 20 failed, 138 passed** (step 5c, list below).
3. **`git merge-tree` of the Q8a-1 branch with the head: exit 1, one conflicted file: `CHANGELOG.md`** (step 5d).
4. Server tracebacks during the socket probes: 4 on the head and 4 on main (2 `AttributeError`, 2 `BrokenPipeError` on each). See step 6 for which request each belongs to.
5. Plants for which every scan returned an empty list (step 5e): `"slack|teams"`, `"slack teams"`, `"/pager-duty/hook"`, `global slack`, the decorator `@slack.hook`, the comment, the docstring. The import-rule scan returned an empty list for both `hadavin_sdk.approvals.slack*` imports (the name scan returned one line for each).

## Not run / not checked

- Slack channel kind with a real store and a correctly signed approval: not run (the real-store probe uses the `app` fixture of `tests/test_p7_tick.py`, which builds the fake channel kind only). The Slack kind was probed with the store set to `None`, as `tests/test_q8a2_callback.py` starts it.
- Mutation run: only `tests/stage_mutants.py` as the brief asked; no other mutation list was run.
- CI, CodeQL, SonarCloud, CodeRabbit: not looked at.
- No line of the diff was reviewed; nothing was fixed.

## 1. Full suite (once, through `/home/user/build/heavy.sh`)

`uv run --all-extras --group test pytest -q -p no:cacheprovider --junitxml=<raw>/full-junit.xml -rfEs` (inside `timeout 2400`).
Queued 15:31:32 UTC, slot received 15:31:32 (wait 0 s), ended 15:37:56, 384 s, **exit code 1**.
JUnit XML: tests=10695, failures=1, errors=0, skipped=1 (counted test cases: 10693 passed, 1 failed, 1 skipped). pytest line: `1 failed, 10693 passed, 1 skipped in 380.79s`.
- FAILED `tests/test_migration_numbers.py::test_the_timing_harness_flags_a_quadratic_stand_in` (see item 1 above).
- SKIPPED `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason given by the test: "Stubber refuses a malformed Converse shape before the kind sees it".

## 2. Lint, security scan, repository scan, mutants (cwd = head worktree)

| command | exit code | time | last line |
|---|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | <1 s | `All checks passed!` |
| `uv run --all-extras --group test ruff format --check` | 0 | <1 s | `323 files already formatted` |
| `uv run --with bandit bandit -ll -r src tools` | 0 | 1 s | `No issues identified.` (severity Medium: 0, High: 0) |
| `uv run --all-extras --group test python tools/scan_repo.py` | 0 | 1 s | (no output besides a uv warning) |
| `heavy.sh ... python tests/stage_mutants.py` | 0 | 52 s (queued 15:32:46, slot 15:33:36, wait 50 s) | `37 of 37 good; problems: []` |
| `git diff origin/main...5f94f598 \| grep -nE '^\+.*(noqa\|nosec\|type: ignore)'` | 1 (grep: no match) | | **0 hits** |

## 3. Fail-before on two bases

Only the head's `tests/test_q8a2_callback.py`, `tests/test_lockin_guard.py` and `tests/contracts/test_capabilities.py` were copied over a clean detached worktree of each base; `PYTHONPATH=<base>/src`; worktrees restored afterwards (`git status --porcelain` empty before and after).

| base | hadavin_sdk imported from | exit code | counts (XML) | import or collection errors |
|---|---|---|---|---|
| (a) origin/main 2a8c2aac | `/home/user/build/EV-Q8a2r2-main/src/hadavin_sdk/__init__.py` | 1 | 239 tests: 56 failed, 183 passed, 0 errors | none (0 lines) |
| (b) 02068ebe | `/home/user/build/EV-Q8a2r2-02068/src/hadavin_sdk/__init__.py` | 1 | 239 tests: 8 failed, 231 passed, 0 errors | none (0 lines) |

Per-test result with the first assertion line of every failure: `fail-before-main.md`, `fail-before-02068ebe.md`.
The 8 failures on 02068ebe: `test_the_refusal_names_the_class_when_the_channel_name_is_not_a_printable_word` ['', 'two\nlines', 'tab\there'] (3; "Regex pattern did not match"), `test_one_checker_holds_the_grammar_and_the_length_limit` (`assert None is not None`), `test_a_double_slash_in_front_of_the_path_is_not_served[fake]` and `[slack]` (`assert 401 == 404`), `tests/contracts/test_capabilities.py::test_channel_names_its_callback_path[fake]` and `[slack]` (`assert None is not None`). No test of `tests/test_lockin_guard.py` failed on 02068ebe.
The 56 failures on main: 34 in `test_q8a2_callback.py`, 20 in `test_lockin_guard.py`, 2 in `contracts/test_capabilities.py`.

## 4. Each new commit

`pytest tests/test_lockin_guard.py tests/test_p7_tick.py tests/test_q8a2_callback.py tests/contracts/test_capabilities.py -q -p no:cacheprovider` with `PYTHONPATH=<worktree>/src`, then `ruff check --no-cache` (file `each-commit.txt`).

| commit | pytest exit code | counts (XML) | time | ruff check exit code |
|---|---|---|---|---|
| e5fbdae9 | 0 | 244 passed, 0 failed, 0 skipped | 43 s | 0 (`All checks passed!`) |
| 5f94f598 | 0 | 280 passed, 0 failed, 0 skipped | 42 s | 0 (`All checks passed!`) |

## 5. The guard

(a) Real-tree scans on the head (file `guard-scan-head.txt`, which also lists what each scan prints when each allow entry is removed in turn):
- `literal_problems(SRC, VENDOR_MODULES, LITERAL_OK)` -> `[]`
- `identifier_problems(SRC, VENDOR_MODULES, IDENTIFIER_OK, TABLE_VENDOR_NAMES)` -> `[]`
- `import_problems(...)` -> `[]`; `vendor_module_problems(...)` -> `[]` (baseline lines of `guard-plants.txt`)

(b) The branch's own removal tests (file `guard-removal-tests.txt`): `pytest tests/test_lockin_guard.py -v -k "allowance or removing or removal or test_core_logic_names_no_vendor or test_core_names_no_vendor_in_identifiers or pinned or planted_in_the_real_receiver"`: exit 0, `24 passed, 134 deselected`. Names and counts: `test_every_allowance_is_checked_by_a_removal_test` (1), `test_each_literal_allowance_covers_exactly_its_own_hits` (10 cases), `test_each_name_allowance_covers_exactly_its_own_hit` (6 cases), `test_removing_one_name_from_the_pinned_table_set_reports_that_name` (1), `test_the_table_skip_is_the_pinned_set` (1), `test_a_vendor_path_or_name_planted_in_the_real_receiver_is_caught` (1), `test_core_logic_names_no_vendor` (1), `test_core_names_no_vendor_in_identifiers` (1), `test_plant_stale_literal_allowance_is_caught` (1), `test_a_module_name_allowance_does_not_allow_a_variable_of_that_name` (1). All 24 PASSED.

(c) Head's `tests/test_lockin_guard.py` copied over a clean worktree of origin/core/q8a-1-live-override-refusals (fcd77a68), `PYTHONPATH` to that tree. Scans (file `guard-scan-on-q8a1-source.txt`), every problem line:
```
hadavin_sdk.approvals.receiver:18: vendor word in a path or key in '/slack/actions'
hadavin_sdk.approvals.gate:102: vendor word 'slack' in the name '_SLACK'
hadavin_sdk.approvals.receiver:22: vendor word 'slack' in the name 'handle_slack_action'
hadavin_sdk.defaults:132: vendor word 'slack' in the name 'K8S_LOG_SLACK_BYTES'
hadavin_sdk.llm.openai_compat:35: vendor word 'openai' in the name '_OPENAI_ALIAS'
hadavin_sdk.runtime.tick:44: vendor word 'slack' in the name 'TICK_SLACK_S'
```
pytest on that file there: exit 1, `20 failed, 138 passed` (names in `guard-on-q8a1-failed-tests.txt`).

(d) `git merge-tree --write-tree origin/core/q8a-1-live-override-refusals 5f94f598`: **exit code 1**; conflicted file: `CHANGELOG.md` (only one). "Auto-merging" was also printed for `src/hadavin_sdk/defaults.py` and `src/hadavin_sdk/runtime/tick.py` without a conflict line (file `merge-tree.txt`).

(e) Plants, one at a time, in a temporary copy of the head's `src` outside the repository (the scan functions take a source root as first argument). Each text was appended to `hadavin_sdk/runtime/tick.py` (line 371 on). Full verbatim output: `guard-plants.txt`. `vendor_module_problems` returned `[]` for every plant. The last column is the receiver-only whole-word pattern (`_WHOLE_WORD`) applied to the planted text alone; that check exists only for `approvals/receiver.py`.

| # | planted text | import scan | literal scan | name scan | whole-word pattern |
|---|---|---|---|---|---|
| 1 | `from hadavin_sdk.approvals.slack import HEADER_PREFIX` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack'` | slack |
| 2 | `import hadavin_sdk.approvals.slack_channel as chat` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack_channel'` | slack |
| 3 | `import boto3 as awsclient` | `hadavin_sdk.runtime.tick: imports boto3 (vendor SDK) outside its allowed modules` | `[]` | `[]` | none |
| 4 | `pager_duty_key = 1` | `[]` | `[]` | `tick:371: vendor word 'pagerduty' in the name 'pager_duty_key'` | none |
| 5 | `x = "slack,teams"` | `[]` | `tick:371: vendor word in a path or key in 'slack,teams'` | `[]` | slack, teams |
| 6 | `x = "slack\|teams"` | `[]` | `[]` | `[]` | slack, teams |
| 7 | `x = "slack teams"` | `[]` | `[]` | `[]` | slack, teams |
| 8 | `x = "/pager-duty/hook"` | `[]` | `[]` | `[]` | none |
| 9 | `x = f"/sl{'ack'}/hook"` | `[]` | `tick:371: vendor word in a path or key in '/slack/hook'` | `[]` | none |
| 10 | `x = "/sl" "ack/hook"` | `[]` | `tick:371: vendor word in a path or key in '/slack/hook'` | `[]` | none |
| 11 | `x = "\x73lack"` | `[]` | `tick:371: bare vendor name in 'slack'` | `[]` | none |
| 12 | `x = b"slack"` | `[]` | `tick:371: bare vendor name in 'slack'` | `[]` | slack |
| 13 | `SLACK = 1` inside a nested function | `[]` | `[]` | `tick:373: vendor word 'slack' in the name 'SLACK'` | SLACK |
| 14 | `class C:  slack_url: str = ""` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack_url'` | slack |
| 15 | `def f(*, slack=None): pass` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack'` | slack |
| 16 | `lambda slack: 0` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack'` | slack |
| 17 | `for slack in (): pass` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack'` | slack |
| 18 | `with open(p) as slack: pass` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack'` | slack |
| 19 | `try: pass` / `except E as slack: pass` | `[]` | `[]` | `tick:373: vendor word 'slack' in the name 'slack'` | slack |
| 20 | `global slack` (inside a function, nothing else) | `[]` | `[]` | `[]` | slack |
| 21 | `@slack.hook` on `def h(): pass` | `[]` | `[]` | `[]` | slack |
| 22 | `obj.slack_token = 1` | `[]` | `[]` | `tick:371: vendor word 'slack' in the name 'slack_token'` | slack |
| 23 | `{"slack": 1}` | `[]` | `tick:371: bare vendor name in 'slack'` | `[]` | slack |
| 24 | `# slack` | `[]` | `[]` | `[]` | slack |
| 25 | a docstring `"""Slack is named here."""` | `[]` | `[]` | `[]` | Slack |

(`tick:` stands for `hadavin_sdk.runtime.tick:`.)

GCS plants in `hadavin_sdk/backends/table.py`:
- A, inside `class GcsRetentionLockSettings`, new line 189 `endpoint: str = "https://storage.googleapis.com"`: literal scan -> `hadavin_sdk.backends.table:189: host in 'https://storage.googleapis.com'`; import scan `[]`; name scan `[]`.
- B (A removed), new class at the end `class GcsOther(KindSettings):` with `gcs_bucket: str = ""`: name scan -> `hadavin_sdk.backends.table:607: vendor word 'gcs' in the name 'GcsOther'` and `hadavin_sdk.backends.table:608: vendor word 'gcs' in the name 'gcs_bucket'`; import scan `[]`; literal scan `[]`.
After each plant the file was restored and all four scans returned `[]` again; the temporary copy was deleted.

## 6. Receiver probes over a real loopback socket

Started as `tests/test_q8a2_callback.py` does: `receiver.serve(Approvals(None, None, None, channel, lambda *a: None), port=0)`, served in a thread, closed after. Raw sockets, request line sent exactly as shown. "Bad signature" = well-formed timestamp and signature headers made with a wrong secret, 9-byte body. Right path: head fake kind `/channel/actions`, head Slack kind `/slack/actions`; main has one path for both kinds, `/slack/actions`. `P` below is the right path of that row's column. Full output: `receiver-probes-head.txt`, `receiver-probes-main.txt`. Every answer line began `HTTP/1.0`.

| request line (bad signature) | head, fake kind | head, Slack kind | main, fake kind | main, Slack kind |
|---|---|---|---|---|
| `POST P HTTP/1.1` | 401 | 401 | 401 | 401 |
| `POST /P` (two slashes) | 404 | 404 | **401** | **401** |
| `POST //P` (three slashes) | 404 | 404 | **401** | **401** |
| `POST P/` | 404 | 404 | 404 | 404 |
| `POST P?x=1` | 404 | 404 | 404 | 404 |
| `POST P#f` | 404 | 404 | 404 | 404 |
| upper-case P | 404 | 404 | 404 | 404 |
| `%61` for the `a` of `actions` | 404 | 404 | 404 | 404 |
| `/x/../x/actions` form | 404 | 404 | 404 | 404 |
| `POST http://127.0.0.1P` (absolute form) | 404 | 404 | 404 | 404 |
| `POST http://evil.example/P` (absolute form, two slashes) | 404 | 404 | 404 | 404 |
| `POST * HTTP/1.1` | 404 | 404 | 404 | 404 |
| `POST  HTTP/1.1` (empty target) | 400 `Bad HTTP/0.9 request type ('POST')` | same | same | same |
| `POST P x HTTP/1.1` | 400 `Bad request syntax` | same | same | same |
| target of 70 characters | 404 | 404 | 404 | 404 |
| target of 9000 characters | 404 | 404 | 404 | 404 |
| NUL byte inside P | 404 | 404 | 404 | 404 |
| NUL byte after P | 404 | 404 | 404 | 404 |
| `POST<tab>P HTTP/1.1` | 401 | 401 | 401 | 401 |
| `POST P<tab>HTTP/1.1` | 401 | 401 | 401 | 401 |

The bold cells are the only rows where head and main differ (apart from the fake kind's path itself).

To the right path:

| request | head, fake | head, Slack | main, fake | main, Slack |
|---|---|---|---|---|
| correctly signed approval body (built like `tests/test_p7_tick.py::_callback`, made-up approval id), store `None` | connection closed, no status | same | same | same |
| body of 2 MB (Content-Length 2097152), bad signature | 413 | 413 (client send stopped: BrokenPipeError) | 413 (client send stopped: BrokenPipeError) | 413 (client send stopped: BrokenPipeError) |

The 2 MB row is from the saved (second) probe run. In the first run, whose output was overwritten, the client-side `BrokenPipeError` note appeared only in the main, fake-kind cell.
| Content-Length 5, body 9 bytes, bad signature | 401 | 401 | 401 | 401 |
| Content-Length 100, body 9 bytes, client timeout 3 s | no status, client timed out after 3.0 s | same | same | same |
| GET | 501 `Unsupported method ('GET')` | 501 | 501 | 501 |
| HEAD | 501 | 501 | 501 | 501 |
| PUT | 501 | 501 | 501 | 501 |

Signed approval with a real store (fake kind; `app` fixture, `_waiting` and `_callback` of `tests/test_p7_tick.py`, served with `receiver.serve(app.approvals, port=0)`; files `receiver-signed-approval-real-store-head.txt` and `-main.txt`):

| request | head (`/channel/actions`) | main (`/slack/actions`) |
|---|---|---|
| signed with the wrong secret | 401 | 401 |
| correctly signed, user who is not an approver | 200, request stays PENDING | 200, request stays PENDING |
| correctly signed approval by an approver | 200, request becomes APPROVED | 200, request becomes APPROVED |
| the same signed approval sent again | 200, APPROVED | 200, APPROVED |
| correctly signed approval, two slashes in front of the path | 404 | 200 |

Server stderr (file `receiver-probe-server-stderr.txt`, with the first 15 lines of each distinct traceback):
- Socket probes, head: 4 tracebacks. 2 x `AttributeError: 'NoneType' object has no attribute 'get_approval_request'` (client ports match the two "correctly signed approval, store None" requests). 2 x `BrokenPipeError: [Errno 32] Broken pipe` at `receiver.py` line 80 `self.wfile.write(out)` (client ports match the two "Content-Length 100, client timeout 3 s" requests).
- Socket probes, main: 4 tracebacks, the same two kinds, matched to the same two requests.
- Real-store probe: 0 tracebacks on head, 0 on main.
- Connections to a non-loopback address attempted by the probe process: 0 (a guard in the probe script counted them).

## 7. gitleaks

- `gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..5f94f598" /home/user/build/EV-Q8a2-5f94f59`: exit 0, `5 commits scanned`, `no leaks found`.
- `gitleaks dir --redact --no-banner --exit-code 0 /home/user/hadavin-sdk/handover/evidence/Q8a-2/5f94f59`: see the last line of this file.

## Clean-up

Stopped: own PostgreSQL on 56151 (data folder removed). Removed: worktrees `EV-Q8a2-5f94f59`, `EV-Q8a2r2-main`, `-02068`, `-e5fb`, `-q8a1`; venv `venv-evq8a2r2`; the temporary source copy. No process of another owner was touched. No commit, no push, no spend, no sub-agent.

## Files in this folder

`RESULTS.md`, `full-suite-failures-and-skips.txt`, `suppression-hits.txt`, `fail-before-main.md`, `fail-before-02068ebe.md`, `each-commit.txt`, `guard-scan-head.txt`, `guard-removal-tests.txt`, `guard-scan-on-q8a1-source.txt`, `guard-on-q8a1-failed-tests.txt`, `merge-tree.txt`, `guard-plants.txt`, `receiver-probes-head.txt`, `receiver-probes-main.txt`, `receiver-signed-approval-real-store-head.txt`, `receiver-signed-approval-real-store-main.txt`, `receiver-probe-server-stderr.txt`.

gitleaks dir on this folder (run 15:40 UTC, before this line was added): exit 0, `scanned ~129915 bytes`, `no leaks found`. Re-run after the last edit: see the final report.
