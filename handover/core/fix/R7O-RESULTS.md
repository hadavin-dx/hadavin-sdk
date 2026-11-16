# R7O results (patch r7o = r7n + 1 source change + tests/test_r7o_findings.py)

## Not done / not checked (first)
- Item 8 NOT folded in: at the end of my run (10:05 UTC) neither handover/core/review/core-fix-on-frozen-r7n-review.md nor handover/core/fix/EV7N-EVIDENCE.md existed, and no message with a Blocker/Major arrived. Needs the lead: send me (or the next builder) those findings; next step = read both files, add tests.
- No full suite run (as ordered). Groups run on final bytes: A = test_load_tools, r7k, r7l, r7j, r7i, r7n, r7o files: 502 passed; B = test_real_check_dry, file_reader_refusals, crash_flag_reads, crm_hubspot, n8n_api_url, r7c_one_json_loader, ca_file_reads, live_claude, r7_inputs_and_replies, load_driver_facts, smtp_provider, crash_points: 562 passed, 1 skipped (root can read a no-permission file). Raw: finalA.log, finalB.log.
- Item 1 second half ("no limit uses another number than the printed one"): I checked that the banner figure is the only place persons/crash factor enter a money number in run_real_check.py (grep: live_worst, persons + 3, cap_run); the real limits are the per-run and total caps from the live settings, which the desk applies itself and the banner prints (per-run cap). I did not read the r7n reviewer's text (not written yet), so a finding there is unchecked.
- Pass-12 text for M9-82 said REAL_DRAIN_SECONDS; that setting has only "above 0". The minimum 5 / refused 4 is REAL_HUBSPOT_READBACK_MAX_CALLS (MIN_READBACK_CALLS = 5, mutant `<` -> `<=`). I pinned that.
- Existing tests changed: NONE (no old/new line needed).

## Source change (one)
- src/lead_desk/regfile.py read_regular_text: decode("utf-8") -> decode("utf-8-sig"). NEEDED-CHECK decision for M10-J09: a leading byte-order mark is ACCEPTED on purpose (the key/password reader, the CA reader and the invariant checker already accept it; Windows editors add it). Effect: json file with BOM loads, flag files with BOM are read as the point name (before: U+FEFF kept, a BOM flag silently never fired, BOM config "not NAME=VALUE"), config with BOM loads. A second mark or one inside the text is kept and is not JSON. All three readers and json agree because they share this one function.
- M9-79, M9-74, M10-J13, M9-56, M10-J02, M9-82: source already right on r7n; tests are PINs.

## Fail-before (r7n copy tree-R7O-fb + the new test file; raw fb1.log)
4 failed (all four BOM tests: json/text reader, only-one-mark, flag readers, config), 14 passed (PIN). On r7o: 18 passed (new1.log).

## Mapping finding -> test -> mutant killed (mutants planted on tree-R7O-mut by mut.py; mut-results.tsv, mutraw-*.txt; tree restored byte-for-byte after each, diff -rq clean except the test file I fixed afterwards)
| finding | test (tests/test_r7o_findings.py) | mutant | result |
|---|---|---|---|
| M9-79 | test_the_live_cost_line_counts_every_call_of_every_person_and_both_desk_processes[8,9,15] | O01 drop `* 2` | KILLED |
| M9-79 | same | O02 persons + 1 | KILLED |
| M9-79 | same | O03 wrong variable (hs.max_calls instead of MODEL_CALLS_PER_LEAD) | KILLED |
| M9-74 | test_a_contact_left_after_the_clean_up_is_said_and_ends_with_the_failed_exit_code (Flaky archive fails first contact, real dry fakes) + test_a_clean_up_that_leaves_nothing_ends_with_zero | O04 `and not left` removed from the return | KILLED |
| M9-74 | same | O11 EXIT_FAILED replaced by 0 | KILLED |
| M10-J13 | test_bytes_that_are_not_utf_8_are_refused_never_decoded_with_a_replacement (4 byte strings, both readers) | O05 errors="replace" | KILLED |
| M10-J09 | test_a_leading_byte_order_mark_is_dropped_..., test_a_flag_file_saved_with_a_byte_order_mark_..., test_a_config_file_saved_with_a_byte_order_mark_... | O06 back to plain utf-8 (the r7n source) | KILLED |
| M10-J09 | test_only_one_leading_mark_is_dropped_... | O07 lstrip of every mark | KILLED |
| M9-56 | test_a_login_part_in_the_hubspot_base_address_is_refused[3 forms] | O08 `parts.username` removed | KILLED |
| M10-J02 | test_too_deep_json_raises_one_fixed_error_without_the_recursion_error_behind_it | O09 `from None` removed | KILLED |
| M9-82 | test_the_minimum_readback_cap_is_accepted_and_one_below_is_refused | O10 `<` -> `<=` | KILLED |
11 mutants of my own, 11 killed. Mutant runs used `-k` on the matching tests plus `-x`, not the whole file, so "killed" means the named tests fail; a mutant that only the rest of the file would catch is not measured.

## Ruff 0.17.1 (on a copy of the final tree): check "All checks passed!", format --check "227 files already formatted". No new suppression. Bandit not run.

## Deliverables (out/R7O/)
core-fix-on-frozen-r7o.patch (CRLF as chain), core-fix-on-frozen-r7o-lf.patch, core-fix-r7n-to-r7o-delta.patch (regfile.py + the new test only), sha256-r7o.txt, apply-matrix-r7o.txt (a, b CRLF checkouts and c LF checkout: git apply --check rc=0 for all three; byte-for-byte same as tree-R7O and delta-on-r7n gives r7o were printed by build_patches.sh), checkpoint.md, scripts build_patches.sh / apply_matrix.sh / mut.py / runtests.sh.
Trees: tree-R7O (work), tree-R7O-base (untouched r7n), tree-R7O-fb (fail-before), tree-R7O-mut (mutants). No pytest or runner left running; nothing applied, pushed or committed.
