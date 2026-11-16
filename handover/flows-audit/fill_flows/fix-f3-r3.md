# F3 fix, round 3 (fixer, 2026-11-16). Files: fill_flows.py, test_fill_flows.py, README.md. Not committed.
Mutants were applied on scratch copies under /tmp/f3m/r3/ (repo never mutated); full suite each: all 4 survivors and the 2 new checks now FAIL the suite.

## Mutants
- M5 (S_ISREG in the no-manifest check): killed by test_no_manifest_force_hash_refuses_a_folder_named_like_a_json_file and test_no_manifest_refuses_a_fifo_without_hanging (a 0600 folder or pipe named x.json passed every other check; unlink would fail half way).
- M7 (manifest-exists refusal on fill): killed by test_fill_names_a_leftover_manifest_plainly (without it: "failed: FileExistsError", no plain message).
- M8 (inside_git(out_dir)): dead code, removed. The output folder must not exist, so it has no .git; its parents are checked by inside_git(parent); a link as output is refused as "already exists". Test: test_fill_into_a_symlink_that_points_into_git_names_the_real_cause.
- M13 (manifest-symlink check on delete): killed by test_delete_no_manifest_refuses_a_symlink_or_folder_in_the_manifest_place (link and folder in the manifest place, with and without --force-hash).

## Hostile cases from evidence section 5 and 6
- Symlinked output parent: now checked (_check_parent_links, fill and delete). Accepted when owned by you or root (target still checked for /mnt and git); refused when made by another user. Tests: test_symlinked_parent_of_my_own_is_accepted_and_works_end_to_end, test_symlinked_parent_made_by_another_user_is_refused; mutants "owner test off" and "call removed" both killed by the second.
- delete --no-manifest on a tool-made folder with a file changed to other valid JSON: accepted, reason in README ("What delete --no-manifest cannot tell"): no fingerprint exists; signature is 0700/0600/yours/.json/parses/no $env.
- Quotes, backslashes, ${x}, unicode, 10 KB, CR, newline, {{x}}, $env.X in values: already correct (written escaped or refused); covered by existing tests.
- Existing output, output symlink, unwritable parent: refused, existing tests. Plain-input folder, extra file, folder 755, truncated JSON, $env text, symlink file, changed file: refused, existing tests.
- Evidence note: check ends 1 while placeholders remain; README exit table now says so.

## Not done
Not run: a live n8n import (take-day step). Group-writable real parent folders are not refused (common home setting); accepted, 0700 folder and 0600 files.

## Round 4 (survivors of evidence-f3-r4)
- Values-file regular-file check: it was unreachable (a folder failed earlier in fdopen; a pipe would hang on open). Fixed: open with O_NONBLOCK, fstat before fdopen. Killed by test_values_file_must_be_a_regular_file and test_values_file_pipe_is_refused_without_hanging (mutant A).
- Symlinked-parent check removed from delete: killed by test_delete_refuses_a_parent_link_made_by_another_user (the earlier test passed only because the folder did not exist). Mutant B.
- check skipping SMTP_CREDENTIAL_ID: killed by test_check_reports_every_one_of_the_six_placeholder_names (all six names). Mutant C.

## Round 4 (security review, review-security-r1.md; each item checked in the code first)
- M1 modes assumed: real. Fixed: every new file is fchmod 0600 and fstat-checked (owner, mode), the folder too; on failure the run removes what it made and says "modes do not hold". Tests: test_modes_that_do_not_hold_on_the_disk_refuse_and_leave_nothing (file and folder). Mutants D, E killed. /mnt hint kept.
- M2 path TOCTOU: real. Fixed: parent opened once, folder opened O_DIRECTORY|O_NOFOLLOW, all mkdir/open/listdir/lstat/unlink/rmdir use dir_fd; no chmod by path. Tests: test_fill_folder_swapped_for_a_link_after_mkdir_writes_nothing_there, test_delete_path_swapped_for_a_link_after_opening_leaves_the_decoy_alone. Mutants M (path unlink) and N (follow link) killed. Not done: refusing a group-writable parent: not needed now, we hold the folder open (the parent path is resolved once; a link there must be yours or root's).
- M3 weak no-manifest signature: real. Fixed: marker file .fill_flows-output (format + folder name, in the manifest too) is required. Tests: test_no_manifest_needs_the_marker_file, ..._refuses_a_marker_for_another_folder_or_format, test_hand_made_folder_of_json_files_is_not_deleted_without_manifest. Mutants F, G killed.
- Minor 4 lexer: test_lexer_agrees_with_a_real_js_engine (600 seeded random expressions; accepted ones compared with the unfilled text in node; skipped where node is absent). It found no difference. It checks outputs, not the lexer's inside; node 22 here.
- Nit 5 raw names: all printed names go through ascii (_a). Test test_names_from_disk_are_printed_safely; mutant L killed.
- Nit 6 manifest hash guessable: documented in README (same owner and mode as the filled files, so no extra exposure). Nonce not added: it would sit in the same file, no gain.
- Nit 7: key collision refused (test_two_keys_that_become_one_are_refused, mutant I); placeholder name alone in a code field refused (test_placeholder_name_inside_a_code_field_is_refused, mutant J); manifest validated before removal with --no-manifest and no folder (test_no_manifest_with_no_folder_still_validates_the_manifest, mutant K); manifest-mode delete checks folder and file owner (test_manifest_delete_refuses_a_folder_that_is_not_yours, mutant H). Embedded-placeholder exit 3 documented.
- Portability: README states Python 3.9+ (run only on 3.11-3.13; 3.9 and 3.10 NOT run: no interpreter here; next step: run the suite on 3.9 in CI or a machine that has it). macOS line replaced by (umask 077; : > file). Test file got `from __future__ import annotations`. Not run: macOS, WSL.
- Tests changed because of the marker file: folder now holds 5 files (4 flows + marker); delete message counts flow files only.
- New tests fail on the pre-round code (/tmp/f3m/fill_flows.r3.bak): 17 failures, 12 errors (the old suite's own tests also need the marker).
