# Raw evidence, pull request 89, head 7a2eb4cc418f09e4cf2a5996b8c46ef765a8cacd (PARTIAL: stopped by lead order)

EVIDENCE RUNNER record. It lists what was run and what came out. It holds no verdict. Model: Fable 5.2. Run as root (uid 0) on Linux, Python 3.13.18.
Times are UTC (IST = UTC + 5:30). Work started 2026-11-11 15:52:52 UTC (21:22:52 IST); stopped by lead order about 16:19 UTC (21:49 IST), 27 minutes of real clock.
Raw logs and XML: `/home/user/build/evidence-raw/P89-7a2eb4c/`. Instruments: `/home/user/build/ev-p89r21-scripts/`.

## NOT RUN or NOT FINISHED (read this first)

1. **Whole mutant list (`python tests/mutation_runner_mutants.py`): NOT FINISHED.** It waited 16 min 1 s for a heavy slot (queued 16:01:24, started 16:17:25) and was stopped by lead order after about 2 minutes. No exit code of its own exists (the runner got SIGTERM). 26 mutant rows were printed before the stop: 26 "ok", 0 "BAD" (`mutants-partial-rows.txt`). The list has about 250 entries; the other rows were never run. This is no result for the list.
2. **`python tests/stage_mutants.py`: NOT RUN** (it was queued behind item 1).
3. **gitleaks on this evidence folder**: run after this file was written; see the last section.
4. Step 1 "rerun each failing test's file": not applicable, the full suite had no failing test. No clean origin/main worktree was made.
5. The perf job of CI (`pytest -m perf`) was not run (the brief asked for the main selection once).
6. Leak probes not done: no probe with a secret in the mutant NAME; no search for pieces of a password other than the forms in the table (a longest-common-piece count is given below); the JUnit `system-out` field was tested only through a JUnit file that the child test overwrote itself (pytest does not write that field with the tool's empty configuration).
7. Address probes: bytes, None and NUL values cannot be put into a real environment; they were simulated by swapping the tool's `os.environ` for a plain dictionary inside the calling process. No real database connection was made in any probe (the child tests do not connect), so what the database library would do with an accepted address was not observed.
8. Lock probes ran on Linux only; nothing was run on Windows or macOS.
9. One side effect of my own probe: lock case `U-T` (tool run as the postgres user with a read-only TMPDIR) made `/tmp/hadavin_mutation_locks_102` outside the case folder. I removed it afterwards.
10. After the stop, two child processes of the stopped mutant run were still alive (a pytest started in its own session by a killer test, and its `sleep 600` child, process group 14198). I ended them and removed their two temp folders (`/tmp/mutant_ini_czsm2_ty`, `/tmp/mutants_iua0ygw7`).

## Setup

| step | command | exit code |
|---|---|---|
| fetch | `git fetch origin core/mutation-runner-keywords main` | 0 |
| worktree | `git worktree add --detach /home/user/build/EV-P89-7a2eb4c 7a2eb4cc...` (HEAD checked: 7a2eb4cc418f09e4cf2a5996b8c46ef765a8cacd; origin/main = 2a8c2aac) | 0 |
| venv | `UV_PROJECT_ENVIRONMENT=/home/user/build/venv-evp89r21 uv sync --all-extras --group test` (1.0 s) | 0 |
| Postgres | own cluster 16.15, `initdb -E UTF8 --locale=C.UTF-8 -A trust`, port 56131, `listen_addresses=127.0.0.1`, socket folder /tmp, PGHOST/PGPORT/PGUSER in the server's environment. Note: `pg_hba.conf` from `initdb -A trust` also holds trust lines for the local socket and ::1; the server listened on 127.0.0.1 only. Stopped at the end (`pg_ctl stop`, exit 0). | 0 |

Every test command ran with `env -u AWS_ACCESS_KEY_ID -u AWS_SECRET_ACCESS_KEY -u AWS_CA_BUNDLE -u ANTHROPIC_BASE_URL -u GH_TOKEN -u GITHUB_TOKEN -u CLOUDSDK_AUTH_ACCESS_TOKEN` and `HADAVIN_TEST_PG_DSN=postgresql://postgres@127.0.0.1:56131/postgres`.

## 1. Full suite (once, through heavy.sh)

Command: `/home/user/build/heavy.sh ... uv run --all-extras --group test pytest -q -p no:cacheprovider -m "not live and not perf" --junitxml=full.xml -rfEs`
Marker selection copied from `.github/workflows/ci.yml` line 92 (`pytest -q -m "not live and not perf" -rs`).
Wait for a slot: 0 s. Start 15:53:23, end 16:04:29. pytest's own exit code: **0** (heavy.sh exit 0).
pytest summary line: `10742 passed, 1 skipped, 28 deselected in 660.66s (0:11:00)`.
Counts from the XML: tests 10743, failures 0, errors 0, skipped 1.
Skip: `tests.contracts.test_llm::test_a_malformed_answer_is_a_provider_error[bedrock]`, reason "Stubber refuses a malformed Converse shape before the kind sees it".
Failures: none. Load note: other sessions' heavy jobs and, from 15:57 to 16:02, my own leak and address probes ran on the same machine at the same time.

## 2. Lint, scans, suppressions, mypy

| command | exit code | output |
|---|---|---|
| `uv run --all-extras --group test ruff check` | 0 | All checks passed! |
| `ruff check src tests demos tools` (CI form) | 0 | All checks passed! |
| `uv run --all-extras --group test ruff format --check` | 0 | 323 files already formatted |
| `uv run --with bandit bandit -ll -r src tools` | 0 | Medium 0, High 0 (Low 12, below the `-ll` threshold) |
| `bandit -q -r src demos tools -ll` (CI form) | 0 | no output |
| `python tools/scan_repo.py` | 0 | no findings printed |
| `python tests/stage_mutants.py` | NOT RUN | see top |
| `uv run --with mypy mypy tools/mutation_runner.py` | 1 | 1 error (`mypy-linux-errors.txt`): line 228 import-untyped |
| same with `--platform win32` | 1 | 13 errors (`mypy-win32-errors.txt`): line 228 import-untyped; lines 963, 978, 1001, 1053 `os.getuid`; 992 `O_DIRECTORY`, `O_NOFOLLOW`; 1202 `P_PID`, `WEXITED`, `WNOHANG`, `WNOWAIT`; 1227 `killpg`, `SIGKILL` |

mypy is not a repository gate; recorded only.

Suppression search `git diff origin/main...7a2eb4cc | grep -nE '^\+.*(noqa|nosec|type: ignore|pragma: no cover|mark\.skip|xfail)'`: **16 hits** (`suppression-hits.txt`, line numbers of the diff): 186 `# noqa: S314  # nosec B314` on `ET.fromstring`; 2997 `# noqa: S603` on a `subprocess.run` in a test; 10 lines `@pytest.mark.skipif(os.name == "nt", ...)` (3928, 3941, 3963, 3979, 4001, 4016, 4031, 4057, 4972, 5043); 4 lines that only hold the word xfail in text or in a test body (283, 486, 1970, 1973).

## 3. Whole mutant list

NOT FINISHED (see top). Partial: 26 rows, all "ok", in `mutants-partial-rows.txt`.

## 4. Fail-before (previous head b95b0ca7, only the head's tests overlaid)

Worktree `/home/user/build/EV-P89-fb-b95b0ca` at b95b0ca762dd74574e44e7fb546f82ef04f55295, own venv (`hadavin_sdk` resolved to that worktree's `src`: checked). Overlaid from 7a2eb4cc: the six files of the brief. `git status` showed that `tests/test_mutation_runner.py` and `tests/conftest.py` are the same in both commits. `tools/mutation_runner.py` and `src/` of b95b0ca7 untouched.
Command: `pytest -q -p no:cacheprovider tests/test_mutation_runner.py tests/test_mutation_runner_keywords.py tests/test_mutation_runner_meta.py --junitxml=... -rfEs` (three files, run directly, not through heavy.sh).

| variant | exit code | passed | failed | errors | collection errors | duration |
|---|---|---|---|---|---|---|
| without the head's manifest (run first) | 1 | 238 | 45 | 0 | none | 120.38 s |
| with the head's manifest overlaid | 1 | 237 | 46 | 0 | none | 87.60 s |

The only difference between the variants: `test_mutation_runner::test_the_manifest_pins_the_files_a_demo_copies` fails with the head's manifest (the pinned sha256 of the head does not match the old tool) and passes without it. The other 45 failures are the same in both, so the manifest pin does not hide them.
Per failing test with its first assertion or error line: `fail-before.md` (44 in the keyword tests, 1 meta test, 1 manifest pin test).

## 5. Leak probes (head)

Instrument: `leak.py` + `worker.py`. Each case is one real `run_mutants(root, [one mutant], ["tests/test_probe.py"], extra_dirs=(), timeout=120, pass_env=("HADAVIN_TEST_PG_DSN",), on_result=..., first_lines=...)` call in its own process with a private TMPDIR and the address `postgresql://probe:<password>@localhost:5432/scratch` (password percent-encoded where needed). The child test reads the password from its environment and puts all forms into the place under test. The instrument wraps the tool's `_pytest` only to copy each JUnit file before the tool deletes it (to prove the forms were really in the child's output); it changes no return value.
13 made-up passwords built from parts (never written here): lengths 3, 4, 8, 24 of letters and digits; one with `@` (written `%40`); one with a space; all digits; a built-in exception class name; a library-style exception class name, once plain and once also given in `shown_classes`; the name of the test function; a word of the caller's `expect` text; a part of the test file path.
44 child behaviours: assertion message (forms after and before the expected text); exception message; chained cause; exception class name (made at run time, and written in the test source); parametrize id; missing fixture name; fixture that raises (setup, teardown); skip reason (test, parametrized, module level); xfail reason; collection error (message, class name, import-time assert); warning; stdout and stderr (print and raw write); test function and test class names (made at run time, and written in the source); a JUnit file overwritten by the child with the forms in `message`, `type`, `classname`, `name`, `system-out` and the failure body; the same in the baseline run (failure, class, skip, collection error) and in the canary run (failure, skip).
Run: 498 calls, 4 min 13 s, every worker exit code 0; 394 calls returned rows, 65 raised RuntimeError (baseline), 39 raised CanaryFailed.

**Result of the search: 0 of 498 cases SHOWN, for every form and every channel** (`leak-table.md`: form x channel with counts). Forms searched: plain, reversed, upper case, lower case, every character percent-encoded, `quote()` percent-encoded (upper and lower hex), base64, hex, with a zero-width character inside, split over two lines. Channels: returned rows (str and repr), rows given to `on_result`, `first_lines`, the raised error's text, repr, args, `rows`, notes, chained cause and context (never present), `traceback.format_exception` text, the calling process's stdout and stderr (empty in all 498), names and contents of everything left in the temp folder.
Proof the forms were planted: found by the same search in the copied raw JUnit files in 476 of 498 cases; the 22 others are the `warning` and `stdio` behaviours, whose text pytest does not write to JUnit (they test the console only, which the tool sends to the null device).
Left in the temp folder after every call that had a value: `hadavin_mutation_locks_0/` and one 0-byte lock file in it; nothing else.
Longest piece of each password found anywhere in returned text (traceback text excluded): 1 character for the five random-like passwords of 3 to 24 characters (2 for the one with a space); 5 for the class-name, function-name and path passwords (the pieces "Error" and "test_" that the tool's own words hold); 2 for the expect word.
"Both halves present, not adjacent": 1 case (`PATH_PART--class_literal`): the halves "test_" and "probe" occur in the row `tests/[REDACTED]/Test[REDACTED]::test_m` and in the mutant name "probe mutant".
What the special passwords looked like (verbatim, no secret in them):
- password = a built-in class name, child raises that class: `[REDACTED] [expect found] value must be one`
- password = a library class name, not in `shown_classes`: `[class not shown] [expect found] value must be one`; in `shown_classes`: `[REDACTED] [expect found] value must be one`
- password = the test function's name: row id `tests/test_probe::[REDACTED]`
- password = a word of `expect`: `AssertionError [expect found] value [REDACTED] be one`
- password = part of the file path: row id `tests/[REDACTED]::[REDACTED]_one`

What a developer sees for an ordinary failure with the CI address `postgresql://postgres@localhost:5432/postgres` (no password; child message "got 2 rows for order 17, wanted 1"): full verbatim output in `ordinary-failure-rows-ci-address.txt`. Examples:
```
('probe mutant', <Verdict.KILLED: 'KILLED'>, 'tests/test_probe::test_probe_one', True)      first_lines: AssertionError [expect found] value must be one
('probe mutant', <Verdict.WRONG_REASON: 'WRONG_REASON'>, 'tests/test_probe::test_probe_one', False)   first_lines: RuntimeError [expect not found] value must be one
('probe mutant', <Verdict.CRASH: 'CRASH'>, 'tests/test_probe::test_probe_one', False)       first_lines: [class not shown] [expect found] value must be one
('probe mutant', <Verdict.KILLED: 'KILLED'>, 'tests/test_probe::test_probe_one[parameters hidden]', True)
('probe mutant', <Verdict.ERROR: 'ERROR'>, 'FIXTURE ERROR', False)      first_lines: RuntimeError   (missing fixture: [class not shown])
('probe mutant', <Verdict.ERROR: 'ERROR'>, 'SKIPPED TESTS', False)      first_lines: skipped: tests/test_probe::test_probe_one
('probe mutant', <Verdict.ERROR: 'ERROR'>, 'COLLECTION ERROR', False)   first_lines: RuntimeError
('probe mutant', <Verdict.KILLED: 'KILLED'>, '[test id not shown]', True)   (test function made at run time)
RuntimeError: the unmutated copy does not pass its tests (exit code 1): AssertionError
RuntimeError: the unmutated copy skipped 1 selected test(s): ['tests/test_probe::test_probe_one[parameters hidden]']
CanaryFailed: the unmutated copy no longer passes its tests after mutant 'probe mutant' (exit code 1): the shared test database holds what the mutant left behind, so the verdicts of the later mutants would not be reliable
```
With this address the child's own message text ("got 2 rows for order 17, wanted 1") appeared in no returned row, `first_lines` entry or error text.
Raw fact also seen: a JUnit file overwritten by the child was read by the tool as the result (the row followed the forged file: KILLED with the forged message, `[test id not shown]` with a forged name).

## 6. Address probes (head)

Instrument: `addr.py`. Each case is a real `run_mutants(root, [], ["tests/test_probe.py"], extra_dirs=(), pass_env=..., throwaway_hosts=...)` call (empty mutant list, so an accepted address leads to exactly one baseline run). "No child ran" is detected two ways: the instrument counts the tool's pytest runs, and the child test writes a marker file when it runs. 136 cases: full table with every exact message in `address-table.md`.
Totals: 28 accepted, 108 refused, 0 instrument errors. **Refused and a child ran: 0. Secret text (the made-up password, its `%40` and `@` forms, the whole value, the made-up PGPASSWORD value) in any message or output: 0 of 136.**

Accepted (a child ran): URL and key=value with `localhost`, `127.0.0.1`, `LOCALHOST`; URL `[::1]`; key=value `host=::1`; `HOST=localhost` (key in upper case); `host=localhost hostaddr=127.0.0.1`; `hostaddr=127.0.0.1` alone; URL with a password and a listed host; URL password with `%40`; URL with an empty password (`svc:@localhost`); `postgres://` and `POSTGRESQL://` schemes; URL port `99999999999`; a value of exactly 2,000 characters; a name listed with a trailing dot and written with it; a socket folder listed exactly; a symlink path that is itself listed; `throwaway_hosts` given as a list, as a set, as `('LOCALHOST',)`; `db.example.org` when the caller lists it; the variable absent (child ran without the variable); parent holding PG* variables (2 cases).
Refused "host is not one of throwaway_hosts": `127.1`, `0x7f.0.0.1`, `2130706433`, `[::ffff:127.0.0.1]` / `::ffff:127.0.0.1`, `localhost.`, `db.example.org`, a listed name written with a trailing dot (and the reverse), a socket folder not listed / listed with a trailing slash / written with a trailing slash / written with `//` / a symlink to a listed folder, `hostaddr` that differs and is not listed, empty host list.
Refused "not in a shape the runner can check": URL `::1` without brackets, key=value `[::1]`, percent-encoded host, two hosts (`host=a,b`, URL `a,b`), `service=`, `passfile=`, `sslrootcert=`, `options=` (both forms), `target_session_attrs=`, any `?query` (also `?sslmode=disable`), `#fragment`, empty host, plain `@` in the password, a second `@host`, a password key in key=value form (any letter case) or in the query, a repeated key, two spaces, spaces around `=`, leading space, `dbname=` holding a URL or a `host=` text, two path parts, no database name, other schemes, no scheme, a port that is not a number, empty text, one space.
Refused by the character check: quote marks (single, double, escaped), tab, NUL (simulated), newline (inside and trailing), non-ASCII host, zero-width character. Refused by length: 2,001 and 10,000 characters.
Refused host lists: `('*',)`, `('local*',)`, `('',)`, `('localhost','')`, `(b'localhost',)`, `(None,)`, `('[::1]',)`, `(' localhost',)`, `('localhost,evil.example',)`, a folder with `..`, `@abstract` (ValueError "throwaway_hosts holds exact host names..."; also when no variable is passed); bare string (TypeError "throwaway_hosts is a sequence of host names, not one string"); `None` and `5` (TypeError from Python: "'NoneType' object is not iterable", "'int' object is not iterable").
`pass_env`: bare string TypeError; `(b'...',)`, `(None,)`, `('PGPASSWORD',)`, `('DATABASE_URL',)`, lower-case name: ValueError "pass_env may name only ('HADAVIN_TEST_PG_DSN',): ... is refused"; `None`: TypeError "'NoneType' object is not iterable".
Simulated values: bytes gave TypeError "'in <string>' requires string as left operand, not int"; None gave TypeError "expected string or bytes-like object, got 'NoneType'"; no child ran in either.

Parent environment held PGHOST, PGHOSTADDR, PGSERVICE, PGSERVICEFILE, PGPASSFILE, PGPASSWORD, PGOPTIONS, PGSSLROOTCERT, PGPORT, PGUSER, PGDATABASE, PGSSLMODE, DATABASE_URL, AWS_PROFILE (made-up values). Variable NAMES the child saw: `HADAVIN_TEST_PG_DSN, HOME, LC_CTYPE, PATH, PYTEST_CURRENT_TEST, PYTEST_VERSION, PYTHONNOUSERSITE, PYTHONPATH, TMPDIR`. **None of the PG* names reached the child.** `HOME` did (so a `~/.pgpass` of the caller would be readable by the child; not exercised).

## 7. Lock folder probes (head, Linux)

Instrument: `lock.py`; 44 cases, each a real `run_mutants` call with the CI address and a private TMPDIR; before/after listing of the temp folder, the XDG folder, the link target and an "outside" folder. Full table with every message: `lock-table.md`.
Where the lock goes: `<XDG_RUNTIME_DIR>/hadavin_mutation_locks_<uid>/hadavin_mutation_<16 hex>.lock` when XDG_RUNTIME_DIR is an absolute, real folder of this user with mode 0700; otherwise `<temp folder>/hadavin_mutation_locks_<uid>/...`. Folder made with mode 0700, file 0600, 0 bytes.

| pre-existing state | what the tool did |
|---|---|
| no folder, XDG unset | ran; made folder 0700 and lock file 0600 in TMPDIR |
| folder is a symlink (to an own private folder, or dangling) | RuntimeError "the lock folder of this run could not be made or opened (NotADirectoryError): remove it as its owner, or give the run a temp folder of its own with TMPDIR"; no child ran; link target unchanged |
| folder name is a regular file / a FIFO | same RuntimeError (NotADirectoryError); no child ran |
| folder mode 0777, 0750, 0701 | RuntimeError "the lock folder of this run is open to group or others (it must have mode 0700): ..."; no child ran; nothing added |
| folder mode 0700, 0500, 1700 (own) | ran; only the lock file added |
| folder owned by postgres (chown, 0700 and 0777; and made by the postgres user itself) while the tool runs as root | RuntimeError "the lock folder of this run belongs to another user: ..."; no child ran; nothing added |
| XDG = private own folder | ran; folder and file made in XDG; TMPDIR unchanged |
| XDG = world-writable 0777 / 1777 (also with a planted symlink under the lock name), 0750, missing, relative, owned by postgres, a symlink to a private folder, empty text | ran; XDG not used; folder and file made in TMPDIR; planted link target unchanged |
| XDG private, lock name inside is a planted symlink / a 0777 folder | RuntimeError (NotADirectoryError / "open to group or others"); no child ran |
| lock FILE is a symlink to an outside file | RuntimeError "the lock file of this run could not be opened (OSError): it is a symbolic link, ..."; outside file unchanged |
| lock file mode 0666 / 0640, owned by postgres, a hard link to an outside file, a FIFO | RuntimeError "the lock file of this run is not a regular file of this user with one name, mode 0600 or narrower ..."; no child ran; outside file unchanged |
| lock file is a folder | RuntimeError "... could not be opened (IsADirectoryError): it is a folder, ..." |
| lock file 0600 or 0400 (own) | ran |
| lock held by another process | RuntimeError "another mutation run that uses the same lock folder has the same passed database address: give each run a database of its own"; no child ran |
| tool run as postgres (uid 102): no folder | ran; `hadavin_mutation_locks_102` 0700 |
| as postgres: folder owned by root 0700 | RuntimeError (PermissionError) |
| as postgres: folder owned by root 0777 | RuntimeError "belongs to another user" |
| as postgres: root-made symlink to a private postgres folder | RuntimeError (NotADirectoryError); target unchanged |
| as postgres: XDG 1777 with a root-planted folder | ran; XDG not used; lock in TMPDIR |
| as postgres: XDG private own | ran; lock in XDG |
| as postgres: TMPDIR read-only (0555, root-owned) | **ran; nothing written in TMPDIR; the lock folder was made in `/tmp/hadavin_mutation_locks_102`** (Python's `tempfile.gettempdir()` falls back to another folder when TMPDIR is not writable). This is the one case where something was written outside the case folder. |
| as root: TMPDIR mode 0500 | ran, lock made in TMPDIR (root is not bound by modes) |

In every refused case the before/after listings were equal (added, changed, removed: nothing).

## 8. gitleaks

`gitleaks git --redact --no-banner --exit-code 0 --log-opts="origin/main..7a2eb4cc" <worktree>`: exit 0, 35 commits scanned, **0 findings**.
`gitleaks dir` on this evidence folder: exit 0, **0 findings** (run at 16:21 UTC, after this file was written; the one line you are reading was filled in afterwards).
