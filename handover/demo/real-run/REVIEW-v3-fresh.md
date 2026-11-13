# Review rv6 of real-run-fixes-v3.patch (bases 2db3926 and db54e13)
Reviewer: fresh, shell, no sub-agent. Work dir /tmp/work/rv6-324 (repo = patched clone, mut = mutant copy, base = unpatched 2db3926 plus the new test file, cases/ = raw outputs of the hostile runs). Made-up data only, `env -i`, loopback only, empty cwd. Preamble rules used: 3, 5, 6, 7, 8, 12, 19 (bible folder not reachable: no R-numbers looked up). No push, no network write. I started no background process that is still running (the `crash_desk` children of my timed-out runs were gone when I checked; processes now in `ps` belong to other reviewers).

## Failures first
No Blocker. The earlier Major is closed by measurement. Remaining:

MINOR 1 (D1-class sibling, not closed): settings that the desk (or run_live_check) opens AFTER the y/N question and refuses there. Measured with the synthetic config plus one bad setting, answer `y` piped, 45 s limit:
| Setting (path does not exist) | Result after `y` |
|---|---|
| DESK_SMTPP_CA_FILE | passes the question, then exit 3 "the run could not finish: the desk ended while starting" (desk log: traceback) |
| DESK_LEADFLOW_FILE | same, exit 3, desk log "the desk refuses a setting: DESK_LEADFLOW_FILE cannot be read" |
| DESK_APPROVERS_FILE | same, exit 3 (traceback in desk log) |
| DESK_REPLIES_PATH | same, exit 3 |
| (run_live_check.py) a corrupt ledger file (`garbage`) | passes the question, then "stopped: LiveCapReached: the spend ledger could not be read or written", exit 2 |
No money, no HubSpot call and no mail happen in these cases (the desk dies at start, the ledger stops spending), so I rate it Minor, not Major. But the person said "y" and a settings typo still costs a run. REAL_IMAP_n_CA_FILE is already refused before the question (prints `refused: FileNotFoundError`), so only the SMTP CA file, leadflow, approvers and replies files are missing. The builder wrote these are "not secrets" and left them out on purpose; that is a decision, but Rule 5 says fix. Fix: Config.from_env({**env, ...}) already parses the desk's own settings (the script uses it for live); calling it, plus `ssl.create_default_context(cafile=...)` for the CA file, before the question would cover all four with the desk's own code. The doc claim in FIXES.md ("`docs/settings.md` line 116 says so", i.e. that other file settings are not checked) is not in the doc: the patched settings.md says nothing about these four being unchecked.

MINOR 2: a TWO-LINE live key file (`--live-model` or run_live_check) is accepted by the pre-check (`LiveQualifier._read_key` does not test for more than one line), goes past the question, then every call fails (LiveTransport). Measured: `cases/live-twoline` reached "Start? [y/N]". This was Nit 4 of rv2 ("note only"); v3 still does not test or document it. The HubSpot/SMTP/IMAP readers refuse two lines; the live reader is the odd one. Needs a one-line check in `_read_key` (core, 2 lines) or in `secret_file_problem`.

NIT 1: `test_every_keep_self_test_in_the_suite_uses_its_own_temp_folder` is a text scan: it only sees tests whose source contains `"--dry-fakes"` and `"--keep"` in double quotes, and any mention of the word `tempfile` in the test body satisfies it. A test written with single quotes, or building the argument list elsewhere, would not be seen. The companion test (`test_own_tempdir_puts_...`) does catch a no-op fixture (measured below), so the damage is limited.
NIT 2: leftover on this machine: my `uvx`/ledger test ran as root and created `/nonexistent/dir` (the live ledger creates missing folders; it is a finding in itself only in that an unwritable-path typo is not refused, see Minor 1). I could not delete `/nonexistent` (removal blocked by the safety check); it holds only an empty folder `dir` and an empty-or-tiny ledger file. Please remove by hand: `rm -r /nonexistent`.
NIT 3: not run: gitleaks (not installed; 27 hygiene tests SKIPPED, so the gitleaks result is not verified by me), Windows, full test suite, `run-dry-checks.sh` (I measured D1-D6 directly instead, below).

## The earlier Major, by running the script (cases/*, exit codes, one run each, answer `y` piped)
| Case | Exit | Output (all fixed text) |
|---|---|---|
| SMTP password file missing | 2 | `refused: DESK_SMTPP_PASSWORD_FILE: the smtp password file cannot be read` |
| SMTP two lines | 2 | `...has more than one line: it must hold only the password` |
| SMTP 3 characters | 2 | `...holds a password that is too short (at least 8 characters)` |
| IMAP 2 password missing / empty / non-ASCII | 2 each | `refused: REAL_IMAP_2_PASSWORD_FILE: the mailbox password file cannot be read / holds no password / holds a password with characters other than plain printable ASCII` |
| HubSpot key missing | 2 | `refused: DESK_HUBSPOT_KEY_FILE: the hubspot key file cannot be read` |
| each of the three password/key files is a directory | 2 | same "cannot be read" texts |
| --live-model, live key missing / 3 chars / empty | 2 each | `refused: DESK_LIVE_KEY_FILE: the key file cannot be read / holds a key that is too short (at least 8 characters) / holds no key` |
| live key bad but WITHOUT --live-model | reaches question | control: not looked at, as designed |
| valid config, `y` | reaches `Start? [y/N]` | control |
In every refusal: "Start?" count 0, grep for the made-up key strings and for the case folder path in the output: 0 hits, cwd stays empty (no desk log, no folder). IMAP 1 and the SMTP password share one file in the synthetic config, so the IMAP-1 case was covered by the unit tests (below), not separately by a script run.

