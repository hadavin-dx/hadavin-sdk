# Q8a-2 independent raw evidence for head f6c2a3d9198defbee2d01ee4979a5d6e75607c8a (fix batch 2)

EVIDENCE RUNNER record: it lists what was run and what came out. It holds no verdict; the reviewers judge.
Date 2026-11-11, real clock about 16:21 to 16:40 UTC (21:51 to 22:10 IST). Model: Sonnet 5.5.
Branch `core/q8a-2-neutral-callback-and-guard`; origin/main = 2a8c2aac. Clean worktree `/home/user/build/EV-Q8a2-f6c2a3d`, venv `/home/user/build/venv-evq8a2`, own PostgreSQL 16 on 127.0.0.1:56277 (stopped at the end).
Every test command ran under `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN -u VAULT_TOKEN -u VAULT_SECRET_ID`.
Not read: nothing of the builder's notes was copied; the notes were read only for the commands. No line of the diff was reviewed; nothing was fixed. Raw files in this folder; scripts in `scripts/`.

## Read first: failures and things that did not go as planned

1. **Full suite exit 1: 1 failed** of 10768 (`1 failed, 10766 passed, 1 skipped, 28 deselected`): `tests/demo_askdata/test_validate_harm.py::test_reading_attack_does_harm_unvalidated_and_is_refused_when_validated[dblink-connect]`, `psycopg.errors.SqlclientUnableToEstablishSqlconnection ... socket "/var/run/postgresql/.s.PGSQL.5432" failed`. The attack SQL (`dblink_connect('dbname=postgres')`) connects from inside the server, which looked at the default socket and port; I had started my PostgreSQL without `PGHOST`/`PGPORT` in the SERVER's own environment. The file is not in the branch diff (14 files, none under tests/demo_askdata). After restarting my PostgreSQL with `PGHOST=127.0.0.1 PGPORT=56277` in its environment, the whole file: exit 0, `253 passed in 28.29s` (`rerun-askdata-validate-harm.log`). So the full-suite run itself has one failure, caused by my set-up; the re-run is of that one file only, not a second full suite.
2. Step 5, `tests/test_p7_tick.py` on origin/main does not import: `ImportError: cannot import name 'handle_action' from hadavin_sdk.approvals.receiver` (collection error, exit 2, 0 tests ran; run A). So fail-before was recorded on the other three files (run B).
3. Step 6: server stderr is not empty in every fault case. Each fault inside the click handler gives exactly one line `a request ended with an error: AttributeError` (no traceback; 0 lines of the word `Traceback` in `step6-server-stderr.txt`). A client reset right after sending a correctly signed click gives one line `a request ended with an error: ConnectionResetError while handling AttributeError` (logged at ERROR level, not DEBUG).
4. Step 7: 4 plants gave an empty result from every scan: `# slack` (comment), a docstring naming Slack, and the SQL comments `-- slack` and `/* slack */` (see `step7-summary.txt`).
5. Step 8, variant A (serial opening of the 50 connections) measured the server's accept queue more than the load: opening 50 connections took 7.2 s (200 took 30.7 s), so connections opened early were already closed by the 10 s bound before the last were open. Variant B (parallel opening) is the cleaner run. Raw files of both kept.
6. Machine load average was 3.9 to 5.9 on 4 cores during all runs (other agents on the machine), so timings are not quiet-machine numbers.

## Results table

| # | command | exit | one-line result | file |
|---|---|---|---|---|
| 1 | `git rev-parse HEAD` in the worktree; `git status --porcelain` | 0 | `f6c2a3d9198defbee2d01ee4979a5d6e75607c8a`, clean | `step1-head.txt` |
| 2 | `heavy.sh ... pytest -q -p no:cacheprovider -m "not live and not perf"` (once, 398 s, slot wait 0 s) | **1** | 1 failed, 10766 passed, 1 skipped, 28 deselected (junit: tests=10768, failures=1, errors=0, skipped=1); the failure is item 1 above; skipped: `tests/contracts/test_llm.py::test_a_malformed_answer_is_a_provider_error[bedrock]` | `full.log`, `full-junit.xml`, `full-meta.txt` |
| 2b | re-run of `tests/demo_askdata/test_validate_harm.py` after restarting PostgreSQL with `PGHOST`/`PGPORT` in its environment | 0 | 253 passed in 28.29 s | `rerun-askdata-validate-harm.log` |
| 3a | `ruff check` | 0 | All checks passed! | `ruff-check.log` |
| 3b | `ruff format --check` | 0 | 323 files already formatted | `ruff-format.log` |
| 3c | `uv run --with bandit bandit -ll -r src tools` | 0 | No issues identified (Medium 0, High 0 at the -ll level) | `bandit.log` |
| 3d | `python tools/scan_repo.py` | 0 | no output | `scan-repo.log` |
| 3e | `git diff origin/main...f6c2a3d9 \| grep -nE '^\+.*(noqa\|nosec\|type: ignore)'` | 1 (no match) | 0 hits | `suppress-hits.txt` |
| 3f | `gitleaks detect --log-opts="origin/main..HEAD"` (v8.30.1) | 0 | no leaks found | `gitleaks.log` |
| 4 | `heavy.sh ... python tests/stage_mutants.py` (35 s, slot wait 5 min 41 s) | 0 | `37 of 37 good; problems: []` | `stage-mutants.log`, `mut-meta.txt` |
| 5 | fail-before: head's `tests/test_q8a2_callback.py`, `tests/test_lockin_guard.py`, `tests/contracts/test_capabilities.py` over a clean origin/main (2a8c2aac) worktree, `PYTHONPATH` = that `src` (imported from `/home/user/build/EV-Q8a2f-main/src/hadavin_sdk/__init__.py`) | 1 | **94 failed, 246 passed**: callback 63 failed / 9 passed; lockin guard 29 failed / 196 passed; capabilities 2 failed / 41 passed; no collection error. Worktree restored (dirty-after 0) | `step5-main-B-3files-pytest.log`, `step5-main-junit.xml`, `step5-main-table.md`, `step5-meta.txt` |
| 5a | same with `tests/test_p7_tick.py` added | 2 | collection ImportError on main (see item 2); 0 tests ran | `step5-main-A-4files-pytest.log` |
| 6 | hostile inputs, in-process receiver on loopback, fake signer, two kinds (fake, slack), `read_timeout_s=2.0` | 0 | see section 6 | `step6-hostile.txt`, `step6-server-stderr.txt` |
| 7 | guard plants (36 plants + 2 GCS table plants + 6 SQL plants) into a temp copy of `src` | 0 | 4 all-empty results (item 4), all others reported by at least one scan | `step7-plants.txt`, `step7-summary.txt` |
| 8 | 50 held connections, fast requests timed, default `read_timeout_s` 10 s | 0 | see section 8 | `step8-load-B-parallel-open.txt`, `step8-load-A-serial-open.txt` |

