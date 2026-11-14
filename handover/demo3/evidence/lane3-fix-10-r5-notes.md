# lane3-fix-10 round 5 notes (builder B23)

Base f3c39cf89ec989f032ea48a23cfd824b88da9c68. Result tree c494f1204dfbc8d9eee3be5b3a13e887b7f9897b (patch applied twice on fresh base worktrees and the 5 parts applied together: the same tree id each time). Patch lane3-fix-10-r5.patch (307805 bytes), parts in lane3-fix-10-r5-parts/ (each under 85 KB), hashes in raw/b23-r5-patch-sha256.txt.

## Not proven or uncertain (first)
1. Windows: every start_all.ps1 check is a TEXT PIN. PowerShell was never run here.
2. IPv6: the real-bind tests are skipped here (the kernel refuses AF_INET6). Only the class choice is tested with stand-ins. start_all with an IPv6 host has not been run end to end.
3. Mutant r4-10 (start_all.sh: the process-alive check dropped from the "up" rule, declared equivalent because the next check covers the same race) was killed by ONE test in test_reset_scripts (leadflow cases). The late-refusal file does not kill it. I did not find why. Either that stub test is timing-coupled or the mutant is not equivalent. Not resolved.
4. The first of the three final consecutive runs of run 3 stopped without a summary line (log cut off, rc line appended mid-line). I do not know why. It was run again alone: 216 passed, 10 skipped. Runs 1 and 2: 216 passed, 10 skipped each.
5. Full suite not run (narrow runs only, as ordered). Callers run (earlier tree, before the last test additions): 2485 passed, 44 skipped.

## Row 10 (ESCALATE)
Scrub not changed. Recommend KEEP as it is (secret-like names blanked always; other settings only when named; fixed advice texts exempt). Three scrub mutants are killed by tests/test_scrub_boundaries.py.

## WINDOWS-RUN-1 lines (for the coordinator, not written into WINDOWS-RUN-1.md)
- Row 5: the demo server counts as up only when fakes.log holds `fakes server ... on port N`; check on Windows, including the SO_REUSEADDR double-bind case (row 23).
- Row 7 (5b): a non-ASCII desk log line reads correctly, the script ends with the table's code, and the console code page is unchanged afterwards.

## Evidence
- fails before (pristine r4 copy): 94 failed, raw/b23-r5-fails-before.log
- lint on a clean ls-files copy: ruff check, ruff format, bandit, mypy linux, mypy win32 all rc 0 (raw/b23-r5-lint-*.log; mypy runs as the project config says, on src, tools, scripts/hubspot_probe.py)
- three runs of start/reset/ps1/round5/real_check_dry/scrub files: raw/b23-r5-start-run1..3.log
- wall-clock files: raw/b23-r5-wallclock-*.log
- mutation: raw/b23-r5-mutation.log (first full run) then rerun of the three survivors after the fixes: r4-3 killed by test_a_valid_config_with_one_non_utf8_byte_is_refused_not_read_with_replacement; r4-13 (mutant corrected to a bare Path(os.environ[...]); the first mutant was invalid) killed by test_no_path_is_read_from_setting_text_except_through_the_one_helper; r5-5 killed by test_a_formatter_that_fails_gives_its_own_line_not_the_empty_log_line. The rerun output is in this chat only, not a raw file.
- Also fixed: stale test-file name in a run_real_check.py comment.
