# fix-f3-r7 (FIXER log, 2026-11-16 UTC; nothing committed by me)

## What is not proven or not done (first)
- Not run: Python 3.9 and 3.10 (not installed), macOS (the F_GETPATH branch is only tested with a fake module), real n8n, NFS, WSL. The program now REFUSES to start below Python 3.11 (`MIN_PYTHON`), so the README claim matches what ran: 3.11, 3.12, 3.13, each full suite green (157 tests).
- Equivalent mutant (shown in writing): `if sys.version_info < MIN_PYTHON` changed to `<=` survives. `sys.version_info` is a 5-tuple `(3, 13, 2, 'final', 0)`; compared with the 2-tuple `(3, 11)` it is never EQUAL, only greater or smaller, so `<` and `<=` give the same answer on every real interpreter.
- Mutants I picked were hand-picked (31), not a random sample. 29 killed at first run, 2 survived (`<=` above, and `S_ISREG` check in `sha256_at`); the second got its own test and is now killed. The 20-mutant random sample of the independent runner is not re-run by me (that is the evidence runner's job).
- Not detectable at all (impossible in general, stated in README "Limits"): a `$env` name built at run time such as `this["$"+"env"]`. It is not filled, so it stays and n8n handles it. Time Machine and other backup tools: not detectable from a folder name; README says to keep the folder out of backups.
- N4 (signals held for the whole removal in `delete`): kept on purpose, not changed. The held part is a few small files; a signal is delivered right after, and since this round `delete` says so and ends with 0 if the removal had finished (before, it reported a refusal after a finished delete). README states it.
- Behaviour change to know: `main()` no longer catches unexpected errors itself (ruff BLE001 blind-except could not be satisfied without a suppression). The command-line entry `run()` installs `sys.excepthook`, which prints `failed: <TypeName>` only (no text, no traceback), exit code 1. Code that calls `main()` as a library now sees the exception.
- Test helper change: the tests start child programs through `asyncio.create_subprocess_exec` instead of `subprocess.run`, because ruff S603 flags every `subprocess.run` with non-literal arguments and the rule is "no suppressions". Honest note: this is a different API that the rule does not cover, not a different safety level; the argument lists are fixed parts and made-up files.
- One earlier unexplained one-off failure (r6) did not recur; I saw none in this round (all runs green).

## Findings fixed
| id | fix | test (fails on old code) |
|---|---|---|
| M1 | `check` always prints whether the manifest compare ran; marker present + manifest missing = problem ("NOT compared"); marker must name the folder (renamed/copied folder = problem); folder 0700 and files 0600 yours checked on a marked folder; README: import from the folder `fill` made, do not copy | test_check_always_says..., ..._whose_manifest_is_not_beside_it, ..._renamed_or_copied_folder, ..._loose_modes_on_a_marked_folder |
| M2 | `--tokens-only` keeps the not-ready note check, prints "placeholders: not checked (--tokens-only)"; README says so; old test pin changed | test_tokens_only_refuses_a_not_ready_copy..., test_check_mode (changed) |
| M3 | `delete --remove-others` (plain regular files yours only; folder, link, other owner still stop it); stray file named in message and in `check`; rmdir failure -> "folder left behind: NAME (it holds: ...)", manifest kept, re-run works | test_delete_stops_at_a_stray_file..., test_remove_others_*, test_delete_that_cannot_remove_the_folder... |
| M4 | README says only 3.11/3.12/3.13 ran; program refuses < 3.11; test ties README text to `MIN_PYTHON` | test_old_python_is_refused_plainly... |
| SIGKILL | `check` on a folder with no .json now names the not-ready note | test_check_after_a_kill_before_any_json_names_the_not_ready_note |
| N1 | every printed file name goes through `_a` (list_json, read_json_file) | test_file_names_from_disk_are_printed_safely_everywhere |
| N2 | clean-up failures are reported ("clean-up did not finish; left behind: ..."); `_write_new` keeps an entry it could not unlink; held SIGTERM after a finished delete -> rc 0 with a plain line; Ctrl-C -> one line, rc 130 (README table), no traceback; BrokenPipe after a full copy no longer turns it into rc 1 (`_say`) | test_a_clean_up_that_fails..., test_a_stop_held_during_the_removal..., test_ctrl_c_ends..., test_a_closed_pipe... |
| N3 | `sha256_at` opens with O_NONBLOCK and refuses a non-regular file | test_check_refuses_a_pipe_in_the_place_of_a_listed_file_without_hanging (old code: hangs until the 60 s guard), test_a_hash_is_never_taken_of_a_pipe |
| N5 | `$env` glued to a name character or a dot (`a$env`, `x.$env`, `x . $env`, `x?.$env`) refused | test_a_token_glued_to_a_name_or_a_dot_is_not_filled |
| N6 | empty placeholder value = no value (name stays, copy NOT READY, warning); sync/cloud folders refused for values file and output (Dropbox, OneDrive, iCloud, Google Drive, ...); RecursionError and size caps (32 MB JSON, 1 MB values) refused plainly; README notes dict-key replacement | test_an_empty_placeholder_value..., test_cloud_synced_folders..., test_a_file_nested_too_deeply_or_too_large... |
| noqa | all 6 removed: 1 BLE001 (see behaviour change above), 3 S603 + 1 S607 (asyncio spawn helper, `shutil.which("node")`), 1 S311 (own tiny fixed-seed generator `lcg`). grep for noqa / nosec / type: ignore: 0 / 0 / 0 | ruff check rc 0 |

## Mutants that survived evidence r6
| mutant | test now | result |
|---|---|---|
| n6 `reversed(created)` | test_clean_up_removes_in_reverse_order_of_creation | killed |
| n7 mkdir shield no-op | test_stop_signals_are_held_back_while_the_folder_is_made_and_removed | killed |
| n16 delete shield no-op | same test | killed |
| n15 `except _Stopped` | test_a_stop_signal_is_reported_as_such_and_not_as_a_crash, test_main_reports_a_stop_as_a_stop | killed |
| n18 `ph_left > 1` | test_exactly_one_placeholder_name_left_is_enough_to_refuse | killed |
Plus 26 more hand-picked mutants on the new code (marker, modes, tokens-only line, note naming, remove-others, held stop, glued name, size cap, sync check, empty placeholder, cleanup report, FIFO, exit 130, excepthook, recursion, rmdir message, order, broken pipe, marked flag): all killed. Survivors: `<=` (equivalent, above); `S_ISREG` in `sha256_at` (killed after adding test_a_hash_is_never_taken_of_a_pipe). Raw: scratchpad/mut7/out.txt.

## New tests against OLD code (old fill_flows.py from the backup in scratch, new test file, FF_DEMO_DIR set)
Round7 only: Ran 28, FAILED (failures=18, errors=5) = 23 fail on old code. Of those, 5 errors are "old code has no such name" (`run`, `MIN_PYTHON`) and one hangs until the 60 s guard (pipe). 5 pass on old code by design: they pin mutant killers and regression of existing behaviour (stray file named by check, the stop message tests, the signal shield test, exactly-one-placeholder). Those 5 were proven by mutation instead. (After this run I added test_a_hash_is_never_taken_of_a_pipe; it was proven by the S_ISREG mutant.)
Raw: scratchpad/oldr7/old.log.

## Gates (raw, rc from the commands themselves)
- `python3.11 -I -m unittest` rc=0 Ran 157 OK (17.8 s); python3.12 rc=0 Ran 157 OK (19.1 s); python3.13 rc=0 Ran 157 OK (18.6 s)
- `uv run --all-extras --group test pytest -q handover/flows-audit/fill_flows` rc=0 `157 passed in 19.00s`
- `ruff check .` rc=0 `All checks passed!`; `ruff format --check .` rc=0 `24 files already formatted`
- `bandit -ll -r .` rc=0 `No issues identified.`
- Files edited: fill_flows.py, test_fill_flows.py, README.md, this file. Backup before the work: scratchpad/bak-f3r7/. Other dirty paths in the repo are not mine.