## D1 to D6 and the keep rule (direct runs)
D1 refused before question (above). D2 `DESK_DB_PATH=:memory:`: exit 4, "the desk refuses to start: the lead book must be a file...", cwd empty. D3 non-UTF-8 config: exit 2, `refused: ValueError: the config file is not UTF-8 text: save it as plain UTF-8 text`, no byte value. D4 run_live_check with stdin /dev/null: exit 1, "stopped, nothing was called: there is no terminal...", no Traceback. D5 run_live_check dead loopback + y: exit 3, "at least one call failed". D6 with a private TMPDIR: success run exit 0, 0 folders left, closing line says deleted and how to keep; `--dry-smtp-script final_452` exit 3, 0 left, same line; `--keep` exit 0, 1 folder kept, `result file: <path>` printed; `--keep` alone: exit 2, `refused: --keep is only for the self-test...`.

## Nit fixes (measured)
Nit 1 (own_tempdir): fixture no-op'd -> `test_own_tempdir_puts_temporary_folders_under_the_test_folder` fails (1 failed). Nit 2 (D6 success path): mutant "delete only when `--dry-smtp-script` is not ok" -> `test_a_clean_self_test_deletes_its_folder_too` and `test_dry_fakes_folder_is_deleted_also_when_the_self_test_fails` both fail (my mutant differs from the builder's "delete only on failure", which I could not express without changing the control flow; the clean-run test is what catches it). Nit 3 (wording): text reverted in each of the three readers (crm_hubspot, smtp_provider, live_claude) -> `test_a_three_character_key_is_called_too_short` fails each time. `grep` for the old texts in tests/ docs/ README n8n: no hit.

## Mutants (one or more per fix; test file tests/test_take_script_refusals.py, 35 tests; mutant copy, original restored each time)
| Mutant | Failed tests |
|---|---|
| A SMTP password check removed | 5 failed (4 SMTP cases + too-short wording test) |
| B IMAP check removed | 9 failed (all IMAP 1 and 2 cases + wording) |
| C live key check removed | 4 failed |
| D HubSpot check removed | 6 failed |
| E whole `secret_file_problem` call off | 21 failed, 14 pass |
| **F all secret checks moved AFTER the question** (the one the builder did not run) | **21 failed, 14 pass (9.7 s). Message: `AssertionError: the y/N question was asked`, so the tests catch it for the right reason** |
| D1 run_live_check key check removed | 2 failed |
| D2 book_problem off | 1 failed |
| D3 UnicodeError catch off | 1 failed |
| D4 EOFError catch off | 1 failed |
| D5 failure returns 0 | 1 failed |
| D6 rmtree callback off | 1 failed |
| --keep refusal off | 1 failed |
| own_tempdir no-op | 1 failed |
| delete-only-when-not-"ok" | 2 failed |
| wording x3 | 1 failed each |
Fail-before: the new test file plus conftest run on an unpatched 2db3926 clone: 33 failed, 2 passed (the two controls).

## Gates (patched tree, 2db3926)
- `git apply --check` and `git apply`: clean on 2db3926 and `--check` clean on db54e13 (I applied only on 2db3926; db54e13 check only).
- New tests: 35 passed (38 s). Touched files together (test_real_check_dry, test_clock_steps, test_live_claude, test_ledger_amounts, test_hygiene, test_gitleaks_exceptions): 284 passed, 27 skipped (gitleaks missing), 300 s.
- ruff check: All checks passed. ruff format --check: 146 files already formatted. mypy linux and win32: Success, no issues in 26 source files each.
- bandit -ll (via uvx, src and scripts): no medium or high issue printed.
- Tooling note: the preamble says `uv run --all-extras --group test ...`; as rv2 found, this repo has no group `test`; I used the `ruff`, `mypy`, `pytest` programs on PATH.

## Not checked
Windows; gitleaks scan; the whole suite; real HubSpot/Gmail/model path; a FIFO or other special file as a key path (a read of a FIFO could block; not tried); run-dry-checks.sh; the two-pass dry check.

## Slips
First `runcase.sh` runs used a relative repo path and failed (redone, only redone results are reported); one background pytest overlapped with a second mutant call in the shared mutant copy; I waited for it to finish and the F-mutant result above was read from a clean run (its 21 failures match mutant E). I could not remove `/nonexistent` (see Nit 2).

Files: patch /tmp/demo-lead/handover/demo/real-run/real-run-fixes-v3.patch; patched clone /tmp/work/rv6-324/repo (uncommitted); outputs /tmp/work/rv6-324/cases/*/out.txt, d56.txt, touched.txt; this report /tmp/work/rv6-report.md. Base SHA 2db3926.
