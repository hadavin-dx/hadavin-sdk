# Evidence: PD part 6 batch 8, head 07bfda12678f49b90f970ad320cb8f07580f44cb (previous 41c84695)
EVIDENCE RUNNER. Records only, no judgement. Date 2026-11-13, clock 02:22 to 02:31 UTC (07:52 to 08:01 IST). Raw logs: /home/user/build/evidence-raw/pdbanner8-runner/.
Checked: worktree /home/user/build/ER-pdbanner8 `git rev-parse HEAD` = 07bfda12678f49b90f970ad320cb8f07580f44cb, `git status --short` empty before and after. Tests ran with PYTHONPATH=src on venv pdbanner-b8-venv (its editable install points at another worktree, so PYTHONPATH was needed). No cloud variables set. Heavy runs went through heavy.sh; every one got a slot at once (no wait).

## 1. Not run / deviations (read first)
- RUN ON LAPTOP: hadavin-sdk 07bfda12678f49b90f970ad320cb8f07580f44cb pytest -q full + banner_mutants complete. The full pytest was NOT run here (order). What I ran instead: 475 focused tests.
- banner_mutants: I ran ALL 247 rows here (chunks of 41, 103, 103; each under 3 minutes), not only the required subset. This is still not the lead's laptop "complete" run (it is the same table, run by my own driver chunk.py that calls the same run_mutants function as tests/banner_mutants.py).
- Builder claims versus what I saw: builder said table 246 rows; the table at this head has 247 rows (and the builder's own banner_mutants.log says "245 of 245"; it was from an earlier head). The builder said 12 intended crash rows: matches (B5 B7 B13 B34 B43 B44 B52 B53 B54 B62 N6 N7).
- Builder said 7 test_pin_* tests pass on the old code. On the old code 5 of the 7 passed and 2 FAILED: test_pin_the_page_lists_and_the_python_lists_of_overrides_agree and test_pin_the_blank_set_of_python_and_of_the_page_literal_is_one_set. The builder's claim does not hold for those two.
- Fail-before used the old src and tools of 41c84695 with the delta test files copied in; the delta also lists tests/refusal.py and tests/test_workflow_files_parse.py, which are byte-identical in both heads (no change to copy).
- The "ValueError ... showing the not-confirmed banner" log line appears on every call of App.mode_banner() for an unsealed or changed App (seen in probe 5). Recorded, not judged.
- Not checked: id() reuse of a replaced part (the seal compares object identities; I did not try to reuse a freed address); own Postgres (no test needed it, none started); the 3 older ER-pdbanner*-old worktrees listed by git belong to earlier runners and were left alone.
- bandit prints two warnings ("Test in comment: bytes is not a test name", nosec B102 at src/hadavin_sdk/tools.py:389 with no failed test); exit 0.

## 2. Results
| item | command | exit | last line |
|---|---|---|---|
| focused tests | pytest -q tests/test_mode_banner.py test_demo_only_guard.py test_demo_only_guard_ci.py test_banner_mutant_table.py test_repo_rules.py test_workflow_files_parse.py test_lockin_guard.py test_stage_names.py test_cuj.py -m "not live and not perf" | 0 | 475 passed in 27.68s |
| banner_mutants chunk 1 (41 rows: all crash rows, R7*, G38 G72 G91 G95 B31 B35 J23a J23b) | chunk.py c1.txt | 0 | 41 of 41 good; problems: []; elapsed 56s |
| banner_mutants chunk 2 (103 rows) | chunk.py c2.txt | 0 | 103 of 103 good; problems: []; elapsed 127s |
| banner_mutants chunk 3 (103 rows) | chunk.py c3.txt | 0 | 103 of 103 good; problems: []; elapsed 128s |
| all chunks together | counts of ok / BAD in c1.chk c2.chk c3.chk (checkpoint files, one per chunk) | | 247 ok, 0 BAD (E9 and E10 of the order = rows R7E9, R7E10; no row is named E9 or E10 alone) |
| stage_mutants | python tests/stage_mutants.py | 0 | 37 of 37 good; problems: [] |
| ruff check | ruff check src tests demos tools | 0 | All checks passed! |
| ruff format | ruff format --check src tests demos tools | 0 | 327 files already formatted |
| bandit | bandit -q -r src demos tools -ll | 0 | warnings only (see above), no issue lines |
| scan_repo | python tools/scan_repo.py | 0 | (no output) |
| gitleaks | gitleaks git --redact --no-banner --config .gitleaks.toml --log-opts refs/remotes/origin/main..HEAD | 0 | 19 commits scanned. no leaks found |
| handover files check | check-no-handover-files.sh wip/cloud-pd-banner 07bfda12 | 0 | (no output) |
| fail-before | the 6 delta test files on a detached worktree of 41c84695 with its old src and tools | 1 | 32 failed, 270 passed in 22.60s |

## 3. Fail-before detail (old code 41c84695, new tests; list in failbefore-failed.txt)
Failed on old code (32): test_banner_mutant_table: test_every_row_of_the_table_has_its_own_label_and_a_search_text_found_exactly_once. test_demo_only_guard (16): compiled_or_packed_file_refused_by_first_bytes; failed_git_call_first_line_masked; one_lstat; over_the_size_cap; program_mark_and_nul_bytes; vanishes_at_any_point; loop_of_links_is_a_hit; loop_of_tracked_links_copy_run; parent_folder_swapped_for_a_link; bzip2_needs_a_level; every_first_byte_kind_is_a_hit_by_kind; git_message_hides_names_with_key_or_token; listings_of_tracked_files_agree; samples_cover_exactly_the_kinds; two_chained_links; without_the_walk_flags_a_link. test_demo_only_guard_ci: changelog_names_exactly_the_first_byte_kinds. test_mode_banner (14): forged_unconfirmed_text; tag_or_text_of_code_points_python_and_page_disagreed_on; ten_million_characters_astral; app_copied_or_changed_after_build; app_made_by_hand; app_build_records_the_overrides; each_override_alone; every_build_parameter_is_an_override_or_on_the_list; given_overrides_counts; no_override_keeps_the_demo_banner; overridden_is_a_required_keyword; test_pin_the_blank_set...; test_pin_the_page_lists...; the_blank_set_is_what_python_strip_and_javascript_trim_both_call_white_space. (The full names are in /home/user/build/evidence-raw/pdbanner8-runner/failbefore-failed.txt; two extra lines there, test_env.py::test_env and test_needs.py::test_needs_folder, are summary lines of small inner pytest runs printed by -rA, not failures of this table.)
Passed on old code, the 5 test_pin_* tests: test_pin_a_tag_that_is_not_plain_text_is_not_painted_as_given; test_pin_a_text_that_is_not_plain_text_is_not_painted_as_given; test_pin_the_changelog_list_of_endings_that_may_skip_the_text_read_is_the_marks_table; test_pin_the_crash_rows_are_exactly_the_pinned_set_and_only_they_expect_an_interpreter_message; test_pin_a_planted_interpreter_message_outside_the_pinned_set_is_reported.

## 4. Hostile probes (made-up data only; scripts probe_guard.py, probe_js.js, probe_app.py; outputs probe_*.log)
Guard (made-up git repos with src/templates/tools/demos; only hits under src/ shown, no traceback in any case):
- link chain a_link -> b -> c -> ../tools: all 3 links hit symlink-in-product-root. Link loop l1 <-> l2: both hit. Parent folder src/sub replaced by a link after commit: src/sub hit (a static swap, not a timed race; the timed race is covered by the test list above).
- File removed right after its first stat: hit "unreadable-file", no traceback.
- Fat Mach-O bytes, Java class bytes, RAR, MZ plus NULs: each 1 hit by kind ("binary-in-product-root"). bzip2 with a valid block mark at level 9, level 5, and an end-of-stream mark at level 5: hit. bzip2 level byte 0: NOT a hit. bzip2 level 5 with a bad block mark: NOT a hit.
- git "dubious ownership" text: shown as "fatal: detected dubious ownership in repository at '<repo>'" (path masked, first line only).
- _hide_secrets: bypass=true shown; bypass_key=abc -> bypass_key=<hidden>; bypass_token=abc -> bypass_token=<hidden>; "Bearer abc" alone unchanged (not hidden); "Authorization: x" -> "Authorization: <hidden>"; https://user:pass@host/p -> https://<hidden>@host/p; 10000-character line unchanged, no error; control characters and U+2028 passed through unchanged by _hide_secrets (the later printable() step handles them); latin-1-style characters fine. _git_failure on non-UTF8 bytes, bytes with NULs, empty and a 10000-character line: never raised; output cut (274 characters in total for the long line).
Page script (node 22, templates/mode-banner/mode_banner.js usable()): forged unconfirmed text -> the fallback; exact own words -> accepted as unconfirmed. U+0085, U+001C, U+FEFF, U+00A0 only, in the tag or in the text -> fallback; U+200B only -> NOT fallback (accepted as visible text). 10,000,000-unit ASCII string and 5,000,000 astral characters (10,000,000 units): refused, 0 ms each. Astral x599 and x600 accepted, x601 refused; plain x600 accepted, x601 refused; mixed 300 astral + 300 plain accepted, 601 refused.
App (built with FakeChannel and FakeSecretProvider through the test helper): build records overridden = ('channel','secrets'), banner tone unconfirmed listing both. Sealed with () and untouched: tone demo. dataclasses.replace of a built App: unconfirmed (original stays demo). Attribute llm set after build: unconfirmed. New non-field attribute: unconfirmed. Hand-made App (never sealed): unconfirmed (it carries overridden=('channel','secrets') copied in, still unconfirmed because it was never sealed).

## 5. Cleanup
Removed worktrees ER-pdbanner8 and ER-pdbanner8-old, folder er8-tmp (probe repos). No Postgres started. No background process of mine left (a start of focused.sh with output to /dev/null at the beginning was stopped by me; its pattern kill touched only my own command lines). Nothing committed or pushed. No spend, no live calls.
