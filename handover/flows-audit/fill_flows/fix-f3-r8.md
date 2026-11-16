# fix-f3-r8 (FIXER log, last batch, 2026-11-16 UTC; nothing committed by me)

## What is not proven or not done (first)
- Not run: Python 3.9 and 3.10 (not installed), macOS (F_GETPATH only with a fake module), real n8n, NFS, WSL, ACL disks. No new review round was run (lead froze it); the fixes are checked by tests and mutants only, not by an independent reviewer.
- F7, F8, F10, F14, F15 left as stated (see the last section).
- Judgement call on F2 for `delete`: the brief said "run the same open-place check on check and delete". For `check` it is a problem (exit 1). For `delete` I made it a WARNING on stderr and the delete still happens, because refusing would leave a copy of values sitting in a git folder or a synced folder with no tool to remove it. If the lead wants a hard refusal in `delete`, change `_warn_delete_place` to raise; one test needs to flip. Same for a hard link in `delete`: warning, the file is removed, the other name stays.
- A file with a second name is counted only for files in the checked folder (not for the manifest file beside it).
- F12 and F13 test changes are strengthenings of existing behaviour: they pass on the old code too (counts below). I checked them by mutants instead.
- Old manifests (made before this round) have no `ready` flag: `check` now reports them as problems ("does not say this copy is ready"); `delete` still reads them. A folder filled earlier must be filled again before import.
- Behaviour change you should know: `check` on an INPUT folder now always has at least one extra problem (no marker, no fingerprint file). `check` of an input folder was only ever a token scan; the README says so.

## Findings and fixes (class-level where possible)
| id | fix | tests |
|---|---|---|
| F1 | `check` of a folder with no marker and no manifest reports a problem (also with `--tokens-only`); README step 2 says why (`cp -r filled/*`, zip, rsync skip dotfiles) | test_check_refuses_a_folder_with_no_marker_no_manifest_and_no_tokens, ..._glob_copy_..., ..._zip_or_rsync_style_copy_...; the two old tests that pinned exit 0 (not-ready note, tokens-only) now use a copy `fill` made; test_check_reads_parsed_json_forms now expects 4 problems |
| F2 | `check` runs `_check_open_place` on the open folder (git, /mnt, cloud-synced) and flags `st_nlink > 1` on any regular file; `delete` warns for place and hard links | test_check_refuses_a_copy_inside_a_git_repository_or_a_synced_folder, ..._on_a_windows_drive, test_check_flags_a_file_with_a_second_name_and_delete_warns, test_delete_warns_about_a_copy_in_a_git_repository_and_still_removes_it |
| F3 | manifest holds `"ready": true/false`; `check` reports a problem unless it is true (missing flag = problem); `delete` ignores it | test_manifest_records_ready_and_check_tokens_only_cannot_pass_a_deleted_note, test_a_manifest_without_the_ready_flag_does_not_pass |
| F4 | README and `_Stopped` docstring reworded: SIGINT, SIGTERM, SIGHUP handled; SIGKILL, SIGQUIT, SIGUSR1, SIGALRM, SIGXCPU and power loss are not | test_readme_names_the_signals_that_are_and_are_not_handled (also ties the handled set to `_STOP_SIGNALS`) |
| F5 | `delete` refuses an empty or not-clean folder name (`--out /`, control characters) before opening anything | test_delete_refuses_an_empty_or_unclean_folder_name |
| F6 | `allow_abbrev=False` on the main parser and the three sub-parsers; `check -h` still works | test_abbreviated_option_names_are_refused |
| F9 | one warning line (once per run) when neither /proc nor F_GETPATH answers | test_a_system_without_proc_or_getpath_says_so_once |
| F11 | README cite now `fix-f3-r8.md` (this file; 3.11/3.12/3.13 runs below) | - |
| F12 | swap test records that the swap ran and that the name is a link afterwards | edited test |
| F13 | each damage case asserts the exact message and the "manifest compare: ran against NAME.manifest.json" line | edited test |

## Gates (each rc taken from the command itself, no pipe)
- python3.11 -I -m unittest: rc 0, Ran 170 tests, OK (157 old + 13 new)
- python3.12 -I -m unittest: rc 0, Ran 170 tests, OK
- python3.13 -I -m unittest: rc 0, Ran 170 tests, OK
- ruff check: rc 0. ruff format --check: rc 0. bandit -ll -r fill_flows.py test_fill_flows.py: rc 0 (1 Low, no Medium or High).
- grep -c noqa/nosec/type: ignore: fill_flows.py 0, test_fill_flows.py 0.

## New tests against the OLD code (backup in the scratchpad `bak-f3r8/fill_flows.py`, new test file and README)
Ran 170, 13 not passing: 10 FAIL + 3 ERROR. Failing on old code: test_a_manifest_without_the_ready_flag_does_not_pass, test_a_system_without_proc_or_getpath_says_so_once, test_manifest_records_ready_..., test_check_reads_parsed_json_forms, test_abbreviated_option_names_are_refused, test_check_flags_a_file_with_a_second_name_and_delete_warns, test_check_refuses_a_copy_inside_a_git_repository_or_a_synced_folder, test_check_refuses_a_copy_on_a_windows_drive, test_check_refuses_a_folder_with_no_marker_no_manifest_and_no_tokens, ..._glob_copy_..., ..._zip_or_rsync_style_copy_..., test_delete_refuses_an_empty_or_unclean_folder_name, test_delete_warns_about_a_copy_in_a_git_repository_and_still_removes_it.
Pass on the old code (not behaviour tests of code): test_readme_names_the_signals... (the README is new in that run, so it checks the text only), F12 and F13 strengthened asserts, and the two re-based tests (they use a legitimate input case and also pass on old code). Raw log: scratchpad `old-code-run.log`.

## Mutants (12 hand-picked, F1/F2/F3/F5/F6/F9 code; full suite with -f, python3.12)
12 mutants: 12 killed, 0 survived after one test fix. First run: 11 killed, 1 survived (F9 "warn every time": `if not _WARNED...` changed to `if True`); the test only called `check` once, so it could not see a second line. I added two more `_fd_path` calls in the same run that must print nothing; re-run of that mutant: killed (rc 1).
Killed: F1 no problem counted for unmarked folder; F1 `marked = True`; F2 nlink `>1` to `>2` in check; F2 place check removed in check; F2 place problem not counted; F2 delete place warning removed; F2 delete nlink `>1` to `>5`; F3 `ready` always true; F3 `is not True` to `is False`; F5 clean-name check off; F6 abbreviation allowed on `check`; F9 warn every time.
Gates re-run after that test change: 3.11, 3.12, 3.13 each rc 0, Ran 170 OK; ruff check 0; ruff format --check 0; bandit -ll 0; noqa/nosec/type: ignore count 0 in both files.

## Left as stated (one line each)
- F7 (README "through that open folder" but the last rmdir/unlink go by name): fail-safe; the name-based final step can only fail, not touch another folder, because the open handle's contents were checked first.
- F8 (no directory fsync in fill): fail-safe; a lost entry after power loss leaves a missing file, which `check` reports.
- F10 (a `~/.git` dotfiles repo counts as a git repo): fails closed (refuses more, never less).
- F14 (values under 4 characters are not detectable in output): by design; such a value cannot be told apart from ordinary text in a screen check.
- F15 (test_exit_codes_are_literal mostly asserts constants): constants test, pins the documented numbers; no behaviour to add.
