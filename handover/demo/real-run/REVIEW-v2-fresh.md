# Review rv2 of real-run-fixes-v2.patch (base 2db3926)
Reviewer: fresh, shell. Work dir /tmp/work/rv2-6309 (repo, mutrepo, m1 = raw outputs). No push, made-up data only, no sub-agent. Rules used: preamble 3, 5, 6, 7, 8, 12, 19 (bible folder not reachable: no R-numbers looked up).

## Failures first
No Blocker. All six D items and the --keep rule hold by measurement. Findings:

MAJOR 1 - same class as D1 left open: other key/password files are not checked before the y/N question.
`run_real_check.py` now checks only DESK_HUBSPOT_KEY_FILE. A config with a missing DESK_SMTPP_PASSWORD_FILE (loopback, otherwise valid) and answer `y` went past the question (output ended at "Start? [y/N]" and the script was still running when my 25 s timeout killed it, exit 124). So a typo in the mail password file (and by reading the code, the two IMAP password files and the --live-model key file; those two I did not run) still costs a run after the person said yes. D1's own rule in settings.md:116 says the script refuses a bad setting. Fix at the same choke point (a check of each file the desk or the script opens later). Rule 7 asks for sibling grep; the patch did not do it.

MINOR/Nit list below. Slips of mine are at the end.

NIT 1 - tests do not guard the own_tempdir fixture. With the fixture made a no-op (mutrepo), the five --keep tests still pass and leave real-dry-* folders in the temp dir (6 folders in a private TMPDIR, see below); no test fails. The litter fix is therefore unprotected against a future test that forgets the fixture.
NIT 2 - D6 success path is not covered by a unit test. The only test (`test_dry_fakes_folder_is_deleted_also_when_the_self_test_fails`) uses a DryFakes that raises at start. I measured the success path by hand (below): it works. A mutant "no cleanup" is killed, but a mutant that removes cleanup only on a normal finish would pass the tests.
NIT 3 - wording: a key of 3 characters gives "the hubspot key file holds no key" (desk's own text, and the live check says the same). Accurate-ish but not plain; "too short" would be clearer. Core text, not changed by the patch.
NIT 4 - run_live_check accepts a two-line key file (exit 3 after y, error LiveTransport 1). The patch text says only "readable, at least 8 characters", so it matches the docstring; settings.md:121 calls n8n key files one-line but nothing says so for the live key. No patch fault; note only.
NIT 5 - preamble rule 8 says `uv run --all-extras --group test ...`; this repo has no group `test` (uv error "Group test is not defined"). I used `uv run --all-extras ruff ...` and the `pytest` tool on PATH. Not a patch issue.

## Verified by measurement (command, exit, output)
Patch: `git apply --check` and `git apply` clean on 2db3926.
All raw outputs: /tmp/work/rv2-6309/m1/*.out (made-up keys only, `env -i`, loopback only, run from an empty cwd).
| Item | Case | Exit | Output / state |
|---|---|---|---|
| D1 | HubSpot key file missing, answer y piped | 2, 0 s | `refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file cannot be read`; no "Start?" text printed (grep count 0) |
| D1 | 2 lines / 3 chars / spaces / 5000 bytes | 2, 0 s each | fixed texts, no key, no path (grep for made-up-key in all outputs: none) |
| D1 control | valid config, n | 1 | reaches `Start? [y/N] stopped, nothing was called` |
| D1 live | run_live_check missing / short key, y | 2 | `refused: the key file cannot be read` / `...holds no key`, no "Start?" |
| D2 | DESK_DB_PATH=:memory:, y | 4 | `the desk refuses to start: the lead book must be a file: ...`; cwd empty afterwards (no desk-1.log) |
| D3 | non-UTF-8 config | 2 | `refused: ValueError: the config file is not UTF-8 text: save it as plain UTF-8 text`; no "0x", no "position" |
| D4 | run_live_check, stdin /dev/null | 1 | `stopped, nothing was called: there is no terminal ...`; no Traceback |
| D5 | all calls failed (dead loopback), y | 3 | `errors by class: {'LiveTransport': 1}` then `at least one call failed: the check did not work` |
| D6 success | `--dry-fakes --assume-yes`, private TMPDIR | 0 | TMPDIR empty afterwards; closing line says folder deleted, use --keep |
| D6 failure | `--dry-smtp-script final_452` | 3 | TMPDIR empty; same closing line |
| D6 keep | `--dry-fakes --assume-yes --keep` | 0 | one real-dry-* folder kept, `result file: <path>` printed |
| --keep alone | `--config C --keep` and `--keep` | 2, 2 | `refused: --keep is only for the self-test (--dry-fakes); ...` |
| own_tempdir | 4 test files (163 tests) with TMPDIR set to a private empty folder | pass | after: only `pytest-of-root`, no real-dry-* |
Note on the system /tmp count: it was 288 before; it showed 290 after my first run, but another reviewer (rv-3126) was running a full pytest at the same time and the two folders were made at times when I was not running dry-fakes tests. The private-TMPDIR run above is the clean measure.

## Gates
- New tests: tests/test_take_script_refusals.py 15 passed. 4 test files together: 163 passed (197-255 s).
- ruff check: All checks passed. ruff format --check: 146 files already formatted.
- mypy linux and win32: Success, no issues in 26 source files (both).
- test_hygiene + test_gitleaks_exceptions: 32 passed, 27 SKIPPED (gitleaks is not installed here). Not verified by me: the gitleaks scan. `git diff --check` clean.
- bandit: NOT RUN (not installed here).
- Secret-like literals: scanned added lines for 28+ char runs, AKIA, made-up: only `"made-up-" + "key-0001"` / `"key-0002"` built from parts, and a docs line that is long prose. No literal key found.

## Mutants (one per item, run on a copy; test file test_take_script_refusals.py)
| Mutant | Result |
|---|---|
| D1 run_real_check: key check disabled | 5 failed (all key-file cases) |
| D1 run_live_check: check removed | 2 failed (missing, short) |
| D1 run_live_check: check moved after the question | 2 failed |
| D2: book_problem check disabled | 1 failed (memory test) |
| D3: UnicodeError catch removed | 1 failed |
| D4: EOFError catch removed | 1 failed |
| D5: failure returns 0 | 1 failed |
| D6: rmtree callback removed | 1 failed |
| --keep refusal removed | 1 failed |
| own_tempdir made a no-op | NOT caught: no test fails; 6 real-dry-* left in private TMPDIR (Nit 1) |
Not tried: D1 run_real_check "check after the question" (the test uses an input() that raises, so it should fail; not run).

## Not checked
Windows; the real HubSpot/Gmail path; the full dry-check script (`run-dry-checks.sh`); IMAP-password and live-key checks of the sibling in Major 1 beyond reading code; bandit; gitleaks scan.

## My slips
After a timeout in the SMTP-password test I ran `pkill -f lead_desk.server --newest` without being sure the process was mine. Afterwards pgrep showed no process on my port and none of mine left; I cannot rule out it hit nothing else, but I saw no effect. Also first isolation attempts failed (wrong python, `-I` on the script); redone, only the redone results are reported.

Files: patch /tmp/demo-lead/handover/demo/real-run/real-run-fixes-v2.patch; patched clone /tmp/work/rv2-6309/repo; this report /tmp/work/rv2-report.md. Base SHA 2db3926 (patch uncommitted).
