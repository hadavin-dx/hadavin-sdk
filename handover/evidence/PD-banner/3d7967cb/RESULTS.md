# Evidence PD banner batch 5, head 3d7967cb653022b66cece04d2767f45303e4b483 (EVIDENCE RUNNER, no judgement)
Worktree /home/user/build/ER-pdbanner5 at that sha, status clean. Raw logs: /home/user/build/evidence-raw/pdbanner5-3d7967cb/ (outside the repo). Priority 1 not used; folder name gave heavy.sh priority 2.

## Not run / deviations (first)
- Item 2 stage_mutants (expect 37 of 37): NOT RUN. Queued behind other agents' heavy jobs for 14+ minutes, never started; I stopped my queued jobs when told to hand back.
- Item 3 banner_mutants (expect 180 of 180): NOT RUN, same reason. Only the table check was run: 180 rows, non_unique_rows() == [].
- check-no-handover-files.sh was run from /home/user/hadavin-sdk (needs origin/main refs), not the worktree.
- Postgres 16 own instance, port 55432, started as OS user postgres; stopped. HADAVIN_TEST_PG_DSN pointed at it; HADAVIN_REQUIRE_NODE=1.
- Full run: 1 skipped (tests/contracts/test_llm.py:95 Stubber); no Vault skips this time.
- Fail-before inner pytest child output adds one extra FAILED line (test_env.py); the 30 count excludes it.
- Probe 6b file-mode-000 case needs a non-root user: run as nobody. Probe configs set exempt_files and allowed_phrases to [] and one fake-id pattern.

## Results
| Item | Command | Exit | Last line |
|---|---|---|---|
| 1 full pytest | heavy.sh uv run --no-sync pytest -m "not live and not perf" -rs | 0 | 10697 passed, 1 skipped, 28 deselected in 355.09s |
| 2 stage_mutants | not run | - | - |
| 3 banner_mutants | not run | - | - |
| 4a ruff check src tests demos tools | | 0 | All checks passed! |
| 4b ruff format --check | | 0 | 326 files already formatted |
| 4c bandit -q -r src demos tools -ll | | 0 | only nosec warning src/hadavin_sdk/tools.py:389 |
| 4d scan_repo.py | | 0 | no problems printed |
| 4e gitleaks (origin/main..HEAD, 11 commits) | | 0 | no leaks found |
| 4f check-no-handover-files | | 0 | no output |
| 5 fail-before (a16b7635 old src; 6 changed test files copied) | pytest 4 test files | 1 | 30 failed, 139 passed |
| 6a banner probes (45 inputs) | probe_a.py | 0 | VIOLATIONS 0 of 45 |
| 6b guard on 15 trees + nobody case + --require + bad root | probe_b.sh | see below | |
| 6c --without-folder | probe_c | see below | |
| 6d page script, 21 cases | probe_d.sh | | threw empty and htmlWrites 0 in all |
| 6e planted duplicates | probe_e.py | 0 | found 2 times / 0 times / label twice |

## Fail-before
34 test functions added in the delta; 24 fail on old code, 10 PASS on old code: PASS-ON-OLD: test_a_failing_mode_attribute_leaves_the_not_confirmed_tone_with_its_text PASS-ON-OLD: test_a_full_width_product_root_that_is_the_folder_is_a_hit PASS-ON-OLD: test_a_planted_duplicate_or_missing_search_text_or_repeated_label_is_reported PASS-ON-OLD: test_a_tool_specs_that_is_not_a_mapping_is_refused_with_a_type_error PASS-ON-OLD: test_a_url_and_a_bare_host_give_the_same_answer_for_every_spelling PASS-ON-OLD: test_an_empty_name_is_never_in_a_text PASS-ON-OLD: test_the_loopback_names_are_pinned_by_content PASS-ON-OLD: test_the_page_trusts_the_tone_it_is_given_and_python_checks_the_sentences PASS-ON-OLD: test_the_table_has_no_loose_expectation_left PASS-ON-OLD: test_the_tools_of_a_real_registry_are_what_the_banner_reads . 30 failing ids: failbefore-failed-ids.txt.

## 6a
No input produced "made-up" with a real service. Raised (not a banner): unknown mode, bad names (control, unicode, full-width, angle brackets, made-up words), non-mapping names/lists, 10000 names (over 600 chars), odd tool hosts types. Real tone: odd hosts (newline, padded, full-width localhost, URLs, 127.0.0.1:8080 in egress), outside systems, tool_modules with tool_specs None. Demo tone only for loopback bare host, empty lists, localhost URL on a system.

## 6b
Exit 0 clean tree; exit 1 for folder in root, naming folder (BOM, CRLF, full-width, UTF-16, UTF-32 in .png), fake id, symlink, .pyc, 9 MB file, FIFO (unreadable-file), mode-000 file (as nobody), missing root; --require without folder exit 2; nonexistent root exit 1. No matched text (sentinels, fake id) printed in any output.

## 6c
--without-folder: passing tree exit 0 (2 passed, package imported from copy); tree whose test needs the folder exit 1; --without-folder-if-present with no folder exit 0.

## 6d
Bad banners (null, undefined, array, empty, missing fields, script tags, contradiction, unknown tone/mode, 601 chars, throwing getter/proxy/list) paint UNCONFIRMED text lines, no HTML writes. Observation: with a failing tone-attribute write, or all writes failing, the element keeps "previous banner text" and has 0 child lines (log probe-d.log).

## 6e
Duplicates planted in a copy: B1, J14, G73 and also J8f reported "found 2 times"; text not found: "found 0 times"; label twice: "label used twice". Real worktree stayed clean.

Helpers stopped: Postgres, queued mutant jobs, monitors. Worktrees ER-pdbanner5 and ER-pdbanner5-old left on disk (not removed).

## Lead note (added when saved)
Stage mutants (37 expected) and banner mutants (180 expected) were NOT run by this runner (queued behind other jobs, then stopped on hand-back); only builder numbers exist for them. Folder name gave heavy slot priority 2. This head is superseded by batch 6 (round 5 found 5 Major raw); the final head needs a complete runner including both mutant tables.