## 6. Hostile inputs (summary of `step6-hostile.txt`; both kinds gave the same status for every case; bad signature unless said)

- Content-Length at the right path: empty 400; header twice (9 and 9, and 9 and 5) 400; 12 digits 413; 13, 4000, 4301, 10000 digits 413; `-5`, `+5`, `+9` 400; Arabic-Indic and fullwidth digit 400; latin-1 superscript two 400; `0x10`, `0x9`, `1_0`, `9.0`, `1e1` 400; `9 ` (trailing space) 400; ` 9` (leading space) 401; `0` 401; `0009` 401; no header 401; 65537 413; 65536 with 9 bytes sent: no answer, connection closed after 2.0 s.
- The same first 13 forms at the wrong path `/nope`: 404 for every one.
- Slow first line, slow headers, slow body (1 byte per 0.5 s), short body (CL 100, 9 sent), connect and send nothing: no status, connection closed by the server at the bound (client saw the close at 2.0 to 3.0 s; "nothing sent" 2.41 s); 0 stderr lines for each.
- Reset (RST) mid-headers, mid-body, right after a whole bad-signature request: 0 stderr lines each; right after a correctly signed request: 1 stderr line (item 3).
- Headers: 99, 100, 101, 200, 5000 extra headers: 431 "Too many headers"; one header value of 70000 bytes: 431; request line of 70000 bytes: 414.
- Request line: tab, vertical tab, 0x1C, two spaces, latin-1 no-break space between the words: 401 (reached the signature check). Doubled slash path, tripled slash path, percent-encoded first letter, percent-encoded slash, query, trailing slash, absolute form: 404. No version: 400. Lower-case method: 501. Extra word after the path: 400.
- Failure inside the handler (correctly signed click, store None): 500 both times; 1 stderr line each, no traceback. 70000-byte body, correct signature: 413. GET and PUT: 501.
- str-subclass path (`__eq__` always True) and a plain str subclass as a channel's `callback_path`: `serve()` raised `ConfigError` for both (not started).
- Non-loopback connections attempted: 0. Threads alive at the end: MainThread only. Server stderr total: 6 lines, 0 of them tracebacks.

## 8. Slow connections (variant B, parallel opening, default bound 10 s; fast request = correctly signed click from a non-approver (200) and a wrong-signature click (401), real store via `tests/test_p7_tick.py` fixtures)

Baseline (no slow connection, first batch; machine busy): signed median 11.8 ms (max 29.7), bad-sig median 4.1 ms. Later batches with 50 held connections, medians: silent 1.6 to 2.7 ms (signed) and 0.5 to 0.7 ms (bad-sig); short body 2.0 to 2.4 / 0.5 to 0.7; partial first line 1.5 to 3.4 / 0.5 to 0.8. Every fast request answered with the expected status (200 or 401), none failed. Largest single value: 1017.7 ms (one signed request in the short-body case, at +1.0 s while the 50 connections were being opened). 200 silent connections held: signed median 2.0 ms, bad-sig 0.8 ms. After the 10 s bound (+2 s): 50 of 50 held connections closed by the server in each of the three patterns; server threads back to 3 (the test's own). Variant A (serial opening): 42, 46 and 40 of 50 closed at the check, the rest had been opened later; see item 5.

## NOT RUN

- A real-store signed approval over the socket for the Slack kind (the real-store fixture builds the fake kind only); the Slack kind was probed with store None.
- A second full-suite run (not asked for; item 1 explains the one failure).
- The merge with `core/q8a-1-live-override-refusals` and the head's guard on that branch's source (not in this brief's list).
- CI, CodeQL, SonarCloud, CodeRabbit: not looked at. Timing/perf tests (`-m perf`) were deselected as the brief says.
