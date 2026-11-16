# EVIDENCE RUNNER results: Q8a-1 batch 17 (round 18), head b5b6c9fd

Head checked out detached at `b5b6c9fdfc7722fe00d86cb6b9518acd5197b0df` (equals `origin/wip/cloud-q8a1-b17`); tree clean before and after. Previous reviewed head 20581c80; `origin/main` = 2a8c2aac. Raw logs: `/home/user/build/evidence-raw/Q8a1b17-b5b6c9fd/`. I record only; nothing was fixed, edited or pushed. Times UTC (IST = UTC + 5:30): started 14:09, finished about 15:10 UTC. Queue wait for heavy slots: about 12 minutes for the first full run, about 5 minutes for the first mutant run.

## FAILED or NOT RUN (read first)

1. **`python tests/stage_mutants.py` (the exact CI command) cannot start at this head.** Exit 1, `RuntimeError: the unmutated copy does not pass its tests`. Cause found by reproducing the runner's copy by hand: `tests/test_changelog_claims.py` reads `CHANGELOG.md` at the repo root at import time, and the runner's temp copy holds only `src`, the listed test files and `tests tools demos docs`, so the file is missing (`FileNotFoundError ... CHANGELOG.md`). With `CHANGELOG.md` added to the copy, the same 10 test files pass (1110 passed). The same failure came from every filter run of it (Z150, Z152, Z153, Z162, Z154) and was reproduced after I had fixed my own environment slip (below). Logs: `stage_mutants.log`, `iso-Z*.log`.
2. **Full pytest, run 2 (the valid run), exit 1: `3 failed, 11536 passed, 1 skipped, 28 deselected` in 290.9 s.**
   - `tests/test_lockin_guard.py::test_vendor_sdks_stay_inside_their_kind_modules`: `'hadavin_sdk.hidden_input: imports pydantic_core (unknown) outside its allowed modules'`. Failed again when re-run alone (still 1 failure). This one is not caused by my environment.
   - `tests/demo_askdata/test_validate_harm.py::...[copy-to-file]` and `...[dblink-connect]`: environment causes on my side. The first writes the fixed file `/tmp/askdata_p2_copy.csv`, which exists owned by another user's database server (from 14:17, not mine; I did not touch it). The second runs `dblink_connect('dbname=postgres')` inside my server, which then used the default socket because my server's own environment had no PGHOST/PGPORT. I restarted only my server with those set and a private `/tmp` (separate mount for the server process only) and re-ran `tests/demo_askdata tests/test_lockin_guard.py`: `1 failed, 1267 passed, 2 deselected` (the two askdata tests then passed; the lock-in test still failed). This is a re-run of a subset, not a second full run.
   - Skip, by name: `tests/contracts/test_llm.py:95` "Stubber refuses a malformed Converse shape before the kind sees it". Python 3.12, semgrep, zizmor, trivy and pip-audit were not run (impossible now, as the brief says).
