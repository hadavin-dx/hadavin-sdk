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
