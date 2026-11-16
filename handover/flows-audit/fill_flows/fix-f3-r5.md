# fix-f3-r5: fixes for review-security-r2.md (12 findings + test notes)

Security path (uncapped). Author: fix builder (Sonnet 5.5). Values in all tests are made up. Nothing committed.
Date of the run: 2026-11-16 (UTC). Machine: Linux, running as root (uid 0), Python 3.11, 3.12, 3.13, node 22 present.

## Failed, uncertain, not checked (first)
- NOT run: Python 3.9 and 3.10 (no interpreter here), macOS (the `F_GETPATH` branch of `_fd_path` is written but never executed), Windows/WSL, NFS/FUSE, sync folders. Third party / environment: needs a Mac and the two interpreters; next step: run `python3 -I -m unittest` there.
- NOT verified against a real n8n: whether `n8n import:workflow --separate --input=DIR` skips non-JSON files. Finding 12 is fixed by exit code 3 plus a `NOT-READY-DO-NOT-IMPORT.txt` file; the README says plainly that a tool that imports every file of a folder on its own is not stopped by the note (only `&&` and the note protect). Needs n8n (the owner's n8n); next step: try it on the free-trial n8n.
- Tests run as root: the chmod 0500 step cannot fail on permissions here; the test now asserts the tool's own message, so it also holds for a non-root user (not run as non-root; no second user was tried).
- Whole-repo `ruff check` / `ruff format --check` from /home/user/hadavin-sdk end rc=1 (1267 errors, 110 files to format) in OTHER handover files that I did not touch. Scoped to this folder: rc 0 / rc 0. I did not fix the other files (outside the task). The full repo `pytest` run was started in the background; its result is at the bottom (see "Full repo pytest").
- A git "board" process commits the working tree about once a minute, so `git status` shows my edits as already committed; I made no commit.
- Finding 2 part "route raw open() writes through WRITTEN" is done for every values-file write in the test file; the three remaining plain `open()` calls write flow files or hash reads, not values.
- Finding 10: the allowlist is a judgement: it lists five address keys (`url`, `toEmail`, `fromEmail`, `ccEmail`, `bccEmail`), none of which the real v5 flows use in a plain text (counted by a test). If a future flow needs a token in a plain field of another name, the fill refuses it and names the field; the owner/builder then adds the key.

## Review items, checked against the code (where the review was wrong or loose)
| # | Verdict on the review | Fix |
|---|---|---|
| 1 lexer | Correct (line numbers were from an older version). The backtick toggle sees a token inside a nested template as outside. | `_expr_part` refuses any part that holds a hit token and a backtick or `${` (message TEMPLATE). `_js_literal` left alone: a backtick or `${` inside a double-quoted string is harmless. Nested forms added to `test_nested_template_refused` and as fixed cases in the node-oracle test. |
| 2 | Correct. | Canary inside the exception text (`flaky` raises `OSError("... CANARY")`, plus `test_exception_text_is_never_printed` for do_check, do_delete, do_fill); `leak_check` now looks for plain, JSON-escaped (both ASCII and not), `ascii()` and `repr()` forms; every hand-written values file goes through `write_raw` (registers values in WRITTEN). `test_leak_check_sees_escaped_forms` proves the checker catches each form. |
| 3 | Correct. | `test_fill_folder_swapped_for_a_link_after_the_open_writes_nothing_there`: swaps right after the folder is opened. |
| 4 | Correct. | `delete --force-hash` removes an empty or cut manifest when no folder exists (still refused: a link, a non-file, a file not yours); without `--force-hash` still refused. Fill's "already exists" message now names `delete --out ... --force-hash`. README says so. Files are now fsynced after the write (a power cut; a kill is not helped by it, said in README). |
| 5 | Correct. | `delete` with nothing there prints "nothing to delete" and exits 0; `test_nothing_there` updated (also the second delete after a real delete). |
| 6 | Correct. | `_fd_path` (Linux `/proc/self/fd`, macOS `F_GETPATH`, else the checked path) and `_check_open_place`: /mnt and git checks re-run on the opened output parent, on the opened output folder, and on the opened values file. Tests swap the link between the name check and the open for the values file and for the output parent. |
| 7 | Correct. | With `--no-manifest` a sibling manifest is removed only if it is a valid manifest, or with `--force-hash` if it is a plain file of yours; an invalid one makes delete refuse before anything is deleted. README matches. |
| 8 | Correct (a backslash name is legal on Linux and then cannot be deleted by the manifest route). | Fill refuses input names and the output folder name that are not plain or hold control/format/line/lone-surrogate characters (not in `check`, which only reads and prints safe names; the existing escape test stays valid). |
| 9 | Correct, and wider than the review said: `1e999` loads as infinity (not NaN), so the old code wrote `Infinity`. | `allow_nan=False` in `dump`; load also refuses a number that reads as infinity (`parse_float`). |
| 10 | Real flows allow it (counted: every token in both v5 sets is inside an `={{ }}` expression; none in a plain text). | `PLAIN_KEYS` allowlist; a plain token elsewhere (also in a key name) is refused with the field name. Tests: `test_plain_token_outside_the_address_fields_is_refused`, `test_real_flows_hold_no_plain_token`. Existing tests that relied on plain fill everywhere were rewritten. |
| 11 | Correct. Mkdir had the same window. | Creation and the clean-up list entry happen in one step with Ctrl-C blocked (`signal.pthread_sigmask`), inside `_write_new` (it now takes the list) and around `os.mkdir`. A pending Ctrl-C is delivered right after. |
| 12 | Partly: exit code was already 3 (non-zero), so `fill; import` was the only gap. | Folder gets `NOT-READY-DO-NOT-IMPORT.txt` (in the manifest, allowed by the `--no-manifest` signature with exact-text check, not counted as a flow file), `check` reports it, the stderr line names it; README says `fill && import`. `test_fill_then_import_stops_when_placeholders_are_left` runs a real `sh -c 'fill && echo IMPORTED'`. |
| notes | Correct. | chmod 0500 and getuid steps now assert "mode 0700 and yours"; property test runs 5 fixed seeds. "Tests need real flows under handover/demo" is kept on purpose (the real flows are the subject; `FF_DEMO_DIR` is documented). |

## Proof the new tests fail on the old code
Method: old `fill_flows.py` (the version before this work, saved in the scratchpad) with the NEW test file, run in a scratch folder (`.../scratchpad/oldrun`), demo folder pointed at the real one.
Result on old code: 113 tests, 27 failures + 4 errors. The failures that show a real old behaviour (not just a changed count or message):
- `test_nested_template_refused`, `test_lexer_agrees_with_a_real_js_engine` (node: the old output means something else than the input)
- `test_plain_token_outside_the_address_fields_is_refused`
- `test_a_number_that_reads_as_infinity_is_refused`
- `test_delete_force_hash_removes_an_empty_or_cut_manifest_when_no_folder`, `test_fill_refusal_names_the_way_out_of_a_cut_manifest`
- `test_nothing_there`
- `test_values_file_swapped_into_git_after_the_name_check_is_refused`, `test_output_parent_swapped_into_git_after_the_name_check_writes_nothing`
- `test_fill_folder_swapped_for_a_link_after_the_open_writes_nothing_there` (old code passes the same idea only for a swap before the open; here it failed because of the changed file count, so this one was ALSO proven with a mutation, below)
- `test_no_manifest_does_not_remove_an_invalid_sibling_manifest`
- `test_input_names_with_a_backslash_or_control_character_are_refused`, `test_output_folder_name_with_a_backslash_is_refused`
- `test_interrupt_right_after_a_file_is_written_leaves_nothing`, `test_a_real_ctrl_c_during_creation_leaves_nothing`
- `test_incomplete_copy_is_marked_not_ready`
Errors on old code (new function missing): `test_fd_path_follows_the_handle_not_the_name`, `test_delete_handles_the_not_ready_note`, `test_token_forms`, `test_token_refusals_in_process` (new `field` argument).
Tests that pass on both old and new code, by design (they check kept behaviour or the test tool): `test_leak_check_sees_escaped_forms`, `test_force_hash_does_not_remove_a_manifest_that_is_a_link`, `test_no_manifest_removes_a_valid_sibling_manifest`, `test_fill_then_import_stops_when_placeholders_are_left` (old exit code was already 3; the test locks the README claim), `test_real_flows_hold_no_plain_token`.

Mutation checks on the NEW code (scratch copies `m-a` .. `m-e`, one change each), new tests must go red:
- a. `main` prints the exception text: `test_exception_text_is_never_printed` and `test_failed_write_removes_everything_and_manifest_goes_first` FAIL (2 of 2).
- b. fill writes by path after the open: `test_fill_folder_swapped_for_a_link_after_the_open_...` FAILS.
- c. Ctrl-C not blocked: `test_a_real_ctrl_c_during_creation_leaves_nothing` FAILS (the other interrupt test passes, as it tests the list entry inside `_write_new`, which was not mutated).
- d. `_fd_path` returns the fallback: `test_fd_path_follows_the_handle_not_the_name` and the values-file swap test FAIL. The output-parent swap test still passes under this mutation: the fallback is `realpath` taken after the swap, so it also sees the new place; the old code is what that test catches.
- e. lexer fix removed: `test_nested_template_refused` and the node-oracle test FAIL.

## Gate results (from /home/user/hadavin-sdk, repo pyproject)
- `python3.11 -m unittest` in the folder: rc 0, 113 tests OK. 3.12: rc 0, 113 OK. 3.13: rc 0, 113 OK (was 91 tests before). The node-oracle test ran (not skipped).
- `uv run --all-extras --group test pytest -q handover/flows-audit/fill_flows`: rc 0, 113 passed.
- `uv run --all-extras --group test ruff check handover/flows-audit/fill_flows`: rc 0. `ruff format --check` same folder: rc 0 (18 files formatted). `bandit -ll -r handover/flows-audit/fill_flows`: rc 0, no issues (6 Low, not shown at -ll).
- Whole-repo ruff check/format (no path): rc 1 because of other handover files (see top).

## Files changed
- fill_flows.py, test_fill_flows.py, README.md, fix-f3-r5.md (all in handover/flows-audit/fill_flows/).

## Full repo pytest
(see the end of this file for the result line once the background run ends)