3. **Full pytest, run 1, was invalid (my slip):** `5 failed, 11534 passed`; the tests that call `git` failed with exit 128 because I ran them as user `nobody` in a worktree owned by root (git "dubious ownership"). I added a gitconfig for that user and re-ran (run 2 above). Kept as `full-pytest-run1-git-ownership.log`.
4. **`tests/migration_numbers_mutants.py`: exit 1, `the unmutated copy does not pass its tests`.** Reproduced by hand: the baseline holds `test_the_timing_harness_flags_a_quadratic_stand_in`, which fails in the copy (it is the known timing test; see item 9 below). No mutant was run.
5. **Supplementary (not the CI command): `tests/stage_mutants.py` run through my own wrapper `probes/supp_runner.py` (outside the repo; the wrapper only adds `CHANGELOG.md` to the runner's copy), as user nobody via heavy.sh: `388 of 405 good`, 17 not good.** List with first lines in `stage-mutants-non-good.txt`. Not good: M18v SURVIVED, Z21 ERROR (SNIPPET NOT FOUND), Z65 SURVIVED, Z90 OTHER_TEST (killed by `test_a_failing_detector_is_logged_by_class_only[plain-error]`, not its pinned test), Z128 ERROR (SNIPPET NOT FOUND), Z152 SURVIVED, Z154 WRONG_REASON, Z159 SURVIVED, Z163 ERROR (SNIPPET NOT FOUND), Z184 WRONG_REASON (TypeError descriptor `__str__`), Z190 ERROR (SNIPPET NOT FOUND), Z192, Z193, Z194 SURVIVED, Z209 SURVIVED, Z221 CRASH (`ValueError: event_id is not a plain file name`), Z223 SURVIVED. I did not check whether these are real or caused by running as nobody or by the wrapper.
6. **Individual isolation (supplementary wrapper, one mutant each):** Z150 killed by its pinned test (`R17a ...`), Z153 killed (`R16d ...`), Z162 killed (`R16n ...`); **Z152 SURVIVED; Z154 WRONG_REASON** (killed by `...planted_fault_alone[X11 ...]`, assertion `('X11 the text of an exception kept in a variable', ['m.py:6: [message] A(m)'])`, not by its own pinned test).
7. **Known timing test** `test_the_timing_harness_flags_a_quadratic_stand_in`, alone with all three heavy slots held: head 3 of 3 FAILED, origin/main 3 of 3 FAILED (each 0.65 to 0.70 s; assertion "a quadratic function must be flagged"). Run on a shared machine; I did not investigate.

## Builder claims versus what I measured (no judgment)

| Builder claim | Measured |
|---|---|
| fail-before on 20581c80: 20 failed, 767 passed | 22 failed, 765 passed (7 changed test files, old `src`, `CHANGELOG.md` NOT copied); 18 failed, 769 passed with the head `CHANGELOG.md` copied in too. Lists: `failbefore-summary.txt` and raw logs |
| targeted tests 638 passed | the 7 changed test files alone: 787 passed on head |
| full pytest and full stage_mutants did not run on head | confirmed, see items 1 and 2: pytest has 3 failures (1 real as far as I can tell); stage_mutants cannot start from CI's own command |
| 405 mutants | 405 listed by the supplementary run |
| 54 handlers, 473 own rows, 55 reasons, 54 checked, 588 in all | not checked by me beyond `tests/test_changelog_claims.py` (6 passed) |

## Table

| # | Item | Command (short) | Exit | Last line |
|---|---|---|---|---|
| 1 | changed files vs `origin/main...HEAD` | `git diff --name-only` | 0 | 108 paths, `diff-name-only.txt` |
| 2 | ruff | `ruff check`, `ruff format --check` over src tests demos tools | 0, 0 | `All checks passed!`, `334 files already formatted` |
| 3 | bandit | `uv run --no-project --with bandit bandit -q -r src demos tools -ll` | 0 | only warnings (a `nosec` B102 at `src/hadavin_sdk/tools.py:417` with no finding) |
| 4 | repo scan | `tools/scan_repo.py` | 0 | no output |
| 4 | gitleaks, `origin/main..HEAD` (47 commits) | `gitleaks git --log-opts` | 0 | `no leaks found` |
| 5 | full pytest run 2 | `pytest -p no:cacheprovider -q -m "not live and not perf" -rs` via heavy.sh, own Postgres 16.15, as nobody | 1 | `3 failed, 11536 passed, 1 skipped, 28 deselected in 290.91s` |
| 5 | re-run of askdata and lock-in tests | see item 2 | 1 | `1 failed, 1267 passed, 2 deselected in 90.37s` |
| 6 | `tests/stage_mutants.py` (CI command) | via heavy.sh as nobody | 1 | `the unmutated copy does not pass its tests` |
| 6 | `tests/mutation_runner_mutants.py` | via heavy.sh as nobody | 0 | `62 of 62 good; problems: []` |
| 7 | `tests/migration_numbers_mutants.py` | via heavy.sh as nobody | 1 | `the unmutated copy does not pass its tests` |
| 7 | supplementary `stage_mutants` (+ CHANGELOG in copy) | wrapper, heavy.sh | 1 | `388 of 405 good` |
| 7 | Z150, Z153, Z162 alone | wrapper | 0 | `1 of 1 good` each |
| 7 | Z152, Z154 alone | wrapper | 1 | `0 of 1 good` each |
| 3 | fail-before on 20581c80 | 7 changed test files into detached worktree of 20581c80; `PYTHONPATH` = old `src` (import path checked: old tree) | 1 | `22 failed, 765 passed` (18 failed with CHANGELOG copied). 18 of the 61 new test ids fail on old code, 43 pass on old code; 4 test ids that existed at 20581c80 also fail |
| 5 (own) | `tests/test_changelog_claims.py` alone | pytest | 0 | `6 passed in 2.08s` |

## Hostile probes (item 6; own script `probe6.py`, output `probe6-output.txt`)

Made-up values built from parts: a capital-letter canary (not word-like), a lower-case word-like canary that is not a loaded id, and a made-up library error text holding the canary. 66 probes; the canary or made-up library text was visible in 3. Each probe checked `str`, `repr`, `args`, traceback, `__cause__`, `__context__`, `errors()` (with and without `include_input`) and `json()` where applicable.

Shown (visible in output):
- `AuditEvent(**{<canary>: 1}, ...)` (an unknown key whose NAME is the canary): the name is in `str`, `repr`, traceback, `errors()` (`loc`) and `json()` (`loc`); the `input` field there is `<hidden>`.
- `errors.shown_name(<word-like name not loaded>)` with no loaded set, and with `loaded=[itself]`: returns the name (by the documented rule).

Not shown: `AuditEvent` with `event_id` = canary, made-up library text, path-like text, a 5120-character text, an `int`, `bytes` (via the constructor, `model_validate`, `model_validate_json`, `model_validate_strings`: no channel held the value); `errors.shown_id` of every value including both `str` subclasses (returns `?`); `shown_name` of the capital canary, library text and both `str` subclasses (returns `<not shown>`); `LocalDirSink.write_intent` / `write_outcome` / `reconcile` with a poison event id (a fixed sentence; log output checked) and with a root under a file whose name holds the canary; all 21 `check-config` runs (unknown keys, bad values, malformed YAML, non-UTF-8 bytes, route and agent names, a path, an action file name): stdout and stderr never held the canary. A `check-config` baseline on the fixture needed `{port}` replaced to be accepted (exit 0); the fixture as shipped is refused (exit 2) on that placeholder.

Also recorded: `AuditEvent(event_id=<str subclass whose __str__ gives the canary>)` is accepted and stored as the plain text of the object (`abc`); the file name and file contents hold no canary (`probe6b-output.txt`). `TypeAdapter(AuditEvent)` raised without the value (the module says this path is not covered; here it was hidden). `agents: id = <canary>` was accepted by `check-config` (exit 0) and printed nowhere.

## Environment, cleanup

Own Postgres 16.15 on 127.0.0.1:56131 as user nobody (data folder under my own build folder); worktrees head, old (20581c80), pristine (20581c80), main; own venv. All commands ran as nobody with a cleaned environment (no cloud, model or token variables). Stopped and removed at the end: the server, its private `/tmp` mount (it ended with the server), the worktrees and my temp folders. Not touched: anything of other agents.
